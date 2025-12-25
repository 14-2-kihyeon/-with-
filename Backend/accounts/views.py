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
    StockRecommendation,
    calculate_risk_type,
    RISK_TYPE_MAPPING
)
from finances.models import DepositProducts, DepositOptions, SavingProducts, SavingOptions
from django.db.models import Max
import re


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

def _is_eligible_for_product(join_member, user_gender, user_age):
    """
    사용자가 상품 가입 대상인지 확인

    Args:
        join_member: 상품의 가입 대상 (예: "만18세이상 여성고객")
        user_gender: 사용자 성별 ('M' or 'F')
        user_age: 사용자 나이

    Returns:
        bool: 가입 가능 여부
    """
    if not join_member or join_member == "제한없음":
        return True

    # 성별 체크
    if user_gender:
        if '여성' in join_member and user_gender == 'M':
            return False
        if '남성' in join_member and user_gender == 'F':
            return False

    # 나이 체크 (정규식 파싱)
    if user_age:
        # "만18세이상", "만65세미만" 등 파싱
        age_patterns = [
            (r'만(\d+)세\s*이상', lambda match: user_age >= int(match.group(1))),
            (r'만(\d+)세\s*미만', lambda match: user_age < int(match.group(1))),
            (r'(\d+)세\s*이상', lambda match: user_age >= int(match.group(1))),
            (r'(\d+)세\s*미만', lambda match: user_age < int(match.group(1))),
        ]

        for pattern, check_func in age_patterns:
            match = re.search(pattern, join_member)
            if match:
                if not check_func(match):
                    return False

    return True


def _calculate_deposit_profit(principal, months, annual_rate):
    """
    예금 예상 수익 계산 (단리)

    Args:
        principal: 원금 (만원)
        months: 투자 기간 (개월)
        annual_rate: 연 이율 (%)

    Returns:
        int: 예상 수익 (만원)
    """
    return int(principal * (annual_rate / 100) * (months / 12))


def _calculate_saving_profit(monthly_deposit, months, annual_rate):
    """
    적금 예상 수익 계산 (복리)

    Args:
        monthly_deposit: 월 납입액 (만원)
        months: 투자 기간 (개월)
        annual_rate: 연 이율 (%)

    Returns:
        int: 예상 수익 (만원)
    """
    monthly_rate = annual_rate / 100 / 12
    total_principal = monthly_deposit * months

    future_value = 0
    for i in range(months):
        future_value += monthly_deposit * ((1 + monthly_rate) ** (months - i))

    return int(future_value - total_principal)


def _evaluate_condition_complexity(spcl_cnd):
    """
    우대조건 복잡도 평가

    Args:
        spcl_cnd: 특별 조건 문자열

    Returns:
        str: 'low' (조건 1~2개), 'medium' (3~4개), 'high' (5개 이상)
    """
    if not spcl_cnd or len(spcl_cnd.strip()) < 10:
        return 'low'

    # 조건 개수 파악 (줄바꿈, 숫자+점, 하이픈 등으로 구분)
    condition_markers = ['\n', '1.', '2.', '3.', '4.', '5.', '-', '•']
    condition_count = sum(spcl_cnd.count(marker) for marker in condition_markers)

    if condition_count <= 2:
        return 'low'
    elif condition_count <= 4:
        return 'medium'
    else:
        return 'high'


def _evaluate_join_convenience(join_way):
    """
    가입 방법 편의성 평가

    Args:
        join_way: 가입 방법 문자열

    Returns:
        int: 편의성 점수 (0~10점)
    """
    if not join_way:
        return 0

    join_way_lower = join_way.lower()
    score = 0

    # 인터넷/모바일 가입 가능 → 가장 편리
    if '인터넷' in join_way or '모바일' in join_way or '스마트폰' in join_way or 'app' in join_way_lower:
        score += 10
    # 영업점만 가능 → 불편
    elif '영업점' in join_way or '창구' in join_way:
        score += 3
    else:
        score += 5

    return min(score, 10)


