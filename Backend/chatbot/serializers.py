from rest_framework import serializers
from .models import ChatMessage, ChatSession


class ChatMessageSerializer(serializers.ModelSerializer):
    """
    챗봇 메시지 시리얼라이저
    """
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'username',
            'user_message',
            'ai_response',
            'recommended_products',
            'created_at',
        ]
        read_only_fields = ['id', 'username', 'created_at', 'ai_response', 'recommended_products']


class ChatRequestSerializer(serializers.Serializer):
    """
    챗봇 요청 시리얼라이저
    """
    message = serializers.CharField(required=True, max_length=2000)


class ChatSessionSerializer(serializers.ModelSerializer):
    """
    채팅 세션 시리얼라이저
    """
    username = serializers.CharField(source='user.username', read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            'id',
            'username',
            'title',
            'message_count',
            'created_at',
            'updated_at',
            'is_active',
        ]
        read_only_fields = ['id', 'username', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.user.chat_messages.count()
