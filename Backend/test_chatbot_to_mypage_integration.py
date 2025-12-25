"""
챗봇 → 마이페이지 통합 테스트
- 챗봇에서 추천받은 예금/적금 상품을 북마크했을 때 마이페이지에 표시되는지 확인
"""
import os
import sys
import django

sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from django.contrib.auth import get_user_model
from chatbot.services import ChatbotService
from rest_framework.test import APIRequestFactory, force_authenticate
from accounts.views import bookmark_recommendation, get_mypage_data

User = get_user_model()

print("=" * 100)
print("챗봇 → 마이페이지 통합 테스트")
print("=" * 100)

# 테스트 사용자
user = User.objects.first()
if not user:
    print("❌ 사용자가 없습니다")
    exit(1)

profile = user.investment_profile
print(f"\n사용자: {user.username}")
print(f"투자 성향: {profile.risk_type}")

# 1. 챗봇에게 상품 추천 받기
print(f"\n{'=' * 100}")
print("1. 챗봇에게 금융 상품 추천 받기")
print("=" * 100)

chatbot = ChatbotService(user)
question = "금리 좋은 예금과 적금 상품 추천해줘"
print(f"\n질문: {question}")

try:
    result = chatbot.chat(question)

    if result['success']:
        print("✅ 챗봇 응답 성공")

        recommended_products = result.get('recommended_products', [])
        print(f"\n추천 상품: {len(recommended_products)}개")

        # 예금/적금 분류
        deposits = [p for p in recommended_products if p['type'] == 'deposit']
        savings = [p for p in recommended_products if p['type'] == 'saving']

        print(f"  예금: {len(deposits)}개")
        print(f"  적금: {len(savings)}개")

        # 테스트용으로 각 타입에서 1개씩 선택
        test_deposit = deposits[0] if deposits else None
        test_saving = savings[0] if savings else None

        print("\n테스트할 상품:")
        if test_deposit:
            print(f"  [예금] {test_deposit['name']} ({test_deposit['code']})")
        if test_saving:
            print(f"  [적금] {test_saving['name']} ({test_saving['code']})")

    else:
        print(f"❌ 챗봇 응답 실패: {result.get('error')}")
        exit(1)

except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 2. 예금 상품 북마크
if test_deposit:
    print(f"\n{'=' * 100}")
    print("2. 예금 상품 북마크 테스트")
    print("=" * 100)

    factory = APIRequestFactory()
    request = factory.post(f'/api/v1/accounts/recommendations/{test_deposit["code"]}/bookmark/')
    force_authenticate(request, user=user)

    try:
        response = bookmark_recommendation(request, test_deposit['code'])
        if response.status_code == 200:
            print(f"✅ 예금 상품 북마크 성공: {test_deposit['name']}")
            print(f"   응답: {response.data['message']}")
        else:
            print(f"❌ 예금 상품 북마크 실패")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

# 3. 적금 상품 북마크
if test_saving:
    print(f"\n{'=' * 100}")
    print("3. 적금 상품 북마크 테스트")
    print("=" * 100)

    factory = APIRequestFactory()
    request = factory.post(f'/api/v1/accounts/recommendations/{test_saving["code"]}/bookmark/')
    force_authenticate(request, user=user)

    try:
        response = bookmark_recommendation(request, test_saving['code'])
        if response.status_code == 200:
            print(f"✅ 적금 상품 북마크 성공: {test_saving['name']}")
            print(f"   응답: {response.data['message']}")
        else:
            print(f"❌ 적금 상품 북마크 실패")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

# 4. 마이페이지에서 북마크 확인
print(f"\n{'=' * 100}")
print("4. 마이페이지에서 북마크 상품 확인")
print("=" * 100)

factory = APIRequestFactory()
request = factory.get('/api/v1/accounts/mypage/')
force_authenticate(request, user=user)

try:
    response = get_mypage_data(request)
    data = response.data

    bookmarked_products = data.get('bookmarked_products', [])
    print(f"\n마이페이지 북마크 상품 수: {len(bookmarked_products)}개")

    # 예금/적금 분류
    deposit_bookmarks = [p for p in bookmarked_products if p.get('product_type') == 'deposit']
    saving_bookmarks = [p for p in bookmarked_products if p.get('product_type') == 'saving']

    print(f"\n예금 북마크: {len(deposit_bookmarks)}개")
    for p in deposit_bookmarks[:3]:
        print(f"  - {p['fin_prdt_nm']} ({p['kor_co_nm']}) - 최고금리: {p['max_rate']}")

    print(f"\n적금 북마크: {len(saving_bookmarks)}개")
    for p in saving_bookmarks[:3]:
        print(f"  - {p['fin_prdt_nm']} ({p['kor_co_nm']}) - 최고금리: {p['max_rate']}")

    # 테스트 결과 검증
    print(f"\n{'=' * 100}")
    print("검증 결과")
    print("=" * 100)

    success_count = 0
    fail_count = 0

    if test_deposit:
        if any(p['fin_prdt_cd'] == test_deposit['code'] for p in bookmarked_products):
            print(f"✅ 예금 상품 '{test_deposit['name']}' 마이페이지에 표시됨")
            success_count += 1
        else:
            print(f"❌ 예금 상품 '{test_deposit['name']}' 마이페이지에 표시되지 않음")
            fail_count += 1

    if test_saving:
        if any(p['fin_prdt_cd'] == test_saving['code'] for p in bookmarked_products):
            print(f"✅ 적금 상품 '{test_saving['name']}' 마이페이지에 표시됨")
            success_count += 1
        else:
            print(f"❌ 적금 상품 '{test_saving['name']}' 마이페이지에 표시되지 않음")
            fail_count += 1

    print(f"\n성공: {success_count}, 실패: {fail_count}")

    if fail_count == 0:
        print("\n🎉 모든 테스트 통과! 챗봇 → 북마크 → 마이페이지 전체 플로우가 정상 작동합니다.")
    else:
        print("\n⚠️ 일부 테스트 실패")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'=' * 100}")
print("테스트 완료")
print("=" * 100)