def _calculate_risk_adjusted_score(profile, product, option):
    """
    투자 성향에 따른 가중치 적용 점수 계산

    안정형 (timid_male, timid_female):
    - 기본금리(intr_rate) 가중치 높음 (70%)
    - 우대조건 간단할수록 가산점
    - 가입 편의성 중요

    중립형 (normal_male, normal_female):
    - 기본금리 + 우대금리 균형 (50% / 50%)
    - 모든 요소 균형있게 평가

    공격형 (speculative_male, speculative_female):
    - 최고금리(intr_rate2) 가중치 높음 (70%)
    - 우대조건 복잡해도 OK
    - 가입 편의성 덜 중요

    Args:
        profile: InvestmentProfile 객체
        product: DepositProducts or SavingProducts 객체
        option: DepositOptions or SavingOptions 객체

    Returns:
        float: 위험 조정 점수 (0~100)
    """
    base_score = 0
    risk_type = profile.risk_type

    # risk_type을 일반 카테고리로 매핑
    if 'timid' in risk_type:
        risk_category = 'conservative'
    elif 'speculative' in risk_type:
        risk_category = 'aggressive'
    else:  # 'normal' in risk_type
        risk_category = 'moderate'

    # 기본금리와 우대금리
    basic_rate = float(option.intr_rate) if option.intr_rate else 0
    max_rate = float(option.intr_rate2) if option.intr_rate2 else 0

    # 1. 금리 점수 (투자 성향별 가중치) - 최대 50점
    if risk_category == 'conservative':  # 안정형
        # 기본금리 70% + 우대금리 30%
        weighted_rate = (basic_rate * 0.7 + max_rate * 0.3)
        rate_score = weighted_rate * 10
    elif risk_category == 'aggressive':  # 공격형
        # 기본금리 30% + 우대금리 70%
        weighted_rate = (basic_rate * 0.3 + max_rate * 0.7)
        rate_score = weighted_rate * 10
    else:  # 중립형 (moderate)
        # 기본금리 50% + 우대금리 50%
        weighted_rate = (basic_rate * 0.5 + max_rate * 0.5)
        rate_score = weighted_rate * 10

    base_score += min(rate_score, 50)

    # 2. 우대조건 복잡도 평가 - 최대 20점
    condition_complexity = _evaluate_condition_complexity(product.spcl_cnd)

    if risk_category == 'conservative':
        # 안정형: 조건 간단할수록 선호
        if condition_complexity == 'low':
            base_score += 20  # 조건 1~2개
        elif condition_complexity == 'medium':
            base_score += 10  # 조건 3~4개
        else:
            base_score += 0   # 조건 5개 이상 (가산점 없음)

    elif risk_category == 'aggressive':
        # 공격형: 조건 많아도 OK (높은 금리 가능성)
        if condition_complexity == 'high':
            base_score += 15  # 복잡한 조건 = 높은 금리 가능
        elif condition_complexity == 'medium':
            base_score += 10
        else:
            base_score += 5

    else:  # 중립형
        # 균형: 적당한 조건 선호
        if condition_complexity == 'medium':
            base_score += 15
        else:
            base_score += 8

    # 3. 가입 방법 편의성 - 최대 15점
    convenience_score = _evaluate_join_convenience(product.join_way)

    if risk_category == 'conservative':
        # 안정형: 편의성 매우 중요
        base_score += convenience_score * 1.5
    elif risk_category == 'aggressive':
        # 공격형: 편의성 덜 중요
        base_score += convenience_score * 0.8
    else:
        # 중립형: 보통 중요
        base_score += convenience_score

    # 4. 투자 기간 일치도 - 최대 15점
    if profile.investment_period and option.save_trm:
        period_diff = abs(profile.investment_period - option.save_trm)
        if period_diff == 0:
            period_score = 15
        elif period_diff <= 3:
            period_score = 12
        elif period_diff <= 6:
            period_score = 8
        elif period_diff <= 12:
            period_score = 4
        else:
            period_score = 0

        base_score += period_score
    else:
        base_score += 7  # 기본 점수

    return min(base_score, 100)


