# naversearch/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from .utils import search_and_save_news, summarize_news_text
from .models import News
from .serializers import NewsSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def news_search(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return Response({"detail": "q(검색어) 쿼리 파라미터를 넣어주세요."},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        saved_count = search_and_save_news(query)
    except Exception as e:
        return Response({"detail": "네이버 API 호출 중 오류가 발생했습니다.", "error": str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"query": query, "saved_count": saved_count}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def news_list(request):
    qs = News.objects.all().order_by("-id")

    bookmarked = request.query_params.get("bookmarked")
    if bookmarked in ("1", "true", "True"):
        qs = qs.filter(is_bookmarked=True)

    serializer = NewsSerializer(qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def news_detail(request, pk):
    try:
        news = News.objects.get(pk=pk)
    except News.DoesNotExist:
        return Response({"detail": "존재하지 않는 기사입니다."},
                        status=status.HTTP_404_NOT_FOUND)

    return Response(NewsSerializer(news).data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])  # 원하면 AllowAny로 바꿔도 됨
def toggle_bookmark(request, pk):
    try:
        news = News.objects.get(pk=pk)
    except News.DoesNotExist:
        return Response({"detail": "존재하지 않는 기사입니다."},
                        status=status.HTTP_404_NOT_FOUND)

    news.is_bookmarked = not news.is_bookmarked
    news.save()

    return Response(NewsSerializer(news).data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])  # 원하면 AllowAny로 바꿔도 됨
def summarize_news(request, pk):
    try:
        news = News.objects.get(pk=pk)
    except News.DoesNotExist:
        return Response({"detail": "존재하지 않는 기사입니다."},
                        status=status.HTTP_404_NOT_FOUND)

    try:
        summary = summarize_news_text(news.title, news.description, news.link)
    except Exception as e:
        print("=== SUMMARY ERROR ===", e)
        return Response({"detail": f"요약 생성 중 오류: {e}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"summary": summary}, status=status.HTTP_200_OK)
