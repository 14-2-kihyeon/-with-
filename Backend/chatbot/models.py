from django.db import models
from django.conf import settings


class ChatMessage(models.Model):
    """
    AI 챗봇 대화 히스토리 모델
    사용자의 질문과 AI의 응답을 저장
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages')
    user_message = models.TextField(verbose_name='사용자 메시지')
    ai_response = models.TextField(verbose_name='AI 응답')

    # 추천된 상품 정보 (JSON 형태로 저장)
    recommended_products = models.JSONField(null=True, blank=True, verbose_name='추천 상품 목록')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 시간')

    class Meta:
        ordering = ['created_at']
        verbose_name = '챗봇 메시지'
        verbose_name_plural = '챗봇 메시지들'

    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class ChatSession(models.Model):
    """
    채팅 세션 모델 (선택사항)
    여러 대화를 세션별로 그룹화
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=200, default='새로운 대화', verbose_name='세션 제목')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 시간')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정 시간')
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')

    class Meta:
        ordering = ['-updated_at']
        verbose_name = '채팅 세션'
        verbose_name_plural = '채팅 세션들'

    def __str__(self):
        return f"{self.user.username} - {self.title}"
