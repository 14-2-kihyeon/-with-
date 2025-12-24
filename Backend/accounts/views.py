from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import (
    InvestmentProfile,
    SurveyQuestion,
    SurveyChoice,
    SurveyResponse,
    ProductRecommendation,
    calculate_risk_type,
    RISK_TYPE_MAPPING
)
from finances.models import DepositProducts, DepositOptions


# ==========================================
# 1. 설문 조사 관련 API
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_survey_questions(request):
    """투자 성향 설문 질문 목록 조회"""
    questions = SurveyQuestion.objects.filter(is_active=True).prefetch_related('choices')
    
    data = []
    for q in questions:
        data.append({
            'id': q.id,
            'category': q.category,
            'category_display': q.get_category_display(),
            'question_text': q.question_text,
            'order': q.order,
            'choices': [
                {
                    'id': choice.id,
                    'choice_text': choice.choice_text,
                    'score': choice.score,
                    'order': choice.order,
                }
                for choice in q.choices.all()
            ]
        })
    
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_survey(request):
    """
    설문 응답 제출 및 투자 성향 결과 계산

    Request Body:
    {
        "responses": [
            {"question_id": 1, "choice_id": 3},
            {"question_id": 2, "choice_id": 5},
            ...
        ],
        "gender": "M",  # "M" 또는 "F" (필수)
        "age": 30,
        "income": 5000,  # 만원
        "savings": 10000,  # 만원
        "investment_goal": "주택구매",
        "investment_period": 36  # 개월
    }
    """
    responses = request.data.get('responses', [])
    gender = request.data.get('gender')

    if not responses:
        return Response(
            {'detail': '응답이 비어있습니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not gender or gender not in ['M', 'F']:
        return Response(
            {'detail': '성별을 선택해주세요. (M 또는 F)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 기존 응답 삭제 (재검사 시)
    SurveyResponse.objects.filter(user=request.user).delete()

    total_score = 0

    # 응답 저장 및 점수 계산
    for resp in responses:
        question_id = resp.get('question_id')
        choice_id = resp.get('choice_id')

        try:
            question = SurveyQuestion.objects.get(id=question_id)
            choice = SurveyChoice.objects.get(id=choice_id, question=question)

            # 응답 저장
            SurveyResponse.objects.create(
                user=request.user,
                question=question,
                choice=choice
            )

            total_score += choice.score

        except (SurveyQuestion.DoesNotExist, SurveyChoice.DoesNotExist):
            return Response(
                {'detail': f'잘못된 질문 또는 선택지입니다. (question_id: {question_id}, choice_id: {choice_id})'},
                status=status.HTTP_400_BAD_REQUEST
            )

    # 투자 성향 결정 (성별 포함)
    risk_type = calculate_risk_type(total_score, gender)

    # InvestmentProfile 생성 또는 업데이트
    profile, created = InvestmentProfile.objects.update_or_create(
        user=request.user,
        defaults={
            'risk_score': total_score,
            'risk_type': risk_type,
            'gender': gender,
            'age': request.data.get('age'),
            'income': request.data.get('income'),
            'savings': request.data.get('savings'),
            'investment_goal': request.data.get('investment_goal'),
            'investment_period': request.data.get('investment_period'),
        }
    )
    
    # 결과 반환
    risk_data = RISK_TYPE_MAPPING[risk_type]

    return Response({
        'risk_type': risk_type,
        'risk_type_name': risk_data['name'],
        'risk_score': total_score,
        'gender': gender,  # ✅ 추가
        'gender_display': '남성' if gender == 'M' else '여성',  # ✅ 추가
        'description': risk_data['description'],
        'characteristics': risk_data['characteristics'],
        'recommended_products': risk_data['recommended_products'],  # ✅ 키 이름 수정 (guide 제거)
        'created': created,  # 처음 작성했는지 여부
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_investment_profile(request):
    """현재 사용자의 투자 성향 프로필 조회"""
    try:
        profile = request.user.investment_profile
    except InvestmentProfile.DoesNotExist:
        return Response(
            {'detail': '투자 성향 검사를 먼저 진행해주세요.'},
            status=status.HTTP_404_NOT_FOUND
        )

    risk_data = RISK_TYPE_MAPPING.get(profile.risk_type, {})

    return Response({
        'risk_type': profile.risk_type,
        'risk_type_name': risk_data.get('name'),
        'risk_score': profile.risk_score,
        'gender': profile.gender,
        'gender_display': profile.get_gender_display(),
        'description': risk_data.get('description'),
        'characteristics': risk_data.get('characteristics'),
        'recommended_products': risk_data.get('recommended_products'),
        'age': profile.age,
        'income': profile.income,
        'savings': profile.savings,
        'investment_goal': profile.investment_goal,
        'investment_period': profile.investment_period,
        'created_at': profile.created_at,
        'updated_at': profile.updated_at,
    })


# ==========================================
# 2. 상품 추천 API
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommend_products(request):
    """
    사용자의 투자 성향에 맞는 예금/적금 상품 추천

    추천 로직:
    1. 투자 성향별 가입기간 매칭
    2. 투자 가능 기간 고려한 상품 분산
    3. 금리 높은 순으로 정렬
    4. 투자 계획 제시
    """
    try:
        profile = request.user.investment_profile
    except InvestmentProfile.DoesNotExist:
        return Response(
            {'detail': '투자 성향 검사를 먼저 진행해주세요.'},
            status=status.HTTP_404_NOT_FOUND
        )

    risk_data = RISK_TYPE_MAPPING[profile.risk_type]
    recommended_period_months = risk_data.get('recommended_period_months', [12, 24, 36])

    # 예금 상품 조회
    deposit_products = DepositProducts.objects.prefetch_related('options').all()

    recommendations = []

    for product in deposit_products:
        # 해당 성향에 맞는 옵션 찾기
        for period in recommended_period_months:
            matching_options = product.options.filter(
                save_trm=period
            ).order_by('-intr_rate2')

            if matching_options.exists():
                best_option = matching_options.first()
                match_score = calculate_match_score(profile, product, best_option)

                recommendations.append({
                    'product': {
                        'fin_prdt_cd': product.fin_prdt_cd,
                        'kor_co_nm': product.kor_co_nm,
                        'fin_prdt_nm': product.fin_prdt_nm,
                        'join_way': product.join_way,
                        'spcl_cnd': product.spcl_cnd,
                    },
                    'option': {
                        'save_trm': best_option.save_trm,
                        'intr_rate': float(best_option.intr_rate) if best_option.intr_rate else 0,
                        'intr_rate2': float(best_option.intr_rate2) if best_option.intr_rate2 else 0,
                    },
                    'match_score': match_score,
                    'reason': generate_recommendation_reason(profile, product, best_option),
                })

    # 매칭 점수 높은 순으로 정렬
    recommendations.sort(key=lambda x: x['match_score'], reverse=True)

    # 투자 계획 생성
    investment_plan = generate_investment_plan(profile, recommendations)

    return Response({
        'profile': {
            'risk_type': profile.risk_type,
            'risk_type_name': risk_data['name'],
            'risk_score': profile.risk_score,
            'gender': profile.gender,
            'gender_display': profile.get_gender_display(),
            'age': profile.age,
            'income': float(profile.income) if profile.income else 0,
            'savings': float(profile.savings) if profile.savings else 0,
            'investment_goal': profile.investment_goal,
            'investment_period': profile.investment_period,
        },
        'recommendations': recommendations[:15],  # 상위 15개
        'investment_plan': investment_plan,
        'total_count': len(recommendations),
    })


def calculate_match_score(profile, product, option):
    """
    매칭 점수 계산 (0~100점)
    
    고려 사항:
    - 투자기간 일치도 (30점)
    - 금리 수준 (40점)
    - 우대조건 매칭 (20점)
    - 가입 방법 편의성 (10점)
    """
    score = 0
    
    # 1. 투자기간 일치도 (30점)
    if profile.investment_period:
        period_diff = abs(profile.investment_period - option.save_trm)
        if period_diff == 0:
            score += 30
        elif period_diff <= 6:
            score += 20
        elif period_diff <= 12:
            score += 10
    else:
        score += 15  # 기본점수
    
    # 2. 금리 수준 (40점)
    # 우대금리 기준으로 점수화
    if option.intr_rate2 >= 4.0:
        score += 40
    elif option.intr_rate2 >= 3.5:
        score += 30
    elif option.intr_rate2 >= 3.0:
        score += 20
    else:
        score += 10
    
    # 3. 우대조건 매칭 (20점)
    # 실제로는 사용자의 급여이체, 카드사용 등을 고려해야 함
    if product.spcl_cnd and len(product.spcl_cnd) > 10:
        score += 15  # 우대조건이 다양하면 높은 점수
    else:
        score += 5
    
    # 4. 가입 방법 편의성 (10점)
    if product.join_way:
        if '인터넷' in product.join_way or '모바일' in product.join_way:
            score += 10
        elif '영업점' in product.join_way:
            score += 5
    
    return min(score, 100)  # 최대 100점


def generate_recommendation_reason(profile, product, option):
    """추천 이유 생성"""
    reasons = []

    # 성향별 추천 이유
    risk_name = RISK_TYPE_MAPPING[profile.risk_type]['name']
    reasons.append(f"{risk_name} 투자자에게 적합한 상품입니다.")

    # 금리 언급
    if option.intr_rate2 >= 3.5:
        reasons.append(f"최고 우대금리 {option.intr_rate2}%로 높은 수익을 기대할 수 있습니다.")

    # 기간 매칭
    if profile.investment_period and abs(profile.investment_period - option.save_trm) <= 6:
        reasons.append(f"희망 투자기간({profile.investment_period}개월)과 가입기간({option.save_trm}개월)이 잘 맞습니다.")

    # 우대조건
    if product.spcl_cnd:
        reasons.append("우대조건을 활용하면 더 높은 금리를 받을 수 있습니다.")

    return " ".join(reasons)


def generate_investment_plan(profile, recommendations):
    """
    투자 계획 생성

    투자 가능 기간과 성향을 고려하여 단계별 투자 계획 제안
    """
    investment_period = profile.investment_period or 12
    risk_data = RISK_TYPE_MAPPING[profile.risk_type]

    plan = {
        'total_period_months': investment_period,
        'risk_level': risk_data['name'],
        'strategy': '',
        'steps': [],
        'tips': []
    }

    # 성향별 전략
    if 'timid' in profile.risk_type:
        plan['strategy'] = '안정성을 최우선으로 하는 보수적 투자 전략입니다. 원금 보장 상품 중심으로 단기~중기 분산 투자를 권장합니다.'
        plan['tips'] = [
            '3개월, 6개월, 12개월 단위로 분산하여 유동성 확보',
            '금리가 높은 예금 상품 위주로 선택',
            '만기 시 재투자하여 복리 효과 극대화',
            '은행별 예금자 보호 한도(5천만원) 고려하여 분산'
        ]
    elif 'normal' in profile.risk_type:
        plan['strategy'] = '안정성과 수익성의 균형을 추구하는 전략입니다. 중기 예금과 일부 변동금리 상품을 혼합하여 포트폴리오를 구성합니다.'
        plan['tips'] = [
            '12개월, 24개월 단위로 분산 투자',
            '고금리 예금 50% + 적금 30% + 유동성자금 20%',
            '우대조건 활용하여 금리 극대화',
            '정기적으로 시장 금리 확인 후 재조정'
        ]
    else:  # speculative
        plan['strategy'] = '적극적인 수익 추구 전략입니다. 장기 고금리 상품과 변동금리 상품을 활용하여 높은 수익을 목표로 합니다.'
        plan['tips'] = [
            '24개월, 36개월 장기 상품으로 고금리 확보',
            '일부 자금은 주식형 펀드나 ETF로 분산',
            '금리 상승기에는 단기 상품, 하락기에는 장기 상품',
            '세제 혜택 상품(ISA, IRP 등) 적극 활용'
        ]

    # 투자 기간에 따른 단계별 계획
    if investment_period <= 12:
        # 단기 (1년 이내)
        plan['steps'].append({
            'period': '즉시~3개월',
            'action': '단기 고금리 예금 가입',
            'description': '유동성 확보를 위한 3~6개월 예금 중심'
        })
        plan['steps'].append({
            'period': '3개월~12개월',
            'action': '중기 예금 전환',
            'description': '만기 도래 시 12개월 예금으로 재투자'
        })
    elif investment_period <= 24:
        # 중기 (1~2년)
        plan['steps'].append({
            'period': '즉시~6개월',
            'action': '6개월 예금 50% + 12개월 예금 50%',
            'description': '분산 투자로 유동성과 수익성 균형'
        })
        plan['steps'].append({
            'period': '6개월~18개월',
            'action': '12개월 예금 집중',
            'description': '안정적인 중기 상품으로 포트폴리오 전환'
        })
        plan['steps'].append({
            'period': '18개월~24개월',
            'action': '목표 달성 및 재투자',
            'description': '만기 시 재평가 후 장기 상품 검토'
        })
    else:
        # 장기 (2년 이상)
        plan['steps'].append({
            'period': '즉시~12개월',
            'action': '12개월 예금 30% + 24개월 예금 40% + 적금 30%',
            'description': '장기 투자 기반 마련'
        })
        plan['steps'].append({
            'period': '12개월~24개월',
            'action': '만기 자금 36개월 예금 전환',
            'description': '고금리 장기 상품으로 재투자'
        })
        plan['steps'].append({
            'period': '24개월 이후',
            'action': '포트폴리오 재조정',
            'description': '시장 상황에 따라 예금/적금/투자 비율 조정'
        })

    return plan


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bookmark_recommendation(request, fin_prdt_cd):
    """추천 상품 북마크 (관심 상품 저장)"""
    from .models import ProductRecommendation
    
    try:
        product = DepositProducts.objects.get(fin_prdt_cd=fin_prdt_cd)
    except DepositProducts.DoesNotExist:
        return Response(
            {'detail': '상품을 찾을 수 없습니다.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # 북마크 토글
    recommendation, created = ProductRecommendation.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={
            'match_score': 0,  # 나중에 계산
            'recommended_reason': '',
        }
    )
    
    if not created:
        recommendation.is_bookmarked = not recommendation.is_bookmarked
        recommendation.save()
    else:
        recommendation.is_bookmarked = True
        recommendation.save()
    
    return Response({
        'bookmarked': recommendation.is_bookmarked,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bookmarked_products(request):
    """사용자의 북마크한 상품 목록"""
    from .models import ProductRecommendation
    
    bookmarks = ProductRecommendation.objects.filter(
        user=request.user,
        is_bookmarked=True
    ).select_related('product')
    
    data = []
    for bookmark in bookmarks:
        product = bookmark.product
        data.append({
            'fin_prdt_cd': product.fin_prdt_cd,
            'kor_co_nm': product.kor_co_nm,
            'fin_prdt_nm': product.fin_prdt_nm,
            'bookmarked_at': bookmark.created_at,
        })
    
    return Response(data)


# ==========================================
# 마이페이지 통합 조회
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mypage_data(request):
    """
    마이페이지 전체 데이터 조회
    - 투자 프로필
    - 북마크한 상품
    - 북마크한 뉴스
    - 유튜브 구독 채널
    - 나중에 볼 영상
    """
    from .models import UserNewsBookmark, UserYouTubeSubscription, UserWatchLater
    from .serializers import (
        UserNewsBookmarkSerializer,
        UserYouTubeSubscriptionSerializer,
        UserWatchLaterSerializer
    )

    user = request.user

    # 1. 투자 프로필
    profile_data = {}
    try:
        profile = user.investment_profile
        profile_data = {
            'risk_type': profile.risk_type,
            'risk_score': profile.risk_score,
            'age': profile.age,
            'gender': profile.gender,
            'income': int(profile.income) if profile.income else 0,
            'savings': int(profile.savings) if profile.savings else 0,
            'investment_goal': profile.investment_goal,
            'investment_period': profile.investment_period,
        }
    except Exception:
        profile_data = None

    # 2. 북마크한 금융 상품
    bookmarked_products = []
    product_bookmarks = ProductRecommendation.objects.filter(
        user=user,
        is_bookmarked=True
    ).select_related('product')

    for bookmark in product_bookmarks:
        product = bookmark.product
        # 최고 금리 옵션 찾기
        best_option = product.options.order_by('-intr_rate2').first()

        bookmarked_products.append({
            'fin_prdt_cd': product.fin_prdt_cd,
            'kor_co_nm': product.kor_co_nm,
            'fin_prdt_nm': product.fin_prdt_nm,
            'max_rate': f"{best_option.intr_rate2:.2f}%" if best_option and best_option.intr_rate2 else "정보없음",
            'bookmarked_at': bookmark.created_at,
        })

    # 3. 북마크한 뉴스
    news_bookmarks = UserNewsBookmark.objects.filter(user=user)
    news_serializer = UserNewsBookmarkSerializer(news_bookmarks, many=True)

    # 4. 유튜브 구독 채널
    youtube_subscriptions = UserYouTubeSubscription.objects.filter(user=user)
    youtube_serializer = UserYouTubeSubscriptionSerializer(youtube_subscriptions, many=True)

    # 5. 나중에 볼 영상 (시청하지 않은 것만)
    watch_later = UserWatchLater.objects.filter(user=user, is_watched=False)
    watch_later_serializer = UserWatchLaterSerializer(watch_later, many=True)

    return Response({
        'profile': profile_data,
        'bookmarked_products': bookmarked_products,
        'bookmarked_news': news_serializer.data,
        'youtube_subscriptions': youtube_serializer.data,
        'watch_later_videos': watch_later_serializer.data,
    })


# ==========================================
# 북마크 관련 Views
# ==========================================

@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def toggle_news_bookmark(request, news_id):
    """
    뉴스 북마크 토글
    POST: 북마크 추가
    DELETE: 북마크 제거
    """
    from naversearch.models import News
    from .models import UserNewsBookmark
    from .serializers import UserNewsBookmarkSerializer

    try:
        # 뉴스가 존재하는지 확인
        news = News.objects.get(pk=news_id)
    except News.DoesNotExist:
        return Response(
            {'error': '뉴스를 찾을 수 없습니다.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'POST':
        # 북마크 추가
        bookmark, created = UserNewsBookmark.objects.get_or_create(
            user=request.user,
            news_id=news_id,
            defaults={
                'title': news.title,
                'description': news.description,
                'link': news.link,
                'pub_date': news.pub_date,
            }
        )

        if created:
            serializer = UserNewsBookmarkSerializer(bookmark)
            return Response(
                {'message': '북마크에 추가되었습니다.', 'bookmark': serializer.data},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'message': '이미 북마크에 추가된 뉴스입니다.'},
                status=status.HTTP_200_OK
            )

    elif request.method == 'DELETE':
        # 북마크 제거
        try:
            bookmark = UserNewsBookmark.objects.get(user=request.user, news_id=news_id)
            bookmark.delete()
            return Response(
                {'message': '북마크에서 제거되었습니다.'},
                status=status.HTTP_200_OK
            )
        except UserNewsBookmark.DoesNotExist:
            return Response(
                {'error': '북마크에 없는 뉴스입니다.'},
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_news_bookmarks(request):
    """사용자의 뉴스 북마크 목록 조회"""
    from .models import UserNewsBookmark
    from .serializers import UserNewsBookmarkSerializer

    bookmarks = UserNewsBookmark.objects.filter(user=request.user)
    serializer = UserNewsBookmarkSerializer(bookmarks, many=True)
    return Response(serializer.data)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def toggle_youtube_subscription(request, channel_id):
    """
    유튜브 채널 구독 토글
    POST: 구독 추가
    DELETE: 구독 제거
    """
    from .models import UserYouTubeSubscription
    from .serializers import UserYouTubeSubscriptionSerializer

    if request.method == 'POST':
        # 요청 데이터 검증
        if not request.data.get('channel_title'):
            return Response(
                {'error': '채널 제목이 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 구독 추가
        subscription, created = UserYouTubeSubscription.objects.get_or_create(
            user=request.user,
            channel_id=channel_id,
            defaults={
                'channel_title': request.data.get('channel_title'),
                'channel_description': request.data.get('channel_description', ''),
                'channel_thumbnail': request.data.get('channel_thumbnail', ''),
            }
        )

        if created:
            serializer = UserYouTubeSubscriptionSerializer(subscription)
            return Response(
                {'message': '채널 구독이 추가되었습니다.', 'subscription': serializer.data},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'message': '이미 구독 중인 채널입니다.'},
                status=status.HTTP_200_OK
            )

    elif request.method == 'DELETE':
        # 구독 제거
        try:
            subscription = UserYouTubeSubscription.objects.get(user=request.user, channel_id=channel_id)
            subscription.delete()
            return Response(
                {'message': '채널 구독이 취소되었습니다.'},
                status=status.HTTP_200_OK
            )
        except UserYouTubeSubscription.DoesNotExist:
            return Response(
                {'error': '구독하지 않은 채널입니다.'},
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_youtube_subscriptions(request):
    """사용자의 유튜브 채널 구독 목록 조회"""
    from .models import UserYouTubeSubscription
    from .serializers import UserYouTubeSubscriptionSerializer

    subscriptions = UserYouTubeSubscription.objects.filter(user=request.user)
    serializer = UserYouTubeSubscriptionSerializer(subscriptions, many=True)
    return Response(serializer.data)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def toggle_watch_later(request, video_id):
    """
    나중에 볼 영상 토글
    POST: 목록에 추가
    DELETE: 목록에서 제거
    """
    from .models import UserWatchLater
    from .serializers import UserWatchLaterSerializer

    if request.method == 'POST':
        # 요청 데이터 검증
        if not request.data.get('video_title'):
            return Response(
                {'error': '영상 제목이 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 목록에 추가
        watch_later, created = UserWatchLater.objects.get_or_create(
            user=request.user,
            video_id=video_id,
            defaults={
                'video_title': request.data.get('video_title'),
                'video_description': request.data.get('video_description', ''),
                'video_thumbnail': request.data.get('video_thumbnail', ''),
                'channel_title': request.data.get('channel_title', ''),
                'published_at': request.data.get('published_at', ''),
            }
        )

        if created:
            serializer = UserWatchLaterSerializer(watch_later)
            return Response(
                {'message': '나중에 볼 영상에 추가되었습니다.', 'video': serializer.data},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'message': '이미 나중에 볼 영상 목록에 있습니다.'},
                status=status.HTTP_200_OK
            )

    elif request.method == 'DELETE':
        # 목록에서 제거
        try:
            watch_later = UserWatchLater.objects.get(user=request.user, video_id=video_id)
            watch_later.delete()
            return Response(
                {'message': '나중에 볼 영상에서 제거되었습니다.'},
                status=status.HTTP_200_OK
            )
        except UserWatchLater.DoesNotExist:
            return Response(
                {'error': '나중에 볼 영상 목록에 없는 영상입니다.'},
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_watch_later_list(request):
    """사용자의 나중에 볼 영상 목록 조회"""
    from .models import UserWatchLater
    from .serializers import UserWatchLaterSerializer

    # 시청 여부 필터링 (선택적)
    is_watched = request.query_params.get('is_watched')

    watch_later = UserWatchLater.objects.filter(user=request.user)

    if is_watched is not None:
        watch_later = watch_later.filter(is_watched=(is_watched.lower() == 'true'))

    serializer = UserWatchLaterSerializer(watch_later, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_video_watched(request, video_id):
    """영상 시청 완료 표시"""
    from .models import UserWatchLater

    try:
        watch_later = UserWatchLater.objects.get(user=request.user, video_id=video_id)
        watch_later.is_watched = request.data.get('is_watched', True)
        watch_later.save()

        from .serializers import UserWatchLaterSerializer
        serializer = UserWatchLaterSerializer(watch_later)
        return Response(serializer.data)
    except UserWatchLater.DoesNotExist:
        return Response(
            {'error': '나중에 볼 영상 목록에 없는 영상입니다.'},
            status=status.HTTP_404_NOT_FOUND
        )


# ==========================================
# 3. 설문 데이터 초기화 (개발용)
# ==========================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initialize_survey_data(request):
    """
    설문 질문 및 선택지 초기 데이터 생성 (개발/테스트용)
    
    주의: 프로덕션에서는 admin 권한 필요
    """
    if not request.user.is_staff:
        return Response(
            {'detail': '관리자 권한이 필요합니다.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    from .models import SURVEY_DATA
    
    # 기존 데이터 삭제 (선택사항)
    # SurveyQuestion.objects.all().delete()
    
    created_count = 0
    
    for q_data in SURVEY_DATA:
        question, created = SurveyQuestion.objects.get_or_create(
            order=q_data['order'],
            defaults={
                'category': q_data['category'],
                'question_text': q_data['question_text'],
            }
        )
        
        if created:
            created_count += 1
            
            # 선택지 생성
            for idx, choice_data in enumerate(q_data['choices'], 1):
                SurveyChoice.objects.create(
                    question=question,
                    choice_text=choice_data['choice_text'],
                    score=choice_data['score'],
                    order=idx,
                )
    
    return Response({
        'message': f'{created_count}개의 질문이 생성되었습니다.',
        'total_questions': SurveyQuestion.objects.count(),
    })