"""
적금 관심상품 등록 버그 수정 테스트
- 적금 상품 북마크가 마이페이지에 표시되는지 확인
"""
import os
import sys
import django

sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import InvestmentProfile, SavingRecommendation
from finances.models import SavingProducts
from rest_framework.test import APIRequestFactory, force_authenticate
from accounts.views import bookmark_recommendation, get_mypage_data

User = get_user_model()

print("=" * 100)
print("적금 북마크 버그 수정 테스트")
print("=" * 100)

# 테스트 사용자
user = User.objects.first()
if not user:
    print("❌ 사용자가 없습니다")
    exit(1)

print(f"\n사용자: {user.username}")

# 1. 적금 상품 찾기
print(f"\n{'=' * 100}")
print("1. 적금 상품 찾기")
print("=" * 100)

saving_product = SavingProducts.objects.first()
if not saving_product:
    print("❌ 적금 상품이 없습니다")
    exit(1)

print(f"테스트 상품: {saving_product.fin_prdt_nm} ({saving_product.fin_prdt_cd})")

# 2. 적금 상품 북마크 추가
print(f"\n{'=' * 100}")
print("2. 적금 상품 북마크 추가")
print("=" * 100)

factory = APIRequestFactory()
request = factory.post(f'/api/v1/accounts/recommendations/{saving_product.fin_prdt_cd}/bookmark/')
force_authenticate(request, user=user)

try:
    response = bookmark_recommendation(request, saving_product.fin_prdt_cd)
    if response.status_code == 200:
        print("✅ 북마크 추가 성공")
        print(f"응답: {response.data}")
    else:
        print(f"❌ 북마크 추가 실패: {response.status_code}")
        print(f"응답: {response.data}")
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()

# 3. SavingRecommendation 테이블 직접 확인
print(f"\n{'=' * 100}")
print("3. SavingRecommendation 테이블 확인")
print("=" * 100)

saving_bookmarks = SavingRecommendation.objects.filter(
    user=user,
    is_bookmarked=True
)

print(f"\n사용자의 적금 북마크 개수: {saving_bookmarks.count()}개")
for bookmark in saving_bookmarks:
    print(f"  - {bookmark.product.fin_prdt_nm} (북마크됨: {bookmark.is_bookmarked})")

# 4. 마이페이지 API 호출하여 확인 (핵심 테스트!)
print(f"\n{'=' * 100}")
print("4. 마이페이지 API로 북마크 상품 조회")
print("=" * 100)

request = factory.get('/api/v1/accounts/mypage/')
force_authenticate(request, user=user)

try:
    response = get_mypage_data(request)
    data = response.data

    bookmarked_products = data.get('bookmarked_products', [])
    print(f"\n✅ 마이페이지 북마크 상품 수: {len(bookmarked_products)}개")

    # 예금/적금 구분하여 출력
    deposits = [p for p in bookmarked_products if p.get('product_type') == 'deposit']
    savings = [p for p in bookmarked_products if p.get('product_type') == 'saving']

    print(f"\n예금 북마크: {len(deposits)}개")
    for p in deposits:
        print(f"  - {p['fin_prdt_nm']} ({p['kor_co_nm']})")

    print(f"\n적금 북마크: {len(savings)}개")
    for p in savings:
        print(f"  - {p['fin_prdt_nm']} ({p['kor_co_nm']})")

    # 방금 추가한 적금 상품이 있는지 확인
    if any(p['fin_prdt_cd'] == saving_product.fin_prdt_cd for p in bookmarked_products):
        print(f"\n✅ 테스트 성공! 적금 상품 '{saving_product.fin_prdt_nm}'이 마이페이지에 표시됩니다.")
    else:
        print(f"\n❌ 테스트 실패! 적금 상품 '{saving_product.fin_prdt_nm}'이 마이페이지에 표시되지 않습니다.")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()

# 최종 요약
print(f"\n{'=' * 100}")
print("테스트 완료")
print("=" * 100)

print("\n예상 결과:")
print("  - 적금 상품을 북마크하면 SavingRecommendation 테이블에 저장됨")
print("  - 마이페이지 API가 예금과 적금 북마크를 모두 반환함")
print("  - product_type 필드로 예금/적금 구분 가능")
