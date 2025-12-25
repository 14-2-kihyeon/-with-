"""
GMS API 'system' role 테스트
"""
import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from django.conf import settings

api_url = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
api_key = settings.GMS_KEY

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# Test with 'system' role
payload = {
    "model": "gpt-5-mini",
    "messages": [
        {
            "role": "system",
            "content": "당신은 친절한 AI 어시스턴트입니다."
        },
        {
            "role": "user",
            "content": "안녕"
        }
    ],
    "max_completion_tokens": 150,
}

print("Testing with 'system' role...")
try:
    response = requests.post(api_url, headers=headers, json=payload, timeout=30)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success: {result['choices'][0]['message']['content']}")
    else:
        print(f"❌ Error: {response.text}")

except Exception as e:
    print(f"❌ Exception: {e}")
