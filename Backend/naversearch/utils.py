# naversearch/utils.py
import os
import re
import requests
import html 
from django.conf import settings
from .models import News

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID") or getattr(settings, "NAVER_CLIENT_ID", None)
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET") or getattr(settings, "NAVER_CLIENT_SECRET", None)
GMS_OPENAI_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
BASE_URL = "https://openapi.naver.com/v1/search/news.json"


def clean_html(raw_text: str) -> str:
    """네이버 응답에 들어있는 <b> 태그, HTML 엔티티 등을 제거"""
    if not raw_text:
        return ""
    text = re.sub(r"<[^>]*>", "", raw_text)  # 태그 제거
    text = html.unescape(text)               # &quot; 같은 엔티티 해석
    return text


def search_and_save_news(query: str, display: int = 20) -> int:
    """
    네이버 뉴스 API를 호출해서 결과를 DB에 저장.
    - 제목이 같은 뉴스는 새로 저장하지 않음.
    - 저장된 개수를 return.
    """
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {
        "query": query,
        "display": display,
        "sort": "date",  # 최신순
    }

    response = requests.get(BASE_URL, headers=headers, params=params)
    response.raise_for_status()  # 오류면 예외 발생

    data = response.json()
    items = data.get("items", [])

    saved_count = 0

    for item in items:
        title = clean_html(item.get("title"))
        description = clean_html(item.get("description"))
        link = item.get("link")
        pub_date = item.get("pubDate")

        # 제목 기준 중복 저장 방지 (unique=True + get_or_create 두 겹 안전장치)
        obj, created = News.objects.get_or_create(
            title=title,
            defaults={
                "description": description,
                "link": link,
                "pub_date": pub_date,
            },
        )
        if created:
            saved_count += 1

    return saved_count


def summarize_news_text(title: str, description: str, link: str | None = None) -> str:
    """
    SSAFY GMS 프록시를 통해 gpt-5-mini로 뉴스 내용을 2~3문장 요약.
    - GMS에서 준 curl 예제와 최대한 동일한 JSON 형태로 요청.
    """
    if not settings.GMS_KEY:
        # .env / settings.py 설정 문제
        raise RuntimeError("GMS_KEY 가 설정되어 있지 않습니다. .env 와 settings.py 를 확인하세요.")

    base_text = description or ""
    if not base_text:
        base_text = f"기사 제목: {title}\n(본문 내용이 부족합니다. 제목만 기반으로 요약해 주세요.)"

    # user에게 넘길 프롬프트
    prompt = (
        "다음 뉴스 기사의 내용을 한국어로 2~3문장, 한 문단으로 요약해줘.\n"
        "불필요한 수식어는 줄이고, 핵심 사실 위주로 정리해줘.\n\n"
        f"제목: {title}\n\n본문:\n{base_text}"
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.GMS_KEY}",
    }

    # ★ SSAFY에서 제공한 curl 포맷과 최대한 동일하게
    data = {
        "model": "gpt-5-mini",
        "messages": [
            {
                "role": "developer",
                "content": "Answer in Korean",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        # temperature, max_tokens 등은 혹시 모를 검증 오류를 피하기 위해 일단 생략
    }

    resp = requests.post(GMS_OPENAI_URL, headers=headers, json=data, timeout=30)

    # 200 이 아니면 GMS의 에러 메시지를 그대로 확인할 수 있게 예외 발생
    if resp.status_code != 200:
        # 디버깅용: 서버 콘솔 + 프론트 응답 둘 다에서 에러 내용을 볼 수 있게
        raise RuntimeError(
            f"GMS 호출 실패 (status={resp.status_code}): {resp.text}"
        )

    payload = resp.json()
    # OpenAI ChatCompletions 응답 형식에 맞게 요약 추출
    summary = payload["choices"][0]["message"]["content"].strip()
    return summary