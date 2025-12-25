# stocks/management/commands/daily_update.py
from __future__ import annotations

from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.utils import timezone

from stocks.models import UpdateLog


def _parse_yyyymmdd(s: str):
    return datetime.strptime(s, "%Y%m%d").date()


def _status_value(name: str) -> str:
    """
    UpdateLog.Status 가 TextChoices인 경우/아닌 경우 모두 대응
    """
    if hasattr(UpdateLog, "Status"):
        if hasattr(UpdateLog.Status, name):
            v = getattr(UpdateLog.Status, name)
            return getattr(v, "value", v)
    return name


def _set_fields(obj, **kwargs):
    for k, v in kwargs.items():
        if hasattr(obj, k):
            setattr(obj, k, v)


class Command(BaseCommand):
    help = "운영용 1회 업데이트: sync_prices -> build_features -> (옵션)sync_stock_news"

    def add_arguments(self, parser):
        parser.add_argument("--date", type=str, default=None, help="YYYYMMDD (기본: 오늘)")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--news", action="store_true", help="뉴스 단계 실행(기본 OFF)")
        parser.add_argument("--max-stocks", type=int, default=200)
        parser.add_argument("--display", type=int, default=20)
        parser.add_argument("--lookback-days", type=int, default=30)
        parser.add_argument("--sleep", type=float, default=0.05)
        parser.add_argument(
            "--force",
            action="store_true",
            help="같은 날짜(as_of) 로그가 이미 있으면 덮어쓰기",
        )

    def handle(self, *args, **opts):
        dry_run = bool(opts["dry_run"])
        run_news = bool(opts["news"])
        force = bool(opts["force"])

        if opts["date"]:
            as_of = _parse_yyyymmdd(opts["date"])
        else:
            as_of = timezone.localdate()

        now = timezone.now()

        # ✅ 핵심: unique(as_of)면 create가 아니라 get_or_create / 덮어쓰기
        log, created = UpdateLog.objects.get_or_create(as_of=as_of)

        if (not created) and (not force):
            raise CommandError(
                f"UpdateLog(as_of={as_of})가 이미 존재합니다. "
                f"재실행하려면 --force 를 붙이거나, 기존 로그를 삭제하세요."
            )

        # 덮어쓰기/초기화
        _set_fields(
            log,
            status=_status_value("RUNNING"),
            started_at=now,
            finished_at=None,
            dry_run=dry_run,
            warnings="",
            message="",
        )
        log.save()

        warnings = ""
        try:
            # 1) 가격 동기화
            self.stdout.write(self.style.NOTICE(f"[daily_update] sync_prices as_of={as_of} dry_run={dry_run}"))
            call_command("sync_prices", date=as_of.strftime("%Y%m%d"), dry_run=dry_run)

            # 2) 피처 생성
            self.stdout.write(self.style.NOTICE(f"[daily_update] build_features as_of={as_of} dry_run={dry_run}"))
            call_command("build_features", date=as_of.strftime("%Y%m%d"), dry_run=dry_run)

            # 3) 뉴스(선택) - 실패해도 전체는 SUCCESS 유지(경고만)
            if run_news:
                try:
                    self.stdout.write(self.style.NOTICE(f"[daily_update] sync_stock_news as_of={as_of} dry_run={dry_run}"))
                    call_command(
                        "sync_stock_news",
                        date=as_of.strftime("%Y%m%d"),
                        max_stocks=int(opts["max_stocks"]),
                        display=int(opts["display"]),
                        lookback_days=int(opts["lookback_days"]),
                        sleep=float(opts["sleep"]),
                        dry_run=dry_run,
                    )
                except Exception as e:
                    warnings = (warnings + "\n" if warnings else "") + f"sync_stock_news failed: {e}"

            _set_fields(
                log,
                status=_status_value("SUCCESS"),
                finished_at=timezone.now(),
                warnings=warnings,
                message="ok",
            )
            log.save()
            self.stdout.write(self.style.SUCCESS(f"[daily_update] SUCCESS as_of={as_of}"))

        except Exception as e:
            _set_fields(
                log,
                status=_status_value("FAILED"),
                finished_at=timezone.now(),
                warnings=warnings,
                message=str(e),
            )
            log.save()
            self.stdout.write(self.style.ERROR(f"[daily_update] FAILED as_of={as_of}: {e}"))
            raise
