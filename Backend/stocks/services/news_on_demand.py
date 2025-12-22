# stocks/services/news_on_demand.py
from __future__ import annotations

import math
from datetime import datetime, timedelta, date as date_type
from typing import Any, Optional

from django.core.cache import cache
from django.utils import timezone

from stocks.models import Stock, StockNews, FeatureDaily
from stocks.services.naver_news_client import NaverNewsClient


def _aware_range_for_asof(as_of: date_type, days: int) -> tuple[datetime, datetime]:
    """
    as_of 기준으로 [as_of-days, as_of+1) 범위의 aware datetime 생성
    """
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(as_of - timedelta(days=days), datetime.min.time()), tz)
    end = timezone.make_aware(datetime.combine(as_of + timedelta(days=1), datetime.min.time()), tz)
    return start, end


def _has_recent_news(stock: Stock, as_of: date_type, days: int = 7) -> bool:
    start_dt, end_dt = _aware_range_for_asof(as_of, days)
    return StockNews.objects.filter(stock=stock, published_at__gte=start_dt, published_at__lt=end_dt).exists()


def ensure_stock_news(
    *,
    stock: Stock,
    as_of: date_type,
    display: int = 20,
    lookback_days: int = 30,
    suffix: str = "주가",
    min_days_for_fetch: int = 7,
    cache_minutes: int = 10,
) -> dict[str, Any]:
    """
    ✅ 핵심: 사용자가 특정 종목을 조회하면 "필요할 때" 뉴스 수집 후 DB 저장

    - as_of 기준 최근 min_days_for_fetch일 내 뉴스가 DB에 하나도 없을 때만 fetch
    - 동일 종목에 대해 cache_minutes 동안은 재호출 방지(네이버 호출 제한/속도)
    """
    # 1) 최근 뉴스가 이미 있으면 스킵
    if _has_recent_news(stock, as_of, days=min_days_for_fetch):
        return {"fetched": False, "reason": "already_has_recent_news", "saved": 0, "skipped_old": 0}

    # 2) 캐시로 과도한 호출 방지
    cache_key = f"news_fetch:{stock.code}"
    if cache.get(cache_key):
        return {"fetched": False, "reason": "cache_hit", "saved": 0, "skipped_old": 0}
    cache.set(cache_key, True, timeout=cache_minutes * 60)

    client = NaverNewsClient()
    query = f"{stock.name} {suffix}".strip()

    cutoff_date = as_of - timedelta(days=lookback_days)

    items = client.search(query=query, display=min(max(display, 1), 100), sort="date")

    saved = 0
    skipped_old = 0

    for it in items:
        pub = it.get("published_at")
        if not pub:
            continue
        if pub.date() < cutoff_date:
            skipped_old += 1
            continue

        link = (it.get("link") or "").strip()
        if not link:
            continue

        # link unique라 중복 저장 방지됨
        _, created = StockNews.objects.get_or_create(
            link=link,
            defaults={
                "stock": stock,
                "published_at": pub,
                "title": (it.get("title") or "")[:500],
                "description": it.get("description") or "",
                "originallink": it.get("originallink") or "",
                "source": "NAVER",
                "query_used": query[:200],
            },
        )
        if created:
            saved += 1

    return {"fetched": True, "reason": "fetched_now", "saved": saved, "skipped_old": skipped_old}


def _news_score(stock: Stock, as_of: date_type, window_days: int, tau: float) -> float:
    start_dt, end_dt = _aware_range_for_asof(as_of, window_days)
    qs = StockNews.objects.filter(stock=stock, published_at__gte=start_dt, published_at__lt=end_dt)

    s = 0.0
    for n in qs:
        delta = (as_of - n.published_at.date()).days
        if delta < 0:
            continue
        s += math.exp(-delta / tau)
    return float(s)


def update_feature_news_scores_if_exists(*, stock: Stock, as_of: date_type) -> dict[str, Any]:
    """
    ✅ FeatureDaily가 이미 존재하면, 그 날짜(as_of)의 news3/news7/news30만 즉시 업데이트
    (build_features로 피처가 만들어진 날에만 의미 있음)
    """
    fd = FeatureDaily.objects.filter(stock=stock, date=as_of).first()
    if not fd:
        return {"updated": False, "reason": "no_feature_daily"}

    fd.news3 = _news_score(stock, as_of, window_days=3, tau=1.5)
    fd.news7 = _news_score(stock, as_of, window_days=7, tau=3.0)
    fd.news30 = _news_score(stock, as_of, window_days=30, tau=10.0)
    fd.save(update_fields=["news3", "news7", "news30"])
    return {"updated": True, "news3": fd.news3, "news7": fd.news7, "news30": fd.news30}


def get_news_topk_for_asof(*, stock: Stock, as_of: date_type, days: int = 7, k: int = 3) -> list[dict[str, Any]]:
    start_dt, end_dt = _aware_range_for_asof(as_of, days)
    qs = (
        StockNews.objects
        .filter(stock=stock, published_at__gte=start_dt, published_at__lt=end_dt)
        .order_by("-published_at")[:k]
    )

    out = []
    for n in qs:
        out.append({
            "title": n.title,
            "description": n.description,
            "link": n.link,
            "originallink": n.originallink,
            "source": n.source,
            "published_at": n.published_at.isoformat() if n.published_at else None,
        })
    return out
