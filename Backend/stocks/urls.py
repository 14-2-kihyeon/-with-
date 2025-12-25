# stocks/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ✅ Market (대시보드)
    path("market/summary/", views.market_summary),
    path("market/prices/", views.market_prices),

    # ✅ 환율: snapshot / latest 둘 다 살려두기
    path("market/fx/snapshot/", views.fx_snapshot),  # <- 너의 프론트가 지금 호출하는 것
    path("market/fx/", views.fx_latest),

    # ✅ 지수
    path("market/index/snapshot/", views.market_index_snapshot),
    path("market/index/<str:symbol>/series/", views.market_index_series),

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
    path("<str:code>/realtime/", views.stock_realtime_price),
    path("<str:code>/intraday/", views.stock_intraday_prices),

    # ✅ 마지막
    path("<str:code>/", views.stock_detail),
]
