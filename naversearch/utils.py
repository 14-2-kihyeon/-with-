# naversearch/utils.py
import os
import re
import requests
import html 
from django.conf import settings
from .models import News

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID") or getattr(settings, "NAVER_CLIENT_ID", None)
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET") or getattr(settings, "NAVER_CLIENT_SECRET", None)

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
