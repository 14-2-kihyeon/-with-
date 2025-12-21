import math
import time
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from stocks.models import Stock, StockNews, FeatureDaily
from stocks.services.naver_news_client import NaverNewsClient
from stocks.services.recommender import recommend_stocks  # 네가 이미 쓰는 추천 함수


def news_score(stock: Stock, as_of_date, window_days: int, tau: float) -> float:
    tz = timezone.get_current_timezone()
    start_dt = datetime.combine(as_of_date - timedelta(days=window_days), datetime.min.time()).replace(tzinfo=tz)
    end_dt = datetime.combine(as_of_date + timedelta(days=1), datetime.min.time()).replace(tzinfo=tz)

    qs = StockNews.objects.filter(stock=stock, published_at__gte=start_dt, published_at__lt=end_dt)

    s = 0.0
    for n in qs:
        delta = (as_of_date - n.published_at.date()).days
        if delta < 0:
            continue
        s += math.exp(-delta / tau)
    return float(s)


class Command(BaseCommand):
    help = "추천 후보 TopK 종목만 뉴스 수집 → news3/news7/news30 계산 → FeatureDaily에 저장"

    def add_arguments(self, parser):
        parser.add_argument("--date", required=True, type=str, help="YYYYMMDD")
        parser.add_argument("--max-stocks", type=int, default=200, help="TopK(기본 200)")
        parser.add_argument("--display", type=int, default=20, help="종목당 뉴스 개수(기본 20)")
        parser.add_argument("--lookback-days", type=int, default=30, help="이보다 오래된 뉴스는 저장 제외")
        parser.add_argument("--sleep", type=float, default=0.05, help="요청 간 sleep")
        parser.add_argument("--suffix", type=str, default="주가", help="검색어 뒤 키워드")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        ymd = opts["date"]
        as_of = datetime.strptime(ymd, "%Y%m%d").date()

        max_stocks = int(opts["max_stocks"])
        display = int(opts["display"])
        lookback_days = int(opts["lookback_days"])
        sleep = float(opts["sleep"])
        suffix = str(opts["suffix"])
        dry_run = bool(opts["dry_run"])

        client = NaverNewsClient()
        cutoff = as_of - timedelta(days=lookback_days)

        # ✅ 1) “뉴스 제외” 상태로 먼저 TopK 후보만 뽑기
        base = recommend_stocks(as_of=as_of, risk="MID", horizon="MID", top_n=max_stocks, include_news=False)
        recs = base.get("recommendations", []) or []
        codes = [r["code"] for r in recs]

        self.stdout.write(self.style.NOTICE(f"[sync_stock_news] as_of={as_of} candidates={len(codes)}"))

        if dry_run:
            self.stdout.write(self.style.WARNING(f"[dry-run] first10={codes[:10]}"))
            return

        saved = 0
        skipped_old = 0

        # ✅ 2) 후보 종목만 뉴스 수집
        for code in codes:
            stock = Stock.objects.filter(code=code).first()
            if not stock:
                continue

            query = f"{stock.name} {suffix}".strip()
            items = client.search(query=query, display=display, sort="date")

            for it in items:
                pub = it.get("published_at")
                if not pub:
                    continue
                if pub.date() < cutoff:
                    skipped_old += 1
                    continue

                link = it.get("link") or ""
                if not link:
                    continue

                obj, created = StockNews.objects.get_or_create(
                    link=link,
                    defaults={
                        "stock": stock,
                        "published_at": pub,
                        "title": it.get("title", "")[:500],
                        "description": it.get("description", ""),
                        "originallink": it.get("originallink", ""),
                        "source": "NAVER",
                        "query_used": query[:200],
                    },
                )
                if created:
                    saved += 1

            time.sleep(sleep)

        # ✅ 3) news 점수 계산 → FeatureDaily 반영
        for code in codes:
            stock = Stock.objects.filter(code=code).first()
            if not stock:
                continue

            fd = FeatureDaily.objects.filter(stock=stock, date=as_of).first()
            if not fd:
                continue

            fd.news3 = news_score(stock, as_of, window_days=3, tau=1.5)
            fd.news7 = news_score(stock, as_of, window_days=7, tau=3.0)
            fd.news30 = news_score(stock, as_of, window_days=30, tau=10.0)
            fd.save(update_fields=["news3", "news7", "news30"])

        self.stdout.write(self.style.SUCCESS(f"[sync_stock_news] done. saved={saved}, skipped_old={skipped_old}"))
