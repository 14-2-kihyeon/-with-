import math
from collections import defaultdict, deque
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from stocks.models import DailyPrice, FeatureDaily


def _stddev(vals):
    n = len(vals)
    if n < 2:
        return 0.0
    mean = sum(vals) / n
    var = sum((x - mean) ** 2 for x in vals) / (n - 1)  # sample std
    return math.sqrt(var)


def _mdd(closes):
    """
    closes: list[float] (최근 window일 종가)
    반환: 최대낙폭(양수, 예: 0.23 = 23% 하락)
    """
    peak = closes[0]
    min_dd = 0.0
    for p in closes:
        if p > peak:
            peak = p
        dd = p / peak - 1.0  # 음수
        if dd < min_dd:
            min_dd = dd
    return abs(min_dd)


def _return_k(closes, k):
    """
    k일 수익률: close[t] / close[t-k] - 1
    """
    if len(closes) <= k:
        return None
    return closes[-1] / closes[-1 - k] - 1.0


def _volume_z(volumes, w):
    """
    log(volume+1) 기준 z-score, 마지막 값이 얼마나 튀는지
    """
    if len(volumes) < w:
        return None
    xs = [math.log(v + 1) for v in volumes[-w:]]
    mean = sum(xs) / len(xs)
    sd = _stddev(xs)
    if sd == 0:
        return 0.0
    return (xs[-1] - mean) / sd


class Command(BaseCommand):
    help = "DailyPrice로부터 FeatureDaily(수익률/변동성/MDD/거래량z)를 계산해 저장합니다."

    def add_arguments(self, parser):
        parser.add_argument("--date", type=str, required=True, help="기준일(YYYYMMDD)")
        parser.add_argument("--lookback-days", type=int, default=400, help="DB에서 조회할 과거 캘린더 일수(기본 400)")
        parser.add_argument("--dry-run", action="store_true", help="DB 저장 없이 계산만")
        parser.add_argument("--chunk", type=int, default=20000, help="DB iterator chunk size")

    def handle(self, *args, **options):
        as_of = datetime.strptime(options["date"], "%Y%m%d").date()
        lookback_days = options["lookback_days"]
        dry_run = options["dry_run"]
        chunk = options["chunk"]

        # 최대 윈도우가 60이므로 최소 61개 종가 필요
        NEED = 61
        start_date = as_of - timedelta(days=lookback_days)

        self.stdout.write(self.style.NOTICE(f"[features] as_of={as_of} start={start_date} NEED={NEED}"))

        # 기준일에 실제로 데이터 있는 종목만 계산(추천 기준일과 맞추기)
        asof_stock_ids = set(
            DailyPrice.objects.filter(date=as_of).values_list("stock_id", flat=True)
        )
        if not asof_stock_ids:
            self.stdout.write(self.style.ERROR(
                f"[features] {as_of} DailyPrice가 0건입니다. sync_prices를 먼저 저장 모드로 실행했는지 확인!"
            ))
            return

        # (stock_id -> 최근 NEED개)만 유지
        series = defaultdict(lambda: deque(maxlen=NEED))

        qs = (
            DailyPrice.objects
            .filter(date__gte=start_date, date__lte=as_of, stock_id__in=asof_stock_ids)
            .order_by("stock_id", "date")
            .values_list("stock_id", "date", "close", "volume")
        )

        for stock_id, d, close, volume in qs.iterator(chunk_size=chunk):
            series[stock_id].append((d, close, volume))

        self.stdout.write(self.style.SUCCESS(f"[features] 시계열 수집 완료: {len(series)}종목"))

        # 기존 피처 삭제 후 재생성(기준일 기준 idempotent)
        if not dry_run:
            FeatureDaily.objects.filter(date=as_of).delete()

        to_create = []
        skipped = 0

        for stock_id, rows in series.items():
            if len(rows) < NEED:
                skipped += 1
                continue

            # 기준일 데이터가 마지막이어야 함
            if rows[-1][0] != as_of:
                skipped += 1
                continue

            closes = [float(r[1]) for r in rows]
            volumes = [int(r[2]) for r in rows]

            # returns
            r1 = _return_k(closes, 1)
            r5 = _return_k(closes, 5)
            r20 = _return_k(closes, 20)
            r60 = _return_k(closes, 60)

            # daily returns for vol
            daily_rets = [(closes[i] / closes[i - 1] - 1.0) for i in range(1, len(closes))]

            vol10 = _stddev(daily_rets[-10:]) if len(daily_rets) >= 10 else None
            vol20 = _stddev(daily_rets[-20:]) if len(daily_rets) >= 20 else None
            vol60 = _stddev(daily_rets[-60:]) if len(daily_rets) >= 60 else None

            # mdd
            mdd10 = _mdd(closes[-10:]) if len(closes) >= 10 else None
            mdd20 = _mdd(closes[-20:]) if len(closes) >= 20 else None
            mdd60 = _mdd(closes[-60:]) if len(closes) >= 60 else None

            # volume z
            vz5 = _volume_z(volumes, 5)
            vz20 = _volume_z(volumes, 20)

            to_create.append(
                FeatureDaily(
                    stock_id=stock_id,
                    date=as_of,
                    r1=r1, r5=r5, r20=r20, r60=r60,
                    vol10=vol10, vol20=vol20, vol60=vol60,
                    mdd10=mdd10, mdd20=mdd20, mdd60=mdd60,
                    vz5=vz5, vz20=vz20,
                )
            )

        self.stdout.write(self.style.NOTICE(f"[features] 생성 대상={len(to_create)} / 스킵={skipped}"))

        if dry_run:
            if to_create:
                sample = to_create[0]
                self.stdout.write(self.style.WARNING(
                    f"[dry-run] sample stock_id={sample.stock_id} r5={sample.r5} vol20={sample.vol20} mdd20={sample.mdd20} vz20={sample.vz20}"
                ))
            return

        with transaction.atomic():
            FeatureDaily.objects.bulk_create(to_create, batch_size=2000)

        self.stdout.write(self.style.SUCCESS(f"[features] 저장 완료: FeatureDaily {len(to_create)}건 (date={as_of})"))
