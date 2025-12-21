import os
import re
import html
import requests
from email.utils import parsedate_to_datetime
from django.conf import settings

BASE_URL = "https://openapi.naver.com/v1/search/news.json"
TAG_RE = re.compile(r"<[^>]*>")

def clean_html(raw_text: str) -> str:
    if not raw_text:
        return ""
    text = TAG_RE.sub("", raw_text)
    return html.unescape(text).strip()

class NaverNewsClient:
    def __init__(self):
        self.client_id = os.environ.get("NAVER_CLIENT_ID") or getattr(settings, "NAVER_CLIENT_ID", None)
        self.client_secret = os.environ.get("NAVER_CLIENT_SECRET") or getattr(settings, "NAVER_CLIENT_SECRET", None)
        if not self.client_id or not self.client_secret:
            raise RuntimeError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 설정이 필요합니다.")

    def search(self, query: str, display: int = 20, start: int = 1, sort: str = "date") -> list[dict]:
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }
        params = {
            "query": query,
            "display": min(max(display, 1), 100),
            "start": min(max(start, 1), 1000),
            "sort": sort,
        }

        r = requests.get(BASE_URL, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        items = data.get("items", []) or []

        out = []
        for it in items:
            pub = it.get("pubDate")
            pub_dt = parsedate_to_datetime(pub) if pub else None

            out.append({
                "title": clean_html(it.get("title", ""))[:500],
                "description": clean_html(it.get("description", "")),
                "link": it.get("link", ""),
                "originallink": it.get("originallink", ""),
                "published_at": pub_dt,
            })
        return out
