from rest_framework import serializers
from .models import DepositProducts, DepositOptions, SavingOptions, SavingProducts

class DepositOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositOptions
        fields = ("save_trm", "intr_rate", "intr_rate2", "rsrv_type")

class DepositProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositProducts
        fields = ("fin_prdt_cd", "kor_co_nm", "fin_prdt_nm")

class DepositProductDetailSerializer(serializers.ModelSerializer):
    options = DepositOptionsSerializer(many=True, read_only=True,)

    class Meta:
        model = DepositProducts
        fields = ("fin_prdt_cd", "kor_co_nm", "fin_prdt_nm", "join_way", "join_deny",
                  "join_member", "spcl_cnd", "options")


class SavingOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingOptions
        fields = "__all__"

class SavingProductsSerializer(serializers.ModelSerializer):
    options = SavingOptionsSerializer(many=True, read_only=True)
    class Meta:
        model = SavingProducts
        fields = "__all__"