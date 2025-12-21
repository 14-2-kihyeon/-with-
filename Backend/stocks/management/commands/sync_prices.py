from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction

from stocks.models import Stock, DailyPrice
from stocks.services.stock_api_client import StockPriceAPIClient


class Command(BaseCommand):
    help = "주식시세정보 API로 DailyPrice(일봉) 데이터를 적재합니다."

    def add_arguments(self, parser):
        parser.add_argument("--date", type=str, help="단일 날짜(YYYYMMDD)")
        parser.add_argument("--start", type=str, help="시작 날짜(YYYYMMDD)")
        parser.add_argument("--end", type=str, help="종료 날짜(YYYYMMDD)")
        parser.add_argument("--rows", type=int, default=1000, help="페이지당 row 수 (기본 1000)")
        parser.add_argument("--sleep", type=float, default=0.1, help="페이지 요청 간 sleep (초)")
        parser.add_argument("--dry-run", action="store_true", help="DB 저장 없이 호출/파싱만")

    def handle(self, *args, **options):
        client = StockPriceAPIClient()

        date_str = options.get("date")
        start = options.get("start")
        end = options.get("end")

        if date_str:
            self._sync_one_date(client, date_str, options)
            return

        if start and end:
            self._sync_range(client, start, end, options)
            return

        raise ValueError("옵션이 필요합니다. 예) --date 20251217 또는 --start 20251001 --end 20251217")

    def _sync_range(self, client, start: str, end: str, options):
        start_dt = datetime.strptime(start, "%Y%m%d").date()
        end_dt = datetime.strptime(end, "%Y%m%d").date()
        if start_dt > end_dt:
            raise ValueError("start는 end보다 클 수 없습니다.")

        cur = start_dt
        while cur <= end_dt:
            yyyymmdd = cur.strftime("%Y%m%d")
            self._sync_one_date(client, yyyymmdd, options)
            cur += timedelta(days=1)

    def _sync_one_date(self, client, yyyymmdd: str, options):
        rows = options["rows"]
        sleep_sec = options["sleep"]
        dry_run = options["dry_run"]

        self.stdout.write(self.style.NOTICE(f"[sync] {yyyymmdd} 호출 시작"))

        items = client.fetch_by_date(yyyymmdd, rows=rows, sleep_sec=sleep_sec)

        if not items:
            self.stdout.write(self.style.WARNING(f"[sync] {yyyymmdd} 데이터 없음(휴장/파라미터/URL 확인 필요)"))
            return

        self.stdout.write(self.style.SUCCESS(f"[sync] {yyyymmdd} 수신 {len(items)}건"))

        if dry_run:
            sample = items[0]
            self.stdout.write(self.style.WARNING(f"[dry-run] sample: {sample}"))
            return

        # 1) Stock upsert(생성 위주)
        codes = [it["code"] for it in items]
        existing = Stock.objects.filter(code__in=codes).in_bulk(field_name="code")

        to_create = []
        to_update = []
        for it in items:
            code = it["code"]
            name = it["name"]
            market = it.get("market", "") or ""

            if code not in existing:
                to_create.append(Stock(code=code, name=name, market=market))
            else:
                s = existing[code]
                changed = False
                if s.name != name:
                    s.name = name
                    changed = True
                # market은 없을 수도 있으니, 빈 값이면 굳이 덮어쓰지 않음
                if market and s.market != market:
                    s.market = market
                    changed = True
                if changed:
                    to_update.append(s)

        with transaction.atomic():
            if to_create:
                Stock.objects.bulk_create(to_create, batch_size=1000)
            if to_update:
                Stock.objects.bulk_update(to_update, ["name", "market"], batch_size=1000)

            # 새로 만든 것까지 포함해서 다시 맵 로딩
            stock_map = Stock.objects.filter(code__in=codes).in_bulk(field_name="code")

            # 2) DailyPrice는 해당 날짜/해당 종목들만 "삭제 후 재삽입" (가장 단순+빠른 업서트)
            date_obj = datetime.strptime(yyyymmdd, "%Y%m%d").date()
            stock_ids = [stock_map[c].id for c in codes if c in stock_map]

            DailyPrice.objects.filter(date=date_obj, stock_id__in=stock_ids).delete()

            dp_objs = []
            for it in items:
                s = stock_map.get(it["code"])
                if not s:
                    continue
                dp_objs.append(
                    DailyPrice(
                        stock_id=s.id,
                        date=it["date"],
                        open=it["open"],
                        high=it["high"],
                        low=it["low"],
                        close=it["close"],
                        volume=it["volume"],
                        amount=it.get("amount"),
                        market_cap=it.get("market_cap"),
                        listed_shares=it.get("listed_shares"),
                    )
                )

            DailyPrice.objects.bulk_create(dp_objs, batch_size=2000)

        self.stdout.write(self.style.SUCCESS(f"[sync] {yyyymmdd} DB 저장 완료 (DailyPrice {len(dp_objs)}건)"))
