# stocks/services/news_bundle.py
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from django.utils import timezone

from stocks.models import Stock, StockNews


def _get_datetime_field() -> str | None:
    """
    StockNews의 날짜 필드명이 프로젝트마다 다를 수 있어서 안전하게 선택
    """
    if hasattr(StockNews, "published_at"):
        return "published_at"
    if hasattr(StockNews, "pub_date"):
        return "pub_date"
    return None


def attach_news_topk(reco_result: dict[str, Any], *, days: int = 7, k: int = 3) -> dict[str, Any]:
    """
    reco_result["recommendations"] 각 항목에 news_top3(기본 k=3) 추가
    """
    recos = reco_result.get("recommendations") or []
    if not recos:
        return reco_result

    codes = [r.get("code") for r in recos if r.get("code")]
    if not codes:
        return reco_result

    stocks = list(Stock.objects.filter(code__in=codes).values("id", "code"))
    code_to_id = {s["code"]: s["id"] for s in stocks}
    ids = list(code_to_id.values())
    if not ids:
        return reco_result

    dt_field = _get_datetime_field()

    qs = StockNews.objects.filter(stock_id__in=ids).order_by("-id")
    # 날짜 필드가 있으면 최근 n일로 자름
    if dt_field:
        since = timezone.now() - timedelta(days=days)
        qs = qs.filter(**{f"{dt_field}__gte": since}).order_by(f"-{dt_field}")

    # 1번 쿼리로 다 긁고, 파이썬에서 stock별 Top K만 골라 담기
    bucket: dict[int, list[dict[str, Any]]] = defaultdict(list)

    for n in qs:
        sid = n.stock_id
        if len(bucket[sid]) >= k:
            continue

        item = {
            "title": getattr(n, "title", None),
            "description": getattr(n, "description", None),
            "link": getattr(n, "link", None),
            "originallink": getattr(n, "originallink", None),
            "source": getattr(n, "source", None),
        }

        if dt_field:
            dt_val = getattr(n, dt_field, None)
            try:
                item["published_at"] = dt_val.isoformat() if dt_val else None
            except Exception:
                item["published_at"] = str(dt_val) if dt_val else None

        bucket[sid].append(item)

    # 추천 결과에 붙이기
    for r in recos:
        code = r.get("code")
        sid = code_to_id.get(code)
        r["news_top3"] = bucket.get(sid, [])

    reco_result["news_window_days"] = days
    reco_result["news_topk"] = k
    return reco_result
