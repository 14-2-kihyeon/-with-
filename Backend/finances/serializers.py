# finances/serializers.py
from rest_framework import serializers
from .models import DepositProducts, DepositOptions, SavingProducts, SavingOptions


# ============================================
# Deposit
# ============================================

class DepositOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositOptions
        fields = ("save_trm", "intr_rate", "intr_rate2", "rsrv_type")


class DepositProductListSerializer(serializers.ModelSerializer):
    intr_rate = serializers.SerializerMethodField()  # 최고금리(우선 intr_rate2)
    save_trm = serializers.SerializerMethodField()   # 최고금리의 기간(월)

    class Meta:
        model = DepositProducts
        fields = ("fin_prdt_cd", "kor_co_nm", "fin_prdt_nm", "intr_rate", "save_trm")

    def _best_option(self, obj):
        # related_name='options'라고 했으니 그대로 사용
        opts = obj.options.all()
        if not opts:
            return None

        def best_rate(o):
            r2 = o.intr_rate2
            r1 = o.intr_rate
            return float(r2 if r2 is not None else (r1 if r1 is not None else 0))

        return max(opts, key=best_rate)

    def get_intr_rate(self, obj):
        best = self._best_option(obj)
        if not best:
            return 0
        return best.intr_rate2 if best.intr_rate2 is not None else (best.intr_rate or 0)

    def get_save_trm(self, obj):
        best = self._best_option(obj)
        return best.save_trm if best and best.save_trm is not None else 0


class DepositProductDetailSerializer(serializers.ModelSerializer):
    options = DepositOptionsSerializer(many=True, read_only=True)

    class Meta:
        model = DepositProducts
        fields = (
            "fin_prdt_cd", "kor_co_nm", "fin_prdt_nm",
            "join_way", "join_deny", "join_member", "spcl_cnd",
            "options",
        )


# ============================================
# Saving
# ============================================

class SavingOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingOptions
        fields = ("save_trm", "intr_rate", "intr_rate2", "rsrv_type")


class SavingProductListSerializer(serializers.ModelSerializer):
    intr_rate = serializers.SerializerMethodField()
    save_trm = serializers.SerializerMethodField()

    class Meta:
        model = SavingProducts
        fields = ("fin_prdt_cd", "kor_co_nm", "fin_prdt_nm", "intr_rate", "save_trm")

    def _best_option(self, obj):
        opts = obj.options.all()
        if not opts:
            return None

        def best_rate(o):
            r2 = o.intr_rate2
            r1 = o.intr_rate
            return float(r2 if r2 is not None else (r1 if r1 is not None else 0))

        return max(opts, key=best_rate)

    def get_intr_rate(self, obj):
        best = self._best_option(obj)
        if not best:
            return 0
        return best.intr_rate2 if best.intr_rate2 is not None else (best.intr_rate or 0)

    def get_save_trm(self, obj):
        best = self._best_option(obj)
        return best.save_trm if best and best.save_trm is not None else 0


class SavingProductDetailSerializer(serializers.ModelSerializer):
    options = SavingOptionsSerializer(many=True, read_only=True)

    class Meta:
        model = SavingProducts
        fields = (
            "fin_prdt_cd", "kor_co_nm", "fin_prdt_nm",
            "join_way", "join_deny", "join_member", "spcl_cnd",
            "options",
        )
