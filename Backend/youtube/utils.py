import requests, html
from django.conf import settings

BASE_URL = "https://www.googleapis.com/youtube/v3"

def youtube_search(query: str, max_results: int = 10, channel_id: str | None = None):
    url = f"{BASE_URL}/search"
    params = {
        "part": "snippet",
        "type": "video",
        "q": query,
        "maxResults": max_results,
        "key": settings.YOUTUBE_API_KEY,
    }
    if channel_id:
        params["channelId"] = channel_id  # ✅ 채널 필터

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    results = []
    for item in data.get("items", []):
        vid = item["id"]["videoId"]
        snip = item["snippet"]
        results.append({
            "videoId" : vid,
            "title": html.unescape(snip.get("title")),
            "channerlTitle" : html.unescape(snip.get("channelTitle")),
            "thumbnail": snip.get("thumbnails", {}).get("medium", {}).get("url"),
        })
    return results


def youtube_video_detail(video_id: str):
    url = f"{BASE_URL}/videos"
    params = {
        "part" : "snippet",
        "id" : video_id,
        "key" : settings.YOUTUBE_API_KEY,
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    items = data.get("items", [])
    if not items:
        return None
    



    snip = items[0]["snippet"]
    return {
        "videoId" : video_id,
        "title" : html.unescape(snip.get("title")),
        "channelTitle": html.unescape(snip.get("channelTitle")),
        "description": html.unescape(snip.get("description")),
        "publishedAt" : snip.get("publishedAt"),
        "thumnail" : snip.get("thumbnails", {}).get("medium", {}).get("url"),
        "channelId": snip.get("channelId"),

    }