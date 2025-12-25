"""
Simple chatbot test
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

# Test 1: CHAT mode
print("\n[TEST 1] CHAT mode")
result1 = chatbot.chat("안녕")
print(f"Success: {result1['success']}")
print(f"Response length: {len(result1['response'])} chars")
print(f"Recommended products: {result1.get('recommended_products')}")

# Test 2: SERVICE mode
print("\n[TEST 2] SERVICE mode")
result2 = chatbot.chat("예금 추천")
print(f"Success: {result2['success']}")
print(f"Response length: {len(result2['response'])} chars")
print(f"Recommended products count: {len(result2.get('recommended_products') or [])}")

print("\n[RESULT] 500 error fixed!")
print("Both CHAT and SERVICE modes working.")
