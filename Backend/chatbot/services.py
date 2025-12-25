import requests
import json
import re
from django.conf import settings
from django.db.models import Max, Prefetch, Q
from finances.models import DepositProducts, SavingProducts, DepositOptions, SavingOptions
from stocks.models import Stock, DailyPrice, StockNews, FeatureDaily
from datetime import datetime, timedelta
from stocks.services.news_on_demand import ensure_stock_news
from naversearch.utils import search_and_save_news
from naversearch.models import News
from .stock_alias import find_stock_by_alias, expand_stock_search_terms
from .mode_classifier import classify_chat_mode
from .vector_store import get_vector_store  # RAG 벡터 스토어


class ChatbotService:
    """
    GMS API를 활용한 챗봇 서비스
    사용자의 투자 프로필과 금융 상품 DB를 기반으로 개인화된 추천 제공
    """

    def __init__(self, user):
        self.user = user
        self.api_url = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
        self.api_key = settings.GMS_KEY

    def get_user_profile_context(self):
        """
        사용자 투자 프로필 정보 가져오기
        """
        try:
            profile = self.user.investment_profile
            return {
                'has_profile': True,
                'risk_type': profile.risk_type,
                'risk_score': profile.risk_score,
                'age': profile.age,
                'gender': profile.gender,
                'annual_income': profile.income,
                'current_savings': profile.savings,
                'investment_goal': profile.investment_goal,
                'investment_period': profile.investment_period,
            }
        except Exception as e:
            print(f"프로필 로드 실패: {str(e)}")  # 디버깅용
            return {
                'has_profile': False,
                'message': '투자 프로필이 없습니다. 기본 정보로 안내드립니다.'
            }

    def get_financial_products_context(self):
        """
        DB에 저장된 금융 상품 정보 가져오기 (금리 정보 포함)
        사용자 프로필에 맞춰 필터링 및 정렬
        """
        from django.db.models import Max, F, Q

        # 사용자 프로필 정보
        user_profile = self.get_user_profile_context()
        user_gender = user_profile.get('gender') if user_profile.get('has_profile') else None
        user_age = user_profile.get('age') if user_profile.get('has_profile') else None
        user_period = user_profile.get('investment_period') if user_profile.get('has_profile') else None

        # 예금 상품 - 최고 금리순으로 정렬하여 가져오기
        deposits = DepositProducts.objects.annotate(
            max_rate=Max('options__intr_rate2')
        ).prefetch_related('options').filter(
            max_rate__isnull=False
        ).order_by('-max_rate')  # 최고 금리 내림차순

        deposit_data = []
        for d in deposits:
            # 성별/나이 필터링
            if not self._is_eligible_for_product(d.join_member, user_gender, user_age):
                continue

            # 각 상품의 옵션 중 최고 금리 찾기
            best_option = d.options.order_by('-intr_rate2').first()
            if best_option:
                # 사용자 투자 기간과 유사한 옵션 찾기 (있다면)
                matching_option = best_option
                if user_period:
                    period_match = d.options.filter(
                        save_trm__gte=user_period - 6,
                        save_trm__lte=user_period + 6
                    ).order_by('-intr_rate2').first()
                    if period_match:
                        matching_option = period_match

                # 예상 수익 계산 (10,000만원 기준)
                expected_profit = self._calculate_deposit_profit(
                    10000, matching_option.save_trm, matching_option.intr_rate2
                )

                deposit_data.append({
                    'type': 'deposit',
                    'bank': d.kor_co_nm,
                    'product_name': d.fin_prdt_nm,
                    'code': d.fin_prdt_cd,
                    'join_way': d.join_way,
                    'join_member': d.join_member if d.join_member else "제한없음",
                    'special_condition': d.spcl_cnd,
                    'basic_rate': f"{matching_option.intr_rate:.2f}%" if matching_option.intr_rate > 0 else "정보없음",
                    'max_rate': f"{matching_option.intr_rate2:.2f}%" if matching_option.intr_rate2 > 0 else "정보없음",
                    'period': f"{matching_option.save_trm}개월",
                    'expected_profit': f"{expected_profit:,.0f}만원",
                })

                if len(deposit_data) >= 15:
                    break

        # 적금 상품 - 최고 금리순으로 정렬하여 가져오기
        savings = SavingProducts.objects.annotate(
            max_rate=Max('options__intr_rate2')
        ).prefetch_related('options').filter(
            max_rate__isnull=False
        ).order_by('-max_rate')  # 최고 금리 내림차순

        saving_data = []
        for s in savings:
            # 성별/나이 필터링
            if not self._is_eligible_for_product(s.join_member, user_gender, user_age):
                continue

            # 각 상품의 옵션 중 최고 금리 찾기
            best_option = s.options.order_by('-intr_rate2').first()
            if best_option:
                # 사용자 투자 기간과 유사한 옵션 찾기
                matching_option = best_option
                if user_period:
                    period_match = s.options.filter(
                        save_trm__gte=user_period - 6,
                        save_trm__lte=user_period + 6
                    ).order_by('-intr_rate2').first()
                    if period_match:
                        matching_option = period_match

                # 예상 수익 계산 (매월 100만원 납입 기준)
                expected_profit = self._calculate_saving_profit(
                    100, matching_option.save_trm, matching_option.intr_rate2
                )

                saving_data.append({
                    'type': 'saving',
                    'bank': s.kor_co_nm,
                    'product_name': s.fin_prdt_nm,
                    'code': s.fin_prdt_cd,
                    'join_way': s.join_way,
                    'join_member': s.join_member if s.join_member else "제한없음",
                    'special_condition': s.spcl_cnd,
                    'basic_rate': f"{matching_option.intr_rate:.2f}%" if matching_option.intr_rate > 0 else "정보없음",
                    'max_rate': f"{matching_option.intr_rate2:.2f}%" if matching_option.intr_rate2 > 0 else "정보없음",
                    'period': f"{matching_option.save_trm}개월",
                    'saving_type': matching_option.rsrv_type_nm if matching_option.rsrv_type_nm else "정보없음",
                    'expected_profit': f"{expected_profit:,.0f}만원",
                })

                if len(saving_data) >= 15:
                    break

        return {
            'deposits': deposit_data,
            'savings': saving_data,
        }

    def get_rag_products_context(self, user_message, top_k=5, intent='PRODUCT'):
        """
        RAG 시스템을 사용하여 사용자 질문과 관련된 금융 상품만 가져오기

        Args:
            user_message: 사용자 질문
            top_k: 가져올 상품 개수 (기본 5개)
            intent: 사용자 의도 ('PRODUCT', 'STOCK' 등)

        Returns:
            str: LLM 프롬프트에 넣을 컨텍스트 문자열
        """
        if intent != 'PRODUCT':
            # PRODUCT 의도가 아니면 빈 문자열 반환
            return ""

        try:
            # 벡터 스토어 가져오기
            vector_store = get_vector_store()

            # 유사 상품 검색
            similar_products = vector_store.search(user_message, top_k=top_k)

            if not similar_products:
                return "검색된 상품이 없습니다."

            # 사용자 프로필 정보
            user_profile = self.get_user_profile_context()
            user_gender = user_profile.get('gender') if user_profile.get('has_profile') else None
            user_age = user_profile.get('age') if user_profile.get('has_profile') else None
            user_period = user_profile.get('investment_period') if user_profile.get('has_profile') else None

            # 상품 상세 정보 가져오기
            context = f"사용자 질문 '{user_message}'와 관련된 상위 {len(similar_products)}개 금융 상품:\n\n"

            for i, item in enumerate(similar_products, 1):
                product_type = item['type']
                fin_prdt_cd = item['fin_prdt_cd']

                # DB에서 상세 정보 조회
                if product_type == 'deposit':
                    product = DepositProducts.objects.filter(fin_prdt_cd=fin_prdt_cd).first()
                    if product:
                        # 최고 금리 옵션 찾기
                        best_option = product.options.order_by('-intr_rate2').first()
                        if best_option:
                            # 예상 수익 계산
                            profit = self._calculate_deposit_profit(10000, best_option.save_trm, best_option.intr_rate2)

                            context += f"{i}. [예금] {product.fin_prdt_nm}\n"
                            context += f"   은행: {product.kor_co_nm}\n"
                            context += f"   최고 금리: {best_option.intr_rate2:.2f}% ({best_option.save_trm}개월)\n"
                            context += f"   예상 수익: {profit:,.0f}만원 (1억원 기준)\n"
                            context += f"   가입 방법: {product.join_way or '정보 없음'}\n"
                            if product.spcl_cnd:
                                context += f"   특별 조건: {product.spcl_cnd[:100]}...\n"
                            context += f"   관련도: {item['similarity_score']:.1%}\n\n"
                else:
                    product = SavingProducts.objects.filter(fin_prdt_cd=fin_prdt_cd).first()
                    if product:
                        # 최고 금리 옵션 찾기
                        best_option = product.options.order_by('-intr_rate2').first()
                        if best_option:
                            # 예상 수익 계산
                            profit = self._calculate_saving_profit(100, best_option.save_trm, best_option.intr_rate2)

                            context += f"{i}. [적금] {product.fin_prdt_nm}\n"
                            context += f"   은행: {product.kor_co_nm}\n"
                            context += f"   최고 금리: {best_option.intr_rate2:.2f}% ({best_option.save_trm}개월)\n"
                            context += f"   예상 수익: {profit:,.0f}만원 (월 100만원 납입)\n"
                            context += f"   가입 방법: {product.join_way or '정보 없음'}\n"
                            if product.spcl_cnd:
                                context += f"   특별 조건: {product.spcl_cnd[:100]}...\n"
                            context += f"   관련도: {item['similarity_score']:.1%}\n\n"

            return context.strip()

        except Exception as e:
            print(f"[ERROR] RAG 검색 실패: {e}")
            # 실패 시 기존 방식 사용
            products = self.get_financial_products_context()
            # 간단한 요약만 반환
            context = "주요 금융 상품:\n\n"
            for i, d in enumerate(products['deposits'][:3], 1):
                context += f"{i}. [예금] {d['product_name']} - {d['max_rate']}\n"
            for i, s in enumerate(products['savings'][:3], len(products['deposits'][:3]) + 1):
                context += f"{i}. [적금] {s['product_name']} - {s['max_rate']}\n"
            return context

    def get_personalized_products_context(self, top_k=5):
        """
        맞춤 추천 페이지와 동일한 로직으로 상품 추천 (최대 5개)
        recommend_products 함수의 로직을 재사용하여 투자 성향 기반 가중치 적용

        Args:
            top_k: 최대 추천 개수 (기본 5개)

        Returns:
            dict: {'rag_context': str, 'recommendation_count': int}
        """
        try:
            from accounts.views import recommend_products
            from rest_framework.test import APIRequestFactory, force_authenticate

            # 가짜 API 요청 생성
            factory = APIRequestFactory()
            request = factory.get('/api/v1/accounts/recommend/')
            force_authenticate(request, user=self.user)

            # 맞춤 추천 API 호출
            response = recommend_products(request)

            if response.status_code != 200:
                return {
                    'rag_context': "추천 상품을 가져올 수 없습니다.",
                    'recommendation_count': 0
                }

            all_recommendations = response.data.get('recommendations', [])

            # 최대 top_k개만 선택 (투자 성향 기반 가중치 점수순으로 이미 정렬됨)
            recommendations = all_recommendations[:top_k]

            if not recommendations:
                return {
                    'rag_context': "추천 가능한 상품이 없습니다.",
                    'recommendation_count': 0
                }

            # AI 프롬프트 형식으로 변환
            context = f"사용자 맞춤 추천 상품 (투자 성향 기반 가중치 적용, 상위 {len(recommendations)}개):\n\n"

            for i, rec in enumerate(recommendations, 1):
                product = rec['product']
                option = rec['option']
                score = rec.get('risk_adjusted_score', 0)
                product_type = rec.get('type', 'unknown')

                # 상품 타입 표시
                type_label = "예금" if product_type == 'deposit' else "적금"

                context += f"{i}. [{type_label}] {product['fin_prdt_nm']}\n"
                context += f"   은행: {product['kor_co_nm']}\n"
                context += f"   기본금리: {option['intr_rate']:.2f}%\n"
                context += f"   최고금리: {option['intr_rate2']:.2f}%\n"
                context += f"   가입기간: {option['save_trm']}개월\n"
                context += f"   투자 성향 적합도: {score:.1f}점 / 100점\n"

                # 가입 방법
                if product.get('join_way'):
                    context += f"   가입 방법: {product['join_way']}\n"

                # 우대조건 (최대 100자)
                if product.get('spcl_cnd'):
                    spcl_cnd = product['spcl_cnd'][:100]
                    context += f"   우대조건: {spcl_cnd}...\n"

                context += "\n"

            # 투자 성향 안내 추가
            user_profile = self.get_user_profile_context()
            if user_profile.get('has_profile'):
                risk_type = user_profile.get('risk_type', '')
                context += f"\n💡 위 상품들은 '{risk_type}' 투자 성향에 맞춰 선별되었습니다.\n"

                if 'timid' in risk_type:
                    context += "   - 기본금리가 높고 우대조건이 단순한 상품 위주로 추천되었습니다.\n"
                elif 'speculative' in risk_type:
                    context += "   - 최고금리가 높은 상품 위주로 추천되었습니다.\n"
                else:
                    context += "   - 기본금리와 최고금리의 균형이 좋은 상품 위주로 추천되었습니다.\n"

            return {
                'rag_context': context.strip(),
                'recommendation_count': len(recommendations)
            }

        except Exception as e:
            print(f"[ERROR] 맞춤 추천 실패: {e}")
            import traceback
            traceback.print_exc()

            # 실패 시 빈 컨텍스트 반환
            return {
                'rag_context': "추천 상품을 가져오는 중 오류가 발생했습니다.",
                'recommendation_count': 0
            }

    def _is_eligible_for_product(self, join_member, user_gender, user_age):
        """
        사용자가 상품 가입 대상인지 확인

        Args:
            join_member: 상품의 가입 대상 (예: "만18세이상 여성고객")
            user_gender: 사용자 성별 ('M' or 'F')
            user_age: 사용자 나이

        Returns:
            bool: 가입 가능 여부
        """
        if not join_member or join_member == "제한없음":
            return True

        join_member_lower = join_member.lower()

        # 성별 체크
        if user_gender:
            if '여성' in join_member and user_gender == 'M':
                return False
            if '남성' in join_member and user_gender == 'F':
                return False

        # 나이 체크 (간단한 파싱)
        if user_age:
            import re
            # "만18세이상", "만19세", "만65세미만" 등 파싱
            # 더 구체적인 패턴을 먼저 매칭해야 함 (이상/미만이 있는 패턴 우선)
            age_patterns = [
                (r'만(\d+)세\s*이상', lambda match: user_age >= int(match.group(1))),
                (r'만(\d+)세\s*미만', lambda match: user_age < int(match.group(1))),
                (r'(\d+)세\s*이상', lambda match: user_age >= int(match.group(1))),
                (r'(\d+)세\s*미만', lambda match: user_age < int(match.group(1))),
            ]

            for pattern, check_func in age_patterns:
                match = re.search(pattern, join_member)
                if match:
                    if not check_func(match):
                        return False

        return True

    def _calculate_deposit_profit(self, principal, months, annual_rate):
        """
        예금 예상 수익 계산 (단리)

        Args:
            principal: 원금 (만원)
            months: 가입 기간 (개월)
            annual_rate: 연 금리 (%)

        Returns:
            float: 예상 수익 (만원)
        """
        return principal * (annual_rate / 100) * (months / 12)

    def _calculate_saving_profit(self, monthly_deposit, months, annual_rate):
        """
        적금 예상 수익 계산 (복리)

        Args:
            monthly_deposit: 월 납입액 (만원)
            months: 가입 기간 (개월)
            annual_rate: 연 금리 (%)

        Returns:
            float: 예상 수익 (만원)
        """
        monthly_rate = annual_rate / 100 / 12
        total_principal = monthly_deposit * months

        # 적금 복리 계산
        future_value = 0
        for i in range(months):
            future_value += monthly_deposit * ((1 + monthly_rate) ** (months - i))

        return future_value - total_principal

    def get_stock_context(self, user_profile, limit=15):
        """
        recommend_stocks API를 사용하여 주식 정보 가져오기
        오늘의 추천과 동일한 알고리즘 사용 (투자 성향, 나이, 소득, 투자 목표 등 모든 프로필 고려)
        """
        from stocks.services.recommender import recommend_stocks
        from stocks.services.reco_utils import resolve_best_as_of

        try:
            # 최근 거래일 자동 결정
            as_of = resolve_best_as_of()  # 최근 영업일 자동 계산

            # 사용자 프로필을 API 파라미터로 변환
            risk_score = user_profile.get('risk_score', 50) if user_profile.get('has_profile') else 50

            # risk_type -> risk 파라미터 변환
            if risk_score < 40:
                risk = "LOW"
            elif risk_score > 60:
                risk = "HIGH"
            else:
                risk = "MID"

            # investment_period -> horizon 파라미터 변환
            investment_period = user_profile.get('investment_period') if user_profile.get('has_profile') else None
            if investment_period:
                if investment_period <= 12:
                    horizon = "SHORT"
                elif investment_period <= 24:
                    horizon = "MID"
                else:
                    horizon = "LONG"
            else:
                horizon = "MID"

            # 전체 프로필 데이터 준비 (챗봇용)
            profile_data = None
            if user_profile.get('has_profile'):
                profile_data = {
                    'risk_type': user_profile.get('risk_type'),
                    'risk_score': user_profile.get('risk_score'),
                    'age': user_profile.get('age'),
                    'gender': user_profile.get('gender'),
                    'income': user_profile.get('annual_income'),
                    'savings': user_profile.get('current_savings'),
                    'investment_goal': user_profile.get('investment_goal'),
                    'investment_period': user_profile.get('investment_period'),
                }

            # recommend_stocks API 호출 (오늘의 추천과 동일한 로직)
            result = recommend_stocks(
                as_of=as_of,
                risk=risk,
                horizon=horizon,
                top_n=limit,
                include_news=True,
                effort="OPTIMIZE",
                user_profile=profile_data
            )

            # 결과를 챗봇 포맷으로 변환
            stock_data = []
            recommendations = result.get('recommendations', [])

            for rec in recommendations:
                try:
                    stock_info = {
                        'type': 'stock',
                        'name': rec['name'],
                        'code': rec['code'],
                        'market': rec.get('market', ''),
                    }

                    # 시세 정보
                    if rec.get('close'):
                        stock_info['current_price'] = f"{rec['close']:,}원"
                        stock_info['date'] = str(rec.get('date', as_of))

                        # 변동률 계산
                        if rec.get('open') and rec['open'] > 0:
                            change_pct = ((rec['close'] - rec['open']) / rec['open'] * 100)
                            stock_info['change'] = f"{change_pct:.2f}%"
                        else:
                            stock_info['change'] = "0%"

                    # 수익률 정보 (FeatureDaily 기반)
                    raw_data = rec.get('raw', {})
                    if raw_data:
                        stock_info['return_5d'] = f"{raw_data.get('r5_raw', 0):.2f}%" if raw_data.get('r5_raw') else "정보없음"
                        stock_info['return_20d'] = f"{raw_data.get('r20_raw', 0):.2f}%" if raw_data.get('r20_raw') else "정보없음"
                        stock_info['volatility_20d'] = f"{raw_data.get('V_raw', 0):.2f}%" if raw_data.get('V_raw') else "정보없음"

                    # 뉴스 정보
                    news_list = rec.get('news', [])
                    if news_list:
                        stock_info['recent_news'] = [
                            {
                                'title': news.get('title', ''),
                                'published': news.get('pub', '')[:10] if news.get('pub') else '',
                            }
                            for news in news_list[:3]  # 최대 3개
                        ]

                    stock_data.append(stock_info)

                except Exception as e:
                    print(f"주식 데이터 변환 오류 ({rec.get('code', 'unknown')}): {str(e)}")
                    continue

            print(f"[챗봇 주식 컨텍스트] recommend_stocks API 사용 - {len(stock_data)}개 종목 반환 (risk={risk}, horizon={horizon})")
            return stock_data

        except Exception as e:
            print(f"[ERROR] recommend_stocks API 호출 실패: {e}")
            import traceback
            traceback.print_exc()

            # 실패 시 빈 리스트 반환 (챗봇이 계속 작동하도록)
            return []

    def analyze_user_question(self, user_message):
        """
        사용자 질문에서 종목명, 날짜, 뉴스 키워드 등을 추출
        """
        print(f"[DEBUG] analyze_user_question 시작 - 사용자 메시지: '{user_message}'")

        result = {
            'stock_names': [],
            'dates': [],
            'is_specific_query': False,
            'is_news_query': False,
            'news_keywords': [],
            'intent': 'UNKNOWN',  # STOCK, PRODUCT, NEWS, GENERAL
            'specific_product_name': None,  # 특정 상품명이 언급된 경우
        }

        # ===== 1단계: Alias 기반 종목명 추출 =====
        alias_matched_stocks = find_stock_by_alias(user_message)
        if alias_matched_stocks:
            print(f"[DEBUG] Alias 매칭 성공: {alias_matched_stocks}")
            # Alias로 찾은 종목명을 DB에서 검증
            for stock_name in alias_matched_stocks:
                stock = Stock.objects.filter(name__icontains=stock_name).first()
                if stock:
                    result['stock_names'].append(stock.name)
                    result['is_specific_query'] = True
                    print(f"[DEBUG] DB 검증 완료: {stock.name}")

        # ===== 2단계: 추가 DB 전체 검색 (Alias에 없는 종목 대비) =====
        if not result['stock_names']:
            stocks = Stock.objects.all()
            for stock in stocks:
                # 종목명 또는 코드가 정확히 포함되어 있는지 확인
                if stock.name in user_message or stock.code in user_message:
                    result['stock_names'].append(stock.name)
                    result['is_specific_query'] = True
                    print(f"[DEBUG] DB 직접 매칭: {stock.name}")

        # 날짜 패턴 추출
        date_patterns = [
            r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일',  # 2025년 12월 17일
            r'(\d{1,2})월\s*(\d{1,2})일',  # 12월 17일
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2025-12-17
            r'(\d{1,2})/(\d{1,2})',  # 12/17
        ]

        current_year = datetime.now().year

        for pattern in date_patterns:
            matches = re.findall(pattern, user_message)
            for match in matches:
                try:
                    if len(match) == 3:
                        if len(match[0]) == 4:  # 연도 포함
                            date = datetime(int(match[0]), int(match[1]), int(match[2])).date()
                        else:  # 월일만
                            date = datetime(current_year, int(match[0]), int(match[1])).date()
                    elif len(match) == 2:  # 월/일
                        date = datetime(current_year, int(match[0]), int(match[1])).date()

                    result['dates'].append(date)
                    result['is_specific_query'] = True
                except:
                    continue

        # 상대적 날짜 표현
        if '오늘' in user_message:
            result['dates'].append(datetime.now().date())
            result['is_specific_query'] = True
        elif '어제' in user_message:
            result['dates'].append((datetime.now() - timedelta(days=1)).date())
            result['is_specific_query'] = True

        # 뉴스 관련 키워드 탐지
        news_keywords = ['뉴스', '기사', '소식', '보도', '언론', '최근 소식', '최신 뉴스', '오늘 뉴스']
        for keyword in news_keywords:
            if keyword in user_message:
                result['is_news_query'] = True
                print(f"[DEBUG] 뉴스 키워드 감지: '{keyword}'")

                # 뉴스 검색어 추출 (종목명이 있으면 종목 뉴스, 없으면 일반 키워드 추출)
                if not result['stock_names']:
                    # 일반 뉴스 키워드 추출 (예: "경제 뉴스", "삼성 뉴스")
                    words = user_message.replace(keyword, '').strip().split()
                    # 불용어 제거
                    stopwords = {'알려줘', '알려주세요', '보여줘', '보여주세요', '찾아줘', '검색', '에', '의', '관련', '대한', '최근', '최신', '오늘'}
                    filtered_words = [w for w in words if w not in stopwords and len(w) > 1]
                    if filtered_words:
                        result['news_keywords'].extend(filtered_words[:3])  # 최대 3개
                        print(f"[DEBUG] 추출된 뉴스 검색 키워드: {filtered_words[:3]}")
                else:
                    print(f"[DEBUG] 종목명이 있어 종목 뉴스 수집 모드")
                break

        # ===== 특정 상품명 추출 (예금/적금) =====
        # 사용자가 특정 상품명을 언급했는지 확인
        from finances.models import DepositProducts, SavingProducts

        # 예금 상품명 검사
        all_deposits = DepositProducts.objects.all()
        for product in all_deposits:
            if product.fin_prdt_nm and product.fin_prdt_nm in user_message:
                result['specific_product_name'] = product.fin_prdt_nm
                result['is_specific_query'] = True
                print(f"[DEBUG] 특정 예금 상품 감지: {product.fin_prdt_nm}")
                break

        # 적금 상품명 검사 (예금에서 찾지 못한 경우)
        if not result['specific_product_name']:
            all_savings = SavingProducts.objects.all()
            for product in all_savings:
                if product.fin_prdt_nm and product.fin_prdt_nm in user_message:
                    result['specific_product_name'] = product.fin_prdt_nm
                    result['is_specific_query'] = True
                    print(f"[DEBUG] 특정 적금 상품 감지: {product.fin_prdt_nm}")
                    break

        # ===== 의도 분류 (INTENT CLASSIFICATION) - 개선된 점수 기반 시스템 =====
        # 핵심 주식 키워드 (명확하게 주식만을 의미)
        stock_core_keywords = ['주가', '시세', '종목', '주식', '매수', '매도', '차트', '상장', '코스피', '코스닥', '거래량']
        # 핵심 예금/적금 키워드 (명확하게 금융상품만을 의미)
        product_core_keywords = ['예금', '적금', '금리', '이자', '은행', '저축', '원금', '만기', '가입']
        # 안정성 관련 키워드 (예금/적금 선호 신호)
        stability_keywords = ['안정', '안전', '보장', '확정', '원금보장']

        # 점수 계산
        stock_score = 0
        product_score = 0

        # 1. 종목명이 추출되었으면 주식 의도 강력 추정
        if result['stock_names']:
            stock_score += 10
            print(f"[DEBUG] 종목명 감지 → stock_score +10")

        # 2. 특정 상품명이 추출되었으면 금융상품 의도 강력 추정
        if result['specific_product_name']:
            product_score += 10
            print(f"[DEBUG] 특정 상품명 감지 → product_score +10")

        # 3. 핵심 키워드 점수 (각 키워드당 3점)
        for kw in stock_core_keywords:
            if kw in user_message:
                stock_score += 3
                print(f"[DEBUG] 주식 핵심 키워드 '{kw}' 감지 → stock_score +3")

        for kw in product_core_keywords:
            if kw in user_message:
                product_score += 3
                print(f"[DEBUG] 금융상품 핵심 키워드 '{kw}' 감지 → product_score +3")

        # 4. 안정성 키워드는 예금/적금에 강력한 가산점 (각 5점)
        for kw in stability_keywords:
            if kw in user_message:
                product_score += 5
                print(f"[DEBUG] 안정성 키워드 '{kw}' 감지 → product_score +5")

        # 5. 애매한 키워드 ('추천', '전망', '분석' 등)는 점수에 포함하지 않음
        #    → 다른 명확한 키워드들로만 판단

        print(f"[DEBUG] 최종 점수 - stock_score: {stock_score}, product_score: {product_score}")

        # 의도 결정 로직
        if stock_score > product_score:
            result['intent'] = 'STOCK'
            print(f"[DEBUG] 의도 분류: STOCK (점수 우위)")
        elif product_score > stock_score:
            result['intent'] = 'PRODUCT'
            print(f"[DEBUG] 의도 분류: PRODUCT (점수 우위)")
        elif result['is_news_query']:
            result['intent'] = 'NEWS'
            print(f"[DEBUG] 의도 분류: NEWS (뉴스 키워드 우선)")
        else:
            # 동점이거나 둘 다 0점인 경우 → 안전하게 PRODUCT 기본값 (예금/적금이 더 안전)
            result['intent'] = 'PRODUCT'
            print(f"[DEBUG] 의도 분류: PRODUCT (기본값 - 동점 또는 키워드 없음)")

        print(f"[DEBUG] 최종 분석 결과: {result}")
        return result

    def get_specific_stock_data(self, stock_names, dates=None):
        """
        특정 종목의 특정 날짜 데이터 조회
        """
        if not stock_names:
            return ""

        result_text = "\n=== 질문하신 종목의 상세 정보 ===\n"

        for stock_name in stock_names:
            try:
                stock = Stock.objects.filter(name__icontains=stock_name).first()
                if not stock:
                    continue

                result_text += f"\n[{stock.name} ({stock.code})]\n"

                # 날짜가 지정되지 않으면 최근 거래일 사용
                if not dates:
                    latest_date = DailyPrice.objects.filter(stock=stock).aggregate(Max('date'))['date__max']
                    if latest_date:
                        dates = [latest_date]

                # 각 날짜별 데이터 조회
                for target_date in dates:
                    price_data = DailyPrice.objects.filter(stock=stock, date=target_date).first()

                    if price_data:
                        result_text += f"[{target_date} 기준]\n"
                        result_text += f"  - 종가: {price_data.close:,}원\n"
                        result_text += f"  - 시가: {price_data.open:,}원\n"
                        result_text += f"  - 고가: {price_data.high:,}원\n"
                        result_text += f"  - 저가: {price_data.low:,}원\n"
                        result_text += f"  - 거래량: {price_data.volume:,}주\n"

                        # 전일 대비 계산
                        prev_date = target_date - timedelta(days=1)
                        prev_price = DailyPrice.objects.filter(
                            stock=stock,
                            date__lt=target_date
                        ).order_by('-date').first()

                        if prev_price:
                            change = price_data.close - prev_price.close
                            change_pct = (change / prev_price.close * 100)
                            result_text += f"  - 전일 대비: {change:+,}원 ({change_pct:+.2f}%)\n"
                    else:
                        result_text += f"[{target_date}] 해당 날짜의 시세 데이터가 없습니다. (주말/휴장일 가능성)\n"

                # 최근 수익률 정보
                latest_feature = FeatureDaily.objects.filter(stock=stock).order_by('-date').first()
                if latest_feature:
                    result_text += f"\n[최근 수익률 분석]\n"
                    if latest_feature.r5:
                        result_text += f"  - 5일 수익률: {latest_feature.r5:.2f}%\n"
                    if latest_feature.r20:
                        result_text += f"  - 20일 수익률: {latest_feature.r20:.2f}%\n"
                    if latest_feature.vol20:
                        result_text += f"  - 20일 변동성: {latest_feature.vol20:.2f}%\n"

                # 최근 뉴스
                recent_news = StockNews.objects.filter(stock=stock).order_by('-published_at')[:3]
                if recent_news:
                    result_text += f"\n[최근 뉴스]\n"
                    for news in recent_news:
                        result_text += f"  - [{news.published_at.strftime('%Y-%m-%d')}] {news.title}\n"

                result_text += "\n"

            except Exception as e:
                print(f"특정 종목 데이터 조회 오류 ({stock_name}): {str(e)}")
                continue

        return result_text

    def fetch_stock_news_on_demand(self, stock_names):
        """
        특정 종목의 최신 뉴스를 자동으로 수집하여 DB에 저장
        """
        news_data = []

        for stock_name in stock_names:
            try:
                print(f"[DEBUG] 종목 검색 중: '{stock_name}'")
                stock = Stock.objects.filter(name__icontains=stock_name).first()
                if not stock:
                    print(f"[WARNING] DB에서 종목을 찾을 수 없음: '{stock_name}'")
                    # 종목을 못 찾아도 계속 진행
                    continue

                print(f"[DEBUG] 종목 찾음: {stock.name} ({stock.code})")

                # 최신 뉴스 자동 수집 (ensure_stock_news 활용)
                today = datetime.now().date()
                print(f"[DEBUG] ensure_stock_news 호출 시작 - stock: {stock.name}, date: {today}")

                fetch_result = ensure_stock_news(
                    stock=stock,
                    as_of=today,
                    lookback_days=7,  # 최근 7일 이내 뉴스만 수집
                    display=15,  # 15개 뉴스
                    min_days_for_fetch=1  # 1일 이내 데이터 없으면 새로 수집
                )

                print(f"[DEBUG] ensure_stock_news 결과: {fetch_result}")

                # 수집된 최신 뉴스 가져오기
                recent_news = StockNews.objects.filter(
                    stock=stock
                ).order_by('-published_at')[:5]

                print(f"[DEBUG] DB에서 조회된 뉴스 개수: {recent_news.count()}")

                if recent_news:
                    news_data.append({
                        'stock_name': stock.name,
                        'stock_code': stock.code,
                        'fetch_info': fetch_result,
                        'news': [
                            {
                                'title': news.title,
                                'description': news.description,
                                'published': news.published_at.strftime('%Y-%m-%d %H:%M'),
                                'link': news.link,
                            }
                            for news in recent_news
                        ]
                    })
                    print(f"[DEBUG] 뉴스 데이터 추가 완료: {stock.name}")
                else:
                    print(f"[WARNING] DB에 뉴스가 없음: {stock.name}")

            except Exception as e:
                print(f"[ERROR] 종목 뉴스 수집 오류 ({stock_name}): {str(e)}")
                import traceback
                traceback.print_exc()
                continue

        print(f"[DEBUG] 최종 수집된 종목 뉴스 개수: {len(news_data)}")
        return news_data

    def fetch_general_news_on_demand(self, keywords):
        """
        일반 키워드 뉴스를 자동으로 수집하여 DB에 저장
        """
        news_data = []

        for keyword in keywords:
            try:
                print(f"[DEBUG] 일반 뉴스 검색 키워드: '{keyword}'")

                # 네이버 뉴스 검색 및 저장
                saved_count = search_and_save_news(query=keyword, display=10)
                print(f"[DEBUG] 네이버 API로부터 {saved_count}건 저장됨")

                # 방금 저장된 뉴스 가져오기 (제목에 키워드 포함)
                recent_news = News.objects.filter(
                    title__icontains=keyword
                ).order_by('-id')[:5]

                print(f"[DEBUG] DB에서 '{keyword}' 관련 뉴스 {recent_news.count()}건 조회됨")

                if recent_news:
                    news_data.append({
                        'keyword': keyword,
                        'saved_count': saved_count,
                        'news': [
                            {
                                'title': news.title,
                                'description': news.description,
                                'published': news.pub_date,
                                'link': news.link,
                            }
                            for news in recent_news
                        ]
                    })
                    print(f"[DEBUG] '{keyword}' 뉴스 데이터 추가 완료")
                else:
                    print(f"[WARNING] '{keyword}' 관련 뉴스 없음")

            except Exception as e:
                print(f"[ERROR] 일반 뉴스 수집 오류 ({keyword}): {str(e)}")
                import traceback
                traceback.print_exc()
                continue

        print(f"[DEBUG] 최종 수집된 일반 뉴스 키워드 개수: {len(news_data)}")
        return news_data

    def _format_deposit_products(self, deposits):
        """예금 상품 정보를 AI가 읽기 쉽게 포맷팅"""
        if not deposits:
            return "=== 예금 상품 ===\n현재 등록된 예금 상품이 없습니다."

        text = f"=== 예금 상품 (총 {len(deposits)}개) ===\n"
        for i, d in enumerate(deposits[:10], 1):  # 상위 10개만
            text += f"{i}. {d['bank']} - {d['product_name']}\n"
            text += f"   - 기본금리: {d['basic_rate']}, 최고금리: {d['max_rate']}\n"
            text += f"   - 가입기간: {d['period']}\n"
            if d.get('join_way'):
                text += f"   - 가입방법: {d['join_way']}\n"
            if d.get('special_condition'):
                text += f"   - 특이사항: {d['special_condition']}\n"
            text += "\n"
        return text

    def _format_saving_products(self, savings):
        """적금 상품 정보를 AI가 읽기 쉽게 포맷팅"""
        if not savings:
            return "=== 적금 상품 ===\n현재 등록된 적금 상품이 없습니다."

        text = f"=== 적금 상품 (총 {len(savings)}개) ===\n"
        for i, s in enumerate(savings[:10], 1):  # 상위 10개만
            text += f"{i}. {s['bank']} - {s['product_name']}\n"
            text += f"   - 기본금리: {s['basic_rate']}, 최고금리: {s['max_rate']}\n"
            text += f"   - 가입기간: {s['period']}\n"
            text += f"   - 적금유형: {s['saving_type']}\n"
            if s.get('join_way'):
                text += f"   - 가입방법: {s['join_way']}\n"
            if s.get('special_condition'):
                text += f"   - 특이사항: {s['special_condition']}\n"
            text += "\n"
        return text

    def _format_stock_data(self, stocks):
        """주식 정보를 AI가 읽기 쉽게 포맷팅"""
        if not stocks:
            return "=== 주식 종목 ===\n현재 등록된 주식 데이터가 없습니다."

        text = f"=== 주식 종목 (총 {len(stocks)}개, 사용자 성향 필터링 적용) ===\n"
        for i, st in enumerate(stocks[:10], 1):  # 상위 10개만
            text += f"{i}. {st['name']} ({st['code']}) - {st['market']}\n"
            if st.get('current_price'):
                text += f"   - 현재가: {st['current_price']} (기준일: {st['date']})\n"
                text += f"   - 당일변동: {st['change']}\n"
            if st.get('return_5d'):
                text += f"   - 5일 수익률: {st['return_5d']}, 20일 수익률: {st['return_20d']}\n"
                text += f"   - 20일 변동성: {st['volatility_20d']}\n"
            if st.get('recent_news'):
                text += f"   - 최근 뉴스:\n"
                for news in st['recent_news'][:2]:  # 뉴스 2개만
                    text += f"     · [{news['published']}] {news['title']}\n"
            # DART 전자공시 링크 추가
            dart_link = self.generate_dart_link(st['name'])
            text += f"   - DART 전자공시: {dart_link}\n"
            text += "\n"
        return text

    def build_system_prompt(self, user_profile, products, stocks, specific_data="", fresh_news="", intent="GENERAL", mode="SERVICE", question_analysis=None):
        """
        GMS API에 전달할 시스템 프롬프트 생성
        specific_data: 사용자 질문에 대한 동적 조회 데이터
        fresh_news: 실시간으로 수집한 최신 뉴스 데이터
        intent: 사용자 의도 (STOCK, PRODUCT, NEWS, GENERAL)
        mode: 챗봇 모드 (CHAT, SERVICE)
        question_analysis: 질문 분석 결과 (특정 상품/종목 정보 포함)
        """
        # ===== CHAT 모드: 간단한 대화 전용 프롬프트 =====
        if mode == "CHAT":
            return """당신은 Finflow 금융 투자 플랫폼의 AI 어시스턴트입니다.

역할:
- 사용자의 인사, 감사, 일상적인 대화에 친절하고 간결하게 응답합니다.
- 금융 상품이나 주식을 추천하지 마세요.
- 짧고 자연스러운 대화체로 답변하세요 (1~3문장).

답변 규칙:
1. 최대 2~3문장으로 짧게 답변
2. 상품/종목/금리 등 구체적인 정보는 언급하지 않음
3. 사용자가 금융 서비스를 이용하고 싶다면 구체적인 질문을 하도록 안내
4. 친근하고 자연스러운 어조 사용

예시:
- 입력: "안녕"
  출력: "안녕하세요! Finflow AI 상담사입니다. 무엇을 도와드릴까요?"

- 입력: "고마워"
  출력: "천만에요! 언제든지 도와드릴게요 😊"

- 입력: "날씨 어때?"
  출력: "저는 금융 상담 AI라 날씨 정보는 잘 모르겠어요. 대신 금융 관련 질문이 있으시면 언제든 물어보세요!"
"""

        # ===== SERVICE 모드: 기존 상세 프롬프트 =====
        profile_text = ""
        if user_profile['has_profile']:
            # 성별 변환
            gender_text = "남성" if user_profile['gender'] == 'M' else "여성"

            # 위험 성향 한글명 추출
            risk_type_display = user_profile['risk_type']
            if risk_type_display:
                if 'timid' in risk_type_display:
                    risk_name = '에겐소심형 (안정형)'
                elif 'speculative' in risk_type_display:
                    risk_name = '테토투기형 (공격형)'
                else:
                    risk_name = '보통형 (중립형)'
            else:
                risk_name = '미설정'

            # DecimalField를 정수로 변환하여 포맷팅
            income_val = int(user_profile['annual_income']) if user_profile['annual_income'] else 0
            savings_val = int(user_profile['current_savings']) if user_profile['current_savings'] else 0

            profile_text = f"""
사용자 투자 프로필:
- 위험 성향: {risk_name} (점수: {user_profile['risk_score']}점)
- 연령: {user_profile['age']}세
- 성별: {gender_text}
- 연 소득: {income_val:,}만원
- 현재 저축액: {savings_val:,}만원
- 투자 목표: {user_profile['investment_goal']}
- 투자 기간: {user_profile['investment_period']}개월
"""
        else:
            profile_text = user_profile['message']

        # 상품 정보 상세 포맷팅
        # RAG 모드인 경우 이미 포맷된 컨텍스트 사용
        if 'rag_context' in products:
            # RAG 컨텍스트 사용 (이미 포맷된 문자열)
            product_context = products['rag_context']
            deposit_details = ""
            saving_details = ""
        else:
            # 기존 방식 (전체 상품 목록)
            deposit_details = self._format_deposit_products(products['deposits'])
            saving_details = self._format_saving_products(products['savings'])
            product_context = deposit_details + "\n\n" + saving_details

        stock_details = self._format_stock_data(stocks)

        # 데이터 업데이트 날짜
        today = datetime.now().strftime('%Y년 %m월 %d일')

        # 동적 조회 데이터가 있으면 강조 (사용자 친화적 문구로 변경)
        specific_section = ""
        if specific_data:
            specific_section = f"""
=== 요청하신 종목의 최신 정보 ({today} 기준) ===
{specific_data}
⚠️ 위 정보를 기반으로 정확하게 답변하세요.
"""

        # 최신 뉴스 데이터가 있으면 최우선 강조 (사용자 친화적 문구로 변경)
        news_section = ""
        if fresh_news:
            news_section = f"""
=== 최신 뉴스 ({today} 기준) ===
{fresh_news}
⚠️ 이 뉴스는 방금 수집한 최신 정보입니다. 반드시 이 데이터를 기반으로 답변하세요.
"""

        # ===== 의도별 맞춤 프롬프트 생성 =====
        if intent == 'STOCK':
            # 주식 질문: 주식 데이터만 포함, 예금/적금 제외
            # 특정 종목 질문인지 확인
            specific_stock_instruction = ""
            if question_analysis and question_analysis.get('stock_names'):
                stock_list = ", ".join(question_analysis['stock_names'])
                specific_stock_instruction = f"""
⚠️⚠️⚠️ 최우선 지침 ⚠️⚠️⚠️
사용자가 "{stock_list}" 종목에 대해 질문했습니다.
- 이 종목에 대해서만 설명하세요.
- **절대로** 다른 종목을 추천하거나 언급하지 마세요.
- 이 종목이 사용자의 프로필(위험 성향: {user_profile.get('risk_type', '미설정')}, 나이: {user_profile.get('age', '미설정')}세)에 적합한지 평가하세요.
- 위험 성향이 안정형인데 고위험 종목이라면 명확히 경고하세요.
- 적합하지 않다면 그 이유를 설명하되, 다른 종목을 추천하지 마세요.
"""

            data_section = f"""
{news_section}
{specific_section}

{stock_details}

{specific_stock_instruction}

⚠️ 중요 지침:
1. 사용자는 주식에 대해 질문하고 있습니다.
2. **절대로** 예금이나 적금 상품을 추천하지 마세요.
3. 위에 나열된 주식 정보만 사용하여 답변하세요.
4. 주식 투자에는 위험이 있음을 반드시 안내하세요.

⚠️ 답변 구조 (반드시 이 순서로 작성):
1. **요약**: 현재 시세, 수익률, 변동성, 최근 뉴스를 간단히 요약 (3-5줄)
2. **해석**: 사용자의 투자 프로필(위험 성향, 나이, 투자 목표, 투자 기간)을 고려한 적합성 평가 (2-3줄)
   - 적합한 경우: 그 이유를 명확히 설명
   - 부적합한 경우: 명확한 주의사항과 리스크 경고
3. **마무리**: "더 궁금한 점이 있으시면 말씀해주세요." 등으로 자연스럽게 대화를 마무리 (1줄)
"""
        elif intent == 'PRODUCT':
            # 금융상품 질문: 예금/적금만 포함, 주식 제외
            # 특정 상품 질문인지 확인
            specific_product_instruction = ""
            if question_analysis and question_analysis.get('specific_product_name'):
                specific_product_instruction = f"""
⚠️⚠️⚠️ 최우선 지침 ⚠️⚠️⚠️
사용자가 "{question_analysis['specific_product_name']}" 상품에 대해 질문했습니다.
- 이 상품에 대해서만 설명하세요.
- **절대로** 다른 상품을 추천하거나 언급하지 마세요.
- 이 상품이 사용자의 프로필(투자 기간: {user_profile.get('investment_period', '미설정')}개월, 목표: {user_profile.get('investment_goal', '미설정')})에 적합한지 평가하세요.
- 적합하지 않다면 그 이유를 설명하되, 다른 상품을 추천하지 마세요.
"""

            data_section = f"""
{product_context}

{specific_product_instruction}

⚠️ 중요 지침:
1. 사용자는 예금/적금 상품에 대해 질문하고 있습니다.
2. **절대로** 주식을 추천하지 마세요.
3. 위에 나열된 예금/적금 상품 중에서만 답변하세요.

⚠️ 답변 구조 (반드시 이 순서로 작성):
1. **요약**: 추천 상품의 금리, 가입 기간, 특징을 간단히 요약 (2-4줄)
2. **해석**: 사용자의 투자 프로필(투자 기간, 목표, 소득, 위험 성향)을 고려한 적합성 평가 (2-3줄)
   - 적합한 경우: 그 이유를 명확히 설명
   - 부적합한 경우: 명확한 주의사항
3. **마무리**: "더 궁금한 점이 있으시면 말씀해주세요." 등으로 자연스럽게 대화를 마무리 (1줄)
"""
        else:
            # 일반 질문 또는 뉴스: 모든 데이터 포함
            data_section = f"""
{news_section}
{specific_section}

{product_context}

{stock_details}
"""

        system_prompt = f"""당신은 Finflow 금융 투자 플랫폼의 AI 재무 상담사입니다.

{profile_text}

=== 데이터 기준일: {today} ===
아래 제공된 데이터는 실제 금융 상품 및 주식 정보입니다.
반드시 이 데이터를 우선적으로 활용하여 답변해주세요.

{data_section}

역할:
1. 위의 실제 DB 데이터를 기반으로 사용자의 투자 성향과 재무 상태에 맞는 상품을 추천합니다.
2. 예금, 적금, 주식 등 다양한 옵션을 제시하되, 반드시 위에 나열된 상품 중에서 선택합니다.
3. 친절하고 전문적인 어조로 답변합니다.
4. 금리, 수익률 등 구체적인 수치를 언급하여 신뢰성을 높입니다.

답변 형식:
- 사용자의 질문에 대한 친절한 답변을 먼저 제공합니다.
- 추천 상품이 있다면, 위 DB 데이터에서 구체적인 상품명, 은행명, 금리를 인용합니다.
  예: "우리은행의 'WON플러스예금'은 최고 3.50% 금리를 제공하며..."
- 답변은 반드시 자연스러운 마무리 문장으로 끝내세요.
  예: "더 궁금한 점이 있으시면 말씀해주세요.", "투자 결정에 도움이 되셨으면 좋겠습니다."
- 주식을 추천할 경우, 최근 수익률과 뉴스를 함께 언급하고, 반드시 DART 전자공시 링크를 제공합니다.
  예: "삼성전자는 최근 20일간 5.2% 상승했으며, 최근 AI 반도체 관련 긍정적 뉴스가 있습니다.
       더 자세한 기업 정보는 전자공시(DART)에서 확인하실 수 있습니다: [DART 링크]"
- 주식 추천 시 DART 링크는 위 데이터에 제공된 링크를 그대로 사용하세요.
- 각 상품의 특징과 사용자에게 적합한 이유를 쉽게 풀어서 설명합니다.
- 상품 코드나 기술적인 정보는 언급하지 않습니다.

주의사항:
- 투자에는 위험이 따를 수 있다는 점을 항상 안내합니다.
- 확정된 수익을 보장하지 않습니다.
- 사용자의 투자 성향을 존중하며 무리한 투자를 권장하지 않습니다.
- JSON 형식이나 구조화된 데이터 형식으로 답변하지 마세요.
- 자연스럽고 친근한 대화체로 답변하세요.
- 위에 제공되지 않은 상품은 추천하지 마세요.
"""

        return system_prompt

    def chat(self, user_message, chat_history=None):
        """
        GMS API를 호출하여 AI 응답 생성
        """
        try:
            # 0. 챗봇 모드 분류 (최우선)
            chat_mode = classify_chat_mode(user_message)
            print(f"[MODE] 챗봇 모드: {chat_mode}")

            # CHAT_MODE 가드: 단순 대화는 DB 조회 생략
            if chat_mode == 'CHAT':
                print(f"[MODE] CHAT 모드 - 간단한 대화 처리")

                # 최소한의 프롬프트로 빠르게 응답
                system_prompt = self.build_system_prompt(
                    user_profile={'has_profile': False},
                    products={'deposits': [], 'savings': []},
                    stocks=[],
                    mode="CHAT"
                )

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]

                # GMS API 호출
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }

                payload = {
                    "model": "gpt-5-mini",
                    "messages": messages,
                    "max_completion_tokens": 1000,  # gpt-5-mini는 reasoning 토큰 포함
                }

                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )

                response.raise_for_status()
                result = response.json()
                ai_response = result['choices'][0]['message']['content']

                # CHAT 모드 후처리
                ai_response = self.post_process_response(ai_response, mode='CHAT')

                return {
                    'success': True,
                    'response': ai_response,
                    'recommended_products': None,  # CHAT 모드는 추천 없음
                }

            # ===== SERVICE 모드: 기존 로직 =====
            # 1. 사용자 질문 분석
            question_analysis = self.analyze_user_question(user_message)
            print(f"질문 분석: {question_analysis}")  # 디버깅

            # 2. 사용자 프로필 및 기본 상품 정보 가져오기
            user_profile = self.get_user_profile_context()

            # 맞춤 추천 시스템 사용: 투자 성향 기반 가중치 적용
            intent = question_analysis.get('intent', 'GENERAL')
            if intent == 'PRODUCT':
                print("[맞춤 추천] 투자 성향 기반 상품 선별 중...")
                personalized_result = self.get_personalized_products_context(top_k=5)
                # products를 문자열 형태로 저장 (기존 dict 형식 대신)
                products = {'rag_context': personalized_result['rag_context']}
                print(f"[맞춤 추천] 선별 완료: {personalized_result['recommendation_count']}개 상품")
            else:
                # STOCK이나 다른 의도는 기존 방식 사용
                products = self.get_financial_products_context()
                print(f"예금 상품: {len(products['deposits'])}개, 적금 상품: {len(products['savings'])}개")

            stocks = self.get_stock_context(user_profile)

            print(f"프로필 로드 성공: {user_profile.get('has_profile')}")  # 디버깅
            print(f"주식 종목: {len(stocks)}개")

            # 3. 특정 종목/날짜 질문이면 동적 데이터 조회
            specific_data = ""
            if question_analysis['is_specific_query'] and question_analysis['stock_names']:
                print(f"특정 종목 조회: {question_analysis['stock_names']}")
                specific_data = self.get_specific_stock_data(
                    question_analysis['stock_names'],
                    question_analysis['dates'] if question_analysis['dates'] else None
                )

            # 4. 뉴스 자동 수집 (뉴스 키워드 또는 주식 종목명이 있으면 자동 실행)
            fresh_news_data = ""

            # 종목명이 있으면 자동으로 종목 뉴스 수집 (뉴스 키워드 없어도 실행)
            if question_analysis['stock_names']:
                print(f"[자동 뉴스 수집] 종목 감지: {question_analysis['stock_names']}")
                stock_news = self.fetch_stock_news_on_demand(question_analysis['stock_names'])
                if stock_news:
                    fresh_news_data += "\n=== [최신 수집] 종목별 뉴스 ===\n"
                    for stock_data in stock_news:
                        fresh_news_data += f"\n[{stock_data['stock_name']} ({stock_data['stock_code']})] - {stock_data['fetch_info'].get('reason', '수집 완료')}\n"
                        for i, news in enumerate(stock_data['news'], 1):
                            fresh_news_data += f"{i}. [{news['published']}] {news['title']}\n"
                            if news.get('description'):
                                fresh_news_data += f"   {news['description']}\n"
                        fresh_news_data += "\n"

            # 뉴스 키워드가 있으면 일반 뉴스 수집 (종목 없이 뉴스만 요청한 경우)
            elif question_analysis['is_news_query'] and question_analysis['news_keywords']:
                print(f"[자동 뉴스 수집] 일반 뉴스 검색: {question_analysis['news_keywords']}")
                general_news = self.fetch_general_news_on_demand(question_analysis['news_keywords'])
                if general_news:
                    fresh_news_data += "\n=== [최신 수집] 검색 뉴스 ===\n"
                    for keyword_data in general_news:
                        fresh_news_data += f"\n['{keyword_data['keyword']}' 검색 결과] - {keyword_data['saved_count']}건 새로 저장됨\n"
                        for i, news in enumerate(keyword_data['news'], 1):
                            fresh_news_data += f"{i}. [{news['published']}] {news['title']}\n"
                            if news.get('description'):
                                fresh_news_data += f"   {news['description']}\n"
                        fresh_news_data += "\n"

            # 5. 시스템 프롬프트 생성 (동적 데이터 + 최신 뉴스 + 의도 + 모드 + 질문 분석 포함)
            system_prompt = self.build_system_prompt(
                user_profile,
                products,
                stocks,
                specific_data,
                fresh_news_data,
                intent=question_analysis.get('intent', 'GENERAL'),
                mode="SERVICE",
                question_analysis=question_analysis
            )

            # 메시지 구성
            messages = [
                {"role": "system", "content": system_prompt},
            ]

            # 대화 히스토리 추가 (선택사항)
            if chat_history:
                # QuerySet을 리스트로 변환한 후 최근 3개만 사용
                history_list = list(chat_history)
                for msg in history_list[:3]:  # 이미 역순으로 정렬되어 있으므로 처음 3개가 최근 3개
                    messages.append({"role": "user", "content": msg.user_message})
                    messages.append({"role": "assistant", "content": msg.ai_response})

            # 현재 사용자 메시지 추가
            messages.append({"role": "user", "content": user_message})

            # GMS API 호출
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            payload = {
                "model": "gpt-5-mini",
                "messages": messages,
                "max_completion_tokens": 5000,  # gpt-5-mini는 reasoning에 많은 토큰을 사용하므로 넉넉하게
            }

            print(f"GMS API 호출 시작...")  # 디버깅

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )

            print(f"GMS API 응답 상태: {response.status_code}")  # 디버깅

            response.raise_for_status()

            result = response.json()
            ai_response = result['choices'][0]['message']['content']

            print(f"AI 응답 생성 완료")  # 디버깅

            # ===== 응답 후처리: 내부 문구 제거 + SERVICE 모드 포맷팅 =====
            ai_response = self.post_process_response(ai_response, mode='SERVICE')

            # 추천 상품 파싱 (응답에서 상품 코드 추출)
            recommended_products = self.extract_recommended_products(ai_response, products, stocks)

            return {
                'success': True,
                'response': ai_response,
                'recommended_products': recommended_products,
            }

        except requests.exceptions.Timeout:
            print("GMS API 타임아웃")
            return {
                'success': False,
                'error': 'GMS API 타임아웃',
                'response': '죄송합니다. 응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.',
            }
        except requests.exceptions.RequestException as e:
            error_msg = f'GMS API 호출 실패: {str(e)}'
            print(error_msg)
            # 응답 본문도 출력
            try:
                print(f"응답 내용: {e.response.text if hasattr(e, 'response') else 'N/A'}")
            except:
                pass
            return {
                'success': False,
                'error': error_msg,
                'response': '죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
            }
        except Exception as e:
            error_msg = f'알 수 없는 오류: {str(e)}'
            print(error_msg)
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': error_msg,
                'response': '죄송합니다. 요청을 처리할 수 없습니다.',
            }

    def format_response_by_mode(self, ai_response, mode):
        """
        모드에 따라 응답 포맷팅 및 길이 제한

        Args:
            ai_response: AI가 생성한 원본 응답
            mode: 'CHAT' | 'SERVICE'

        Returns:
            포맷팅된 응답 문자열
        """
        if mode == 'CHAT':
            # CHAT 모드: 짧고 간결하게 (최대 300자)
            max_length = 300

            # 불필요한 상품 추천 섹션 제거
            lines = ai_response.split('\n')
            filtered_lines = []
            skip_product_section = False

            for line in lines:
                # 상품 추천 시작 패턴 감지
                if any(keyword in line for keyword in ['추천', '상품', '예금', '적금', '주식', '종목']):
                    if any(marker in line for marker in ['===', '##', '**', '1.', '2.', '3.']):
                        skip_product_section = True
                        continue

                # 빈 줄이 여러 개 나오면 섹션 종료
                if not line.strip():
                    skip_product_section = False
                    continue

                if not skip_product_section:
                    filtered_lines.append(line)

            cleaned = '\n'.join(filtered_lines).strip()

            # 길이 제한
            if len(cleaned) > max_length:
                # 문장 단위로 자르기
                sentences = re.split(r'([.!?])\s+', cleaned)
                result = ""
                for i in range(0, len(sentences), 2):
                    if i + 1 < len(sentences):
                        sentence = sentences[i] + sentences[i + 1]
                    else:
                        sentence = sentences[i]

                    if len(result) + len(sentence) <= max_length:
                        result += sentence + " "
                    else:
                        break

                cleaned = result.strip()

            return cleaned

        else:
            # SERVICE 모드: 구조화된 응답 (최대 800자 - 채팅창에 맞게)
            max_length = 800

            # 불릿 포인트 정리 및 가독성 개선
            lines = ai_response.split('\n')
            formatted_lines = []
            in_list = False

            for line in lines:
                stripped = line.strip()

                # 빈 줄 처리 (연속된 빈 줄 방지, 리스트 구분은 유지)
                if not stripped:
                    if formatted_lines and formatted_lines[-1] != '':
                        if in_list:
                            in_list = False  # 리스트 종료
                        formatted_lines.append('')
                    continue

                # 섹션 헤더 (===, ##, **) - 앞뒤 공백 추가
                if stripped.startswith(('===', '##', '**')):
                    if formatted_lines and formatted_lines[-1]:
                        formatted_lines.append('')  # 헤더 전 빈 줄
                    formatted_lines.append(stripped)
                    formatted_lines.append('')  # 헤더 후 빈 줄
                    in_list = False

                # 불릿 포인트 리스트
                elif stripped.startswith(('•', '-', '*', '·')):
                    formatted_lines.append(stripped)  # 불릿은 원본 유지
                    in_list = True

                # 숫자 목록
                elif re.match(r'^\d+\.', stripped):
                    formatted_lines.append(stripped)  # 숫자 목록 원본 유지
                    in_list = True

                # 일반 문장
                else:
                    formatted_lines.append(stripped)
                    in_list = False

            cleaned = '\n'.join(formatted_lines).strip()

            # 연속된 빈 줄 제거 (최대 1개까지만 허용)
            cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

            # 길이 제한
            if len(cleaned) > max_length:
                # 문장 단위로 자르기 시도
                sentences = cleaned.split('\n')
                result = []
                current_length = 0

                for sentence in sentences:
                    if current_length + len(sentence) + 1 <= max_length:
                        result.append(sentence)
                        current_length += len(sentence) + 1
                    else:
                        break

                cleaned = '\n'.join(result)
                if len(cleaned) > max_length:
                    cleaned = cleaned[:max_length] + "..."

            # 줄 수 제한을 더 엄격하게 (최대 12줄 - 채팅창에 맞게)
            all_lines = cleaned.split('\n')
            non_empty_lines = [l for l in all_lines if l.strip()]

            # 마무리 문장 감지 패턴
            closing_patterns = [
                r'궁금한.*말씀',
                r'도움.*되[^가-힣]*좋겠',
                r'문의.*주[시세]',
                r'투자.*결정',
                r'추가.*질문',
                r'언제든.*말씀',
                r'더.*필요.*사항',
            ]

            if len(non_empty_lines) > 12:
                # 중요한 정보 우선 유지 + 마무리 문장 보존
                result_lines = []
                content_count = 0
                max_content = 8  # 8개 컨텐츠까지 (줄이기)
                found_closing = False

                for i, line in enumerate(all_lines):
                    stripped = line.strip()

                    # 빈 줄은 항상 포함 (연속되지 않은 경우)
                    if not stripped:
                        if result_lines and result_lines[-1].strip():
                            result_lines.append(line)
                        continue

                    # 헤더는 항상 포함
                    if stripped.startswith(('===', '##', '**')):
                        result_lines.append(line)
                        continue

                    # 마무리 문장 감지
                    is_closing = any(re.search(pattern, stripped) for pattern in closing_patterns)

                    # 일반 내용은 제한
                    if content_count < max_content:
                        result_lines.append(line)
                        content_count += 1
                        if is_closing:
                            found_closing = True
                    elif is_closing and not found_closing:
                        # 제한을 넘었지만 마무리 문장이면 포함
                        result_lines.append(line)
                        found_closing = True
                        break
                    else:
                        # 제한 초과하고 마무리 문장도 아니면 중단
                        break

                # 마무리 문장이 없으면 마지막에 기본 마무리 추가
                if not found_closing and result_lines:
                    result_lines.append('')
                    result_lines.append('더 궁금한 점이 있으시면 언제든 말씀해주세요.')

                cleaned = '\n'.join(result_lines).strip()

            return cleaned

    def post_process_response(self, ai_response, mode='SERVICE'):
        """
        AI 응답 후처리: 내부 구현 문구 제거 및 사용자 친화적 변경

        Args:
            ai_response: AI가 생성한 원본 응답
            mode: 'CHAT' | 'SERVICE'
        """
        # 제거할 내부 문구 패턴
        forbidden_phrases = [
            "내 DB기준",
            "내 DB 기준",
            "DB기준",
            "DB 기준",
            "DB에서 조회한",
            "DB에서 직접 조회한",
            "DB 데이터",
            "실제 DB",
            "우리 DB",
            "시스템 DB",
            "제공 데이터 내",
            "제공된 데이터 내",
            "제공 데이터에서",
            "제공된 데이터에서",
        ]

        cleaned_response = ai_response

        # 금지 문구 제거
        for phrase in forbidden_phrases:
            cleaned_response = cleaned_response.replace(phrase, "")

        # 괄호 안의 "제공 데이터" 문구 제거 (예: "(제공 데이터 내 **)")
        cleaned_response = re.sub(r'\(제공\s*데이터[^)]*\)', '', cleaned_response)
        cleaned_response = re.sub(r'\(제공된\s*데이터[^)]*\)', '', cleaned_response)

        # 중복 공백 정리 (줄바꿈은 유지)
        cleaned_response = re.sub(r'  +', ' ', cleaned_response)  # 2개 이상의 연속 공백만 제거

        # 날짜 표현 개선
        today = datetime.now()
        date_str = today.strftime('%Y년 %m월 %d일')

        # "기준" 만 남은 경우 적절히 치환
        cleaned_response = re.sub(
            r'([^가-힣\s])기준',
            r'\1' + f' 기준 (최종 확인일: {date_str})',
            cleaned_response
        )

        # 모드별 포맷팅 적용
        cleaned_response = self.format_response_by_mode(cleaned_response.strip(), mode)

        return cleaned_response

    def generate_dart_link(self, company_name):
        """
        DART 전자공시 검색 링크 생성
        """
        from urllib.parse import quote
        # DART 통합검색 URL (회사명 검색)
        base_url = "https://dart.fss.or.kr/dsab007/main.do"
        # 회사명에서 '주식회사', '(주)' 등 제거하여 검색 정확도 향상
        clean_name = company_name.replace('주식회사', '').replace('(주)', '').strip()
        # textCrpNm 파라미터로 회사명 검색
        search_url = f"{base_url}?textCrpNm={quote(clean_name)}"
        return search_url

    def extract_recommended_products(self, ai_response, products, stocks):
        """
        AI 응답에서 추천된 상품명/종목명을 추출
        """
        recommended = []

        # RAG 모드인 경우: 상품 정보를 DB에서 직접 조회
        if 'rag_context' in products:
            # AI 응답에서 상품명 추출하여 DB 조회
            from finances.models import DepositProducts, SavingProducts

            # 예금 상품 확인
            deposits = DepositProducts.objects.all()
            for deposit in deposits:
                if deposit.fin_prdt_nm in ai_response:
                    best_option = deposit.options.order_by('-intr_rate2').first()
                    recommended.append({
                        'type': 'deposit',
                        'code': deposit.fin_prdt_cd,
                        'name': deposit.fin_prdt_nm,
                        'bank': deposit.kor_co_nm,
                        'rate': f"{best_option.intr_rate2:.2f}%" if best_option else '',
                    })

            # 적금 상품 확인
            savings = SavingProducts.objects.all()
            for saving in savings:
                if saving.fin_prdt_nm in ai_response:
                    best_option = saving.options.order_by('-intr_rate2').first()
                    recommended.append({
                        'type': 'saving',
                        'code': saving.fin_prdt_cd,
                        'name': saving.fin_prdt_nm,
                        'bank': saving.kor_co_nm,
                        'rate': f"{best_option.intr_rate2:.2f}%" if best_option else '',
                    })

        # 기존 모드인 경우
        else:
            # 예금 상품 확인
            for product in products.get('deposits', []):
                product_name = product.get('product_name', '')
                if product_name and product_name in ai_response:
                    recommended.append({
                        'type': 'deposit',
                        'code': product.get('code'),
                        'name': product_name,
                        'bank': product.get('bank', ''),
                        'rate': product.get('max_rate', ''),
                    })

            # 적금 상품 확인
            for product in products.get('savings', []):
                product_name = product.get('product_name', '')
                if product_name and product_name in ai_response:
                    recommended.append({
                        'type': 'saving',
                        'code': product.get('code'),
                        'name': product_name,
                        'bank': product.get('bank', ''),
                        'rate': product.get('max_rate', ''),
                    })

        # 주식 종목 확인
        for stock in stocks:
            stock_name = stock.get('name', '')
            if stock_name and stock_name in ai_response:
                dart_link = self.generate_dart_link(stock_name)
                recommended.append({
                    'type': 'stock',
                    'code': stock.get('code'),
                    'name': stock_name,
                    'market': stock.get('market', ''),
                    'price': stock.get('current_price', ''),
                    'dart_link': dart_link,  # DART 전자공시 링크 추가
                })

        return recommended if recommended else None
