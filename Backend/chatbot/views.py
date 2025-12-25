from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ChatMessage, ChatSession
from .serializers import ChatMessageSerializer, ChatRequestSerializer, ChatSessionSerializer
from .services import ChatbotService


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat(request):
    """
    챗봇과 대화하기
    POST /chatbot/chat/
    Body: { "message": "예금 상품 추천해주세요" }
    """
    try:
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_message = serializer.validated_data['message']

        # 챗봇 서비스 초기화
        chatbot = ChatbotService(request.user)

        # 최근 대화 히스토리 가져오기 (컨텍스트용)
        chat_history = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:5]

        # AI 응답 생성
        result = chatbot.chat(user_message, chat_history)

        if not result['success']:
            print(f"챗봇 AI 응답 실패: {result.get('error')}")
            return Response(
                {'error': result.get('error', '알 수 없는 오류'), 'ai_response': result.get('response', '죄송합니다. 일시적인 오류가 발생했습니다.')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 대화 내용 DB에 저장
        chat_message = ChatMessage.objects.create(
            user=request.user,
            user_message=user_message,
            ai_response=result['response'],
            recommended_products=result.get('recommended_products'),
        )

        # 응답 반환
        response_serializer = ChatMessageSerializer(chat_message)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        print(f"챗봇 처리 중 예외 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'서버 오류: {str(e)}', 'ai_response': '죄송합니다. 요청을 처리할 수 없습니다.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def chat_history_handler(request):
    """
    사용자의 채팅 히스토리 조회 및 삭제
    GET /chatbot/history/ - 조회
    DELETE /chatbot/history/ - 전체 삭제
    Query params (GET): ?limit=20 (기본값: 50)
    """
    if request.method == 'GET':
        limit = int(request.GET.get('limit', 50))
        messages = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:limit]
        serializer = ChatMessageSerializer(messages, many=True)

        # 오름차순으로 정렬하여 반환 (최신 메시지가 마지막에)
        return Response(list(reversed(serializer.data)), status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        deleted_count, _ = ChatMessage.objects.filter(user=request.user).delete()
        return Response(
            {'message': f'{deleted_count}개의 메시지가 삭제되었습니다.'},
            status=status.HTTP_200_OK
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_single_message(request, message_id):
    """
    특정 메시지 삭제
    DELETE /chatbot/messages/{message_id}/
    """
    try:
        message = ChatMessage.objects.get(id=message_id, user=request.user)
        message.delete()
        return Response(
            {'message': '메시지가 삭제되었습니다.'},
            status=status.HTTP_200_OK
        )
    except ChatMessage.DoesNotExist:
        return Response(
            {'error': '메시지를 찾을 수 없습니다.'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chatbot_avatar(request):
    """
    사용자 투자 성향에 맞는 챗봇 아바타 이미지 경로 반환
    GET /chatbot/avatar/
    Response: { "avatar": "timid_male" | "normal_female" | "speculative_male", "risk_type": "...", "risk_score": ... }
    """
    try:
        profile = request.user.investment_profile
        # risk_type 전체를 그대로 반환 (예: timid_male, normal_female, speculative_male)
        return Response({
            'avatar': profile.risk_type,  # 전체 risk_type 반환
            'risk_type': profile.risk_type,
            'risk_score': profile.risk_score,
        }, status=status.HTTP_200_OK)

    except Exception:
        # 프로필이 없으면 기본 아바타 반환
        return Response({
            'avatar': 'normal',
            'risk_type': None,
            'risk_score': None,
        }, status=status.HTTP_200_OK)
