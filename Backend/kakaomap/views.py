# Backend/kakaomap/views.py
import requests
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes


@api_view(["GET"])
@permission_classes([AllowAny])
def route(request):
    origin = request.query_params.get("origin")          # "lng,lat"
    destination = request.query_params.get("destination")  # "lng,lat"

    if not origin or not destination:
        return Response(
            {"detail": "origin, destination이 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    rest_key = getattr(settings, "KAKAO_MOBILITY_REST_KEY", None)
    if not rest_key:
        return Response(
            {"detail": "KAKAO_MOBILITY_REST_KEY가 설정되지 않았습니다. (Backend .env / settings 로딩 확인)"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    url = "https://apis-navi.kakaomobility.com/v1/directions"

    try:
        r = requests.get(
            url,
            params={
                "origin": origin,
                "destination": destination,
                # 필요하면 옵션 추가 가능:
                # "priority": "RECOMMEND",
            },
            headers={"Authorization": f"KakaoAK {rest_key}"},
            timeout=10,
        )
    except requests.RequestException as e:
        return Response(
            {"detail": "카카오 모빌리티 API 요청 실패", "error": str(e)},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    # JSON 파싱
    try:
        data = r.json()
    except ValueError:
        return Response(
            {"detail": "카카오 응답이 JSON이 아닙니다.", "status_code": r.status_code, "text": r.text[:300]},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    # 카카오가 에러코드 반환한 경우
    if r.status_code != 200:
        return Response(
            {"detail": "카카오 모빌리티 API 오류", "status_code": r.status_code, "data": data},
            status=r.status_code,
        )

    routes = data.get("routes") or []
    if not routes:
        return Response(
            {"detail": "경로를 찾을 수 없습니다. (routes가 비어있음)", "data": data},
            status=status.HTTP_400_BAD_REQUEST,
        )

    sections = routes[0].get("sections") or []
    if not sections:
        return Response(
            {"detail": "경로를 찾을 수 없습니다. (sections가 비어있음)", "data": data},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 좌표 가공
    path = []
    for section in sections:
        for road in section.get("roads", []):
            v = road.get("vertexes", [])
            for i in range(0, len(v), 2):
                path.append({"lng": v[i], "lat": v[i + 1]})

    if not path:
        return Response(
            {"detail": "경로 좌표가 비어있습니다.", "data": data},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({"path": path})
