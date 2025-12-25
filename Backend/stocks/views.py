# stocks/views.py
from __future__ import annotations

from datetime import datetime, timedelta, date as date_type

from django.db.models import Sum
from django.db.models import Q
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as drf_status

from .models import Stock, DailyPrice, FeatureDaily, StockNews, UpdateLog
from .services.recommender import recommend_stocks
from .services.news_bundle import attach_news_topk
from stocks.services.reco_utils import resolve_best_as_of
from stocks.services.naver_news_client import NaverNewsClient

from stocks.services.llm_client import gms_chat
from stocks.services.explain import build_explain_messages
from stocks.services.yfinance_client import YFinanceClient


# -------------------------
# 공용 유틸
# -------------------------
def parse_date_any(s: str | None) -> date_type | None:
    """
    '20251218' 또는 '2025-12-18' 모두 지원
    """
    if not s:
        return None
    s = s.strip()
    try:
        if len(s) == 8 and s.isdigit():
            return datetime.strptime(s, "%Y%m%d").date()
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def get_as_of(request) -> date_type:
    q = request.query_params.get("date")
    d = parse_date_any(q)
    return d or timezone.localdate()


def bool_q(v) -> bool:
    return str(v).lower() in ("1", "true", "yes", "y")


def serialize_feature(fd: FeatureDaily) -> dict:
    """
    FeatureDaily 필드가 프로젝트마다 조금씩 다를 수 있어서
    '있는 것만' 안전하게 내려줌
    """
    keys = [
        "r1", "r5", "r20", "r60",
        "vol10", "vol20", "vol60", "vol",
        "mdd10", "mdd20", "mdd60", "mdd",

        # ✅ build_features 실제 생성 필드명
        "vz5", "vz20",

        # (혹시 다른 프로젝트에서 쓰는 이름도 지원)
        "volume_z5", "volume_z20", "volume_z",

        "news3", "news7", "news30", "news",
    ]
    out = {"date": str(fd.date)}
    for k in keys:
        if hasattr(fd, k):
            v = getattr(fd, k)
            if v is None:
                continue
            try:
                out[k] = float(v)
            except Exception:
                out[k] = v
    return out


def _news_datetime_field() -> str | None:
    if hasattr(StockNews, "published_at"):
        return "published_at"
    if hasattr(StockNews, "pub_date"):
        return "pub_date"
    return None


def standard_not_found(*, code: str, endpoint: str):
    # ✅ 404여도 프론트가 파싱하기 쉬운 형태
    return Response(
        {
            "endpoint": endpoint,
            "code": code,
            "name": None,
            "count": 0,
            "detail": "존재하지 않는 종목입니다.",
        },
        status=drf_status.HTTP_404_NOT_FOUND,
    )


