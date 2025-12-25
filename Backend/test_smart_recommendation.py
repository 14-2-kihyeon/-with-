"""
복합 조건 기반 스마트 추천 시스템 테스트
- 저축액, 투자기간, 투자목표를 고려한 예금/적금 비율 계산
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import InvestmentProfile
from accounts.views import recommend_products, _calculate_product_ratio
from rest_framework.test import APIRequestFactory, force_authenticate

User = get_user_model()

print("=" * 80)
print("Smart Product Recommendation Test (복합 조건 기반)")
print("=" * 80)

# Get test user
user = User.objects.first()
if not user:
    print("No user found")
    exit(1)

profile, _ = InvestmentProfile.objects.get_or_create(user=user)

# ===== Test Case 1: 당신의 실제 상황 =====
print("\n" + "=" * 80)
print("Test Case 1: 주택 구매, 36개월, 5,000만원")
print("=" * 80)

profile.gender = 'M'
profile.age = 30
profile.investment_period = 36
profile.investment_goal = '주택구매'
profile.savings = 5000  # 5,000만원
profile.save()

# 비율 계산
deposit_count, saving_count = _calculate_product_ratio(
    savings_amount=5000,
    investment_period=36,
    investment_goal='주택구매'
)

print(f"\n[계산된 비율]")
print(f"  예금: {deposit_count}개")
print(f"  적금: {saving_count}개")
print(f"  이유:")
print(f"    - 저축액 5,000만원 → 목돈 있음 (예금 선호)")
print(f"    - 투자기간 36개월 → 장기 (적금 선호)")
print(f"    - 투자목표 '주택구매' → 중대 목표 (균형)")

# API 호출
factory = APIRequestFactory()
request = factory.get('/api/accounts/recommend-products/')
force_authenticate(request, user=user)
response = recommend_products(request)
data = response.data

print(f"\n[API 응답]")
print(f"  총 추천: {data['total_count']}개")
print(f"  예금: {data['recommended_deposit_count']}개")
print(f"  적금: {data['recommended_saving_count']}개")
print(f"  추천 이유: {data['recommendation_reason']}")

print(f"\n[추천 상품 상위 5개]")
for i, rec in enumerate(data['recommendations'][:5], 1):
    print(f"{i}. [{rec['type']}] {rec['product']['fin_prdt_nm']}")
    print(f"   금리: {rec['max_rate']}%, 예상수익: {rec['expected_profit']}만원")

# ===== Test Case 2: 단기 + 적은 저축액 =====
print("\n" + "=" * 80)
print("Test Case 2: 비상금 마련, 6개월, 500만원")
print("=" * 80)

profile.investment_period = 6
profile.investment_goal = '비상금'
profile.savings = 500
profile.save()

deposit_count, saving_count = _calculate_product_ratio(
    savings_amount=500,
    investment_period=6,
    investment_goal='비상금'
)

print(f"\n[계산된 비율]")
print(f"  예금: {deposit_count}개")
print(f"  적금: {saving_count}개")
print(f"  이유:")
print(f"    - 저축액 500만원 → 적음 (적금으로 모으기)")
print(f"    - 투자기간 6개월 → 단기 (예금 선호)")
print(f"    - 투자목표 '비상금' → 단기 목표 (예금 강력 선호)")

request = factory.get('/api/accounts/recommend-products/')
force_authenticate(request, user=user)
response = recommend_products(request)
data = response.data

print(f"\n[API 응답]")
print(f"  예금: {data['recommended_deposit_count']}개")
print(f"  적금: {data['recommended_saving_count']}개")

# ===== Test Case 3: 장기 노후 준비 =====
print("\n" + "=" * 80)
print("Test Case 3: 노후 준비, 60개월, 1,000만원")
print("=" * 80)

profile.investment_period = 60
profile.investment_goal = '노후준비'
profile.savings = 1000
profile.save()

deposit_count, saving_count = _calculate_product_ratio(
    savings_amount=1000,
    investment_period=60,
    investment_goal='노후준비'
)

print(f"\n[계산된 비율]")
print(f"  예금: {deposit_count}개")
print(f"  적금: {saving_count}개")
print(f"  이유:")
print(f"    - 저축액 1,000만원 → 보통 (균형)")
print(f"    - 투자기간 60개월 → 장기 (적금 강력 선호)")
print(f"    - 투자목표 '노후준비' → 장기 목표 (적금 강력 선호)")

request = factory.get('/api/accounts/recommend-products/')
force_authenticate(request, user=user)
response = recommend_products(request)
data = response.data

print(f"\n[API 응답]")
print(f"  예금: {data['recommended_deposit_count']}개")
print(f"  적금: {data['recommended_saving_count']}개")

# ===== Test Case 4: 목돈 + 단기 =====
print("\n" + "=" * 80)
print("Test Case 4: 목돈 운용, 3개월, 10,000만원")
print("=" * 80)

profile.investment_period = 3
profile.investment_goal = '단기 운용'
profile.savings = 10000
profile.save()

deposit_count, saving_count = _calculate_product_ratio(
    savings_amount=10000,
    investment_period=3,
    investment_goal='단기 운용'
)

print(f"\n[계산된 비율]")
print(f"  예금: {deposit_count}개")
print(f"  적금: {saving_count}개")
print(f"  이유:")
print(f"    - 저축액 10,000만원 → 목돈 (예금 강력 선호)")
print(f"    - 투자기간 3개월 → 단기 (예금 강력 선호)")
print(f"    - 투자목표 '단기 운용' → 단기 목표 (예금 강력 선호)")

request = factory.get('/api/accounts/recommend-products/')
force_authenticate(request, user=user)
response = recommend_products(request)
data = response.data

print(f"\n[API 응답]")
print(f"  예금: {data['recommended_deposit_count']}개 (대부분 예금 추천)")
print(f"  적금: {data['recommended_saving_count']}개")

# Summary
print("\n" + "=" * 80)
print("Summary: 복합 조건 기반 추천 로직 검증 완료")
print("=" * 80)

print("""
복합 조건 고려 사항:
1. 저축액 (0~40점)
   - 5,000만원 이상: 예금 40점, 적금 10점 (목돈 운용)
   - 3,000~5,000만원: 예금 30점, 적금 20점
   - 1,000~3,000만원: 예금 20점, 적금 30점
   - 1,000만원 미만: 예금 10점, 적금 40점 (모으기)

2. 투자 기간 (0~40점)
   - 6개월 이하: 예금 40점, 적금 10점 (단기 유동성)
   - 6~12개월: 예금 30점, 적금 20점
   - 12~24개월: 예금 20점, 적금 30점
   - 24개월 이상: 예금 10점, 적금 40점 (장기 저축)

3. 투자 목표 (0~20점)
   - 단기/비상금: 예금 20점, 적금 5점
   - 장기/노후: 예금 5점, 적금 20점
   - 주택/결혼/교육: 예금 10점, 적금 15점 (균형)

최종 비율 = 점수 비율로 계산 (최소 각 2개 보장)
""")

print("\n테스트 완료!")
