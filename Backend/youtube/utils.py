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
    # 비디오 정보 가져오기
    video_url = f"{BASE_URL}/videos"
    video_params = {
        "part" : "snippet",
        "id" : video_id,
        "key" : settings.YOUTUBE_API_KEY,
    }
    r = requests.get(video_url, params=video_params, timeout=10)
    r.raise_for_status()
    data = r.json()

    items = data.get("items", [])
    if not items:
        return None

    snip = items[0]["snippet"]
    channel_id = snip.get("channelId")

    # 채널 정보 가져오기
    channel_description = ""
    channel_thumbnail = ""
    if channel_id:
        try:
            channel_url = f"{BASE_URL}/channels"
            channel_params = {
                "part": "snippet",
                "id": channel_id,
                "key": settings.YOUTUBE_API_KEY,
            }
            channel_res = requests.get(channel_url, params=channel_params, timeout=10)
            channel_res.raise_for_status()
            channel_data = channel_res.json()

            if channel_data.get("items"):
                channel_snip = channel_data["items"][0]["snippet"]
                channel_description = html.unescape(channel_snip.get("description", ""))
                channel_thumbnail = channel_snip.get("thumbnails", {}).get("medium", {}).get("url", "")
        except Exception as e:
            print(f"채널 정보 조회 실패: {e}")

    return {
        "videoId" : video_id,
        "title" : html.unescape(snip.get("title")),
        "channelTitle": html.unescape(snip.get("channelTitle")),
        "channelId": channel_id,
        "channelDescription": channel_description,
        "channelThumbnail": channel_thumbnail,
        "description": html.unescape(snip.get("description")),
        "publishedAt" : snip.get("publishedAt"),
        "thumnail" : snip.get("thumbnails", {}).get("medium", {}).get("url"),
    }