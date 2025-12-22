from django.db import models
from django.utils import timezone

class Stock(models.Model):
    """
    종목 마스터
    - code: 단축코드(보통 6자리, 예: 005930)
    """
    code = models.CharField(max_length=10, unique=True, db_index=True)
    name = models.CharField(max_length=100, db_index=True)

    # 선택 필드(있으면 채우기)
    market = models.CharField(max_length=20, blank=True, default="")   # KOSPI/KOSDAQ 등
    sector = models.CharField(max_length=100, blank=True, default="")  # 업종(나중에 확장)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} {self.name}"


class DailyPrice(models.Model):
    """
    일봉(전일 종가 기반 포함) 시계열
    - (stock, date)는 유일해야 함 (중복 적재 방지 핵심)
    """
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="prices")
    date = models.DateField(db_index=True)  # basDt

    # OHLC: API는 문자열로 오기도 해서 저장은 int로 (원화 단위)
    open = models.IntegerField()   # mkp
    high = models.IntegerField()   # hipr
    low = models.IntegerField()    # lopr
    close = models.IntegerField()  # clpr

    volume = models.BigIntegerField()  # trqu (거래량)
    amount = models.BigIntegerField(null=True, blank=True)  # 거래대금(trPrc/trprc) - API에서 이름 다를 수 있어 optional

    # 추가로 있으면 유용한 필드(있으면 채움)
    market_cap = models.BigIntegerField(null=True, blank=True)        # mrktTotAmt
    listed_shares = models.BigIntegerField(null=True, blank=True)     # lstgStCnt

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(fields=["stock", "date"], name="uniq_stock_date"),
        ]
        indexes = [
            models.Index(fields=["stock", "date"], name="idx_stock_date"),
        ]

    def __str__(self) -> str:
        return f"{self.stock.code} {self.date} close={self.close}"


class FeatureDaily(models.Model):
    """
    추천 엔진용 피처(지표) 테이블: 기준일(date) 기준으로 1종목 1행
    """
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="features")
    date = models.DateField(db_index=True)  # 기준일(as_of)

    # returns
    r1 = models.FloatField(null=True, blank=True)
    r5 = models.FloatField(null=True, blank=True)
    r20 = models.FloatField(null=True, blank=True)
    r60 = models.FloatField(null=True, blank=True)

    # volatility (std of daily returns)
    vol10 = models.FloatField(null=True, blank=True)
    vol20 = models.FloatField(null=True, blank=True)
    vol60 = models.FloatField(null=True, blank=True)

    # max drawdown (window)
    mdd10 = models.FloatField(null=True, blank=True)
    mdd20 = models.FloatField(null=True, blank=True)
    mdd60 = models.FloatField(null=True, blank=True)

    # 뉴스 점수 컬럼
    news3 = models.FloatField(default=0.0)
    news7 = models.FloatField(default=0.0)
    news30 = models.FloatField(default=0.0)

    # volume z-score (log(volume+1))
    vz5 = models.FloatField(null=True, blank=True)
    vz20 = models.FloatField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(fields=["stock", "date"], name="uniq_feature_stock_date"),
        ]
        indexes = [
            models.Index(fields=["stock", "date"], name="idx_feature_stock_date"),
        ]

    def __str__(self) -> str:
        return f"{self.stock.code} {self.date} r5={self.r5}"
    

class StockNews(models.Model):
    stock = models.ForeignKey("stocks.Stock", on_delete=models.CASCADE, related_name="stock_news")
    published_at = models.DateTimeField(db_index=True)

    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, default="")

    link = models.URLField(max_length=1000, unique=True)  # 중복 방지 핵심
    originallink = models.URLField(max_length=1000, blank=True, default="")
    source = models.CharField(max_length=30, default="NAVER")

    query_used = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["stock", "published_at"], name="idx_stocknews_stock_pub"),
        ]

    def __str__(self):
        return f"{self.stock.code} {self.published_at} {self.title[:30]}"






