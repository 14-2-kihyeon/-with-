import requests
import json
from django.conf import settings
from finances.models import DepositProducts, SavingProducts
from stocks.models import Stock


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
        DB에 저장된 금융 상품 정보 가져오기
        """
        # 예적금 상품 (상위 10개)
        deposits = DepositProducts.objects.all()[:10]
        savings = SavingProducts.objects.all()[:10]

        # 주식 정보 (상위 10개)
        stocks = Stock.objects.all()[:10]

        deposit_data = [
            {
                'type': 'deposit',
                'bank': d.kor_co_nm,
                'product_name': d.fin_prdt_nm,
                'code': d.fin_prdt_cd,
                'join_way': d.join_way,
                'special_condition': d.spcl_cnd,
            }
            for d in deposits
        ]

        saving_data = [
            {
                'type': 'saving',
                'bank': s.kor_co_nm,
                'product_name': s.fin_prdt_nm,
                'code': s.fin_prdt_cd,
                'join_way': s.join_way,
                'special_condition': s.spcl_cnd,
            }
            for s in savings
        ]

        stock_data = [
            {
                'type': 'stock',
                'name': st.name,
                'code': st.code,
                'market': st.market,
            }
            for st in stocks
        ]

        return {
            'deposits': deposit_data,
            'savings': saving_data,
            'stocks': stock_data,
        }

    def build_system_prompt(self, user_profile, products):
        """
        GMS API에 전달할 시스템 프롬프트 생성
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

        # 상품 정보 요약
        deposit_summary = f"\n예금 상품 {len(products['deposits'])}개"
        saving_summary = f"\n적금 상품 {len(products['savings'])}개"
        stock_summary = f"\n주식 종목 {len(products['stocks'])}개"

        system_prompt = f"""당신은 Finflow 금융 투자 플랫폼의 AI 재무 상담사입니다.

{profile_text}

현재 DB에 등록된 금융 상품:{deposit_summary}{saving_summary}{stock_summary}

역할:
1. 사용자의 투자 성향과 재무 상태에 맞는 금융 상품을 추천합니다.
2. 예금, 적금, 주식, 금/은 투자 등 다양한 옵션을 제시합니다.
3. 친절하고 전문적인 어조로 답변합니다.
4. 상품을 추천할 때는 자연스러운 문장으로 설명합니다.

답변 형식:
- 먼저 사용자의 질문에 대한 친절한 답변을 제공합니다.
- 추천 상품이 있다면, 상품명과 은행명을 자연스러운 문장으로 설명합니다.
- 각 상품의 특징과 사용자에게 적합한 이유를 쉽게 풀어서 설명합니다.
- 상품 코드나 기술적인 정보는 언급하지 않습니다.
- 사용자가 이해하기 쉽도록 전문 용어는 최소화하고 일상적인 표현을 사용합니다.

주의사항:
- 투자에는 위험이 따를 수 있다는 점을 항상 안내합니다.
- 확정된 수익을 보장하지 않습니다.
- 사용자의 투자 성향을 존중하며 무리한 투자를 권장하지 않습니다.
- JSON 형식이나 구조화된 데이터 형식으로 답변하지 마세요.
- 자연스럽고 친근한 대화체로 답변하세요.
"""

        return system_prompt

    def chat(self, user_message, chat_history=None):
        """
        GMS API를 호출하여 AI 응답 생성
        """
        try:
            # 사용자 프로필 및 상품 정보 가져오기
            user_profile = self.get_user_profile_context()
            products = self.get_financial_products_context()

            print(f"프로필 로드 성공: {user_profile.get('has_profile')}")  # 디버깅

            # 시스템 프롬프트 생성
            system_prompt = self.build_system_prompt(user_profile, products)

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
            recommended_products = self.extract_recommended_products(ai_response, products)

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

    def extract_recommended_products(self, ai_response, products):
        """
        AI 응답에서 추천된 상품 코드를 추출
        """
        recommended = []

        # 모든 상품 코드 목록 생성
        all_products = (
            products['deposits'] +
            products['savings'] +
            products['stocks']
        )

        # AI 응답에서 상품 코드가 언급되었는지 확인
        for product in all_products:
            code = product.get('code', '')
            if code and code in ai_response:
                recommended.append({
                    'type': product['type'],
                    'code': code,
                    'name': product.get('product_name') or product.get('name'),
                    'bank': product.get('bank', ''),
                })

        return recommended if recommended else None
