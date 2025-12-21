# stocks/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("recommendations/", views.recommendations),
    path("recommendations/history/", views.reco_history),
    path("search/", views.search_stocks),

    path("status/", views.status),
    path("status/history/", views.status_history),
    path("health/", views.health),

    path("<str:code>/prices/", views.stock_prices),
    path("<str:code>/news/", views.stock_news),

    # ✅ 새로 추가
    path("<str:code>/explain/", views.stock_explain),

    # ✅ 마지막
    path("<str:code>/", views.stock_detail),
]
