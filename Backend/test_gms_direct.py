"""
GMS API 직접 호출 테스트
"""
import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from django.conf import settings

print("=" * 80)
print("GMS API 직접 호출 테스트")
print("=" * 80)

api_url = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
api_key = settings.GMS_KEY

# 테스트 1: CHAT 모드 (짧은 응답)
print("\n[테스트 1] CHAT 모드 - 간단한 인사")
print("-" * 80)

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

payload = {
    "model": "gpt-5-mini",
    "messages": [
        {
            "role": "developer",
            "content": "당신은 친절한 AI 어시스턴트입니다. 간단히 답변하세요."
        },
        {
            "role": "user",
            "content": "안녕"
        }
    ],
    "max_completion_tokens": 150,
}

print(f"요청 URL: {api_url}")
print(f"요청 페이로드:")
import json
print(json.dumps(payload, indent=2, ensure_ascii=False))

try:
    response = requests.post(
        api_url,
        headers=headers,
        json=payload,
        timeout=30
    )

    print(f"\n응답 상태 코드: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        ai_response = result['choices'][0]['message']['content']
        print(f"[성공] AI 응답: {ai_response}")
    else:
        print(f"[실패] 에러 응답:")
        print(response.text)

except Exception as e:
    print(f"[에러] {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("테스트 완료")
print("=" * 80)
