"""
RAG 시스템 테스트
- 사용자 질문과 관련된 상품 검색 확인
- 토큰 사용량 비교
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from chatbot.vector_store import get_vector_store
from django.contrib.auth import get_user_model
from chatbot.services import ChatbotService

User = get_user_model()

print("=" * 80)
print("RAG 시스템 테스트")
print("=" * 80)

# 벡터 스토어 가져오기
vector_store = get_vector_store()

# 테스트 질문
test_queries = [
    "안정적인 예금 상품 추천해줘",
    "금리 높은 적금 알려줘",
    "단기 예금 상품 찾아줘",
    "장기 적금 추천해주세요",
]

print("\n테스트 1: 벡터 검색 결과")
print("=" * 80)

for query in test_queries:
    print(f"\n질문: '{query}'")
    print("-" * 80)

    # 유사 상품 검색
    results = vector_store.search(query, top_k=3)

    if results:
        for i, item in enumerate(results, 1):
            product_type_kr = "예금" if item['type'] == 'deposit' else "적금"
            print(f"{i}. [{product_type_kr}] {item['fin_prdt_nm']}")
            print(f"   은행: {item['kor_co_nm']}")
            print(f"   관련도: {item['similarity_score']:.1%}")
    else:
        print("검색 결과 없음")

# 토큰 사용량 비교
print("\n\n테스트 2: 토큰 사용량 비교")
print("=" * 80)

user = User.objects.first()
if user:
    chatbot = ChatbotService(user)

    # 기존 방식 (모든 상품)
    old_products = chatbot.get_financial_products_context()
    old_text = str(old_products)
    old_tokens = len(old_text) // 4  # 대략적인 토큰 수

    # RAG 방식 (관련 상품 5개)
    rag_context = chatbot.get_rag_products_context("안정적인 예금 추천해줘", top_k=5, intent='PRODUCT')
    rag_tokens = len(rag_context) // 4

    print(f"\n기존 방식 (전체 상품):")
    print(f"  - 예금: {len(old_products['deposits'])}개")
    print(f"  - 적금: {len(old_products['savings'])}개")
    print(f"  - 예상 토큰: ~{old_tokens:,} 토큰")

    print(f"\nRAG 방식 (관련 상품만):")
    print(f"  - 검색 결과: Top-5 상품")
    print(f"  - 예상 토큰: ~{rag_tokens:,} 토큰")

    if old_tokens > 0:
        reduction = (1 - rag_tokens / old_tokens) * 100
        print(f"\n토큰 절감률: {reduction:.1f}%")

print("\n테스트 3: RAG 컨텍스트 샘플")
print("=" * 80)

rag_sample = chatbot.get_rag_products_context("금리 높은 적금", top_k=3, intent='PRODUCT')
print(rag_sample[:500] + "...")

print("\n" + "=" * 80)
print("RAG 시스템 테스트 완료!")
print("=" * 80)
