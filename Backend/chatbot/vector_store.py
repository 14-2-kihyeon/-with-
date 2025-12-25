"""
RAG 시스템용 벡터 스토어
- TF-IDF 기반 로컬 임베딩으로 예금/적금 상품 벡터화
- FAISS로 유사도 검색
"""
import os
import pickle
import numpy as np
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
from django.conf import settings
from finances.models import DepositProducts, SavingProducts

class ProductVectorStore:
    """예금/적금 상품 벡터 검색 시스템"""

    def __init__(self):
        # TF-IDF 벡터라이저 (로컬 임베딩)
        self.vectorizer = TfidfVectorizer(
            max_features=512,  # 벡터 차원
            ngram_range=(1, 2),  # 단어와 2-gram 사용
            min_df=1
        )
        self.embedding_dim = 512  # TF-IDF 벡터 차원
        self.index = None
        self.product_metadata = []  # 상품 정보 저장
        self.product_texts = []  # 상품 텍스트 저장 (재검색용)
        self.cache_file = os.path.join(settings.BASE_DIR, 'chatbot', 'vector_cache.pkl')

    def _create_product_text(self, product, product_type):
        """상품 정보를 텍스트로 변환 (임베딩용)"""
        # spcl_cnd (특별 조건) 필드 사용
        special_condition = getattr(product, 'spcl_cnd', None)
        text = f"""
        상품 타입: {product_type}
        은행: {product.kor_co_nm}
        상품명: {product.fin_prdt_nm}
        가입 방법: {product.join_way or '정보 없음'}
        특별 조건: {special_condition or '정보 없음'}
        """
        return text.strip()

    def _get_embedding(self, text):
        """
        텍스트를 벡터로 변환 (TF-IDF 사용)
        주의: build_index() 후에만 사용 가능 (vectorizer가 fit되어야 함)
        """
        try:
            vector = self.vectorizer.transform([text]).toarray()[0]
            # L2 정규화
            vector = vector / (np.linalg.norm(vector) + 1e-10)
            return vector.astype(np.float32)
        except Exception as e:
            print(f"[ERROR] 임베딩 생성 실패: {e}")
            # 실패 시 제로 벡터 반환
            return np.zeros(self.embedding_dim, dtype=np.float32)

    def build_index(self, force_rebuild=False):
        """
        벡터 인덱스 구축 (초기화 또는 재구축)
        - force_rebuild=True: 캐시 무시하고 재구축
        - force_rebuild=False: 캐시 있으면 로드
        """
        # 캐시 확인
        if not force_rebuild and os.path.exists(self.cache_file):
            print("[INFO] 캐시된 벡터 인덱스 로드 중...")
            try:
                with open(self.cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    self.index = cache_data['index']
                    self.product_metadata = cache_data['metadata']
                    self.vectorizer = cache_data['vectorizer']  # vectorizer도 로드
                    self.product_texts = cache_data.get('texts', [])
                print(f"[INFO] 캐시 로드 완료: {len(self.product_metadata)}개 상품")
                return
            except Exception as e:
                print(f"[WARNING] 캐시 로드 실패: {e}. 재구축합니다.")

        print("[INFO] 벡터 인덱스 구축 시작...")

        # 1. 모든 상품 가져오기
        deposits = DepositProducts.objects.all()
        savings = SavingProducts.objects.all()

        all_products = []

        # 예금 추가
        for deposit in deposits:
            all_products.append({
                'type': 'deposit',
                'product': deposit,
                'text': self._create_product_text(deposit, '예금')
            })

        # 적금 추가
        for saving in savings:
            all_products.append({
                'type': 'saving',
                'product': saving,
                'text': self._create_product_text(saving, '적금')
            })

        if not all_products:
            print("[WARNING] 상품 데이터가 없습니다.")
            return

        print(f"[INFO] 총 {len(all_products)}개 상품 벡터화 중...")

        # 2. TF-IDF 벡터라이저 학습
        texts = [item['text'] for item in all_products]
        self.product_texts = texts  # 저장

        print("[INFO] TF-IDF 벡터라이저 학습 중...")
        tfidf_matrix = self.vectorizer.fit_transform(texts)

        # L2 정규화
        embeddings_array = normalize(tfidf_matrix, norm='l2').toarray().astype(np.float32)
        print(f"[INFO] 임베딩 생성 완료: {embeddings_array.shape}")

        # 3. 메타데이터 저장
        self.product_metadata = []
        for item in all_products:
            product = item['product']
            self.product_metadata.append({
                'type': item['type'],
                'fin_prdt_cd': product.fin_prdt_cd,
                'kor_co_nm': product.kor_co_nm,
                'fin_prdt_nm': product.fin_prdt_nm,
                'join_way': product.join_way,
                'text': item['text']
            })

        # 4. FAISS 인덱스 생성

        # L2 거리 기반 인덱스 (유사도 검색)
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.index.add(embeddings_array)

        print(f"[INFO] FAISS 인덱스 구축 완료: {self.index.ntotal}개 벡터")

        # 5. 캐시 저장
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump({
                    'index': self.index,
                    'metadata': self.product_metadata,
                    'vectorizer': self.vectorizer,  # vectorizer 저장
                    'texts': self.product_texts
                }, f)
            print(f"[INFO] 캐시 저장 완료: {self.cache_file}")
        except Exception as e:
            print(f"[WARNING] 캐시 저장 실패: {e}")

    def search(self, query, top_k=5, product_type=None):
        """
        유사 상품 검색

        Args:
            query (str): 사용자 질문
            top_k (int): 반환할 상품 개수
            product_type (str): 'deposit', 'saving' 또는 None (모두)

        Returns:
            list: 유사 상품 메타데이터 리스트
        """
        if self.index is None or not self.product_metadata:
            print("[WARNING] 벡터 인덱스가 없습니다. build_index()를 먼저 호출하세요.")
            return []

        # 1. 쿼리 임베딩
        query_embedding = self._get_embedding(query)
        query_embedding = query_embedding.reshape(1, -1)

        # 2. 검색 (상품 타입 필터링 고려하여 더 많이 가져오기)
        search_k = top_k * 3 if product_type else top_k
        distances, indices = self.index.search(query_embedding, search_k)

        # 3. 결과 수집
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx >= len(self.product_metadata):
                continue

            metadata = self.product_metadata[idx]

            # 상품 타입 필터링
            if product_type and metadata['type'] != product_type:
                continue

            results.append({
                **metadata,
                'similarity_score': float(1 / (1 + distance))  # 거리를 유사도로 변환
            })

            if len(results) >= top_k:
                break

        return results

    def get_context_string(self, query, top_k=5, product_type=None):
        """
        검색 결과를 LLM 프롬프트용 문자열로 변환

        Args:
            query (str): 사용자 질문
            top_k (int): 반환할 상품 개수
            product_type (str): 'deposit', 'saving' 또는 None

        Returns:
            str: 프롬프트에 넣을 컨텍스트 문자열
        """
        results = self.search(query, top_k, product_type)

        if not results:
            return "검색된 상품이 없습니다."

        context = f"사용자 질문과 관련된 상위 {len(results)}개 금융 상품:\n\n"

        for i, item in enumerate(results, 1):
            product_type_kr = "예금" if item['type'] == 'deposit' else "적금"
            context += f"{i}. [{product_type_kr}] {item['fin_prdt_nm']}\n"
            context += f"   은행: {item['kor_co_nm']}\n"
            context += f"   가입방법: {item['join_way'] or '정보 없음'}\n"
            context += f"   관련도: {item['similarity_score']:.2%}\n\n"

        return context.strip()


# 전역 인스턴스 (싱글톤)
_vector_store = None

def get_vector_store():
    """벡터 스토어 싱글톤 인스턴스 가져오기"""
    global _vector_store
    if _vector_store is None:
        _vector_store = ProductVectorStore()
        # 초기화 시 인덱스 로드 또는 구축
        _vector_store.build_index(force_rebuild=False)
    return _vector_store
