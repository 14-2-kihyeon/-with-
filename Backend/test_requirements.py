"""
3가지 요구사항 테스트:
1. "(제공 데이터 내 **)" 문구 제거
2. 가독성 개선
3. 특정 상품/종목 질문 시 해당 항목에 대해서만 응답
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from chatbot.services import ChatbotService
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

if not user:
    print("No user found")
    exit(1)

chatbot = ChatbotService(user)

print("=" * 80)
print("3가지 요구사항 테스트")
print("=" * 80)

# Test 1: Check for forbidden phrases removal
print("\n[TEST 1] '(제공 데이터 내)' 문구 제거 확인")
result1 = chatbot.chat("삼성전자 어때?")
if result1['success']:
    response = result1['response']
    if '제공 데이터' in response or '제공된 데이터' in response:
        print("FAIL: '제공 데이터' 문구가 여전히 존재합니다.")
    else:
        print("PASS: '제공 데이터' 문구가 성공적으로 제거되었습니다.")
    print(f"Response length: {len(response)} chars")

# Test 2: Readability check
print("\n[TEST 2] 가독성 확인")
result2 = chatbot.chat("예금 추천해줘")
if result2['success']:
    response = result2['response']
    lines = [l for l in response.split('\n') if l.strip()]
    print(f"Total lines: {len(lines)}")
    print(f"Response length: {len(response)} chars")
    print("First 300 chars:")
    print(response[:300])

# Test 3: Specific product query - should only talk about that product
print("\n[TEST 3] 특정 상품 질문 - 해당 상품만 설명")

# First, let's get a real product name from the database
from finances.models import DepositProducts
first_product = DepositProducts.objects.first()

if first_product:
    product_name = first_product.fin_prdt_nm
    print(f"Testing with product: {product_name}")

    result3 = chatbot.chat(f"{product_name} 어때?")
    if result3['success']:
        response = result3['response']
        print(f"Response length: {len(response)} chars")
        print("Response preview:")
        print(response[:400])

        # Check if it mentions the specific product
        if product_name in response:
            print(f"PASS: Response mentions the specific product '{product_name}'")
        else:
            print(f"WARNING: Response doesn't mention '{product_name}'")
else:
    print("No deposit products found in database")

# Test 4: Specific stock query
print("\n[TEST 4] 특정 종목 질문 - 해당 종목만 설명")
result4 = chatbot.chat("삼성전자 주가 분석해줘")
if result4['success']:
    response = result4['response']

    # Check if it mentions other stocks or products
    forbidden_words = ['예금', '적금', '저축']
    found_forbidden = [word for word in forbidden_words if word in response]

    if found_forbidden:
        print(f"WARNING: Response mentions forbidden words: {found_forbidden}")
    else:
        print("PASS: Response doesn't mention deposit/saving products")

    print(f"Response length: {len(response)} chars")
    print("Response preview:")
    print(response[:400])

print("\n" + "=" * 80)
print("테스트 완료")
print("=" * 80)