class UpdateLog(models.Model):
    class Status(models.TextChoices):
        RUNNING = "RUNNING", "RUNNING"
        SUCCESS = "SUCCESS", "SUCCESS"
        FAILED  = "FAILED",  "FAILED"

    as_of = models.DateField(unique=True, db_index=True)  # 기준일(거래일)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.RUNNING)

    attempt = models.PositiveIntegerField(default=0)

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    prices_count = models.PositiveIntegerField(default=0)
    features_count = models.PositiveIntegerField(default=0)
    duration_sec = models.FloatField(default=0.0)
    warnings = models.TextField(blank=True, default="")

    note = models.TextField(blank=True, default="")
    error = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_running(self):
        self.status = self.Status.RUNNING
        self.attempt += 1
        self.started_at = timezone.now()
        self.finished_at = None
        self.error = ""
        self.save(update_fields=["status", "attempt", "started_at", "finished_at", "error", "updated_at"])

    def mark_success(self, prices_count: int, features_count: int, note: str = "", warnings: str = "", duration_sec: float = 0.0):
        self.status = self.Status.SUCCESS
        self.finished_at = timezone.now()
        self.prices_count = prices_count
        self.features_count = features_count
        self.note = note
        self.warnings = warnings
        self.duration_sec = duration_sec
        self.save(update_fields=[
            "status","finished_at","prices_count","features_count","note","warnings","duration_sec","updated_at"
        ])

    def mark_failed(self, error: str):
        self.status = self.Status.FAILED
        self.finished_at = timezone.now()
        self.error = error[:8000]  # 너무 길면 잘라 저장
        self.save(update_fields=["status", "finished_at", "error", "updated_at"])

    def __str__(self):
        return f"{self.as_of} {self.status} (prices={self.prices_count}, features={self.features_count})"
    

class RecommendationLog(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="reco_logs")
    as_of = models.DateField(db_index=True)  # 추천 기준일(거래일)
    created_at = models.DateTimeField(auto_now_add=True)

    # 어떤 프로필로 돌렸는지
    risk = models.CharField(max_length=8, default="MID")
    horizon = models.CharField(max_length=8, default="MID")
    effort = models.CharField(max_length=12, default="OPTIMIZE")

    # 추천 결과(Top N 전체를 JSON으로 저장)
    payload = models.JSONField(default=dict)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "as_of"], name="idx_reco_user_asof"),
        ]

    def __str__(self):
        return f"{self.user_id} {self.as_of} {self.risk}/{self.horizon}"



# 메인 차트

class MarketIndex(models.Model):
    """
    지수 마스터 (예: KS11, KQ11)
    """
    symbol = models.CharField(max_length=20, unique=True, db_index=True)  # 'KS11'
    name = models.CharField(max_length=100, blank=True, default="")      # 'KOSPI'

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["symbol"]

    def __str__(self):
        return f"{self.symbol} {self.name}".strip()


class MarketIndexDaily(models.Model):
    """
    지수 일봉 시계열
    FinanceDataReader DataReader(symbol) 결과(Open/High/Low/Close/Volume) 저장용
    """
    index = models.ForeignKey(MarketIndex, on_delete=models.CASCADE, related_name="prices")
    date = models.DateField(db_index=True)

    open = models.FloatField(null=True, blank=True)
    high = models.FloatField(null=True, blank=True)
    low = models.FloatField(null=True, blank=True)
    close = models.FloatField()

    volume = models.BigIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(fields=["index", "date"], name="uniq_index_date"),
        ]
        indexes = [
            models.Index(fields=["index", "date"], name="idx_index_date"),
        ]

    def __str__(self):
        return f"{self.index.symbol} {self.date} close={self.close}"



class FxRateDaily(models.Model):
    pair = models.CharField(max_length=15)   # 예: "USD/KRW"
    date = models.DateField()
    close = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("pair", "date")
        indexes = [
            models.Index(fields=["pair", "-date"]),
        ]

    def __str__(self):
        return f"{self.pair} {self.date} {self.close}"
