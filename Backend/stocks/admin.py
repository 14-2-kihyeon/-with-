from django.contrib import admin
from .models import Stock, DailyPrice
from .models import FeatureDaily  # 추가
from .models import UpdateLog


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "market", "sector")
    search_fields = ("code", "name")
    list_filter = ("market",)


@admin.register(DailyPrice)
class DailyPriceAdmin(admin.ModelAdmin):
    list_display = ("stock", "date", "open", "high", "low", "close", "volume")
    search_fields = ("stock__code", "stock__name")
    list_filter = ("date",)


@admin.register(FeatureDaily)
class FeatureDailyAdmin(admin.ModelAdmin):
    list_display = ("stock", "date", "r5", "vol20", "mdd20", "vz20", "updated_at")
    search_fields = ("stock__code", "stock__name")
    list_filter = ("date",)


@admin.register(UpdateLog)
class UpdateLogAdmin(admin.ModelAdmin):
    list_display = ("as_of", "status", "attempt", "prices_count", "features_count", "started_at", "finished_at")
    list_filter = ("status", "as_of")
    search_fields = ("as_of",)