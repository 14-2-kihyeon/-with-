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
        "age": 30,
        "income": 5000,  # 만원
        "savings": 10000,  # 만원
        "investment_goal": "주택구매",
        "investment_period": 36  # 개월
    }
    """
    responses = request.data.get('responses', [])
    
    if not responses:
        return Response(
            {'detail': '응답이 비어있습니다.'}, 
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
    
    # 투자 성향 결정
    risk_type = calculate_risk_type(total_score)
    
    # InvestmentProfile 생성 또는 업데이트
    profile, created = InvestmentProfile.objects.update_or_create(
        user=request.user,
        defaults={
            'risk_score': total_score,
            'risk_type': risk_type,
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
        'description': risk_data['description'],
        'characteristics': risk_data['characteristics'],
        'recommended_products_guide': risk_data['recommended_products'],
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
        'description': risk_data.get('description'),
        'characteristics': risk_data.get('characteristics'),
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
    사용자의 투자 성향에 맞는 상품 추천
    
    추천 로직:
    1. 투자 성향별 가입기간 매칭
    2. 금리 높은 순으로 정렬
    3. 우대조건 고려
    4. 상위 10개 추천
    """
    try:
        profile = request.user.investment_profile
    except InvestmentProfile.DoesNotExist:
        return Response(
            {'detail': '투자 성향 검사를 먼저 진행해주세요.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # 성향별 추천 기간 매핑
    PERIOD_MAPPING = {
        'very_conservative': [3, 6],        # 불안형: 3~6개월
        'conservative': [6, 12],            # 안정추구형: 6~12개월
        'moderate': [12, 24],               # 중립형: 12~24개월
        'aggressive': [24, 36],             # 적극투자형: 24~36개월
        'very_aggressive': [36, 60],        # 투기형: 36개월 이상
    }
    
    recommended_periods = PERIOD_MAPPING.get(profile.risk_type, [12, 24])
    
    # 예금 상품 조회 (적금도 유사하게 처리)
    products = DepositProducts.objects.prefetch_related('depositoptions_set').all()
    
    recommendations = []
    
    for product in products:
        # 해당 성향에 맞는 옵션 찾기
        matching_options = product.depositoptions_set.filter(
            save_trm__gte=recommended_periods[0],
            save_trm__lte=recommended_periods[1]
        ).order_by('-intr_rate2')  # 최고 우대금리 순
        
        if matching_options.exists():
            best_option = matching_options.first()
            
            # 매칭 점수 계산 (단순 예시)
            match_score = calculate_match_score(profile, product, best_option)
            
            recommendations.append({
                'product': {
                    'fin_prdt_cd': product.fin_prdt_cd,
                    'kor_co_nm': product.kor_co_nm,
                    'fin_prdt_nm': product.fin_prdt_nm,
                    'join_way': product.join_way,
                    'spcl_cnd': product.spcl_cnd,
                },
                'best_option': {
                    'save_trm': best_option.save_trm,
                    'intr_rate': best_option.intr_rate,
                    'intr_rate2': best_option.intr_rate2,
                },
                'match_score': match_score,
                'recommended_reason': generate_recommendation_reason(
                    profile, product, best_option
                ),
            })
    
    # 매칭 점수 높은 순으로 정렬 후 상위 10개
    recommendations.sort(key=lambda x: x['match_score'], reverse=True)
    top_recommendations = recommendations[:10]
    
    return Response({
        'risk_type': profile.risk_type,
        'risk_type_name': RISK_TYPE_MAPPING[profile.risk_type]['name'],
        'total_count': len(recommendations),
        'recommendations': top_recommendations,
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