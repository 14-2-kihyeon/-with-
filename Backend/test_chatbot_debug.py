"""
챗봇 500 에러 디버깅 스크립트
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from chatbot.services import ChatbotService
from django.contrib.auth import get_user_model

print("=" * 80)
print("Chatbot Debug Test Start")
print("=" * 80)

try:
    User = get_user_model()
    user = User.objects.first()

    if not user:
        print("[ERROR] No test user found")
        exit(1)

    print(f"[OK] User loaded: {user.username}")

    # ChatbotService initialization
    chatbot = ChatbotService(user)
    print(f"[OK] ChatbotService initialized")

    # CHAT mode test
    print("\n[Test 1] CHAT mode - 'Hello'")
    print("-" * 80)
    try:
        result = chatbot.chat("안녕")
        print(f"[OK] Response success!")
        print(f"   Response: {result['response']}")
        print(f"   Recommended products: {result.get('recommended_products')}")
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

    # SERVICE mode test
    print("\n[Test 2] SERVICE mode - 'Deposit recommendation'")
    print("-" * 80)
    try:
        result = chatbot.chat("예금 추천")
        print(f"[OK] Response success!")
        print(f"   Response length: {len(result['response'])} chars")
        print(f"   Response preview: {result['response'][:200]}...")
        print(f"   Recommended products: {len(result.get('recommended_products', []) or [])}")
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"[ERROR] Initialization failed: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)
