from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # 챗봇 대화
    path('chat/', views.chat, name='chat'),

    # 대화 히스토리 조회 및 삭제 (GET: 조회, DELETE: 삭제)
    path('history/', views.chat_history_handler, name='chat_history_handler'),

    # 특정 메시지 삭제
    path('messages/<int:message_id>/', views.delete_single_message, name='delete_single_message'),

    # 챗봇 아바타 조회
    path('avatar/', views.get_chatbot_avatar, name='get_chatbot_avatar'),
]
