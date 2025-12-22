from datetime import date
from typing import Optional

from stocks.models import UpdateLog, FeatureDaily, DailyPrice


def resolve_best_as_of() -> Optional[date]:
    # 1) FeatureDaily 최신
    d = FeatureDaily.objects.order_by("-date").values_list("date", flat=True).first()
    if d:
        return d

    # 2) UpdateLog SUCCESS 최신
    last_success = UpdateLog.objects.filter(status=UpdateLog.Status.SUCCESS).order_by("-as_of").first()
    if last_success:
        return last_success.as_of

    # 3) DailyPrice 최신
    d2 = DailyPrice.objects.order_by("-date").values_list("date", flat=True).first()
    return d2
