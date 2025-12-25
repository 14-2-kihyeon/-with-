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
    """뉴스 목록 조회 - 로그인한 사용자의 경우 북마크 상태 포함"""
    from accounts.models import UserNewsBookmark

    qs = News.objects.all().order_by("-id")
    serializer = NewsSerializer(qs, many=True)
    news_list = serializer.data

    # 로그인한 사용자의 경우 북마크 상태 추가
    if request.user.is_authenticated:
        bookmarked_news_ids = set(
            UserNewsBookmark.objects.filter(user=request.user)
            .values_list('news_id', flat=True)
        )

        for news in news_list:
            news['is_bookmarked'] = news['id'] in bookmarked_news_ids
    else:
        # 비로그인 사용자는 모두 북마크되지 않음
        for news in news_list:
            news['is_bookmarked'] = False

    # 북마크 필터링 (선택적)
    bookmarked = request.query_params.get("bookmarked")
    if bookmarked in ("1", "true", "True"):
        news_list = [n for n in news_list if n.get('is_bookmarked')]

    return Response(news_list, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def news_detail(request, pk):
    """뉴스 상세 조회 - 로그인한 사용자의 경우 북마크 상태 포함"""
    from accounts.models import UserNewsBookmark

    try:
        news = News.objects.get(pk=pk)
    except News.DoesNotExist:
        return Response({"detail": "존재하지 않는 기사입니다."},
                        status=status.HTTP_404_NOT_FOUND)

    news_data = NewsSerializer(news).data

    # 로그인한 사용자의 경우 북마크 상태 추가
    if request.user.is_authenticated:
        is_bookmarked = UserNewsBookmark.objects.filter(
            user=request.user,
            news_id=news.id
        ).exists()
        news_data['is_bookmarked'] = is_bookmarked
    else:
        news_data['is_bookmarked'] = False

    return Response(news_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_bookmark(request, pk):
    """뉴스 북마크 토글 - 사용자별로 관리"""
    from accounts.models import UserNewsBookmark

    try:
        news = News.objects.get(pk=pk)
    except News.DoesNotExist:
        return Response({"detail": "존재하지 않는 기사입니다."},
                        status=status.HTTP_404_NOT_FOUND)

    # 사용자별 북마크 토글
    bookmark, created = UserNewsBookmark.objects.get_or_create(
        user=request.user,
        news_id=news.id,
        defaults={
            'title': news.title,
            'description': news.description,
            'link': news.link,
            'pub_date': news.pub_date,
        }
    )

    # 이미 존재하면 삭제 (토글)
    if not created:
        bookmark.delete()
        is_bookmarked = False
    else:
        is_bookmarked = True

    # 응답 데이터에 북마크 상태 포함
    news_data = NewsSerializer(news).data
    news_data['is_bookmarked'] = is_bookmarked

    return Response(news_data, status=status.HTTP_200_OK)


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