def _calculate_product_ratio(savings_amount, investment_period, investment_goal):
    """
    복합 조건 기반 예금/적금 추천 비율 계산

    Args:
        savings_amount: 현재 저축액 (만원)
        investment_period: 투자 기간 (개월)
        investment_goal: 투자 목표

    Returns:
        (deposit_count, saving_count): 예금 개수, 적금 개수
    """
    deposit_score = 0
    saving_score = 0

    # 1. 저축액 기반 점수 (0~40점)
    if savings_amount >= 5000:  # 5,000만원 이상
        deposit_score += 40  # 목돈 있음 → 예금 강력 선호
        saving_score += 10
    elif savings_amount >= 3000:  # 3,000~5,000만원
        deposit_score += 30  # 예금 선호
        saving_score += 20
    elif savings_amount >= 1000:  # 1,000~3,000만원
        deposit_score += 20  # 균형
        saving_score += 30
    else:  # 1,000만원 미만
        deposit_score += 10  # 적금으로 모으기
        saving_score += 40

    # 2. 투자 기간 기반 점수 (0~40점)
    if investment_period <= 6:  # 6개월 이하
        deposit_score += 40  # 단기 → 예금 (즉시 인출)
        saving_score += 10
    elif investment_period <= 12:  # 6~12개월
        deposit_score += 30  # 예금 선호
        saving_score += 20
    elif investment_period <= 24:  # 12~24개월
        deposit_score += 20  # 균형
        saving_score += 30
    else:  # 24개월 이상
        deposit_score += 10  # 장기 → 적금 (꾸준히 모으기)
        saving_score += 40

    # 3. 투자 목표 기반 점수 (0~20점)
    goal_lower = investment_goal.lower()
    if any(keyword in goal_lower for keyword in ['단기', '비상금', '생활비']):
        deposit_score += 20  # 단기 목표 → 예금
        saving_score += 5
    elif any(keyword in goal_lower for keyword in ['장기', '노후', '은퇴']):
        deposit_score += 5   # 장기 목표 → 적금
        saving_score += 20
    elif any(keyword in goal_lower for keyword in ['주택', '결혼', '자녀', '교육']):
        deposit_score += 10  # 중대 목표 → 균형
        saving_score += 15
    else:
        deposit_score += 10  # 기본값 → 균형
        saving_score += 10

    # 4. 점수 기반 비율 계산 (총 15개)
    total_score = deposit_score + saving_score
    deposit_ratio = deposit_score / total_score
    saving_ratio = saving_score / total_score

    # 최소 각 2개는 보장, 최대 13개까지
    deposit_count = max(2, min(13, int(15 * deposit_ratio)))
    saving_count = 15 - deposit_count

    return deposit_count, saving_count


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommend_products(request):
    """
    사용자의 투자 성향에 맞는 예금/적금 상품 추천

    개선된 추천 로직:
    1. 성별/나이 필터링 - 부적합 상품 제외
    2. 최고 금리순 정렬
    3. 예금 + 적금 모두 포함
    4. 예상 수익 계산
    5. 투자 기간 매칭
    """
    try:
        profile = request.user.investment_profile
    except InvestmentProfile.DoesNotExist:
        return Response(
            {'detail': '투자 성향 검사를 먼저 진행해주세요.'},
            status=status.HTTP_404_NOT_FOUND
        )

    user_gender = profile.gender
    user_age = profile.age
    user_period = profile.investment_period
    risk_data = RISK_TYPE_MAPPING[profile.risk_type]

    # 기본 투자금 (프로필에 저축액이 있으면 사용, 없으면 1000만원 가정)
    principal_amount = int(profile.savings) if profile.savings else 1000
    monthly_deposit = 100  # 적금 월 납입액 (100만원)

    # ===== 예금 상품 추천 =====
    deposits = DepositProducts.objects.annotate(
        max_rate=Max('options__intr_rate2')
    ).prefetch_related('options').filter(
        max_rate__isnull=False
    ).order_by('-max_rate')  # 최고 금리 내림차순

    deposit_recommendations = []
    for d in deposits:
        # 성별/나이 필터링
        if not _is_eligible_for_product(d.join_member, user_gender, user_age):
            continue

        # 투자 기간 매칭 (±6개월 범위)
        if user_period:
            period_match = d.options.filter(
                save_trm__gte=user_period - 6,
                save_trm__lte=user_period + 6
            ).order_by('-intr_rate2').first()
        else:
            period_match = None

        # 기간 매칭 없으면 최고 금리 옵션 사용
        if period_match:
            matching_option = period_match
        else:
            matching_option = d.options.order_by('-intr_rate2').first()

        if not matching_option:
            continue

        # 예상 수익 계산
        rate = float(matching_option.intr_rate2) if matching_option.intr_rate2 else 0
        expected_profit = _calculate_deposit_profit(principal_amount, matching_option.save_trm, rate)

        # 투자 성향 기반 가중치 점수 계산
        risk_adjusted_score = _calculate_risk_adjusted_score(profile, d, matching_option)

        deposit_recommendations.append({
            'type': 'deposit',
            'product': {
                'fin_prdt_cd': d.fin_prdt_cd,
                'kor_co_nm': d.kor_co_nm,
                'fin_prdt_nm': d.fin_prdt_nm,
                'join_way': d.join_way,
                'join_member': d.join_member,
                'spcl_cnd': d.spcl_cnd,
            },
            'option': {
                'save_trm': matching_option.save_trm,
                'intr_rate': float(matching_option.intr_rate) if matching_option.intr_rate else 0,
                'intr_rate2': rate,
            },
            'expected_profit': expected_profit,
            'max_rate': rate,
            'risk_adjusted_score': risk_adjusted_score,  # 가중치 점수 추가
        })

    # ===== 적금 상품 추천 =====
    savings = SavingProducts.objects.annotate(
        max_rate=Max('options__intr_rate2')
    ).prefetch_related('options').filter(
        max_rate__isnull=False
    ).order_by('-max_rate')  # 최고 금리 내림차순

    saving_recommendations = []
    for s in savings:
        # 성별/나이 필터링
        if not _is_eligible_for_product(s.join_member, user_gender, user_age):
            continue

        # 투자 기간 매칭 (±6개월 범위)
        if user_period:
            period_match = s.options.filter(
                save_trm__gte=user_period - 6,
                save_trm__lte=user_period + 6
            ).order_by('-intr_rate2').first()
        else:
            period_match = None

        # 기간 매칭 없으면 최고 금리 옵션 사용
        if period_match:
            matching_option = period_match
        else:
            matching_option = s.options.order_by('-intr_rate2').first()

        if not matching_option:
            continue

        # 예상 수익 계산
        rate = float(matching_option.intr_rate2) if matching_option.intr_rate2 else 0
        expected_profit = _calculate_saving_profit(monthly_deposit, matching_option.save_trm, rate)

        # 투자 성향 기반 가중치 점수 계산
        risk_adjusted_score = _calculate_risk_adjusted_score(profile, s, matching_option)

        saving_recommendations.append({
            'type': 'saving',
            'product': {
                'fin_prdt_cd': s.fin_prdt_cd,
                'kor_co_nm': s.kor_co_nm,
                'fin_prdt_nm': s.fin_prdt_nm,
                'join_way': s.join_way,
                'join_member': s.join_member,
                'spcl_cnd': s.spcl_cnd,
            },
            'option': {
                'save_trm': matching_option.save_trm,
                'intr_rate': float(matching_option.intr_rate) if matching_option.intr_rate else 0,
                'intr_rate2': rate,
            },
            'expected_profit': expected_profit,
            'max_rate': rate,
            'risk_adjusted_score': risk_adjusted_score,
        })

    # ===== 복합 조건 기반 예금/적금 비율 결정 =====
    deposit_count, saving_count = _calculate_product_ratio(
        savings_amount=int(profile.savings) if profile.savings else 0,
        investment_period=user_period or 12,
        investment_goal=profile.investment_goal or ""
    )

    # 예금 + 적금 합치기 (비율에 맞게)
    # 1. 각각 금리순으로 정렬되어 있음
    # 2. 지정된 개수만큼 가져오기
    selected_deposits = deposit_recommendations[:deposit_count]
    selected_savings = saving_recommendations[:saving_count]

    # 3. 합치기
    all_recommendations = selected_deposits + selected_savings

    # 4. 투자 성향 기반 가중치 점수로 정렬 (예금+적금 혼합하여 최적 상품 우선)
    all_recommendations.sort(key=lambda x: x['risk_adjusted_score'], reverse=True)

    # 투자 계획 생성 (기존 함수 호환을 위해 변환)
    legacy_format_recommendations = []
    for rec in all_recommendations:
        legacy_format_recommendations.append({
            'product': rec['product'],
            'option': rec['option'],
            'match_score': rec['risk_adjusted_score'],  # 투자 성향 기반 가중치 점수
            'reason': f"최고 금리 {rec['max_rate']}%로 {rec['expected_profit']}만원의 수익이 예상됩니다.",
        })

    investment_plan = generate_investment_plan(profile, legacy_format_recommendations)

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
        'recommendations': all_recommendations,  # 비율에 맞춘 추천 (15개)
        'investment_plan': investment_plan,
        'total_count': len(all_recommendations),
        'total_deposits_available': len(deposit_recommendations),
        'total_savings_available': len(saving_recommendations),
        'recommended_deposit_count': deposit_count,  # 실제 추천된 예금 개수
        'recommended_saving_count': saving_count,    # 실제 추천된 적금 개수
        'recommendation_reason': f"저축액 {int(profile.savings) if profile.savings else 0}만원, "
                                f"투자기간 {user_period or 12}개월, "
                                f"투자목표 '{profile.investment_goal or '미설정'}'를 고려하여 "
                                f"예금 {deposit_count}개, 적금 {saving_count}개를 추천합니다.",
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
    """추천 상품 북마크 (관심 상품 저장 - 예금/적금 모두 지원)"""
    from .models import ProductRecommendation, SavingRecommendation
    from finances.models import SavingProducts

    # 1. 먼저 예금 상품인지 확인
    deposit_product = DepositProducts.objects.filter(fin_prdt_cd=fin_prdt_cd).first()

    if deposit_product:
        # 예금 상품 북마크 처리
        recommendation, created = ProductRecommendation.objects.get_or_create(
            user=request.user,
            product=deposit_product,
            defaults={
                'match_score': 0,
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
            'product_type': 'deposit',
            'message': '예금 상품이 관심상품에 추가되었습니다.' if recommendation.is_bookmarked else '예금 상품이 관심상품에서 제거되었습니다.'
        })

    # 2. 적금 상품인지 확인
    saving_product = SavingProducts.objects.filter(fin_prdt_cd=fin_prdt_cd).first()

    if saving_product:
        # 적금 상품 북마크 처리
        recommendation, created = SavingRecommendation.objects.get_or_create(
            user=request.user,
            product=saving_product,
            defaults={
                'match_score': 0,
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
            'product_type': 'saving',
            'message': '적금 상품이 관심상품에 추가되었습니다.' if recommendation.is_bookmarked else '적금 상품이 관심상품에서 제거되었습니다.'
        })

    # 3. 둘 다 아니면 404
    return Response(
        {'detail': '상품을 찾을 수 없습니다. (예금/적금 모두 확인했으나 존재하지 않음)'},
        status=status.HTTP_404_NOT_FOUND
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bookmarked_products(request):
    """사용자의 북마크한 상품 목록 (예금 + 적금)"""
    from .models import ProductRecommendation, SavingRecommendation

    data = []

    # 예금 북마크
    deposit_bookmarks = ProductRecommendation.objects.filter(
        user=request.user,
        is_bookmarked=True
    ).select_related('product')

    for bookmark in deposit_bookmarks:
        product = bookmark.product
        data.append({
            'fin_prdt_cd': product.fin_prdt_cd,
            'kor_co_nm': product.kor_co_nm,
            'fin_prdt_nm': product.fin_prdt_nm,
            'product_type': 'deposit',
            'bookmarked_at': bookmark.created_at,
        })

    # 적금 북마크
    saving_bookmarks = SavingRecommendation.objects.filter(
        user=request.user,
        is_bookmarked=True
    ).select_related('product')

    for bookmark in saving_bookmarks:
        product = bookmark.product
        data.append({
            'fin_prdt_cd': product.fin_prdt_cd,
            'kor_co_nm': product.kor_co_nm,
            'fin_prdt_nm': product.fin_prdt_nm,
            'product_type': 'saving',
            'bookmarked_at': bookmark.created_at,
        })

    # 북마크 시간 기준으로 최신순 정렬
    data.sort(key=lambda x: x['bookmarked_at'], reverse=True)

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
        risk_data = RISK_TYPE_MAPPING.get(profile.risk_type, {})
        profile_data = {
            'risk_type': profile.risk_type,
            'risk_type_name': risk_data.get('name'),
            'risk_score': profile.risk_score,
            'age': profile.age,
            'gender': profile.gender,
            'gender_display': '남성' if profile.gender == 'M' else '여성',
            'income': int(profile.income) if profile.income else 0,
            'savings': int(profile.savings) if profile.savings else 0,
            'investment_goal': profile.investment_goal,
            'investment_period': profile.investment_period,
        }
    except Exception:
        profile_data = None

    # 2. 북마크한 금융 상품 (예금 + 적금)
    bookmarked_products = []

    # 예금 북마크
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
            'product_type': 'deposit',
            'max_rate': f"{best_option.intr_rate2:.2f}%" if best_option and best_option.intr_rate2 else "정보없음",
            'bookmarked_at': bookmark.created_at,
        })

    # 적금 북마크
    from .models import SavingRecommendation
    from finances.models import SavingOptions

    saving_bookmarks = SavingRecommendation.objects.filter(
        user=user,
        is_bookmarked=True
    ).select_related('product')

    for bookmark in saving_bookmarks:
        product = bookmark.product
        # 최고 금리 옵션 찾기
        best_option = SavingOptions.objects.filter(product=product).order_by('-intr_rate2').first()

        bookmarked_products.append({
            'fin_prdt_cd': product.fin_prdt_cd,
            'kor_co_nm': product.kor_co_nm,
            'fin_prdt_nm': product.fin_prdt_nm,
            'product_type': 'saving',
            'max_rate': f"{best_option.intr_rate2:.2f}%" if best_option and best_option.intr_rate2 else "정보없음",
            'bookmarked_at': bookmark.created_at,
        })

    # 북마크 시간 기준 최신순 정렬
    bookmarked_products.sort(key=lambda x: x['bookmarked_at'], reverse=True)

    # 3. 북마크한 주식 (관심종목)
    bookmarked_stocks = []
    stock_bookmarks = StockRecommendation.objects.filter(
        user=user,
        is_bookmarked=True
    ).select_related('stock')

    for bookmark in stock_bookmarks:
        stock = bookmark.stock
        # 최신 가격 정보 가져오기
        latest_price = stock.prices.first()  # ordering = ['-date'] 기준

        bookmarked_stocks.append({
            'code': stock.code,
            'name': stock.name,
            'market': stock.market,
            'current_price': float(latest_price.close) if latest_price else None,
            'bookmarked_at': bookmark.created_at,
        })

    # 4. 북마크한 뉴스
    news_bookmarks = UserNewsBookmark.objects.filter(user=user)
    news_serializer = UserNewsBookmarkSerializer(news_bookmarks, many=True)

    # 5. 유튜브 구독 채널
    youtube_subscriptions = UserYouTubeSubscription.objects.filter(user=user)
    youtube_serializer = UserYouTubeSubscriptionSerializer(youtube_subscriptions, many=True)

    # 6. 나중에 볼 영상 (시청하지 않은 것만)
    watch_later = UserWatchLater.objects.filter(user=user, is_watched=False)
    watch_later_serializer = UserWatchLaterSerializer(watch_later, many=True)

    return Response({
        'profile': profile_data,
        'bookmarked_products': bookmarked_products,
        'bookmarked_stocks': bookmarked_stocks,
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_youtube_subscription(request, channel_id):
    """
    유튜브 채널 구독 토글 (POST만 사용)
    이미 구독 중이면 구독 취소, 아니면 구독
    """
    from .models import UserYouTubeSubscription
    from .serializers import UserYouTubeSubscriptionSerializer

    # 요청 데이터 검증
    if not request.data.get('channel_title'):
        return Response(
            {'error': '채널 제목이 필요합니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 토글 처리
    subscription, created = UserYouTubeSubscription.objects.get_or_create(
        user=request.user,
        channel_id=channel_id,
        defaults={
            'channel_title': request.data.get('channel_title'),
            'channel_description': request.data.get('channel_description', ''),
            'channel_thumbnail': request.data.get('channel_thumbnail', ''),
        }
    )

    # 이미 존재하면 삭제 (토글)
    if not created:
        subscription.delete()
        return Response(
            {
                'message': '채널 구독이 취소되었습니다.',
                'is_subscribed': False
            },
            status=status.HTTP_200_OK
        )
    else:
        serializer = UserYouTubeSubscriptionSerializer(subscription)
        return Response(
            {
                'message': '채널 구독이 추가되었습니다.',
                'is_subscribed': True,
                'subscription': serializer.data
            },
            status=status.HTTP_201_CREATED
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_watch_later(request, video_id):
    """
    나중에 볼 영상 토글 (POST만 사용)
    이미 존재하면 삭제, 없으면 추가
    """
    from .models import UserWatchLater
    from .serializers import UserWatchLaterSerializer

    # 요청 데이터 검증
    if not request.data.get('video_title'):
        return Response(
            {'error': '영상 제목이 필요합니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 토글 처리
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

    # 이미 존재하면 삭제 (토글)
    if not created:
        watch_later.delete()
        return Response(
            {
                'message': '나중에 볼 영상에서 제거되었습니다.',
                'is_saved': False
            },
            status=status.HTTP_200_OK
        )
    else:
        serializer = UserWatchLaterSerializer(watch_later)
        return Response(
            {
                'message': '나중에 볼 영상에 추가되었습니다.',
                'is_saved': True,
                'video': serializer.data
            },
            status=status.HTTP_201_CREATED
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


# ==========================================
# 주식 관심종목 API
# ==========================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bookmark_stock(request, stock_code):
    """주식 관심종목 추가/제거 (토글)"""
    from .models import StockRecommendation
    from stocks.models import Stock

    try:
        stock = Stock.objects.get(code=stock_code)
    except Stock.DoesNotExist:
        return Response(
            {'detail': '주식을 찾을 수 없습니다.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # 북마크 토글
    recommendation, created = StockRecommendation.objects.get_or_create(
        user=request.user,
        stock=stock,
        defaults={
            'match_score': 0,
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
def get_bookmarked_stocks(request):
    """사용자의 관심종목 목록 조회"""
    from .models import StockRecommendation

    bookmarks = StockRecommendation.objects.filter(
        user=request.user,
        is_bookmarked=True
    ).select_related('stock')

    data = []
    for bookmark in bookmarks:
        stock = bookmark.stock

        # 최신 가격 정보 가져오기
        latest_price = stock.prices.first()  # ordering = ['-date'] 기준

        data.append({
            'code': stock.code,
            'name': stock.name,
            'market': stock.market,
            'current_price': float(latest_price.close) if latest_price else None,
            'bookmarked_at': bookmark.created_at,
        })

    return Response(data)