def fetch_and_store_news(
    *,
    stock: Stock,
    display: int = 20,
    lookback_days: int = 30,
    suffix: str = "주가",
):
    """
    네이버 뉴스 수집 + StockNews 저장
    - 키 없거나 실패해도 예외를 밖으로 던지지 않고 (ok=False)로 반환
    """
    cutoff = timezone.now() - timedelta(days=lookback_days)
    query = f"{stock.name} {suffix}".strip()

    try:
        client = NaverNewsClient()
        items = client.search(query=query, display=display, sort="date")
    except Exception as e:
        return {"ok": False, "saved": 0, "reason": f"naver_fetch_failed: {e}"}

    saved = 0
    for it in items:
        pub = it.get("published_at")
        link = it.get("link") or ""
        if not pub or not link:
            continue

        # 오래된 뉴스 제외
        try:
            if pub < cutoff:
                continue
        except Exception:
            pass

        obj, created = StockNews.objects.get_or_create(
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

    return {"ok": True, "saved": saved, "reason": "fetched_now"}


# -------------------------
# 1) 추천 API (항상 같은 키)
# -------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])  # 로그인 필요로 변경
def recommendations(request):
    """
    GET /api/stocks/recommendations/?date=20251218&risk=MID&horizon=MID&top=20&auto=1&include_news=1
    - 프론트 편하게: 항상 같은 키 반환
    - auto=1이면 해당 날짜 데이터 없을 때 최신 as_of로 자동 fallback
    - 사용자 프로필을 고려한 추천 (나이, 소득, 투자 목표 등)
    """
    from accounts.models import InvestmentProfile

    requested_as_of = get_as_of(request)

    # 사용자 프로필 가져오기
    user_profile = None
    try:
        profile = request.user.investment_profile
        user_profile = {
            'risk_type': profile.risk_type,
            'risk_score': profile.risk_score,
            'age': profile.age,
            'gender': profile.gender,
            'income': profile.income,
            'savings': profile.savings,
            'investment_goal': profile.investment_goal,
            'investment_period': profile.investment_period,
        }
    except InvestmentProfile.DoesNotExist:
        user_profile = None

    risk = (request.query_params.get("risk") or "MID").upper()
    horizon = (request.query_params.get("horizon") or "MID").upper()
    top_n = int(request.query_params.get("top") or 20)

    include_news_q = request.query_params.get("include_news")
    include_news = True if include_news_q is None else bool_q(include_news_q)

    auto_q = request.query_params.get("auto")
    auto = True if auto_q is None else bool_q(auto_q)

    # 1) 먼저 요청 날짜로 추천 시도 (사용자 프로필 포함)
    as_of_used = requested_as_of
    result = recommend_stocks(
        as_of=as_of_used,
        risk=risk,
        horizon=horizon,
        top_n=top_n,
        effort="OPTIMIZE",
        include_news=include_news,
        user_profile=user_profile,  # 사용자 프로필 전달
    )

    # 2) 데이터 없으면(auto=1) 최신 as_of로 fallback
    if not isinstance(result, dict) or ("recommendations" not in result):
        if auto:
            best = resolve_best_as_of()
            if best and best != as_of_used:
                as_of_used = best
                result = recommend_stocks(
                    as_of=as_of_used,
                    risk=risk,
                    horizon=horizon,
                    top_n=top_n,
                    effort="OPTIMIZE",
                    include_news=include_news,
                    user_profile=user_profile,  # 사용자 프로필 전달
                )

    # 3) 그래도 데이터 없으면 "표준 형태"로 빈 추천 내려주기
    if not isinstance(result, dict) or ("recommendations" not in result):
        return Response(
            {
                "endpoint": "recommendations",
                "requested_as_of": str(requested_as_of),
                "as_of_used": str(as_of_used),
                "profile": {"risk": risk, "horizon": horizon, "effort": "OPTIMIZE"},
                "include_news": bool(include_news),
                "auto": bool(auto),

                "weights": None,
                "feature_fields_used": None,

                "count": 0,
                "recommendations": [],
                "detail": (result.get("detail") if isinstance(result, dict) else None)
                          or f"FeatureDaily 데이터가 없습니다: date={requested_as_of}",
                "error": None,
            },
            status=drf_status.HTTP_200_OK,
        )

    # 4) 항상 키 존재하도록 보정
    result.setdefault("recommendations", [])
    result["count"] = len(result["recommendations"])

    # ✅ 프론트 고정 키
    result["endpoint"] = "recommendations"
    result["requested_as_of"] = str(requested_as_of)
    result["as_of_used"] = str(as_of_used)
    result["include_news"] = bool(include_news)
    result["auto"] = bool(auto)
    result.setdefault("detail", None)
    result.setdefault("error", None)

    # 5) 뉴스 top3 붙이기(추천이 있을 때만)
    if include_news and result["recommendations"]:
        result = attach_news_topk(result, days=7, k=3)
        result.setdefault("news_window_days", 7)
        result.setdefault("news_topk", 3)

    return Response(result, status=drf_status.HTTP_200_OK)


# -------------------------
# 2) 검색 API
# -------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def search_stocks(request):
    """
    GET /api/stocks/search/?q=삼성
    """
    q = (request.query_params.get("q") or "").strip()
    if not q:
        return Response(
            {
                "endpoint": "search_stocks",
                "q": q,
                "count": 0,
                "results": [],
                "detail": "q 파라미터가 필요합니다.",
                "error": None,
            },
            status=drf_status.HTTP_400_BAD_REQUEST,
        )

    qs = Stock.objects.filter(Q(code__icontains=q) | Q(name__icontains=q)).order_by("code")[:50]
    data = [{"code": s.code, "name": s.name, "market": getattr(s, "market", None)} for s in qs]
    return Response(
        {
            "endpoint": "search_stocks",
            "q": q,
            "count": len(data),
            "results": data,
            "detail": None,
            "error": None,
        },
        status=drf_status.HTTP_200_OK,
    )


# -------------------------
# 3) 차트(가격 시계열) API
# -------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def stock_prices(request, code: str):
    """
    GET /api/stocks/<code>/prices/?from=2025-10-01&to=2025-12-18
    """
    stock = Stock.objects.filter(code=code).first()
    if not stock:
        return Response(
            {
                "endpoint": "stock_prices",
                "code": code,
                "name": None,
                "from": request.query_params.get("from"),
                "to": request.query_params.get("to"),
                "count": 0,
                "prices": [],
                "detail": "존재하지 않는 종목입니다.",
                "error": None,
            },
            status=drf_status.HTTP_404_NOT_FOUND,
        )

    d1 = parse_date_any(request.query_params.get("from"))
    d2 = parse_date_any(request.query_params.get("to"))

    qs = DailyPrice.objects.filter(stock=stock).order_by("date")
    if d1:
        qs = qs.filter(date__gte=d1)
    if d2:
        qs = qs.filter(date__lte=d2)
    qs = qs[:1500]

    prices = [{
        "date": str(p.date),
        "open": getattr(p, "open", None),
        "high": getattr(p, "high", None),
        "low": getattr(p, "low", None),
        "close": getattr(p, "close", None),
        "volume": getattr(p, "volume", None),
        "amount": getattr(p, "amount", None),
    } for p in qs]

    return Response(
        {
            "endpoint": "stock_prices",
            "code": stock.code,
            "name": stock.name,
            "from": str(d1) if d1 else None,
            "to": str(d2) if d2 else None,
            "count": len(prices),
            "prices": prices,
            "detail": None,
            "error": None,
        },
        status=drf_status.HTTP_200_OK,
    )


# -------------------------
# 4) 종목 상세(피처 포함) API (항상 같은 키 + auto fallback)
# -------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def stock_detail(request, code: str):
    """
    GET /api/stocks/<code>/?date=20251218&auto=1
    """
    requested_as_of = get_as_of(request)
    auto = bool_q(request.query_params.get("auto", "1"))

    stock = Stock.objects.filter(code=code).first()
    if not stock:
        return Response(
            {
                "endpoint": "stock_detail",
                "code": code,
                "name": None,
                "market": None,
                "requested_as_of": str(requested_as_of),
                "as_of_used": str(requested_as_of),
                "auto": bool(auto),
                "feature": None,
                "latest_feature_date": None,
                "detail": "존재하지 않는 종목입니다.",
                "error": None,
            },
            status=drf_status.HTTP_404_NOT_FOUND,
        )

    fd = FeatureDaily.objects.filter(stock=stock, date=requested_as_of).first()
    latest_fd = FeatureDaily.objects.filter(stock=stock).order_by("-date").first()

    as_of_used = requested_as_of
    detail = None

    if not fd and auto and latest_fd:
        fd = latest_fd
        as_of_used = latest_fd.date
        detail = f"요청 날짜({requested_as_of})의 지표가 없어 최신 지표({as_of_used})로 대체했습니다."

    return Response(
        {
            "endpoint": "stock_detail",
            "code": stock.code,
            "name": stock.name,
            "market": getattr(stock, "market", None),

            "requested_as_of": str(requested_as_of),
            "as_of_used": str(as_of_used),
            "auto": bool(auto),

            "feature": serialize_feature(fd) if fd else None,
            "latest_feature_date": str(latest_fd.date) if latest_fd else None,

            "detail": detail,
            "error": None,
        },
        status=drf_status.HTTP_200_OK,
    )


# -------------------------
# 5) 종목 뉴스 API (항상 items + refresh=1 강제 수집)
# -------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def stock_news(request, code: str):
    """
    GET /api/stocks/<code>/news/?days=7&limit=30&refresh=1
    """
    stock = Stock.objects.filter(code=code).first()
    days = int(request.query_params.get("days") or 7)
    limit = int(request.query_params.get("limit") or 50)
    limit = min(max(limit, 1), 200)

    refresh = bool_q(request.query_params.get("refresh", "0"))

    if not stock:
        return Response(
            {
                "endpoint": "stock_news",
                "code": code,
                "name": None,
                "days": days,
                "limit": limit,
                "count": 0,
                "items": [],
                "news_fetch": {"fetched": False, "saved": 0, "reason": "stock_not_found"},
                "detail": "존재하지 않는 종목입니다.",
                "error": None,
            },
            status=drf_status.HTTP_404_NOT_FOUND,
        )

    dt_field = _news_datetime_field()

    def _load_items():
        qs = StockNews.objects.filter(stock=stock)
        if dt_field:
            since = timezone.now() - timedelta(days=days)
            qs = qs.filter(**{f"{dt_field}__gte": since}).order_by(f"-{dt_field}")
        else:
            qs = qs.order_by("-id")
        qs = qs[:limit]

        out = []
        for n in qs:
            item = {
                "title": getattr(n, "title", None),
                "description": getattr(n, "description", None),
                "link": getattr(n, "link", None),
                "originallink": getattr(n, "originallink", None),
                "source": getattr(n, "source", None),
            }
            if dt_field:
                dt = getattr(n, dt_field, None)
                try:
                    item["published_at"] = dt.isoformat() if dt else None
                except Exception:
                    item["published_at"] = str(dt) if dt else None
            out.append(item)
        return out

    items = _load_items()
    news_fetch = {"fetched": False, "saved": 0, "reason": "already_has_news" if items else "no_news_in_db"}

    # ✅ DB에 없거나 refresh=1이면 수집/저장 시도
    if refresh or not items:
        res = fetch_and_store_news(stock=stock, display=max(20, limit), lookback_days=30, suffix="주가")
        if res["ok"]:
            news_fetch = {"fetched": True, "saved": res["saved"], "reason": res["reason"]}
        else:
            news_fetch = {"fetched": False, "saved": 0, "reason": res["reason"]}

        items = _load_items()

    return Response(
        {
            "endpoint": "stock_news",
            "code": stock.code,
            "name": stock.name,
            "days": days,
            "limit": limit,
            "count": len(items),
            "items": items,
            "news_fetch": news_fetch,
            "detail": None,
            "error": None,
        },
        status=drf_status.HTTP_200_OK,
    )


# -------------------------
# 6) AI 설명 API (항상 같은 키 + refresh_news 옵션)
# -------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def stock_explain(request, code: str):
    """
    POST /api/stocks/<code>/explain/?date=20251218&auto=1&refresh_news=1
    body: { "question": "왜 이 종목이 추천됐어?" }
    """
    requested_as_of = get_as_of(request)
    body = request.data or {}

    if isinstance(body, dict) and body.get("date"):
        d = parse_date_any(str(body.get("date")))
        if d:
            requested_as_of = d

    auto = bool_q(request.query_params.get("auto", "1"))
    refresh_news = bool_q(request.query_params.get("refresh_news", "0"))

    question = (body.get("question") or "").strip() or "왜 추천됐는지 지표와 뉴스 근거로 설명해줘."

    stock = Stock.objects.filter(code=code).first()
    if not stock:
        return Response(
            {
                "endpoint": "stock_explain",
                "code": code,
                "name": None,
                "requested_as_of": str(requested_as_of),
                "as_of_used": str(requested_as_of),
                "auto": bool(auto),
                "refresh_news": bool(refresh_news),

                "question": question,
                "answer": "",

                "feature": None,
                "news_top3": [],
                "used": {"feature_available": False, "news_count": 0, "news_fetch": None},

                "detail": "존재하지 않는 종목입니다.",
                "error": None,
            },
            status=drf_status.HTTP_404_NOT_FOUND,
        )

    # feature: 요청일 -> 없으면 최신으로 fallback (auto=1)
    fd = FeatureDaily.objects.filter(stock=stock, date=requested_as_of).first()
    latest_fd = FeatureDaily.objects.filter(stock=stock).order_by("-date").first()

    as_of_used = requested_as_of
    detail = None
    if not fd and auto and latest_fd:
        fd = latest_fd
        as_of_used = latest_fd.date
        detail = f"요청 날짜({requested_as_of})의 지표가 없어 최신 지표({as_of_used})로 대체했습니다."

    feature = serialize_feature(fd) if fd else None
    as_of_str = str(as_of_used)

    dt_field = _news_datetime_field()

    def _load_top3():
        qs = StockNews.objects.filter(stock=stock)
        if dt_field:
            since = timezone.now() - timedelta(days=7)
            qs = qs.filter(**{f"{dt_field}__gte": since}).order_by(f"-{dt_field}")
        else:
            qs = qs.order_by("-id")
        return list(qs[:3])

    news_fetch_info = None
    news_objs = _load_top3()

    if refresh_news or (len(news_objs) == 0):
        res = fetch_and_store_news(stock=stock, display=30, lookback_days=30, suffix="주가")
        news_fetch_info = {
            "fetched": bool(res.get("ok")),
            "saved": int(res.get("saved") or 0),
            "reason": res.get("reason"),
        }
        news_objs = _load_top3()
    else:
        news_fetch_info = {"fetched": False, "saved": 0, "reason": "already_has_news"}

    news_top3 = []
    for n in news_objs:
        item = {
            "title": getattr(n, "title", None),
            "description": getattr(n, "description", None),
            "link": getattr(n, "link", None),
            "originallink": getattr(n, "originallink", None),
            "source": getattr(n, "source", None),
        }
        if dt_field:
            dt = getattr(n, dt_field, None)
            try:
                item["published_at"] = dt.isoformat() if dt else None
            except Exception:
                item["published_at"] = str(dt) if dt else None
        news_top3.append(item)

    messages = build_explain_messages(
        code=stock.code,
        name=stock.name,
        as_of=as_of_str,
        question=question,
        feature=feature,
        weights=None,
        components=None,
        news_topk=news_top3,
    )

    answer = ""
    error = None

    try:
        answer = gms_chat(messages=messages, model="gpt-5-mini", timeout=(10, 120))

        # ✅ 줄바꿈은 유지하고, 과한 공백만 정리
        answer = (answer or "").replace("\r\n", "\n").replace("\r", "\n").strip()

    except Exception as e:
        error = str(e)

    return Response(
        {
            "endpoint": "stock_explain",
            "code": stock.code,
            "name": stock.name,
            "requested_as_of": str(requested_as_of),
            "as_of_used": str(as_of_used),
            "auto": bool(auto),
            "refresh_news": bool(refresh_news),

            "question": question,
            "answer": answer,

            "feature": feature,
            "news_top3": news_top3,
            "used": {
                "feature_available": bool(feature),
                "news_count": len(news_top3),
                "news_fetch": news_fetch_info,
            },

            "detail": detail if not error else "AI 설명 생성 중 오류",
            "error": error,
        },
        status=drf_status.HTTP_200_OK,
    )


# -------------------------
# 상태/운영 API들 (프론트-friendly 형태로 약간 보정)
# -------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def status(request):
    latest = UpdateLog.objects.order_by("-as_of").first()
    if not latest:
        return Response(
            {
                "endpoint": "status",
                "as_of": None,
                "status": None,
                "started_at": None,
                "finished_at": None,
                "dry_run": None,
                "message": None,
                "warnings": None,
                "detail": "UpdateLog가 없습니다.",
                "error": None,
            },
            status=drf_status.HTTP_200_OK,
        )

    return Response(
        {
            "endpoint": "status",
            "as_of": str(latest.as_of),
            "status": getattr(latest, "status", None),
            "started_at": getattr(latest, "started_at", None),
            "finished_at": getattr(latest, "finished_at", None),
            "dry_run": getattr(latest, "dry_run", None),
            "message": getattr(latest, "message", None),
            "warnings": getattr(latest, "warnings", None),
            "detail": None,
            "error": None,
        },
        status=drf_status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def status_history(request):
    limit = int(request.query_params.get("limit") or 30)
    limit = min(max(limit, 1), 200)

    qs = UpdateLog.objects.order_by("-as_of")[:limit]
    items = []
    for u in qs:
        items.append({
            "as_of": str(u.as_of),
            "status": getattr(u, "status", None),
            "started_at": getattr(u, "started_at", None),
            "finished_at": getattr(u, "finished_at", None),
            "dry_run": getattr(u, "dry_run", None),
            "message": getattr(u, "message", None),
            "warnings": getattr(u, "warnings", None),
        })

    return Response(
        {
            "endpoint": "status_history",
            "count": len(items),
            "items": items,
            "detail": None,
            "error": None,
        },
        status=drf_status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    latest_price = DailyPrice.objects.order_by("-date").values_list("date", flat=True).first()
    latest_feature = FeatureDaily.objects.order_by("-date").values_list("date", flat=True).first()

    dt_field = _news_datetime_field()
    latest_news = None
    if dt_field:
        latest_news = StockNews.objects.order_by(f"-{dt_field}").values_list(dt_field, flat=True).first()

    return Response(
        {
            "endpoint": "health",
            "counts": {
                "stocks": Stock.objects.count(),
                "daily_prices": DailyPrice.objects.count(),
                "feature_daily": FeatureDaily.objects.count(),
                "stock_news": StockNews.objects.count(),
            },
            "latest": {
                "price_date": str(latest_price) if latest_price else None,
                "feature_date": str(latest_feature) if latest_feature else None,
                "news_datetime": latest_news.isoformat() if latest_news else None,
            },
            "detail": None,
            "error": None,
        },
        status=drf_status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def reco_history(request):
    """
    RecommendationLog가 있으면 보여주고, 없으면 빈 리스트
    """
    try:
        from .models import RecommendationLog
    except Exception:
        return Response(
            {
                "endpoint": "reco_history",
                "count": 0,
                "items": [],
                "detail": "RecommendationLog 모델이 없습니다.",
                "error": None,
            },
            status=drf_status.HTTP_200_OK,
        )

    limit = int(request.query_params.get("limit") or 50)
    limit = min(max(limit, 1), 200)

    qs = RecommendationLog.objects.order_by("-id")[:limit]
    items = []
    for r in qs:
        items.append({
            "id": r.id,
            "as_of": str(getattr(r, "as_of", "")) if getattr(r, "as_of", None) else None,
            "risk": getattr(r, "risk", None),
            "horizon": getattr(r, "horizon", None),
            "effort": getattr(r, "effort", None),
            "created_at": getattr(r, "created_at", None),
            "payload": getattr(r, "payload", None),
        })

    return Response(
        {
            "endpoint": "reco_history",
            "count": len(items),
            "items": items,
            "detail": None,
            "error": None,
        },
        status=drf_status.HTTP_200_OK,
    )


from .models import MarketIndex, MarketIndexDaily, FxRateDaily

def _week_key(d):
    # ISO year-week
    y, w, _ = d.isocalendar()
    return (y, w)

def _to_weekly(rows: list[dict]) -> list[dict]:
    if not rows:
        return []
    out = []
    cur_key = None
    bucket = None

    for r in rows:
        d = datetime.strptime(r["date"], "%Y-%m-%d").date()
        k = _week_key(d)
        if k != cur_key:
            if bucket:
                out.append(bucket)
            cur_key = k
            bucket = {
                "date": r["date"],  # 그 주의 첫 날짜로 표시
                "open": r.get("open"),
                "high": r.get("high"),
                "low": r.get("low"),
                "close": r.get("close"),
                "volume": r.get("volume"),
            }
        else:
            # high/low 갱신, close는 마지막 값
            if bucket.get("high") is None or (r.get("high") is not None and r["high"] > bucket["high"]):
                bucket["high"] = r.get("high")
            if bucket.get("low") is None or (r.get("low") is not None and r["low"] < bucket["low"]):
                bucket["low"] = r.get("low")
            bucket["close"] = r.get("close")
            if bucket.get("volume") is not None and r.get("volume") is not None:
                bucket["volume"] += r["volume"]

    if bucket:
        out.append(bucket)
    return out


@api_view(["GET"])
@permission_classes([AllowAny])
def market_index_series(request, symbol: str):
    """
    GET /api/stocks/market/index/<symbol>/series/?from=YYYY-MM-DD&to=YYYY-MM-DD&interval=day|week
    """
    interval = (request.query_params.get("interval") or "day").lower()
    d1 = parse_date_any(request.query_params.get("from"))
    d2 = parse_date_any(request.query_params.get("to"))

    idx = MarketIndex.objects.filter(symbol=symbol).first()
    if not idx:
        return Response(
            {"endpoint":"market_index_series","symbol":symbol,"count":0,"series":[],"detail":"존재하지 않는 지수입니다.","error":None},
            status=drf_status.HTTP_404_NOT_FOUND,
        )

    qs = MarketIndexDaily.objects.filter(index=idx).order_by("date")
    if d1: qs = qs.filter(date__gte=d1)
    if d2: qs = qs.filter(date__lte=d2)
    qs = qs[:3000]

    series = [{
        "date": str(p.date),
        "open": p.open,
        "high": p.high,
        "low": p.low,
        "close": p.close,
        "volume": p.volume,
    } for p in qs]

    if interval == "week":
        series = _to_weekly(series)

    # 최신값/등락 계산
    latest = series[-1]["close"] if len(series) >= 1 else None
    prev = series[-2]["close"] if len(series) >= 2 else None
    change = (latest - prev) if (latest is not None and prev is not None) else None
    change_pct = (change / prev * 100.0) if (change is not None and prev) else None

    return Response(
        {
            "endpoint": "market_index_series",
            "symbol": idx.symbol,
            "name": idx.name or idx.symbol,
            "from": str(d1) if d1 else None,
            "to": str(d2) if d2 else None,
            "interval": interval,
            "count": len(series),
            "latest": {"value": latest, "change": change, "change_pct": change_pct},
            "series": series,
            "detail": None,
            "error": None,
        },
        status=drf_status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def market_index_snapshot(request):
    """
    GET /api/stocks/market/index/snapshot/?symbols=KS11,KQ11,KS200,KQ150,KRX100
    """
    raw = (request.query_params.get("symbols") or "KS11,KQ11,KS200,KQ150,KRX100").strip()
    symbols = [s.strip() for s in raw.split(",") if s.strip()][:20]

    items = []
    for sym in symbols:
        idx = MarketIndex.objects.filter(symbol=sym).first()
        if not idx:
            items.append({"symbol": sym, "name": sym, "value": None, "change": None, "change_pct": None})
            continue

        last2 = list(MarketIndexDaily.objects.filter(index=idx).order_by("-date").values("close","date")[:2])
        if not last2:
            items.append({"symbol": idx.symbol, "name": idx.name or idx.symbol, "value": None, "change": None, "change_pct": None})
            continue

        latest = float(last2[0]["close"])
        prev = float(last2[1]["close"]) if len(last2) > 1 else None
        change = (latest - prev) if prev is not None else None
        change_pct = (change / prev * 100.0) if (change is not None and prev) else None

        items.append({
            "symbol": idx.symbol,
            "name": idx.name or idx.symbol,
            "date": str(last2[0]["date"]),
            "value": latest,
            "change": change,
            "change_pct": change_pct,
        })

    return Response(
        {"endpoint":"market_index_snapshot","count":len(items),"items":items,"detail":None,"error":None},
        status=drf_status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def market_summary(request):
    """
    GET /api/stocks/market/summary/?date=YYYYMMDD&auto=1&market=KOSPI|KOSDAQ|ALL
    - breadth(상승/하락/보합/unknown)
    - turnover(거래량/거래대금)
    - top movers (상승/하락)
    """
    requested_as_of = get_as_of(request)
    auto = bool_q(request.query_params.get("auto", "1"))
    market = (request.query_params.get("market") or "ALL").upper()

    as_of_used = requested_as_of
    base = FeatureDaily.objects.filter(date=as_of_used)

    if not base.exists() and auto:
        best = resolve_best_as_of()
        if best:
            as_of_used = best
            base = FeatureDaily.objects.filter(date=as_of_used)

    # market 필터 (stock.market가 비어있으면 ALL로 동작)
    if market != "ALL":
        base = base.filter(stock__market=market)

    total = base.count()
    adv = base.filter(r1__gt=0).count()
    dec = base.filter(r1__lt=0).count()
    unch = base.filter(r1=0).count()
    unknown = base.filter(r1__isnull=True).count()

    # 거래량/대금 합계 (DailyPrice 기준)
    price_qs = DailyPrice.objects.filter(date=as_of_used)
    if market != "ALL":
        price_qs = price_qs.filter(stock__market=market)

    agg = price_qs.aggregate(
        volume=Sum("volume"),
        amount=Sum("amount"),
    )

    # Top movers (r1 기준)
    gainers = list(base.filter(r1__isnull=False).order_by("-r1").values("stock__code","stock__name","r1")[:5])
    losers = list(base.filter(r1__isnull=False).order_by("r1").values("stock__code","stock__name","r1")[:5])

    # close 붙이기
    codes = [x["stock__code"] for x in gainers] + [x["stock__code"] for x in losers]
    price_map = {
        (p["stock__code"]): p
        for p in DailyPrice.objects.filter(date=as_of_used, stock__code__in=codes)
            .values("stock__code","close","volume","amount")
    }

    def _enrich(rows):
        out = []
        for r in rows:
            code = r["stock__code"]
            p = price_map.get(code, {})
            out.append({
                "code": code,
                "name": r["stock__name"],
                "r1": float(r["r1"]),
                "close": p.get("close"),
                "volume": p.get("volume"),
                "amount": p.get("amount"),
            })
        return out

    return Response(
        {
            "endpoint": "market_summary",
            "requested_as_of": str(requested_as_of),
            "as_of_used": str(as_of_used),
            "market": market,
            "breadth": {"adv": adv, "dec": dec, "unch": unch, "unknown": unknown, "total": total},
            "turnover": {"volume": agg.get("volume"), "amount": agg.get("amount")},
            "top": {"gainers": _enrich(gainers), "losers": _enrich(losers)},
            "detail": None if total else "해당 날짜 FeatureDaily가 없습니다.",
            "error": None,
        },
        status=drf_status.HTTP_200_OK,
    )
    
    
@api_view(["GET"])
@permission_classes([AllowAny])
def fx_snapshot(request):
    """
    GET /api/stocks/market/fx/snapshot/
    DB에 저장된 환율에서 '최신 1개 + 직전 1개'로 change 계산 (주말/휴장 대응)
    """
    pairs = ["USD/KRW", "JPY/KRW", "EUR/KRW", "CNY/KRW"]

    items = []
    as_of = None

    for pair in pairs:
        last2 = list(
            FxRateDaily.objects
            .filter(pair=pair)
            .order_by("-date")
            .values("date", "close")[:2]
        )

        if not last2:
            items.append({"pair": pair, "date": None, "rate": None, "change": None, "change_pct": None})
            continue

        latest = float(last2[0]["close"]) if last2[0]["close"] is not None else None
        prev = float(last2[1]["close"]) if (len(last2) > 1 and last2[1]["close"] is not None) else None

        change = (latest - prev) if (latest is not None and prev is not None) else None
        change_pct = (change / prev * 100.0) if (change is not None and prev not in (None, 0)) else None

        d = str(last2[0]["date"])
        as_of = d if as_of is None else max(as_of, d)

        items.append({
            "pair": pair,
            "date": d,
            "rate": latest,
            "change": change,
            "change_pct": change_pct,
        })

    return Response(
        {"endpoint": "fx_snapshot", "as_of": as_of, "count": len(items), "items": items, "detail": None, "error": None},
        status=drf_status.HTTP_200_OK,
    )
    
def _parse_ymd(s):
    if not s:
        return None
    s = str(s).strip()
    try:
        if len(s) == 10 and "-" in s:
            return datetime.strptime(s, "%Y-%m-%d").date()
        if len(s) == 8 and s.isdigit():
            return datetime.strptime(s, "%Y%m%d").date()
    except Exception:
        return None
    return None


@api_view(["GET"])
@permission_classes([AllowAny])
def market_prices(request):
    """
    GET /api/stocks/market/prices/?symbol=KS11&from=2025-01-01&to=2025-12-22
    """
    symbol = (request.query_params.get("symbol") or "KS11").strip()
    d1 = _parse_ymd(request.query_params.get("from") or request.query_params.get("start"))
    d2 = _parse_ymd(request.query_params.get("to") or request.query_params.get("end")) or timezone.localdate()

    idx = MarketIndex.objects.filter(symbol=symbol).first()
    if not idx:
        return Response(
            {"endpoint": "market_prices", "symbol": symbol, "count": 0, "prices": [], "detail": "지수(symbol)를 찾을 수 없습니다.", "error": None},
            status=drf_status.HTTP_404_NOT_FOUND,
        )

    qs = MarketIndexDaily.objects.filter(index=idx).order_by("date")
    if d1:
        qs = qs.filter(date__gte=d1)
    if d2:
        qs = qs.filter(date__lte=d2)
    qs = qs[:4000]

    prices = [{"date": str(p.date), "close": float(p.close) if p.close is not None else None} for p in qs]

    latest = None
    if len(prices) >= 2 and prices[-1]["close"] is not None and prices[-2]["close"] is not None:
        cur = prices[-1]["close"]
        prev = prices[-2]["close"]
        ch = cur - prev
        pct = (ch / prev * 100) if prev else None
        latest = {"date": prices[-1]["date"], "value": cur, "change": ch, "change_pct": pct}
    elif len(prices) == 1:
        latest = {"date": prices[-1]["date"], "value": prices[-1]["close"], "change": None, "change_pct": None}

    return Response(
        {
            "endpoint": "market_prices",
            "symbol": idx.symbol,
            "name": getattr(idx, "name", idx.symbol),
            "from": str(d1) if d1 else None,
            "to": str(d2) if d2 else None,
            "count": len(prices),
            "prices": prices,
            "latest": latest,
            "detail": None,
            "error": None,
        },
        status=drf_status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def fx_latest(request):
    """
    GET /api/stocks/market/fx/?pairs=USD/KRW,JPY/KRW,EUR/KRW,CNY/KRW
    """
    raw = (request.query_params.get("pairs") or "").strip()
    pairs = [p.strip() for p in raw.split(",") if p.strip()] or ["USD/KRW", "JPY/KRW", "EUR/KRW", "CNY/KRW"]

    import FinanceDataReader as fdr

    end = timezone.localdate()
    start = end - timedelta(days=14)

    items = []
    for pair in pairs:
        try:
            df = fdr.DataReader(pair, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        except Exception:
            df = None

        if df is None or getattr(df, "empty", True):
            items.append({"pair": pair, "date": None, "value": None, "change": None, "change_pct": None})
            continue

        close_col = "Close" if "Close" in df.columns else df.columns[0]
        s = df[close_col].dropna()
        if len(s) == 0:
            items.append({"pair": pair, "date": None, "value": None, "change": None, "change_pct": None})
            continue

        last = float(s.iloc[-1])
        dt = s.index[-1]
        d = dt.date().isoformat() if hasattr(dt, "date") else str(dt)

        if len(s) >= 2:
            prev = float(s.iloc[-2])
            ch = last - prev
            pct = (ch / prev * 100) if prev else None
        else:
            ch, pct = None, None

        items.append({"pair": pair, "date": d, "value": last, "change": ch, "change_pct": pct})

    as_of = next((it["date"] for it in items if it["date"]), None)

    return Response(
        {"endpoint": "fx", "as_of": as_of, "count": len(items), "items": items, "detail": None, "error": None},
        status=drf_status.HTTP_200_OK,
    )


# -------------------------
# yfinance 실시간 주가 API
# -------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def stock_realtime_price(request, code: str):
    """
    GET /api/stocks/{code}/realtime/
    yfinance를 사용한 실시간 주가 조회 (15-20분 지연)

    Returns:
        {
            "endpoint": "realtime",
            "code": "005930",
            "data": {
                "code": "005930",
                "name": "삼성전자",
                "current_price": 70000,
                "previous_close": 69500,
                "open": 69800,
                "high": 70500,
                "low": 69300,
                "volume": 12345678,
                "change": 500,
                "change_percent": 0.72,
                "market_cap": 1234567890000,
                "updated_at": "2025-12-24 15:30:00",
                "market_state": "REGULAR"
            },
            "market_status": {
                "is_open": true,
                "current_time": "2025-12-24 14:30:00",
                "next_open": null,
                "next_close": "2025-12-24 15:30:00"
            },
            "detail": null,
            "error": null
        }
    """
    try:
        # Stock 조회하여 market 정보 가져오기
        stock = Stock.objects.filter(code=code).first()

        # market 타입 자동 감지
        if stock:
            market = stock.market
        elif "-" in code:  # BTC-USD, ETH-USD 등
            market = "CRYPTO"
        elif code.isdigit():  # 한국 주식은 숫자 코드
            market = "KOSPI"  # 기본값, DB에 없으면 찾을 수 없음
        else:  # AAPL, TSLA 등 문자 코드
            market = "US"

        # 실시간 주가 조회
        realtime_data = YFinanceClient.get_realtime_price(code, market)

        if not realtime_data:
            return Response(
                {
                    "endpoint": "realtime",
                    "code": code,
                    "data": None,
                    "market_status": YFinanceClient.get_market_hours_status(),
                    "detail": "실시간 주가를 가져올 수 없습니다.",
                    "error": "YFINANCE_ERROR"
                },
                status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 시장 상태 정보
        market_status = YFinanceClient.get_market_hours_status()

        return Response(
            {
                "endpoint": "realtime",
                "code": code,
                "data": realtime_data,
                "market_status": market_status,
                "detail": None,
                "error": None
            },
            status=drf_status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {
                "endpoint": "realtime",
                "code": code,
                "data": None,
                "market_status": None,
                "detail": f"오류가 발생했습니다: {str(e)}",
                "error": "INTERNAL_ERROR"
            },
            status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def stock_intraday_prices(request, code: str):
    """
    GET /api/stocks/{code}/intraday/?interval=5m&days=1
    yfinance를 사용한 인트라데이 차트 데이터 조회

    Query Parameters:
        - interval: 시간 간격 (1m, 5m, 15m, 30m, 1h) - default: 5m
        - days: 조회 일수 (1, 5, 30, 60) - default: 1

    Returns:
        {
            "endpoint": "intraday",
            "code": "005930",
            "name": "삼성전자",
            "interval": "5m",
            "days": 1,
            "count": 78,
            "prices": [
                {
                    "datetime": "2025-12-24 09:00:00",
                    "open": 69800,
                    "high": 70000,
                    "low": 69700,
                    "close": 69900,
                    "volume": 123456
                },
                ...
            ],
            "detail": null,
            "error": null
        }
    """
    try:
        # Query parameters
        interval = request.query_params.get("interval", "5m")
        days = int(request.query_params.get("days", "1"))

        # Validate interval
        if not YFinanceClient.validate_interval(interval):
            return Response(
                {
                    "endpoint": "intraday",
                    "code": code,
                    "name": None,
                    "interval": interval,
                    "days": days,
                    "count": 0,
                    "prices": [],
                    "detail": "유효하지 않은 interval입니다. (1m, 5m, 15m, 30m, 1h 중 선택)",
                    "error": "INVALID_INTERVAL"
                },
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        # Stock 조회하여 market 정보 가져오기
        stock = Stock.objects.filter(code=code).first()

        # market 타입 자동 감지
        if stock:
            market = stock.market
            name = stock.name
        elif "-" in code:  # BTC-USD, ETH-USD 등
            market = "CRYPTO"
            name = code
        elif code.isdigit():  # 한국 주식은 숫자 코드
            market = "KOSPI"
            name = code
        else:  # AAPL, TSLA 등 문자 코드
            market = "US"
            name = code

        # 인트라데이 데이터 조회
        intraday_data = YFinanceClient.get_intraday_prices(
            code,
            market,
            interval=interval,
            days=days
        )

        return Response(
            {
                "endpoint": "intraday",
                "code": code,
                "name": name,
                "interval": interval,
                "days": days,
                "count": len(intraday_data),
                "prices": intraday_data,
                "detail": None,
                "error": None
            },
            status=drf_status.HTTP_200_OK,
        )

    except ValueError as e:
        return Response(
            {
                "endpoint": "intraday",
                "code": code,
                "name": None,
                "interval": interval,
                "days": 0,
                "count": 0,
                "prices": [],
                "detail": f"유효하지 않은 파라미터입니다: {str(e)}",
                "error": "INVALID_PARAMETER"
            },
            status=drf_status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {
                "endpoint": "intraday",
                "code": code,
                "name": None,
                "interval": None,
                "days": 0,
                "count": 0,
                "prices": [],
                "detail": f"오류가 발생했습니다: {str(e)}",
                "error": "INTERNAL_ERROR"
            },
            status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR,
        )