
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .utils import youtube_search, youtube_video_detail


@api_view(['GET'])
def search_view(request):
    q = request.GET.get("q","").strip()
    if not q:
        return Response({"detail": "q(query) is required"}, status=status.HTTP_400_BAD_REQUEST)
    channel_id = request.GET.get("channelId", "").strip()
    results = youtube_search(q, channel_id=channel_id or None)
    return Response(results)

@api_view(['GET'])
def detail_view(request, video_id):
    detail = youtube_video_detail(video_id)
    if detail is None:
        return Response({"detail": "Video not found"}, status=status.HTTP_400_BAD_REQUEST)
    return Response(detail)