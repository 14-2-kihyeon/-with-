"""
간단히 상품 데이터 구조 확인
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
products = chatbot.get_financial_products_context()

print("Products keys:", products.keys())
print("\nDeposits count:", len(products.get('deposits', [])))
print("Savings count:", len(products.get('savings', [])))

if products.get('deposits'):
    print("\nFirst deposit product keys:")
    print(products['deposits'][0].keys())
    print("\nFirst deposit product:")
    for key, value in products['deposits'][0].items():
        print(f"  {key}: {value}")
