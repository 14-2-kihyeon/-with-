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
    # 상품 추천 관련
    # ==========================================
    
    # 맞춤 상품 추천
    path('recommendations/', views.recommend_products, name='recommend_products'),
    
    # 추천 상품 북마크 토글
    path('recommendations/<str:fin_prdt_cd>/bookmark/', views.bookmark_recommendation, name='bookmark_recommendation'),
    
    # 북마크한 상품 목록
    path('bookmarks/', views.get_bookmarked_products, name='bookmarked_products'),
    
    # ==========================================
    # 개발/관리자용
    # ==========================================
    
    # 설문 데이터 초기화 (개발용, is_staff 필요)
    path('survey/initialize/', views.initialize_survey_data, name='initialize_survey'),
]
