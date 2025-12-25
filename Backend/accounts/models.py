from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class User(AbstractUser):
    pass
    # def __str__(self):
    #     return self.username

from django.conf import settings

class InvestmentProfile(models.Model):
    """사용자 투자 성향 프로필"""

    GENDER_CHOICES = [
        ('M', '남성'),
        ('F', '여성'),
    ]

    RISK_TYPE_CHOICES = [
        # 남성 유형
        ('timid_male', '에겐소심남'),           
        ('normal_male', '중간남'),              
        ('speculative_male', '테토투기남'),     
        # 여성 유형
        ('timid_female', '에겐소심녀'),        
        ('normal_female', '중간녀'),            
        ('speculative_female', '테토투기녀'),   
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='investment_profile'
    )

    # 투자 성향 결과
    risk_type = models.CharField(
        max_length=20,
        choices=RISK_TYPE_CHOICES,
        null=True,
        blank=True
    )
    risk_score = models.IntegerField(default=0)  # 점수 (0~100점)

    # 기본 정보
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        null=True,
        blank=True,
        help_text="성별"
    )
    age = models.IntegerField(null=True, blank=True)
    income = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        help_text="연 소득 (만원)"
    )
    savings = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        help_text="현재 저축액 (만원)"
    )
    
    # 투자 목표
    investment_goal = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="예: 주택구매, 노후준비, 자녀교육 등"
    )
    investment_period = models.IntegerField(
        null=True, 
        blank=True,
        help_text="투자 가능 기간 (개월)"
    )
    
    # 메타 정보
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_risk_type_display()}"
    
    class Meta:
        db_table = 'investment_profile'
        verbose_name = '투자 성향 프로필'
        verbose_name_plural = '투자 성향 프로필들'


class SurveyQuestion(models.Model):
    """투자 성향 설문 질문"""
    
    CATEGORY_CHOICES = [
        ('risk_tolerance', '위험감수성'),
        ('investment_experience', '투자경험'),
        ('financial_status', '재무상태'),
        ('investment_period', '투자기간'),
        ('investment_knowledge', '투자지식'),
    ]
    
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    question_text = models.TextField(help_text="질문 내용")
    order = models.IntegerField(default=0, help_text="질문 순서")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:30]}"
    
    class Meta:
        db_table = 'survey_question'
        ordering = ['order']


class SurveyChoice(models.Model):
    """투자 성향 설문 선택지"""
    
    question = models.ForeignKey(
        SurveyQuestion, 
        on_delete=models.CASCADE,
        related_name='choices'
    )
    choice_text = models.TextField(help_text="선택지 내용")
    score = models.IntegerField(
        help_text="점수 (1~5점, 높을수록 공격적)"
    )
    order = models.IntegerField(default=0, help_text="선택지 순서")
    
    def __str__(self):
        return f"{self.choice_text[:30]} (점수: {self.score})"
    
    class Meta:
        db_table = 'survey_choice'
        ordering = ['order']


class SurveyResponse(models.Model):
    """사용자의 설문 응답 기록"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='survey_responses'
    )
    question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.CASCADE
    )
    choice = models.ForeignKey(
        SurveyChoice,
        on_delete=models.CASCADE
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - Q{self.question.order}"
    
    class Meta:
        db_table = 'survey_response'
        unique_together = ('user', 'question')  # 한 질문당 하나의 답변만
        ordering = ['-created_at']


class ProductRecommendation(models.Model):
    """사용자별 상품 추천 기록"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommendations'
    )
    product = models.ForeignKey(
        'finances.DepositProducts',  # 또는 SavingProducts
        on_delete=models.CASCADE
    )

    # 추천 근거
    match_score = models.FloatField(
        help_text="매칭 점수 (0~100)"
    )
    recommended_reason = models.TextField(
        help_text="추천 이유"
    )

    # 사용자 액션
    is_viewed = models.BooleanField(default=False)
    is_bookmarked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.fin_prdt_nm}"

    class Meta:
        db_table = 'product_recommendation'
        ordering = ['-match_score', '-created_at']
        unique_together = ('user', 'product')


