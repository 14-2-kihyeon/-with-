"""
상품 필터링 및 추천 시스템 테스트
1. 성별/나이 필터링 확인
2. 금리순 정렬 확인
3. 적금 상품 포함 확인
4. 예상 수익 계산 확인
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from chatbot.services import ChatbotService
from django.contrib.auth import get_user_model
from accounts.models import InvestmentProfile

User = get_user_model()

print("=" * 80)
print("상품 필터링 및 추천 시스템 테스트")
print("=" * 80)

# 테스트용 사용자 찾기 (또는 생성)
user = User.objects.first()
if not user:
    print("No user found")
    exit(1)

# 사용자 프로필 확인/생성
profile, created = InvestmentProfile.objects.get_or_create(user=user)
if created or not profile.gender:
    profile.gender = 'M'  # 남성으로 설정
    profile.age = 30
    profile.investment_period = 12
    profile.save()
    print(f"Created/Updated user profile: gender={profile.gender}, age={profile.age}")

print(f"\n테스트 사용자: {user.username}")
print(f"성별: {profile.gender}, 나이: {profile.age}, 투자기간: {profile.investment_period}개월")

chatbot = ChatbotService(user)

# Test 1: 상품 컨텍스트 가져오기
print("\n" + "=" * 80)
print("[TEST 1] 상품 컨텍스트 - 필터링 및 정렬 확인")
print("=" * 80)

products = chatbot.get_financial_products_context()

# 예금 상품 확인
print(f"\n예금 상품 개수: {len(products['deposits'])}")
if products['deposits']:
    print("\n상위 5개 예금 상품:")
    for i, d in enumerate(products['deposits'][:5], 1):
        print(f"\n{i}. {d['product_name']}")
        print(f"   은행: {d['bank']}")
        print(f"   최고금리: {d['max_rate']}")
        print(f"   가입대상: {d.get('join_member', 'N/A')}")
        print(f"   예상수익: {d.get('expected_profit', 'N/A')}")

        # 여성 전용 상품 체크
        join_member = d.get('join_member', '')
        if '여성' in join_member:
            print(f"   ⚠️ WARNING: 남성 사용자에게 여성 전용 상품이 표시됨!")

# 적금 상품 확인
print(f"\n적금 상품 개수: {len(products['savings'])}")
if products['savings']:
    print("\n상위 5개 적금 상품:")
    for i, s in enumerate(products['savings'][:5], 1):
        print(f"\n{i}. {s['product_name']}")
        print(f"   은행: {s['bank']}")
        print(f"   최고금리: {s['max_rate']}")
        print(f"   가입대상: {s.get('join_member', 'N/A')}")
        print(f"   예상수익: {s.get('expected_profit', 'N/A')}")

        # 여성 전용 상품 체크
        join_member = s.get('join_member', '')
        if '여성' in join_member:
            print(f"   ⚠️ WARNING: 남성 사용자에게 여성 전용 상품이 표시됨!")
else:
    print("⚠️ WARNING: 적금 상품이 하나도 없습니다!")

# Test 2: 실제 챗봇 응답 테스트
print("\n" + "=" * 80)
print("[TEST 2] 챗봇 상품 추천 응답 확인")
print("=" * 80)

print("\n질문: '예금과 적금 추천해줘'")
result = chatbot.chat("예금과 적금 추천해줘")

if result['success']:
    response = result['response']
    print(f"\n응답 길이: {len(response)} chars")
    print(f"응답 내용:\n{response}")

    # 응답에 적금이 포함되어 있는지 확인
    if '적금' in response:
        print("\n✅ PASS: 응답에 적금이 포함됨")
    else:
        print("\n⚠️ WARNING: 응답에 적금이 포함되지 않음")

    # 미즈월 상품이 포함되어 있는지 확인
    if '미즈' in response:
        print("⚠️ WARNING: 남성 사용자에게 여성 전용 상품(미즈월)이 추천됨!")
    else:
        print("✅ PASS: 여성 전용 상품이 추천되지 않음")
else:
    print(f"❌ FAIL: {result.get('error')}")

# Test 3: 특정 상품 직접 확인
print("\n" + "=" * 80)
print("[TEST 3] 미즈월 상품 필터링 확인")
print("=" * 80)

from finances.models import DepositProducts

mizz_products = DepositProducts.objects.filter(fin_prdt_nm__contains='미즈')
print(f"\nDB에서 '미즈' 포함 상품: {mizz_products.count()}개")

for mizz in mizz_products:
    print(f"\n상품명: {mizz.fin_prdt_nm}")
    print(f"가입대상: {mizz.join_member}")

    # 필터링 함수 직접 테스트
    is_eligible = chatbot._is_eligible_for_product(mizz.join_member, 'M', 30)
    print(f"남성(30세) 가입 가능: {is_eligible}")

    if is_eligible:
        print("⚠️ WARNING: 여성 전용 상품이 남성에게 허용됨!")
    else:
        print("✅ PASS: 여성 전용 상품이 올바르게 필터링됨")

print("\n" + "=" * 80)
print("테스트 완료")
print("=" * 80)
