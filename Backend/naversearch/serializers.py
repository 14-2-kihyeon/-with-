# naversearch/serializers.py
from rest_framework import serializers
from .models import News


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = "__all__"  # id, title, description, link, pub_date, is_bookmarked
