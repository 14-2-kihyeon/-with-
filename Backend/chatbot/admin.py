from django.contrib import admin
from .models import ChatMessage, ChatSession


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'user_message_preview', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['user__username', 'user_message', 'ai_response']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    def user_message_preview(self, obj):
        """메시지 미리보기 (50자)"""
        return obj.user_message[:50] + '...' if len(obj.user_message) > 50 else obj.user_message
    user_message_preview.short_description = '사용자 메시지'


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['user__username', 'title']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']