class SavingRecommendation(models.Model):
    """사용자별 적금 상품 추천 기록"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saving_recommendations'
    )
    product = models.ForeignKey(
        'finances.SavingProducts',
        on_delete=models.CASCADE
    )

    # 추천 근거
    match_score = models.FloatField(
        help_text="매칭 점수 (0~100)"
    )
    recommended_reason = models.TextField(
        help_text="추천 이유"
    )

    # 사용자 액션
    is_viewed = models.BooleanField(default=False)
    is_bookmarked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.fin_prdt_nm}"

    class Meta:
        db_table = 'saving_recommendation'
        ordering = ['-match_score', '-created_at']
        unique_together = ('user', 'product')


class StockRecommendation(models.Model):
    """사용자별 주식 추천 및 관심종목"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stock_recommendations'
    )
    stock = models.ForeignKey(
        'stocks.Stock',
        on_delete=models.CASCADE
    )

    # 추천 근거
    match_score = models.FloatField(
        default=0.0,
        help_text="매칭 점수 (0~100)"
    )
    recommended_reason = models.TextField(
        blank=True,
        help_text="추천 이유"
    )

    # 사용자 액션
    is_viewed = models.BooleanField(default=False)
    is_bookmarked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.stock.name}"

    class Meta:
        db_table = 'stock_recommendation'
        ordering = ['-match_score', '-created_at']
        unique_together = ('user', 'stock')


class UserNewsBookmark(models.Model):
    """사용자별 뉴스 북마크"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookmarked_news'
    )

    # 뉴스 정보 (naversearch.News 모델 참조하지 않고 직접 저장)
    news_id = models.IntegerField(
        help_text="뉴스 ID (naversearch.News의 PK)"
    )
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    link = models.URLField(max_length=1000)
    pub_date = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title[:30]}"

    class Meta:
        db_table = 'user_news_bookmark'
        ordering = ['-created_at']
        unique_together = ('user', 'news_id')


class UserYouTubeSubscription(models.Model):
    """사용자별 유튜브 채널 구독"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='youtube_subscriptions'
    )

    # 채널 정보
    channel_id = models.CharField(
        max_length=100,
        help_text="유튜브 채널 ID"
    )
    channel_title = models.CharField(
        max_length=200,
        help_text="채널명"
    )
    channel_description = models.TextField(
        blank=True,
        help_text="채널 설명"
    )
    channel_thumbnail = models.URLField(
        max_length=500,
        blank=True,
        help_text="채널 썸네일 URL"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.channel_title}"

    class Meta:
        db_table = 'user_youtube_subscription'
        ordering = ['-created_at']
        unique_together = ('user', 'channel_id')


