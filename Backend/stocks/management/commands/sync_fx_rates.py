# stocks/management/commands/sync_fx_rates.py
from __future__ import annotations

from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from stocks.models import FxRateDaily


class Command(BaseCommand):
    help = "FinanceDataReader로 환율을 받아 DB(FxRateDaily)에 저장합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--pairs",
            nargs="+",
            default=["USD/KRW", "JPY/KRW", "EUR/KRW", "CNY/KRW"],
            help='환율 pair 목록 (기본: "USD/KRW" "JPY/KRW" "EUR/KRW" "CNY/KRW")',
        )
        parser.add_argument("--start", default=None, help="YYYY-MM-DD (기본: 오늘-14일)")
        parser.add_argument("--end", default=None, help="YYYY-MM-DD (기본: 오늘)")

    def handle(self, *args, **opts):
        try:
            import FinanceDataReader as fdr
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"FinanceDataReader import 실패: {e}"))
            return

        pairs = opts["pairs"]
        end = opts["end"] or timezone.localdate().strftime("%Y-%m-%d")
        start = opts["start"] or (timezone.localdate() - timedelta(days=14)).strftime("%Y-%m-%d")

        self.stdout.write(self.style.SUCCESS(f"[sync_fx_rates] {pairs} {start} ~ {end}"))

        for pair in pairs:
            try:
                df = fdr.DataReader(pair, start, end)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  - {pair}: fetch 실패 ({e})"))
                continue

            if df is None or getattr(df, "empty", True):
                self.stdout.write(self.style.WARNING(f"  - {pair}: no data"))
                continue

            close_col = "Close" if "Close" in df.columns else df.columns[0]

            saved_new = 0
            updated = 0

            with transaction.atomic():
                for idx, row in df.iterrows():
                    d = idx.date() if hasattr(idx, "date") else idx
                    close = row.get(close_col)
                    close = float(close) if close is not None else None

                    obj, created = FxRateDaily.objects.update_or_create(
                        pair=pair,
                        date=d,
                        defaults={"close": close},
                    )
                    if created:
                        saved_new += 1
                    else:
                        updated += 1

            self.stdout.write(self.style.SUCCESS(f"  - {pair}: rows={len(df)} new={saved_new} updated={updated}"))
