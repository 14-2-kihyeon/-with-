from django.urls import path
from . import views


app_name = 'accounts'
urlpatterns = [
    # path('login/', views.login, name='login'),
    # path('logout/', views.logout, name='logout'),
    # path('signup/', views.signup, name='signup'),
    # path('delete/', views.delete, name='delete'),
    # path('update/', views.update, name='update'),
    # path('password/', views.password, name='password'),
    
    # 설문 질문 조회
    path('survey/questions/', views.get_survey_questions, name='survey_questions'),
    
    # 설문 응답 제출 (투자 성향 결과 계산)
    path('survey/submit/', views.submit_survey, name='submit_survey'),
    
    # 내 투자 성향 프로필 조회
    path('investment-profile/', views.get_investment_profile, name='investment_profile'),

    # ==========================================
    # 마이페이지 통합 조회
    # ==========================================

    # 마이페이지 전체 데이터 (프로필 + 모든 북마크)
    path('mypage/', views.get_mypage_data, name='get_mypage_data'),

    # ==========================================
    # 상품 추천 관련
    # ==========================================
    
    # 맞춤 상품 추천
    path('recommendations/', views.recommend_products, name='recommend_products'),
    
    # 추천 상품 북마크 토글
    path('recommendations/<str:fin_prdt_cd>/bookmark/', views.bookmark_recommendation, name='bookmark_recommendation'),
    
    # 북마크한 상품 목록
    path('bookmarks/', views.get_bookmarked_products, name='bookmarked_products'),

    # ==========================================
    # 뉴스 북마크 관련
    # ==========================================

    # 뉴스 북마크 토글 (POST: 추가, DELETE: 제거)
    path('news/<int:news_id>/bookmark/', views.toggle_news_bookmark, name='toggle_news_bookmark'),

    # 내 뉴스 북마크 목록 조회
    path('news/bookmarks/', views.get_news_bookmarks, name='get_news_bookmarks'),

    # ==========================================
    # 유튜브 구독 관련
    # ==========================================

    # 유튜브 채널 구독 토글 (POST: 구독, DELETE: 구독 취소)
    path('youtube/channels/<str:channel_id>/subscribe/', views.toggle_youtube_subscription, name='toggle_youtube_subscription'),

    # 내 유튜브 구독 채널 목록 조회
    path('youtube/subscriptions/', views.get_youtube_subscriptions, name='get_youtube_subscriptions'),

    # ==========================================
    # 나중에 볼 영상 관련
    # ==========================================

    # 나중에 볼 영상 토글 (POST: 추가, DELETE: 제거)
    path('youtube/videos/<str:video_id>/watch-later/', views.toggle_watch_later, name='toggle_watch_later'),

    # 나중에 볼 영상 목록 조회 (?is_watched=true/false)
    path('youtube/watch-later/', views.get_watch_later_list, name='get_watch_later_list'),

    # 영상 시청 완료 표시 (PATCH)
    path('youtube/videos/<str:video_id>/mark-watched/', views.mark_video_watched, name='mark_video_watched'),

    # ==========================================
    # 개발/관리자용
    # ==========================================
    
    # 설문 데이터 초기화 (개발용, is_staff 필요)
    path('survey/initialize/', views.initialize_survey_data, name='initialize_survey'),
]
