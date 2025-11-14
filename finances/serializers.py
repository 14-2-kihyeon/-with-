from rest_framework import serializers
from .models import DepositProducts, DepositOptions

class DepositOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositOptions
        fields = '__all__'


class DepositProductsSerializer(serializers.ModelSerializer):
    options = DepositOptionsSerializer(many=True, read_only=True, source='depositoptions_set')

    class Meta:
        model = DepositProducts
        fields = '__all__'
