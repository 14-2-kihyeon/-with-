# stocks/services/llm_client.py
from __future__ import annotations

import requests
from django.conf import settings

GMS_OPENAI_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"

def gms_chat(
    *,
    messages: list[dict],
    model: str = "gpt-5-mini",
    timeout: int | tuple[int, int] = (10, 120),  # (connect, read)
) -> str:
    if not getattr(settings, "GMS_KEY", None):
        raise RuntimeError("GMS_KEY 가 설정되어 있지 않습니다. (.env / settings.py 확인)")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.GMS_KEY}",
    }

    # ✅ GMS 프록시가 엄격할 수 있어서 model+messages만 보냄
    data = {
        "model": model,
        "messages": messages,
    }

    resp = requests.post(GMS_OPENAI_URL, headers=headers, json=data, timeout=timeout)

    # ✅ 400/401/403일 때 “왜 틀렸는지” 본문을 반드시 노출
    if resp.status_code != 200:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise RuntimeError(f"GMS_HTTP_{resp.status_code}: {detail}")

    payload = resp.json()
    return payload["choices"][0]["message"]["content"].strip()
