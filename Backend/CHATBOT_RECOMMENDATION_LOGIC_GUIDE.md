# 챗봇 예금/적금 추천 로직 상세 가이드

## 📋 목차
1. [전체 추천 프로세스](#전체-추천-프로세스)
2. [사용자 프로필 기반 필터링](#사용자-프로필-기반-필터링)
3. [상품 정렬 및 선택 기준](#상품-정렬-및-선택-기준)
4. [RAG 시스템 통합](#rag-시스템-통합)
5. [예상 수익 계산](#예상-수익-계산)
6. [코드 예시](#코드-예시)

---

## 🔄 전체 추천 프로세스

### 단계별 흐름

```
[1단계] 사용자 질문 입력
         ↓
[2단계] 의도 분류 (PRODUCT, STOCK, NEWS, GENERAL)
         ↓
[3단계] 사용자 프로필 로드
         ├─ 투자 성향 (risk_type)
         ├─ 나이, 성별
         ├─ 투자 기간 (investment_period)
         ├─ 투자 목표 (investment_goal)
         └─ 연소득, 현재 저축액
         ↓
[4단계] RAG 벡터 검색 (질문과 유사한 상품 Top-5)
         ↓
[5단계] 사용자 프로필 기반 필터링
         ├─ 성별/나이 제한 확인
         ├─ 투자 기간 매칭
         └─ 금리 우선 순위 정렬
         ↓
[6단계] LLM에게 컨텍스트 전달
         ├─ 사용자 프로필
         ├─ 필터링된 상품 정보 (5개)
         └─ 예상 수익 정보
         ↓
[7단계] AI 응답 생성 및 반환
```

---

## 👤 사용자 프로필 기반 필터링

### 1. 프로필 정보 수집

챗봇은 먼저 사용자의 투자 프로필을 확인합니다.

**파일**: `chatbot/services.py` - `get_user_profile_context()` (27-49번째 줄)

```python
def get_user_profile_context(self):
    """사용자 투자 프로필 정보 가져오기"""
    try:
        profile = self.user.investment_profile
        return {
            'has_profile': True,
            'risk_type': profile.risk_type,        # 투자 성향: '안정형', '중립형', '공격형'
            'risk_score': profile.risk_score,      # 위험 점수: 0~100
            'age': profile.age,                    # 나이
            'gender': profile.gender,              # 성별: 'M' or 'F'
            'annual_income': profile.income,       # 연소득
            'current_savings': profile.savings,    # 현재 저축액
            'investment_goal': profile.investment_goal,     # 투자 목표
            'investment_period': profile.investment_period, # 투자 기간 (개월)
        }
    except:
        return {'has_profile': False}  # 프로필 없으면 기본 정보로 안내
```

### 투자 성향 분류 (InvestmentProfile 모델)

**파일**: `accounts/models.py` (55-87번째 줄)

```python
class InvestmentProfile(models.Model):
    """투자 성향 프로필"""

    RISK_TYPE_CHOICES = [
        ('conservative', '안정형'),   # 원금보장 중시, 낮은 수익률 감수
        ('moderate', '중립형'),        # 중간 수준의 위험과 수익
        ('aggressive', '공격형'),      # 높은 수익률 추구, 높은 위험 감수
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='investment_profile')
    risk_type = models.CharField(max_length=20, choices=RISK_TYPE_CHOICES)
    risk_score = models.IntegerField(default=0)  # 0~100

    # 기본 정보
    age = models.IntegerField()
    gender = models.CharField(max_length=1, choices=[('M', '남성'), ('F', '여성')])
    income = models.BigIntegerField(help_text="연 소득 (원)")
    savings = models.BigIntegerField(help_text="현재 저축액 (원)")

    # 투자 정보
    investment_goal = models.CharField(max_length=100)  # 예: "주택 구입", "노후 대비"
    investment_period = models.IntegerField(help_text="투자 기간 (개월)")
```

### 2. 성별/나이 필터링

**파일**: `chatbot/services.py` - `_is_eligible_for_product()` (256-298번째 줄)

```python
def _is_eligible_for_product(self, join_member, user_gender, user_age):
    """
    사용자가 상품 가입 대상인지 확인

    Args:
        join_member: 상품의 가입 대상 (예: "만18세이상 여성고객", "만19세이상", "제한없음")
        user_gender: 사용자 성별 ('M' or 'F')
        user_age: 사용자 나이

    Returns:
        bool: 가입 가능 여부
    """
    # 1. 제한 없는 상품은 모두 통과
    if not join_member or join_member == "제한없음":
        return True

    # 2. 성별 체크
    if user_gender:
        if '여성' in join_member and user_gender == 'M':
            return False  # 여성 전용 상품인데 남성이면 제외
        if '남성' in join_member and user_gender == 'F':
            return False  # 남성 전용 상품인데 여성이면 제외

    # 3. 나이 체크 (정규표현식 파싱)
    if user_age:
        # "만18세이상", "만19세", "만65세미만" 등 파싱
        age_patterns = [
            (r'만(\d+)세\s*이상', lambda match: user_age >= int(match.group(1))),
            (r'만(\d+)세\s*미만', lambda match: user_age < int(match.group(1))),
        ]

        for pattern, check_func in age_patterns:
            match = re.search(pattern, join_member)
            if match:
                if not check_func(match):
                    return False  # 나이 조건 불충족 시 제외

    return True  # 모든 조건 통과
```

**예시**:
- 사용자: 25세 여성
- 상품 A: "만18세이상" → ✅ 통과
- 상품 B: "만18세이상 여성고객" → ✅ 통과
- 상품 C: "만18세이상 남성고객" → ❌ 제외
- 상품 D: "만30세이상" → ❌ 제외

---

## 📊 상품 정렬 및 선택 기준

### 1. 기존 모드: 최고 금리순 정렬

**파일**: `chatbot/services.py` - `get_financial_products_context()` (51-165번째 줄)

```python
def get_financial_products_context(self):
    """DB에 저장된 금융 상품 정보 가져오기 (금리 정보 포함)"""

    # 사용자 프로필 정보
    user_profile = self.get_user_profile_context()
    user_gender = user_profile.get('gender')
    user_age = user_profile.get('age')
    user_period = user_profile.get('investment_period')  # 예: 12개월

    # ===== 예금 상품 처리 =====
    deposits = DepositProducts.objects.annotate(
        max_rate=Max('options__intr_rate2')  # 최고 우대금리 계산
    ).prefetch_related('options').filter(
        max_rate__isnull=False
    ).order_by('-max_rate')  # 🔥 최고 금리 내림차순 정렬

    deposit_data = []
    for d in deposits:
        # 1️⃣ 성별/나이 필터링
        if not self._is_eligible_for_product(d.join_member, user_gender, user_age):
            continue  # 가입 불가 상품은 건너뛰기

        # 2️⃣ 최고 금리 옵션 찾기
        best_option = d.options.order_by('-intr_rate2').first()

        # 3️⃣ 사용자 투자 기간과 유사한 옵션 찾기
        matching_option = best_option
        if user_period:
            # 사용자가 12개월 투자 희망 → 6~18개월 옵션 중 최고금리 선택
            period_match = d.options.filter(
                save_trm__gte=user_period - 6,  # 12 - 6 = 6개월 이상
                save_trm__lte=user_period + 6   # 12 + 6 = 18개월 이하
            ).order_by('-intr_rate2').first()

            if period_match:
                matching_option = period_match  # 기간 매칭되는 옵션으로 교체

        # 4️⃣ 예상 수익 계산 (1억원 기준)
        expected_profit = self._calculate_deposit_profit(
            10000,  # 1억원 = 10,000만원
            matching_option.save_trm,
            matching_option.intr_rate2
        )

        # 5️⃣ 데이터 추가
        deposit_data.append({
            'type': 'deposit',
            'bank': d.kor_co_nm,
            'product_name': d.fin_prdt_nm,
            'code': d.fin_prdt_cd,
            'max_rate': f"{matching_option.intr_rate2:.2f}%",
            'period': f"{matching_option.save_trm}개월",
            'expected_profit': f"{expected_profit:,.0f}만원",
        })

        # 6️⃣ 최대 15개까지만 수집
        if len(deposit_data) >= 15:
            break

    # ===== 적금 상품도 동일한 로직 =====
    # ... (생략)

    return {
        'deposits': deposit_data,
        'savings': saving_data,
    }
```

### 정렬 우선순위

1. **최고 금리 우선** (내림차순)
2. **사용자 프로필 필터링**
   - 성별/나이 제한 확인
   - 투자 기간 매칭 (±6개월 범위)
3. **상위 15개 선택**

---

## 🔍 RAG 시스템 통합

### 1. RAG 기반 상품 검색

**파일**: `chatbot/services.py` - `get_rag_products_context()` (167-254번째 줄)

```python
def get_rag_products_context(self, user_message, top_k=5, intent='PRODUCT'):
    """
    RAG 시스템을 사용하여 사용자 질문과 관련된 금융 상품만 가져오기

    Args:
        user_message: 사용자 질문 (예: "안정적인 예금 상품 추천해줘")
        top_k: 가져올 상품 개수 (기본 5개)
        intent: 사용자 의도 ('PRODUCT', 'STOCK' 등)

    Returns:
        str: LLM 프롬프트에 넣을 컨텍스트 문자열
    """
    if intent != 'PRODUCT':
        return ""

    # 1️⃣ 벡터 스토어에서 유사 상품 검색
    vector_store = get_vector_store()
    similar_products = vector_store.search(user_message, top_k=top_k)

    # 검색 결과 예시:
    # [
    #     {'type': 'deposit', 'fin_prdt_cd': 'WR0001B', 'fin_prdt_nm': 'NH올원e예금',
    #      'kor_co_nm': '농협은행', 'similarity_score': 0.391},
    #     {'type': 'deposit', 'fin_prdt_cd': 'WR0002B', 'fin_prdt_nm': 'The플러스예금',
    #      'kor_co_nm': '광주은행', 'similarity_score': 0.385},
    #     ...
    # ]

    # 2️⃣ 사용자 프로필 정보
    user_profile = self.get_user_profile_context()
    user_gender = user_profile.get('gender')
    user_age = user_profile.get('age')
    user_period = user_profile.get('investment_period')

    # 3️⃣ 검색된 상품에 대해 상세 정보 조회
    context = f"사용자 질문 '{user_message}'와 관련된 상위 {len(similar_products)}개 금융 상품:\n\n"

    for i, item in enumerate(similar_products, 1):
        product_type = item['type']
        fin_prdt_cd = item['fin_prdt_cd']

        if product_type == 'deposit':
            # DB에서 예금 상품 조회
            product = DepositProducts.objects.filter(fin_prdt_cd=fin_prdt_cd).first()

            # 성별/나이 필터링 (가입 불가면 건너뛰기)
            if not self._is_eligible_for_product(product.join_member, user_gender, user_age):
                continue

            # 최고 금리 옵션
            best_option = product.options.order_by('-intr_rate2').first()

            # 사용자 기간 매칭 옵션
            matching_option = best_option
            if user_period:
                period_match = product.options.filter(
                    save_trm__gte=user_period - 6,
                    save_trm__lte=user_period + 6
                ).order_by('-intr_rate2').first()
                if period_match:
                    matching_option = period_match

            # 예상 수익 계산
            profit = self._calculate_deposit_profit(
                10000, matching_option.save_trm, matching_option.intr_rate2
            )

            # 컨텍스트 문자열 생성
            context += f"{i}. [예금] {product.fin_prdt_nm}\n"
            context += f"   은행: {product.kor_co_nm}\n"
            context += f"   최고 금리: {matching_option.intr_rate2:.2f}% ({matching_option.save_trm}개월)\n"
            context += f"   예상 수익: {profit:,.0f}만원 (1억원 기준)\n"
            context += f"   가입 방법: {product.join_way or '정보 없음'}\n"
            context += f"   특별 조건: {product.spcl_cnd or '없음'}\n"
            context += f"   관련도: {item['similarity_score']:.1%}\n\n"

    return context.strip()
```

### RAG vs 기존 모드 비교

| 항목 | 기존 모드 | RAG 모드 |
|------|----------|----------|
| **검색 방식** | 전체 상품 조회 (30개) | 유사도 검색 (Top-5) |
| **토큰 사용량** | ~2,833 토큰 | ~173 토큰 |
| **정렬 기준** | 최고 금리순 | 질문 관련도 + 금리 |
| **장점** | 모든 상품 고려 | 질문에 더 정확한 추천 |
| **단점** | 토큰 낭비 | 일부 상품 누락 가능 |

---

## 💰 예상 수익 계산

### 1. 예금 수익 계산 (단리)

**파일**: `chatbot/services.py` - `_calculate_deposit_profit()` (300-312번째 줄)

```python
def _calculate_deposit_profit(self, principal, months, annual_rate):
    """
    예금 예상 수익 계산 (단리)

    Args:
        principal: 원금 (만원)
        months: 가입 기간 (개월)
        annual_rate: 연 금리 (%)

    Returns:
        float: 예상 수익 (만원)

    공식: 원금 × 연금리(%) ÷ 100 × (개월 ÷ 12)
    """
    return principal * (annual_rate / 100) * (months / 12)
```

**예시 계산**:
```python
# 1억원(10,000만원)을 연 3.5% 금리로 12개월 예금
profit = 10000 * (3.5 / 100) * (12 / 12)
      = 10000 * 0.035 * 1
      = 350만원

# 결과: 만기 시 10,350만원 수령 (이자 350만원)
```

### 2. 적금 수익 계산 (복리)

**파일**: `chatbot/services.py` - `_calculate_saving_profit()` (314-335번째 줄)

```python
def _calculate_saving_profit(self, monthly_deposit, months, annual_rate):
    """
    적금 예상 수익 계산 (복리)

    Args:
        monthly_deposit: 월 납입액 (만원)
        months: 가입 기간 (개월)
        annual_rate: 연 금리 (%)

    Returns:
        float: 예상 수익 (만원)

    공식: 매월 복리 계산
    """
    monthly_rate = annual_rate / 100 / 12  # 월 금리
    total_principal = monthly_deposit * months  # 총 납입액

    # 적금 복리 계산
    future_value = 0
    for i in range(months):
        # 각 월 납입금이 남은 기간만큼 복리로 증식
        future_value += monthly_deposit * ((1 + monthly_rate) ** (months - i))

    # 이자 = 만기 금액 - 총 납입액
    return future_value - total_principal
```

**예시 계산**:
```python
# 월 100만원씩 12개월, 연 3.6% 적금
monthly_rate = 3.6 / 100 / 12 = 0.003

1개월: 100만원 × (1.003)^11 = 103.36만원
2개월: 100만원 × (1.003)^10 = 103.05만원
3개월: 100만원 × (1.003)^9  = 102.74만원
...
12개월: 100만원 × (1.003)^0 = 100.00만원

만기 금액 = 1,221.98만원
총 납입액 = 1,200만원
이자 = 21.98만원
```

---

## 📝 코드 예시

### 전체 추천 흐름 예시

```python
# 1. 사용자 질문
user_message = "안정적인 예금 상품 추천해줘"

# 2. 의도 분류
analysis = chatbot.analyze_user_question(user_message)
# {'intent': 'PRODUCT', 'stock_names': [], ...}

# 3. 사용자 프로필
user_profile = chatbot.get_user_profile_context()
# {
#     'has_profile': True,
#     'risk_type': 'conservative',  # 안정형
#     'age': 25,
#     'gender': 'F',
#     'investment_period': 12,
#     ...
# }

# 4. RAG 벡터 검색
rag_context = chatbot.get_rag_products_context(user_message, top_k=5)
# """
# 사용자 질문 '안정적인 예금 상품 추천해줘'와 관련된 상위 5개 금융 상품:
#
# 1. [예금] NH올원e예금
#    은행: 농협은행
#    최고 금리: 3.50% (12개월)
#    예상 수익: 350만원 (1억원 기준)
#    관련도: 39.1%
#
# 2. [예금] The플러스예금
#    은행: 광주은행
#    최고 금리: 3.45% (12개월)
#    예상 수익: 345만원 (1억원 기준)
#    관련도: 38.5%
# ...
# """

# 5. LLM 프롬프트 구성
system_prompt = f"""
당신은 금융 상품 추천 전문가입니다.

사용자 프로필:
- 투자 성향: 안정형 (원금보장 중시)
- 나이: 25세, 성별: 여성
- 투자 기간: 12개월

{rag_context}

위 상품 중에서 사용자에게 가장 적합한 예금 상품을 추천해주세요.
"""

# 6. AI 응답 생성
response = chatbot.chat(user_message)
# {
#     'success': True,
#     'response': '25세 여성 고객님께 안정적인 예금 상품을 추천드립니다...',
#     'recommended_products': [
#         {'type': 'deposit', 'name': 'NH올원e예금', 'bank': '농협은행', ...}
#     ]
# }
```

---

## 🎯 추천 로직 요약

### 기준별 우선순위

1. **필수 조건 (필터링)**
   - ✅ 성별/나이 가입 제한 확인
   - ✅ 상품 존재 및 활성화 여부

2. **우선 고려 사항 (정렬)**
   - 🔥 질문 관련도 (RAG 유사도 점수)
   - 🔥 최고 금리
   - 🔥 사용자 투자 기간 매칭

3. **부가 정보 (참고)**
   - 💰 예상 수익 계산
   - 📋 특별 조건 (우대금리 조건)
   - 🏦 은행 정보
   - 📱 가입 방법

### 최종 추천 결정

LLM(Claude)이 다음을 종합하여 최종 추천:
- 사용자 프로필 (투자 성향, 나이, 목표)
- 필터링된 상품 정보 (Top-5)
- 각 상품의 금리, 기간, 예상 수익
- 질문의 의도 ("안정적인", "금리 높은" 등)

---

## 📌 주요 특징

### 1. 개인화 추천
- 사용자의 나이, 성별, 투자 성향 고려
- 가입 불가능한 상품 자동 제외
- 투자 기간 매칭 (±6개월 범위)

### 2. 효율성
- RAG 시스템으로 토큰 93.9% 절감
- 질문과 관련 높은 상품만 선별
- 최대 5개 상품만 LLM에 전달

### 3. 정확성
- 실제 DB 데이터 기반 추천
- 실시간 금리 정보 반영
- 정확한 예상 수익 계산

### 4. 투명성
- 추천 이유 명시 (금리, 기간, 조건)
- 관련도 점수 표시
- 특별 조건 안내

---

## 🔗 관련 파일

### 핵심 로직
- **[chatbot/services.py](chatbot/services.py)** - 추천 로직 전체
  - `get_user_profile_context()` (27-49줄) - 프로필 조회
  - `get_financial_products_context()` (51-165줄) - 기존 모드 상품 조회
  - `get_rag_products_context()` (167-254줄) - RAG 모드 상품 검색
  - `_is_eligible_for_product()` (256-298줄) - 가입 자격 확인
  - `_calculate_deposit_profit()` (300-312줄) - 예금 수익 계산
  - `_calculate_saving_profit()` (314-335줄) - 적금 수익 계산

### 데이터 모델
- **[accounts/models.py](accounts/models.py)** - 사용자 프로필
  - `InvestmentProfile` (55-87줄) - 투자 성향 프로필
  - `SurveyQuestion`, `SurveyChoice` - 설문 데이터

### RAG 시스템
- **[chatbot/vector_store.py](chatbot/vector_store.py)** - 벡터 검색
  - `ProductVectorStore.search()` (142-199줄) - 유사 상품 검색

---

**작성일**: 2025년 12월 25일
**버전**: 1.0.0
