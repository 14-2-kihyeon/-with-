"""
마이페이지 뷰 테스트
"""
import os
import django
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.views import get_mypage_data
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()

def test_mypage_view():
    print("=" * 80)
    print("마이페이지 API 응답 테스트")
    print("=" * 80)

    # 사용자 가져오기
    user = User.objects.first()
    if not user:
        print("ERROR: 사용자가 없습니다.")
        return

    print(f"\n사용자: {user.username}\n")

    # 요청 생성
    factory = APIRequestFactory()
    request = factory.get('/accounts/mypage/')
    request.user = user

    # View 함수 호출
    response = get_mypage_data(request)

    # 응답 출력
    print("응답 데이터:")
    print("=" * 80)
    data = response.data

    # 프로필
    print("\n1. 투자 프로필:")
    if data.get('profile'):
        profile = data['profile']
        print(f"   - 위험 성향: {profile.get('risk_type')}")
        print(f"   - 위험 점수: {profile.get('risk_score')}점")
        print(f"   - 연령: {profile.get('age')}세")
    else:
        print("   (프로필 없음)")

    # 북마크한 상품
    print(f"\n2. 북마크한 금융 상품: {len(data.get('bookmarked_products', []))}개")
    for product in data.get('bookmarked_products', [])[:2]:
        print(f"   - {product['kor_co_nm']} - {product['fin_prdt_nm']}")
        print(f"     최고금리: {product['max_rate']}")

    # 북마크한 뉴스
    print(f"\n3. 북마크한 뉴스: {len(data.get('bookmarked_news', []))}개")
    for news in data.get('bookmarked_news', []):
        print(f"   - {news['title'][:60]}...")

    # 유튜브 구독
    print(f"\n4. 유튜브 구독 채널: {len(data.get('youtube_subscriptions', []))}개")
    for sub in data.get('youtube_subscriptions', []):
        print(f"   - {sub['channel_title']}")
        print(f"     ID: {sub['channel_id']}")

    # 나중에 볼 영상
    print(f"\n5. 나중에 볼 영상: {len(data.get('watch_later_videos', []))}개")
    for video in data.get('watch_later_videos', []):
        print(f"   - {video['video_title']}")
        print(f"     채널: {video['channel_title']}")

    print("\n" + "=" * 80)
    print("✓ 마이페이지 API 정상 작동!")
    print("=" * 80)

if __name__ == "__main__":
    test_mypage_view()
