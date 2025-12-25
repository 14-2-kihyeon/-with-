# accounts/serializers.py
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from rest_framework import serializers
from .models import (
    UserNewsBookmark,
    UserYouTubeSubscription,
    UserWatchLater,
    InvestmentProfile
)

class CustomRegisterSerializer(RegisterSerializer):
    # ✅ email을 optional로
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        # ✅ email이 아예 없어도 키가 생기게
        data["email"] = self.validated_data.get("email", "")
        return data


class InvestmentProfileSerializer(serializers.ModelSerializer):
    """투자 성향 프로필 Serializer"""
    class Meta:
        model = InvestmentProfile
        fields = ['risk_type', 'risk_score', 'investment_period', 'gender', 'age']


class CustomUserDetailsSerializer(UserDetailsSerializer):
    """사용자 정보에 투자 성향 포함"""
    investment_profile = InvestmentProfileSerializer(read_only=True)

    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + ('investment_profile',)


# ============================================
# 북마크 관련 Serializers
# ============================================

class UserNewsBookmarkSerializer(serializers.ModelSerializer):
    """뉴스 북마크 Serializer"""

    class Meta:
        model = UserNewsBookmark
        fields = [
            'id',
            'news_id',
            'title',
            'description',
            'link',
            'pub_date',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserYouTubeSubscriptionSerializer(serializers.ModelSerializer):
    """유튜브 채널 구독 Serializer"""

    class Meta:
        model = UserYouTubeSubscription
        fields = [
            'id',
            'channel_id',
            'channel_title',
            'channel_description',
            'channel_thumbnail',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserWatchLaterSerializer(serializers.ModelSerializer):
    """나중에 볼 영상 Serializer"""

    class Meta:
        model = UserWatchLater
        fields = [
            'id',
            'video_id',
            'video_title',
            'video_description',
            'video_thumbnail',
            'channel_title',
            'published_at',
            'is_watched',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
