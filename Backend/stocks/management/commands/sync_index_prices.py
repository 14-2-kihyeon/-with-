# stocks/management/commands/sync_index_prices.py
from __future__ import annotations

from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction

from stocks.models import MarketIndex, MarketIndexDaily

class Command(BaseCommand):
    help = "FinanceDataReader로 지수(예: KS11, KQ11, KS200...) 일봉을 받아 DB에 저장합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--symbols",
            nargs="+",
            default=["KS11", "KQ11", "KS200", "KQ150", "KRX100"],
            help="지수 심볼 목록 (기본: KS11 KQ11 KS200 KQ150 KRX100)",
        )
        parser.add_argument("--start", default="2015-01-01", help="YYYY-MM-DD")
        parser.add_argument("--end", default=None, help="YYYY-MM-DD (기본: 오늘)")

    def handle(self, *args, **opts):
        import FinanceDataReader as fdr

        symbols = opts["symbols"]
        start = opts["start"]
        end = opts["end"] or datetime.now().strftime("%Y-%m-%d")

        self.stdout.write(self.style.SUCCESS(f"[sync_index_prices] {symbols} {start} ~ {end}"))

        for sym in symbols:
            df = fdr.DataReader(sym, start, end)  # columns: Open High Low Close Volume
            if df is None or df.empty:
                self.stdout.write(self.style.WARNING(f"  - {sym}: no data"))
                continue

            idx_obj, _ = MarketIndex.objects.get_or_create(symbol=sym, defaults={"name": sym})

            saved = 0
            with transaction.atomic():
                for dt, row in df.iterrows():
                    d = dt.date() if hasattr(dt, "date") else dt
                    defaults = {
                        "open": float(row.get("Open")) if row.get("Open") is not None else None,
                        "high": float(row.get("High")) if row.get("High") is not None else None,
                        "low": float(row.get("Low")) if row.get("Low") is not None else None,
                        "close": float(row.get("Close")),
                        "volume": int(row.get("Volume")) if row.get("Volume") is not None else None,
                    }
                    _, created = MarketIndexDaily.objects.update_or_create(
                        index=idx_obj, date=d, defaults=defaults
                    )
                    if created:
                        saved += 1

            self.stdout.write(self.style.SUCCESS(f"  - {sym}: rows={len(df)} saved_new={saved}"))
