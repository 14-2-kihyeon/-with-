"""
마이페이지 API 테스트
"""
import os
import django
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import UserNewsBookmark, UserYouTubeSubscription, UserWatchLater
from naversearch.models import News

User = get_user_model()

def test_mypage_setup():
    """테스트 데이터 셋업"""
    print("=" * 80)
    print("마이페이지 테스트 데이터 생성")
    print("=" * 80)

    # 테스트 사용자
    user = User.objects.first()
    if not user:
        print("ERROR: 사용자가 없습니다.")
        return

    print(f"\n사용자: {user.username}")

    # 1. 뉴스 북마크 추가
    print("\n1. 뉴스 북마크 추가 중...")
    news_list = News.objects.all()[:3]
    for news in news_list:
        bookmark, created = UserNewsBookmark.objects.get_or_create(
            user=user,
            news_id=news.id,
            defaults={
                'title': news.title,
                'description': news.description,
                'link': news.link,
                'pub_date': news.pub_date,
            }
        )
        if created:
            print(f"   ✓ 북마크 추가: {news.title[:50]}")

    # 2. 유튜브 채널 구독 추가
    print("\n2. 유튜브 채널 구독 추가 중...")
    test_channels = [
        {
            'channel_id': 'UC_test_finance',
            'channel_title': '금융 전문가 채널',
            'channel_description': '투자 정보 제공',
            'channel_thumbnail': 'https://example.com/thumb1.jpg',
        },
        {
            'channel_id': 'UC_test_stock',
            'channel_title': '주식 투자 가이드',
            'channel_description': '주식 투자 팁',
            'channel_thumbnail': 'https://example.com/thumb2.jpg',
        },
    ]

    for channel_data in test_channels:
        subscription, created = UserYouTubeSubscription.objects.get_or_create(
            user=user,
            channel_id=channel_data['channel_id'],
            defaults={
                'channel_title': channel_data['channel_title'],
                'channel_description': channel_data['channel_description'],
                'channel_thumbnail': channel_data['channel_thumbnail'],
            }
        )
        if created:
            print(f"   ✓ 구독 추가: {channel_data['channel_title']}")

    # 3. 나중에 볼 영상 추가
    print("\n3. 나중에 볼 영상 추가 중...")
    test_videos = [
        {
            'video_id': 'video_test_1',
            'video_title': '초보자를 위한 투자 가이드',
            'video_description': '투자 기초 강의',
            'video_thumbnail': 'https://example.com/video1.jpg',
            'channel_title': '금융 전문가 채널',
            'published_at': '2025-12-20',
        },
        {
            'video_id': 'video_test_2',
            'video_title': 'ETF 투자 전략',
            'video_description': 'ETF 투자 방법',
            'video_thumbnail': 'https://example.com/video2.jpg',
            'channel_title': '주식 투자 가이드',
            'published_at': '2025-12-22',
        },
    ]

    for video_data in test_videos:
        watch_later, created = UserWatchLater.objects.get_or_create(
            user=user,
            video_id=video_data['video_id'],
            defaults={
                'video_title': video_data['video_title'],
                'video_description': video_data['video_description'],
                'video_thumbnail': video_data['video_thumbnail'],
                'channel_title': video_data['channel_title'],
                'published_at': video_data['published_at'],
            }
        )
        if created:
            print(f"   ✓ 영상 추가: {video_data['video_title']}")

    # 통계 출력
    print("\n" + "=" * 80)
    print("생성된 데이터 통계:")
    print("=" * 80)
    print(f"뉴스 북마크:       {UserNewsBookmark.objects.filter(user=user).count()}개")
    print(f"유튜브 구독 채널:  {UserYouTubeSubscription.objects.filter(user=user).count()}개")
    print(f"나중에 볼 영상:    {UserWatchLater.objects.filter(user=user).count()}개")
    print("=" * 80)

if __name__ == "__main__":
    test_mypage_setup()
