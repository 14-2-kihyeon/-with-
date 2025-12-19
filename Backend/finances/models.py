from django.db import models

class DepositProducts(models.Model):
    fin_prdt_cd = models.CharField(max_length=50, unique=True)
    kor_co_nm = models.CharField(max_length=100)
    fin_prdt_nm = models.CharField(max_length=200)
    join_way = models.CharField(max_length=200, null=True, blank=True)
    join_deny = models.IntegerField(default=1)
    join_member = models.CharField(max_length=200, null=True, blank=True)
    spcl_cnd = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.fin_prdt_nm


class DepositOptions(models.Model):
    product = models.ForeignKey(DepositProducts, on_delete=models.CASCADE, related_name="options")
    intr_rate = models.FloatField(default=-1)      # 기본 금리
    intr_rate2 = models.FloatField(default=-1)     # 최고 우대금리
    save_trm = models.IntegerField()               # 가입 기간(개월)
    rsrv_type = models.CharField(max_length=20, null=True, blank=True)    # 적립 유형

    def __str__(self):
        return f"{self.product.fin_prdt_nm} - {self.save_trm}개월"



class SavingProducts(models.Model):
    fin_prdt_cd = models.CharField(max_length=50, unique=True)
    kor_co_nm = models.CharField(max_length=100)
    fin_prdt_nm = models.CharField(max_length=200)

    join_way = models.CharField(max_length=200, null=True, blank=True)
    join_deny = models.IntegerField(default=1)
    join_member = models.CharField(max_length=200, null=True, blank=True)
    spcl_cnd = models.TextField(null=True, blank=True)

    # 적금에는 만기 후 이자율 설명(mtrt_int)이 자주 옴
    mtrt_int = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.fin_prdt_nm


class SavingOptions(models.Model):
    product = models.ForeignKey(SavingProducts, on_delete=models.CASCADE, related_name="options")

    intr_rate = models.FloatField(default=-1)
    intr_rate2 = models.FloatField(default=-1)
    save_trm = models.IntegerField()

    # 적금 옵션에 있음 (자유적립/정액적립)
    rsrv_type = models.CharField(max_length=20, null=True, blank=True)
    rsrv_type_nm = models.CharField(max_length=50, null=True, blank=True)

    # 금리유형도 종종 있음(단리/복리 등)
    intr_rate_type = models.CharField(max_length=20, null=True, blank=True)
    intr_rate_type_nm = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.product.fin_prdt_nm} - {self.save_trm}개월"
