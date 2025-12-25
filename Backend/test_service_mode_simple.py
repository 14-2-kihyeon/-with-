"""
SERVICE 모드 간단 테스트
"""
import os
import django
import requests
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from django.conf import settings

api_url = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
api_key = settings.GMS_KEY

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# Simple SERVICE mode test
system_prompt = """당신은 금융 상담 AI입니다. 사용자의 질문에 간단히 답변하세요."""

payload = {
    "model": "gpt-5-mini",
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "예금 추천해줘"}
    ],
    "max_completion_tokens": 2000,
}

print("=" * 80)
print("SERVICE 모드 간단 테스트")
print("=" * 80)
print(f"\n요청 payload:")
print(json.dumps(payload, indent=2, ensure_ascii=False))

try:
    response = requests.post(api_url, headers=headers, json=payload, timeout=30)
    print(f"\n응답 상태: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n전체 응답:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        ai_response = result['choices'][0]['message']['content']
        print(f"\nAI 응답 내용:")
        print(ai_response)
        print(f"\nAI 응답 길이: {len(ai_response)}자")
    else:
        print(f"\n에러 응답:")
        print(response.text)

except Exception as e:
    print(f"\n예외 발생: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
