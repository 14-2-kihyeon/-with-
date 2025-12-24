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
        """
        # 예금 상품 - 옵션과 함께 가져오기 (최고 금리 기준 상위 15개)
        deposits = DepositProducts.objects.prefetch_related('options').all()[:15]

        deposit_data = []
        for d in deposits:
            # 각 상품의 옵션 중 최고 금리 찾기
            best_option = d.options.order_by('-intr_rate2').first()
            if best_option:
                deposit_data.append({
                    'type': 'deposit',
                    'bank': d.kor_co_nm,
                    'product_name': d.fin_prdt_nm,
                    'code': d.fin_prdt_cd,
                    'join_way': d.join_way,
                    'special_condition': d.spcl_cnd,
                    'basic_rate': f"{best_option.intr_rate:.2f}%" if best_option.intr_rate > 0 else "정보없음",
                    'max_rate': f"{best_option.intr_rate2:.2f}%" if best_option.intr_rate2 > 0 else "정보없음",
                    'period': f"{best_option.save_trm}개월",
                })

        # 적금 상품 - 옵션과 함께 가져오기 (최고 금리 기준 상위 15개)
        savings = SavingProducts.objects.prefetch_related('options').all()[:15]

        saving_data = []
        for s in savings:
            # 각 상품의 옵션 중 최고 금리 찾기
            best_option = s.options.order_by('-intr_rate2').first()
            if best_option:
                saving_data.append({
                    'type': 'saving',
                    'bank': s.kor_co_nm,
                    'product_name': s.fin_prdt_nm,
                    'code': s.fin_prdt_cd,
                    'join_way': s.join_way,
                    'special_condition': s.spcl_cnd,
                    'basic_rate': f"{best_option.intr_rate:.2f}%" if best_option.intr_rate > 0 else "정보없음",
                    'max_rate': f"{best_option.intr_rate2:.2f}%" if best_option.intr_rate2 > 0 else "정보없음",
                    'period': f"{best_option.save_trm}개월",
                    'saving_type': best_option.rsrv_type_nm if best_option.rsrv_type_nm else "정보없음",
                })

        return {
            'deposits': deposit_data,
            'savings': saving_data,
        }

    def get_stock_context(self, user_profile, limit=15):
        """
        DB에 저장된 주식 정보 가져오기 (최근 시세, 수익률, 뉴스 포함)
        사용자 프로필에 따라 필터링
        """
        # 최근 거래일 찾기
        latest_date = DailyPrice.objects.aggregate(Max('date'))['date__max']
        if not latest_date:
            return []

        stock_data = []

        # 사용자 위험 성향에 따른 변동성 필터링
        risk_score = user_profile.get('risk_score', 50) if user_profile.get('has_profile') else 50

        # 최근 데이터가 있는 주식들 가져오기
        stocks_query = Stock.objects.filter(
            prices__date=latest_date
        ).prefetch_related(
            Prefetch('prices', queryset=DailyPrice.objects.filter(date=latest_date)),
            Prefetch('features', queryset=FeatureDaily.objects.filter(date=latest_date)),
            'stock_news'  # 슬라이싱은 나중에 Python에서 처리
        ).distinct()

        # 위험 성향에 따라 주식 필터링
        filtered_stocks = []
        for stock in stocks_query:
            latest_feature = stock.features.first() if hasattr(stock, 'features') else None

            # 보수적 투자자 (risk_score < 40): 낮은 변동성
            if risk_score < 40:
                if latest_feature and latest_feature.vol20 and latest_feature.vol20 < 3.0:
                    filtered_stocks.append(stock)
            # 공격적 투자자 (risk_score > 60): 높은 수익률 가능성
            elif risk_score > 60:
                if latest_feature and latest_feature.r20 and latest_feature.r20 > 0:
                    filtered_stocks.append(stock)
            # 중립적 투자자
            else:
                filtered_stocks.append(stock)

            if len(filtered_stocks) >= limit:
                break

        for stock in filtered_stocks[:limit]:
            try:
                # 최근 시세
                latest_price = stock.prices.first()
                # 최근 피처 (수익률, 변동성 등)
                latest_feature = stock.features.first()
                # 최근 뉴스 (최대 3개)
                recent_news = list(stock.stock_news.all()[:3])

                stock_info = {
                    'type': 'stock',
                    'name': stock.name,
                    'code': stock.code,
                    'market': stock.market,
                }

                # 시세 정보 추가
                if latest_price:
                    stock_info.update({
                        'current_price': f"{latest_price.close:,}원",
                        'date': str(latest_price.date),
                        'change': f"{((latest_price.close - latest_price.open) / latest_price.open * 100):.2f}%" if latest_price.open > 0 else "0%",
                    })

                # 수익률 정보 추가
                if latest_feature:
                    stock_info.update({
                        'return_5d': f"{latest_feature.r5:.2f}%" if latest_feature.r5 else "정보없음",
                        'return_20d': f"{latest_feature.r20:.2f}%" if latest_feature.r20 else "정보없음",
                        'volatility_20d': f"{latest_feature.vol20:.2f}%" if latest_feature.vol20 else "정보없음",
                    })

                # 뉴스 정보 추가
                if recent_news:
                    stock_info['recent_news'] = [
                        {
                            'title': news.title,
                            'published': news.published_at.strftime('%Y-%m-%d'),
                        }
                        for news in recent_news
                    ]

                stock_data.append(stock_info)

            except Exception as e:
                print(f"주식 데이터 처리 오류 ({stock.code}): {str(e)}")
                continue

        return stock_data

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
            'news_keywords': []
        }

        # 주식 종목명 추출 (DB에 있는 종목만)
        stocks = Stock.objects.all()
        for stock in stocks:
            if stock.name in user_message or stock.code in user_message:
                result['stock_names'].append(stock.name)
                result['is_specific_query'] = True
                print(f"[DEBUG] 종목명 감지: {stock.name}")

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

        print(f"[DEBUG] 분석 결과: {result}")
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

    def build_system_prompt(self, user_profile, products, stocks, specific_data="", fresh_news=""):
        """
        GMS API에 전달할 시스템 프롬프트 생성
        specific_data: 사용자 질문에 대한 동적 조회 데이터
        fresh_news: 실시간으로 수집한 최신 뉴스 데이터
        """
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
        deposit_details = self._format_deposit_products(products['deposits'])
        saving_details = self._format_saving_products(products['savings'])
        stock_details = self._format_stock_data(stocks)

        # 데이터 업데이트 날짜
        today = datetime.now().strftime('%Y년 %m월 %d일')

        # 동적 조회 데이터가 있으면 강조
        specific_section = ""
        if specific_data:
            specific_section = f"""
