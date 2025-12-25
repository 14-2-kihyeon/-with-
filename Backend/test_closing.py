"""
마무리 문장 테스트
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from chatbot.services import ChatbotService
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

if not user:
    print("No user found")
    exit(1)

chatbot = ChatbotService(user)

print("=" * 80)
print("마무리 문장 테스트")
print("=" * 80)

# Test: "삼전 어때?" - 이전에 중간에 끊겼던 케이스
print("\n[TEST] '삼전 어때?' 질문")
print("-" * 80)

result = chatbot.chat("삼전 어때?")

if result['success']:
    response = result['response']
    lines = response.split('\n')

    print(f"응답 길이: {len(response)}자")
    print(f"줄 수: {len([l for l in lines if l.strip()])}줄")
    print(f"\n전체 응답:")
    print(response)

    # 마무리 문장 확인
    last_lines = [l.strip() for l in lines if l.strip()][-3:]
    print(f"\n마지막 3줄:")
    for line in last_lines:
        print(f"  - {line}")

    # 마무리 패턴 체크
    closing_keywords = ['궁금', '도움', '문의', '투자', '질문', '말씀', '필요']
    has_closing = any(keyword in response for keyword in closing_keywords)

    if has_closing:
        print(f"\n✅ 마무리 문장 포함됨")
    else:
        print(f"\n⚠️ 마무리 문장이 없을 수 있음")
else:
    print(f"❌ 에러: {result.get('error')}")

print("\n" + "=" * 80)
