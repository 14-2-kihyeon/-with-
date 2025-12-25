"""
성별 필터링 테스트 - 미즈월 상품이 남성에게 표시되는지 확인
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from chatbot.services import ChatbotService
from django.contrib.auth import get_user_model
from accounts.models import InvestmentProfile
from finances.models import DepositProducts

User = get_user_model()

print("=" * 80)
print("Gender Filtering Test")
print("=" * 80)

# Get or create test user
user = User.objects.first()
if not user:
    print("No user found")
    exit(1)

# Set user profile to male
profile, created = InvestmentProfile.objects.get_or_create(user=user)
profile.gender = 'M'
profile.age = 30
profile.investment_period = 12
profile.save()

print(f"\nTest User: {user.username}")
print(f"Gender: {profile.gender}, Age: {profile.age}")

chatbot = ChatbotService(user)

# Test 1: Check if _is_eligible_for_product works
print("\n" + "=" * 80)
print("TEST 1: _is_eligible_for_product function")
print("=" * 80)

test_cases = [
    ("제한없음", 'M', 30, True),
    ("", 'M', 30, True),
    ("만18세이상 여성고객", 'M', 30, False),
    ("만18세이상 여성고객", 'F', 25, True),
    ("만19세이상 남성고객", 'M', 30, True),
    ("만19세이상 남성고객", 'F', 30, False),
    ("만65세미만", 'M', 30, True),
    ("만65세미만", 'M', 70, False),
]

for join_member, gender, age, expected in test_cases:
    result = chatbot._is_eligible_for_product(join_member, gender, age)
    status = "PASS" if result == expected else "FAIL"
    print(f"{status}: join_member='{join_member}', gender={gender}, age={age} -> {result} (expected {expected})")

# Test 2: Check if Mizwol products are filtered out
print("\n" + "=" * 80)
print("TEST 2: Mizwol products filtering for male user")
print("=" * 80)

# Find Mizwol products in DB
mizz_products = DepositProducts.objects.filter(fin_prdt_nm__contains='미즈')
print(f"\nMizwol products in DB: {mizz_products.count()}")

for mizz in mizz_products:
    print(f"\n  Product: {mizz.fin_prdt_nm}")
    print(f"  join_member: {mizz.join_member}")
    is_eligible = chatbot._is_eligible_for_product(mizz.join_member, 'M', 30)
    print(f"  Eligible for male(30): {is_eligible}")

    if is_eligible:
        print("  FAIL: Women-only product allowed for male user!")
    else:
        print("  PASS: Correctly filtered out")

# Test 3: Check if Mizwol appears in product context
print("\n" + "=" * 80)
print("TEST 3: Product context for male user")
print("=" * 80)

products = chatbot.get_financial_products_context()

# Check deposits
mizz_in_deposits = False
for d in products['deposits']:
    if '미즈' in d['product_name']:
        mizz_in_deposits = True
        print(f"FAIL: Found Mizwol in deposits: {d['product_name']}")
        print(f"      join_member: {d.get('join_member')}")

if not mizz_in_deposits:
    print("PASS: No Mizwol products in deposits for male user")

# Test 4: Check top products by interest rate
print("\n" + "=" * 80)
print("TEST 4: Top 10 deposit products (sorted by interest rate)")
print("=" * 80)

for i, d in enumerate(products['deposits'][:10], 1):
    join_member = d.get('join_member', 'N/A')
    has_gender_restriction = '여성' in join_member or '남성' in join_member

    print(f"\n{i}. {d['product_name']}")
    print(f"   Rate: {d['max_rate']}")
    print(f"   Eligibility: {join_member}")

    if '여성' in join_member:
        print("   FAIL: Women-only product shown to male user!")

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)
