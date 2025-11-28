from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .utils import search_and_save_news
from .models import News
from .serializers import NewsSerializer

def news_home(request):
    # 우리가 만든 index.html (base.html 상속)
    return render(request, "naversearch/index.html")


@api_view(["GET"])
def news_search(request):
    """
    GET /api/news/search/?q=검색어
    -> 네이버 API 호출 & DB 저장 후, 저장된 개수 반환
    """
    query = request.GET.get("q", "").strip()

    if not query:
        return Response(
            {"detail": "q(검색어) 쿼리 파라미터를 넣어주세요."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        saved_count = search_and_save_news(query)
    except Exception as e:
        return Response(
            {"detail": "네이버 API 호출 중 오류가 발생했습니다.", "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {"query": query, "saved_count": saved_count},
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def news_list(request):
    """
    GET /api/news/
    -> 저장된 전체 뉴스 목록을 반환
    """
    qs = News.objects.all().order_by("-id")  # 최근 뉴스가 위로 오도록
    serializer = NewsSerializer(qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def news_detail(request, pk):
    """
    GET /api/news/<id>/
    -> 단일 뉴스 상세 정보 반환
    """
    try:
        news = News.objects.get(pk=pk)
    except News.DoesNotExist:
        return Response(
            {"detail": "존재하지 않는 기사입니다."},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = NewsSerializer(news)
    return Response(serializer.data, status=status.HTTP_200_OK)
  
  
  