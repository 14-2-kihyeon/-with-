"""
간단한 응답 테스트 - 왜 응답이 비어있는지 확인
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from chatbot.services import ChatbotService
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

chatbot = ChatbotService(user)

print("Testing simple query...")
result = chatbot.chat("삼성전자 어때?")

print(f"\nSuccess: {result['success']}")
print(f"Response length: {len(result['response'])} chars")

if result['response']:
    print(f"\nFull response:")
    print(result['response'])
else:
    print("\nResponse is empty!")
    print(f"Error: {result.get('error')}")
