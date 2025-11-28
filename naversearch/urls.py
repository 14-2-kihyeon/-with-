from django.urls import path
from .views import news_search, news_list, news_home, news_detail, toggle_bookmark, summarize_news

urlpatterns = [
    # HTML 페이지
    path("", news_home, name="news-home"),   # /naver/ 같은 prefix로 묶을 거야

    # API
    path("news/search/", news_search, name="news-search"),  # /api/news/search/
    path("news/", news_list, name="news-list"),             # /api/news/
    path("news/<int:pk>/", news_detail, name="news-detail"),  # F03
    path("news/<int:pk>/bookmark/", toggle_bookmark, name="news-bookmark"),  # ★ F04
    path("news/<int:pk>/summary/", summarize_news, name="news-summary"),
]