class UserWatchLater(models.Model):
    """사용자별 나중에 볼 영상"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='watch_later_videos'
    )

    # 영상 정보
    video_id = models.CharField(
        max_length=100,
        help_text="유튜브 영상 ID"
    )
    video_title = models.CharField(
        max_length=200,
        help_text="영상 제목"
    )
    video_description = models.TextField(
        blank=True,
        help_text="영상 설명"
    )
    video_thumbnail = models.URLField(
        max_length=500,
        blank=True,
        help_text="영상 썸네일 URL"
    )
    channel_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="채널명"
    )
    published_at = models.CharField(
        max_length=100,
        blank=True,
        help_text="게시일"
    )

    # 시청 상태
    is_watched = models.BooleanField(
        default=False,
        help_text="시청 완료 여부"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.video_title[:30]}"

    class Meta:
        db_table = 'user_watch_later'
        ordering = ['-created_at']
        unique_together = ('user', 'video_id')


# ==========================================
# 예시 데이터 (초기 설정용)
# ==========================================

SURVEY_DATA = [
    {
        "category": "risk_tolerance",
        "question_text": "투자 원금에 손실이 발생하면 어떻게 하시겠습니까?",
        "order": 1,
        "choices": [
            {"choice_text": "손실을 절대 감수할 수 없어 원금 보장 상품만 선택", "score": 2},
            {"choice_text": "최소한의 손실(5% 이내)만 감수 가능", "score": 4},
            {"choice_text": "어느 정도 손실(10~20%)은 감수 가능", "score": 6},
            {"choice_text": "높은 수익을 위해 손실(20~30%)도 감수 가능", "score": 8},
            {"choice_text": "고수익을 위해 큰 손실(30% 이상)도 감수 가능", "score": 10},
        ]
    },
    {
        "category": "investment_experience",
        "question_text": "금융상품 투자 경험은 어느 정도입니까?",
        "order": 2,
        "choices": [
            {"choice_text": "투자 경험이 전혀 없음", "score": 2},
            {"choice_text": "예·적금, 보험 등 안전 자산만 투자", "score": 4},
            {"choice_text": "펀드, 채권 등 간접투자 경험 있음", "score": 6},
            {"choice_text": "주식, ETF 등 직접투자 경험 있음", "score": 8},
            {"choice_text": "파생상품, 선물옵션 등 고위험 상품 투자 경험", "score": 10},
        ]
    },
    {
        "category": "financial_status",
        "question_text": "현재 수입과 지출 상황은 어떻습니까?",
        "order": 3,
        "choices": [
            {"choice_text": "수입보다 지출이 많아 투자 여력 없음", "score": 2},
            {"choice_text": "수입과 지출이 비슷해 소액만 투자 가능", "score": 4},
            {"choice_text": "수입의 10~20%를 투자에 활용 가능", "score": 6},
            {"choice_text": "수입의 30~50%를 투자에 활용 가능", "score": 8},
            {"choice_text": "수입의 50% 이상을 투자에 활용 가능", "score": 10},
        ]
    },
    {
        "category": "investment_period",
        "question_text": "투자금을 얼마나 오래 유지할 수 있습니까?",
        "order": 4,
        "choices": [
            {"choice_text": "6개월 이내 (단기 자금 필요)", "score": 2},
            {"choice_text": "6개월 ~ 1년", "score": 4},
            {"choice_text": "1년 ~ 3년", "score": 6},
            {"choice_text": "3년 ~ 5년", "score": 8},
            {"choice_text": "5년 이상 장기 투자 가능", "score": 10},
        ]
    },
    {
        "category": "investment_knowledge",
        "question_text": "금융 및 투자에 대한 본인의 지식 수준은?",
        "order": 5,
        "choices": [
            {"choice_text": "금융 상품에 대해 거의 모름", "score": 2},
            {"choice_text": "예·적금 정도만 이해", "score": 4},
            {"choice_text": "펀드, 채권의 기본 개념 이해", "score": 6},
            {"choice_text": "주식, 파생상품의 원리 이해", "score": 8},
            {"choice_text": "복잡한 금융 상품도 분석 가능", "score": 10},
        ]
    },
    {
        "category": "risk_tolerance",
        "question_text": "연 10%의 수익률을 기대할 수 있는 투자 상품이 있습니다. 단, 원금 손실 가능성도 있습니다. 투자하시겠습니까?",
        "order": 6,
        "choices": [
            {"choice_text": "절대 투자하지 않음", "score": 2},
            {"choice_text": "투자 금액의 10% 정도만 투자", "score": 4},
            {"choice_text": "투자 금액의 30% 정도 투자", "score": 6},
            {"choice_text": "투자 금액의 50% 정도 투자", "score": 8},
            {"choice_text": "투자 금액의 70% 이상 투자", "score": 10},
        ]
    },
    {
        "category": "investment_period",
        "question_text": "투자 목적은 무엇입니까?",
        "order": 7,
        "choices": [
            {"choice_text": "생활비 또는 비상금 마련", "score": 2},
            {"choice_text": "단기 목돈 마련 (주택 계약금, 결혼자금 등)", "score": 4},
            {"choice_text": "중기 목표 (주택 구입, 자녀 교육비)", "score": 6},
            {"choice_text": "장기 자산 증식", "score": 8},
            {"choice_text": "은퇴 후 노후 자금 마련", "score": 10},
        ]
    },
    {
        "category": "financial_status",
        "question_text": "현재 보유한 비상금(긴급 자금)은 얼마입니까?",
        "order": 8,
        "choices": [
            {"choice_text": "거의 없음 (월 생활비 1개월 미만)", "score": 2},
            {"choice_text": "월 생활비 1~3개월 정도", "score": 4},
            {"choice_text": "월 생활비 3~6개월 정도", "score": 6},
            {"choice_text": "월 생활비 6~12개월 정도", "score": 8},
            {"choice_text": "월 생활비 1년 이상", "score": 10},
        ]
    },
    {
        "category": "risk_tolerance",
        "question_text": "투자한 상품의 가격이 단기간에 10% 하락했습니다. 어떻게 하시겠습니까?",
        "order": 9,
        "choices": [
            {"choice_text": "즉시 전량 매도", "score": 2},
            {"choice_text": "일부 매도하여 손실 최소화", "score": 4},
            {"choice_text": "보유 유지하며 상황 지켜봄", "score": 6},
            {"choice_text": "추가 매수 기회로 판단", "score": 8},
            {"choice_text": "적극적으로 추가 매수", "score": 10},
        ]
    },
    {
        "category": "investment_knowledge",
        "question_text": "새로운 금융상품 정보를 얼마나 자주 찾아보십니까?",
        "order": 10,
        "choices": [
            {"choice_text": "거의 찾아보지 않음", "score": 2},
            {"choice_text": "필요할 때만 가끔", "score": 4},
            {"choice_text": "월 1~2회 정도", "score": 6},
            {"choice_text": "주 1~2회 정도", "score": 8},
            {"choice_text": "거의 매일 확인", "score": 10},
        ]
    },
]


# ==========================================
# 투자 성향별 점수 구간 및 설명
# ==========================================

RISK_TYPE_MAPPING = {
    # 남성 유형
    'timid_male': {
        'score_range': (0, 50),  # ✅ 변경: 0~50점
        'gender': 'M',
        'name': '에겐소심남',
        'description': '투자에 매우 신중하고 보수적인 성향을 가진 남성 투자자입니다. 안정성을 최우선으로 생각합니다.',
        'characteristics': [
            '원금 보장을 가장 중요하게 생각',
            '투자 경험이 거의 없거나 매우 보수적',
            '안정적인 저축 상품을 선호',
            '위험 회피 성향이 강함',
        ],
        'recommended_products': '정기예금, 적금, CMA, MMF, 국채',
        'recommended_period_months': [3, 6, 12],  # 단기~중기
    },
    'normal_male': {
        'score_range': (51, 66),  # ✅ 변경: 51~66점
        'gender': 'M',
        'name': '보통남',
        'description': '위험과 수익의 균형을 추구하는 평범한 남성 투자자입니다. 안정성과 수익성을 모두 고려합니다.',
        'characteristics': [
            '안정과 수익의 균형 추구',
            '적절한 분산투자 선호',
            '중장기 투자 관심',
            '기본적인 투자 지식 보유',
        ],
        'recommended_products': '혼합형 펀드, 배당주, 우량 회사채, ISA 계좌, ETF',
        'recommended_period_months': [12, 24, 36],  # 중기
    },
    'speculative_male': {
        'score_range': (67, 100),
        'gender': 'M',
        'name': '테토투기남',
        'description': '높은 수익을 위해 적극적으로 위험을 감수하는 공격적인 남성 투자자입니다.',
        'characteristics': [
            '공격적인 고수익 추구',
            '주식, 파생상품 등 직접투자 경험 풍부',
            '단기 고수익 투자 선호',
            '높은 위험 감수 능력',
        ],
        'recommended_products': '주식, 선물/옵션, 레버리지 ETF, 암호화폐, 고위험 펀드',
        'recommended_period_months': [24, 36, 60],  # 중장기
    },
    # 여성 유형
    'timid_female': {
        'score_range': (0, 50),  # ✅ 변경: 0~50점
        'gender': 'F',
        'name': '에겐소심녀',
        'description': '투자에 매우 신중하고 보수적인 성향을 가진 여성 투자자입니다. 안정성을 최우선으로 생각합니다.',
        'characteristics': [
            '원금 보장을 가장 중요하게 생각',
            '투자 경험이 거의 없거나 매우 보수적',
            '안정적인 저축 상품을 선호',
            '위험 회피 성향이 강함',
        ],
        'recommended_products': '정기예금, 적금, CMA, MMF, 국채',
        'recommended_period_months': [3, 6, 12],  # 단기~중기
    },
    'normal_female': {
        'score_range': (51, 66),  # ✅ 변경: 51~66점
        'gender': 'F',
        'name': '보통녀',
        'description': '위험과 수익의 균형을 추구하는 평범한 여성 투자자입니다. 안정성과 수익성을 모두 고려합니다.',
        'characteristics': [
            '안정과 수익의 균형 추구',
            '적절한 분산투자 선호',
            '중장기 투자 관심',
            '기본적인 투자 지식 보유',
        ],
        'recommended_products': '혼합형 펀드, 배당주, 우량 회사채, ISA 계좌, ETF',
        'recommended_period_months': [12, 24, 36],  # 중기
    },
    'speculative_female': {
        'score_range': (67, 100),
        'gender': 'F',
        'name': '테토투기녀',
        'description': '높은 수익을 위해 적극적으로 위험을 감수하는 공격적인 여성 투자자입니다.',
        'characteristics': [
            '공격적인 고수익 추구',
            '주식, 파생상품 등 직접투자 경험 풍부',
            '단기 고수익 투자 선호',
            '높은 위험 감수 능력',
        ],
        'recommended_products': '주식, 선물/옵션, 레버리지 ETF, 암호화폐, 고위험 펀드',
        'recommended_period_months': [24, 36, 60],  # 중장기
    },
}


def calculate_risk_type(total_score, gender):
    """
    총점과 성별을 기준으로 투자 성향 결정

    Args:
        total_score (int): 설문 총점 (0~100점)
        gender (str): 성별 ('M' 또는 'F')

    Returns:
        str: 투자 성향 타입 (예: 'timid_male', 'normal_female' 등)
    """
    for risk_type, data in RISK_TYPE_MAPPING.items():
        min_score, max_score = data['score_range']
        if data['gender'] == gender and min_score <= total_score <= max_score:
            return risk_type

    # 기본값 (성별에 맞는 보통 유형)
    return 'normal_male' if gender == 'M' else 'normal_female'