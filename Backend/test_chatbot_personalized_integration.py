"""
챗봇 맞춤 추천 통합 테스트
- 챗봇이 맞춤 추천 페이지와 동일한 로직으로 상품을 추천하는지 확인
"""
import os
import sys
import django

# Windows 인코딩 문제 해결
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import InvestmentProfile
from chatbot.services import ChatbotService

User = get_user_model()

def create_test_user(username, risk_type, gender='M'):
    """테스트 사용자 생성"""
    user, _ = User.objects.get_or_create(username=username)

    profile, _ = InvestmentProfile.objects.get_or_create(user=user)
    profile.risk_type = risk_type
    profile.risk_score = {'timid_male': 30, 'normal_male': 60, 'speculative_male': 90}[risk_type]
    profile.gender = gender
    profile.age = 30
    profile.savings = 10000000  # 1천만원
    profile.investment_period = 12  # 12개월
    profile.investment_goal = 'stable_income'
    profile.save()

    return user

print("=" * 100)
print("챗봇 맞춤 추천 통합 테스트")
print("=" * 100)

# 3가지 투자 성향별 테스트
test_cases = [
    ('timid_male', '안정형 (에겐소심남)', 'test_chatbot_timid'),
    ('normal_male', '중립형 (보통남)', 'test_chatbot_normal'),
    ('speculative_male', '공격형 (테토투기남)', 'test_chatbot_speculative'),
]

test_questions = [
    "안정적인 예금 상품 추천해줘",
    "금리 높은 적금 추천해줘",
    "예금과 적금 골고루 추천해줘",
]

for risk_type, risk_name, username in test_cases:
    print(f"\n{'=' * 100}")
    print(f"[{risk_name}] 테스트")
    print("=" * 100)

    # 사용자 생성
    user = create_test_user(username, risk_type)
    chatbot = ChatbotService(user)

    for i, question in enumerate(test_questions, 1):
        print(f"\n[질문 {i}] {question}")
        print("-" * 100)

        try:
            result = chatbot.chat(question)

            if result['success']:
                print("✅ 응답 성공")

                # 응답 내용 (처음 300자만)
                response_text = result['response']
                if len(response_text) > 300:
                    print(f"\n[응답] {response_text[:300]}...")
                else:
                    print(f"\n[응답] {response_text}")

                # 추천 상품 확인
                if result.get('recommended_products'):
                    products = result['recommended_products']
                    print(f"\n[추천 상품] {len(products)}개")
                    for j, product in enumerate(products[:3], 1):
                        product_type = "예금" if product['type'] == 'deposit' else "적금"
                        print(f"  {j}. [{product_type}] {product['name']} ({product.get('bank', 'N/A')})")
                        print(f"     금리: {product.get('rate', 'N/A')}")
                else:
                    print("\n[추천 상품] 없음")

                print(f"\n응답 길이: {len(response_text)}자")

            else:
                print(f"❌ 응답 실패: {result.get('error')}")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()

# 맞춤 추천 페이지와 비교 테스트
print(f"\n\n{'=' * 100}")
print("맞춤 추천 페이지와 비교")
print("=" * 100)

from rest_framework.test import APIRequestFactory, force_authenticate
from accounts.views import recommend_products

user = create_test_user('test_comparison', 'normal_male')

# 1. 맞춤 추천 페이지 호출
factory = APIRequestFactory()
request = factory.get('/api/v1/accounts/recommend/')
force_authenticate(request, user=user)
response = recommend_products(request)
page_recommendations = response.data.get('recommendations', [])[:5]

# 2. 챗봇 맞춤 추천 컨텍스트 호출
chatbot = ChatbotService(user)
chatbot_result = chatbot.get_personalized_products_context(top_k=5)

print(f"\n[맞춤 추천 페이지] 상위 5개:")
for i, rec in enumerate(page_recommendations, 1):
    score = rec.get('risk_adjusted_score', 0)
    product_type = "예금" if rec['type'] == 'deposit' else "적금"
    print(f"  {i}. [{product_type}] {rec['product']['fin_prdt_nm'][:30]:30} (점수: {score:.2f})")

print(f"\n[챗봇 맞춤 추천] 결과:")
print(f"추천 개수: {chatbot_result['recommendation_count']}개")
print("\n컨텍스트 미리보기:")
context_preview = chatbot_result['rag_context'][:500]
print(context_preview)
print("...\n")

# 최종 결과
print(f"\n{'=' * 100}")
print("테스트 완료")
print("=" * 100)

print("\n✅ 예상 결과:")
print("  - 챗봇이 맞춤 추천 페이지와 동일한 상품을 추천해야 함")
print("  - 투자 성향별로 다른 상품이 추천되어야 함")
print("  - 최대 5개 상품만 AI에게 전달되어야 함")
print("  - AI가 자연어로 설명하며 3~5개 상품을 선별하여 추천")