=== [중요] 사용자가 질문한 종목의 정확한 데이터 ===
{specific_data}
위 데이터는 사용자가 질문한 종목의 DB에서 직접 조회한 정확한 정보입니다.
반드시 이 데이터를 우선적으로 사용하여 정확하게 답변하세요.
"""

        # 최신 뉴스 데이터가 있으면 최우선 강조
        news_section = ""
        if fresh_news:
            news_section = f"""
=== [최우선] 방금 실시간으로 수집한 최신 뉴스 ===
{fresh_news}
⚠️ 위 뉴스는 사용자 질문에 대응하여 방금 네이버 뉴스 API에서 실시간으로 수집한 데이터입니다.
반드시 이 최신 뉴스를 기반으로 답변하세요. 이 데이터가 가장 최신이고 정확합니다.
"""

        system_prompt = f"""당신은 Finflow 금융 투자 플랫폼의 AI 재무 상담사입니다.

{profile_text}

=== 중요: 데이터 사용 지침 ===
아래 제공된 DB 데이터는 {today} 기준으로 실제 금융 상품 및 주식 정보입니다.
반드시 이 데이터를 우선적으로 활용하여 답변해주세요.
일반적인 지식보다 아래 실제 데이터를 기반으로 구체적인 추천을 제공하세요.
{news_section}
{specific_section}

{deposit_details}

{saving_details}

{stock_details}

역할:
1. 위의 실제 DB 데이터를 기반으로 사용자의 투자 성향과 재무 상태에 맞는 상품을 추천합니다.
2. 예금, 적금, 주식 등 다양한 옵션을 제시하되, 반드시 위에 나열된 상품 중에서 선택합니다.
3. 친절하고 전문적인 어조로 답변합니다.
4. 금리, 수익률 등 구체적인 수치를 언급하여 신뢰성을 높입니다.

답변 형식:
- 사용자의 질문에 대한 친절한 답변을 먼저 제공합니다.
- 추천 상품이 있다면, 위 DB 데이터에서 구체적인 상품명, 은행명, 금리를 인용합니다.
  예: "우리은행의 'WON플러스예금'은 최고 3.50% 금리를 제공하며..."
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
            # 1. 사용자 질문 분석
            question_analysis = self.analyze_user_question(user_message)
            print(f"질문 분석: {question_analysis}")  # 디버깅

            # 2. 사용자 프로필 및 기본 상품 정보 가져오기
            user_profile = self.get_user_profile_context()
            products = self.get_financial_products_context()
            stocks = self.get_stock_context(user_profile)

            print(f"프로필 로드 성공: {user_profile.get('has_profile')}")  # 디버깅
            print(f"예금 상품: {len(products['deposits'])}개, 적금 상품: {len(products['savings'])}개")
            print(f"주식 종목: {len(stocks)}개")

            # 3. 특정 종목/날짜 질문이면 동적 데이터 조회
            specific_data = ""
            if question_analysis['is_specific_query'] and question_analysis['stock_names']:
                print(f"특정 종목 조회: {question_analysis['stock_names']}")
                specific_data = self.get_specific_stock_data(
                    question_analysis['stock_names'],
                    question_analysis['dates'] if question_analysis['dates'] else None
                )

            # 4. 뉴스 질문이면 최신 뉴스 자동 수집 및 조회
            fresh_news_data = ""
            if question_analysis['is_news_query']:
                print(f"뉴스 질문 감지!")

                # 종목 뉴스 수집
                if question_analysis['stock_names']:
                    print(f"종목 뉴스 수집 중: {question_analysis['stock_names']}")
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

                # 일반 키워드 뉴스 수집
                elif question_analysis['news_keywords']:
                    print(f"일반 뉴스 수집 중: {question_analysis['news_keywords']}")
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

            # 5. 시스템 프롬프트 생성 (동적 데이터 + 최신 뉴스 포함)
            system_prompt = self.build_system_prompt(user_profile, products, stocks, specific_data, fresh_news_data)

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

        # 예금 상품 확인
        for product in products['deposits']:
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
        for product in products['savings']:
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
