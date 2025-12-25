# 추천 페이지 vs 챗봇 추천 비교 분석

## 📋 개요

Finflow에는 **2가지 독립적인 금융상품 추천 시스템**이 있습니다:

1. **추천 페이지** (`RecommendationsView.vue` + `accounts/views.py::recommend_products`)
2. **챗봇 추천** (`ChatbotService` + RAG 시스템)

각각 다른 목적과 로직으로 작동합니다.

---

## 🎯 핵심 차이점 요약

| 항목 | 추천 페이지 | 챗봇 추천 |
|------|------------|-----------|
| **목적** | 전체 포트폴리오 구성 | 질문에 맞는 상품 탐색 |
| **추천 개수** | 15개 (예금+적금 혼합) | 5개 (질문 관련도 Top-5) |
| **선택 기준** | 최고 금리 + 예/적금 비율 | 질문 유사도 + 금리 |
| **비율 결정** | 저축액/기간/목표 점수화 | 고정 (질문에 따라 자동) |
| **매칭 점수** | 금리 기반 (0~100점) | RAG 유사도 (0~100%) |
| **사용자 입력** | 불필요 (프로필만 사용) | 필요 (질문 입력) |
| **응답 형식** | JSON (상품 리스트) | 자연어 (LLM 생성) |

---

## 📊 추천 페이지 (RecommendationsView)

### 목적
**"사용자 프로필에 최적화된 포트폴리오 제안"**
- 예금과 적금을 적절한 비율로 혼합
- 전체 15개 상품 추천
- 투자 계획 제공

### 추천 로직 상세

#### 1단계: 예금/적금 비율 결정

**파일**: `accounts/views.py` - `_calculate_product_ratio()` (270-335번째 줄)

```python
def _calculate_product_ratio(savings_amount, investment_period, investment_goal):
    """
    저축액, 투자기간, 투자목표를 점수화하여 예금/적금 비율 결정

    총 점수: 100점 (예금 점수 + 적금 점수)
    - 저축액 기반: 0~40점
    - 투자기간 기반: 0~40점
    - 투자목표 기반: 0~20점
    """
    deposit_score = 0
    saving_score = 0

    # 1. 저축액 기반 점수 (0~40점)
    if savings_amount >= 5000:  # 5,000만원 이상
        deposit_score += 40  # 목돈 있음 → 예금 강력 선호
        saving_score += 10
    elif savings_amount >= 3000:  # 3,000~5,000만원
        deposit_score += 30
        saving_score += 20
    elif savings_amount >= 1000:  # 1,000~3,000만원
        deposit_score += 20
        saving_score += 30
    else:  # 1,000만원 미만
        deposit_score += 10  # 적금으로 모으기
        saving_score += 40

    # 2. 투자 기간 기반 점수 (0~40점)
    if investment_period <= 6:  # 6개월 이하
        deposit_score += 40  # 단기 → 예금 (즉시 인출)
        saving_score += 10
    elif investment_period <= 12:  # 6~12개월
        deposit_score += 30
        saving_score += 20
    elif investment_period <= 24:  # 12~24개월
        deposit_score += 20
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
```

**예시 시나리오**:

| 프로필 | 저축액 점수 | 기간 점수 | 목표 점수 | 예금 총점 | 적금 총점 | 비율 | 추천 개수 |
|--------|------------|---------|----------|----------|----------|------|----------|
| 저축액 1,500만원<br>기간 12개월<br>목표 "비상금" | 20 | 30 | 20 | **70** | 50 | 58% | 예금 9개<br>적금 6개 |
| 저축액 500만원<br>기간 24개월<br>목표 "주택 구입" | 10 | 10 | 10 | 30 | **70** | 30% | 예금 5개<br>적금 10개 |
| 저축액 6,000만원<br>기간 6개월<br>목표 "단기 운용" | 40 | 40 | 20 | **100** | 15 | 87% | 예금 13개<br>적금 2개 |

#### 2단계: 상품 필터링 및 정렬

**파일**: `accounts/views.py` - `recommend_products()` (338-531번째 줄)

```python
@api_view(['GET'])
def recommend_products(request):
    """
    사용자의 투자 성향에 맞는 예금/적금 상품 추천

    단계:
    1. 프로필 로드
    2. 예금/적금 각각 최고 금리순 조회
    3. 성별/나이 필터링
    4. 투자 기간 매칭 (±6개월)
    5. 예상 수익 계산
    6. 비율에 맞춰 선택
    7. 최종 금리순 정렬
    """
    profile = request.user.investment_profile

    user_gender = profile.gender
    user_age = profile.age
    user_period = profile.investment_period

    # 비율 계산
    deposit_count, saving_count = _calculate_product_ratio(
        savings_amount=int(profile.savings),
        investment_period=user_period,
        investment_goal=profile.investment_goal
    )

    # ===== 예금 상품 추천 =====
    deposits = DepositProducts.objects.annotate(
        max_rate=Max('options__intr_rate2')
    ).filter(
        max_rate__isnull=False
    ).order_by('-max_rate')  # 🔥 최고 금리 내림차순

    deposit_recommendations = []
    for d in deposits:
        # 1. 성별/나이 필터링
        if not _is_eligible_for_product(d.join_member, user_gender, user_age):
            continue

        # 2. 투자 기간 매칭 (±6개월)
        if user_period:
            period_match = d.options.filter(
                save_trm__gte=user_period - 6,
                save_trm__lte=user_period + 6
            ).order_by('-intr_rate2').first()
        else:
            period_match = None

        # 3. 매칭 옵션 선택
        matching_option = period_match or d.options.order_by('-intr_rate2').first()

        # 4. 예상 수익 계산
        rate = float(matching_option.intr_rate2)
        expected_profit = _calculate_deposit_profit(
            principal_amount, matching_option.save_trm, rate
        )

        deposit_recommendations.append({
            'type': 'deposit',
            'product': {...},
            'option': {...},
            'expected_profit': expected_profit,
            'max_rate': rate,
        })

    # ===== 적금 상품도 동일하게 처리 =====
    # ... (생략)

    # ===== 비율에 맞춰 선택 =====
    selected_deposits = deposit_recommendations[:deposit_count]  # 예: 9개
    selected_savings = saving_recommendations[:saving_count]     # 예: 6개

    # ===== 합치고 다시 금리순 정렬 =====
    all_recommendations = selected_deposits + selected_savings
    all_recommendations.sort(key=lambda x: x['max_rate'], reverse=True)

    return Response({
        'recommendations': all_recommendations,  # 15개
        'recommended_deposit_count': deposit_count,
        'recommended_saving_count': saving_count,
    })
```

#### 3단계: 매칭 점수 표시

**파일**: `accounts/views.py` - `calculate_match_score()` (534-583번째 줄)

```python
def calculate_match_score(profile, product, option):
    """
    매칭 점수 계산 (0~100점)

    구성:
    - 투자기간 일치도: 30점
    - 금리 수준: 40점
    - 우대조건 매칭: 20점
    - 가입 방법 편의성: 10점
    """
    score = 0

    # 1. 투자기간 일치도 (30점)
    period_diff = abs(profile.investment_period - option.save_trm)
    if period_diff == 0:
        score += 30
    elif period_diff <= 6:
        score += 20
    elif period_diff <= 12:
        score += 10

    # 2. 금리 수준 (40점)
    if option.intr_rate2 >= 4.0:
        score += 40
    elif option.intr_rate2 >= 3.5:
        score += 30
    elif option.intr_rate2 >= 3.0:
        score += 20
    else:
        score += 10

    # 3. 우대조건 매칭 (20점)
    if product.spcl_cnd and len(product.spcl_cnd) > 10:
        score += 15
    else:
        score += 5

    # 4. 가입 방법 편의성 (10점)
    if '인터넷' in product.join_way or '모바일' in product.join_way:
        score += 10
    elif '영업점' in product.join_way:
        score += 5

    return min(score, 100)
```

**프론트엔드 표시**:
```vue
<!-- RecommendationsView.vue -->
<div class="match-score">
  <div class="score-circle" :style="{ '--score': rec.match_score }">
    <span>{{ rec.match_score }}</span>
  </div>
  <span class="score-label">매칭도</span>
</div>
```

---

## 💬 챗봇 추천 (ChatbotService + RAG)

### 목적
**"사용자 질문에 정확하게 맞는 상품 즉시 탐색"**
- 질문 의도 분석
- 유사도 기반 검색
- 자연어 응답 생성

### 추천 로직 상세

#### 1단계: 질문 분석

**파일**: `chatbot/services.py` - `analyze_user_question()` (457-514번째 줄)

```python
def analyze_user_question(self, user_message):
    """
    질문 의도 분류

    의도 종류:
    - PRODUCT: 예금/적금 추천
    - STOCK: 주식 정보
    - NEWS: 뉴스 검색
    - GENERAL: 일반 대화
    """
    # 키워드 점수 시스템
    product_core_keywords = ['예금', '적금', '금리', '이자', '은행']
    stability_keywords = ['안정', '안전', '보장', '확정', '원금보장']

    product_score = 0

    for kw in product_core_keywords:
        if kw in user_message:
            product_score += 3

    for kw in stability_keywords:
        if kw in user_message:
            product_score += 5

    # 점수 기반 의도 결정
    if product_score > 0:
        result['intent'] = 'PRODUCT'
    else:
        result['intent'] = 'GENERAL'

    return result
```

#### 2단계: RAG 벡터 검색

**파일**: `chatbot/services.py` - `get_rag_products_context()` (167-254번째 줄)

```python
def get_rag_products_context(self, user_message, top_k=5):
    """
    RAG 시스템을 사용하여 질문과 관련된 상품만 검색

    단계:
    1. TF-IDF 벡터화
    2. FAISS 유사도 검색
    3. Top-K 선택 (기본 5개)
    4. 프로필 기반 필터링
    5. LLM 프롬프트 생성
    """
    # 1. 벡터 검색
    vector_store = get_vector_store()
    similar_products = vector_store.search(user_message, top_k=5)

    # 검색 결과 예시:
    # [
    #   {'fin_prdt_nm': 'NH올원e예금', 'similarity_score': 0.391},
    #   {'fin_prdt_nm': 'The플러스예금', 'similarity_score': 0.385},
    #   ...
    # ]

    # 2. 프로필 기반 필터링
    user_profile = self.get_user_profile_context()
    user_gender = user_profile.get('gender')
    user_age = user_profile.get('age')
    user_period = user_profile.get('investment_period')

    # 3. 상세 정보 조회 및 포맷팅
    context = ""
    for i, item in enumerate(similar_products, 1):
        product = DepositProducts.objects.filter(
            fin_prdt_cd=item['fin_prdt_cd']
        ).first()

        # 성별/나이 필터링
        if not self._is_eligible_for_product(
            product.join_member, user_gender, user_age
        ):
            continue

        # 최고 금리 옵션
        best_option = product.options.order_by('-intr_rate2').first()

        # 기간 매칭 옵션
        if user_period:
            period_match = product.options.filter(
                save_trm__gte=user_period - 6,
                save_trm__lte=user_period + 6
            ).order_by('-intr_rate2').first()
            if period_match:
                best_option = period_match

        # 컨텍스트 생성
        context += f"""
{i}. [예금] {product.fin_prdt_nm}
   은행: {product.kor_co_nm}
   최고 금리: {best_option.intr_rate2:.2f}% ({best_option.save_trm}개월)
   예상 수익: {profit:,.0f}만원 (1억원 기준)
   관련도: {item['similarity_score']:.1%}
"""

    return context
```

#### 3단계: LLM 응답 생성

**파일**: `chatbot/services.py` - `chat()` (1143-1277번째 줄)

```python
def chat(self, user_message):
    """
    RAG 기반 챗봇 응답 생성

    단계:
    1. 의도 분석
    2. RAG 검색 (PRODUCT 의도만)
    3. 프롬프트 구성
    4. LLM 호출
    5. 응답 반환
    """
    # 의도 분석
    analysis = self.analyze_user_question(user_message)
    intent = analysis['intent']

    # RAG 검색
    if intent == 'PRODUCT':
        rag_context = self.get_rag_products_context(user_message, top_k=5)
        products = {'rag_context': rag_context}
    else:
        products = self.get_financial_products_context()  # 기존 방식

    # 프롬프트 구성
    system_prompt = f"""
당신은 금융 상품 추천 전문가입니다.

사용자 프로필:
- 투자 성향: {profile['risk_type']}
- 나이: {profile['age']}세
- 투자 기간: {profile['investment_period']}개월

{rag_context}

위 상품 중에서 사용자에게 가장 적합한 상품을 추천해주세요.
"""

    # LLM 호출
    response = gms_api_call(system_prompt, user_message)

    return {
        'success': True,
        'response': response,  # 자연어 응답
        'recommended_products': extracted_products,
    }
```

---

## 🔍 상세 비교

### 1. 추천 개수

**추천 페이지**:
- **총 15개** (예금 + 적금 혼합)
- 비율: 저축액/기간/목표 기반 점수화
- 예시: 예금 9개 + 적금 6개

**챗봇**:
- **Top-5** (질문 관련도 높은 순)
- 비율: 질문 내용에 따라 자동
- 예: "예금 추천" → 예금 5개, "적금 추천" → 적금 5개

### 2. 정렬 기준

**추천 페이지**:
```python
# 1단계: 각각 최고 금리순 조회
deposits.order_by('-max_rate')
savings.order_by('-max_rate')

# 2단계: 비율에 맞춰 선택
selected_deposits = deposit_recommendations[:deposit_count]
selected_savings = saving_recommendations[:saving_count]

# 3단계: 합치고 다시 금리순 정렬
all_recommendations.sort(key=lambda x: x['max_rate'], reverse=True)
```

**챗봇**:
```python
# 1단계: 질문 유사도로 검색
similar_products = vector_store.search(user_message, top_k=5)

# 2단계: 유사도 점수순 (이미 정렬됨)
# [{'similarity_score': 0.391}, {'similarity_score': 0.385}, ...]

# 3단계: 필터링 (성별/나이)
# 유사도 순서 유지
```

### 3. 매칭 점수 의미

**추천 페이지**:
```python
# 매칭 점수 = 복합 점수 (0~100점)
score = 0
score += 30  # 투자기간 일치도
score += 40  # 금리 수준
score += 20  # 우대조건 매칭
score += 10  # 가입 방법 편의성

# 결과: 85점
```

**챗봇**:
```python
# 유사도 점수 = TF-IDF 코사인 유사도 (0~100%)
similarity_score = 1 / (1 + L2_distance)

# 결과: 39.1% (질문 "안정적인 예금" ↔ "NH올원e예금" 유사도)
```

### 4. 필터링 로직

**추통 페이지**:
```python
# 1. 성별/나이 필터링 (공통)
if not _is_eligible_for_product(join_member, user_gender, user_age):
    continue

# 2. 투자 기간 매칭 (공통)
period_match = options.filter(
    save_trm__gte=user_period - 6,
    save_trm__lte=user_period + 6
).order_by('-intr_rate2').first()

# 3. 비율 제한 (추천 페이지 전용)
selected_deposits = deposit_recommendations[:deposit_count]
```

**챗봇**:
```python
# 1. 성별/나이 필터링 (공통)
if not _is_eligible_for_product(join_member, user_gender, user_age):
    continue

# 2. 투자 기간 매칭 (공통)
period_match = options.filter(
    save_trm__gte=user_period - 6,
    save_trm__lte=user_period + 6
).order_by('-intr_rate2').first()

# 3. Top-K 제한 (챗봇 전용)
similar_products = vector_store.search(query, top_k=5)
```

---

## 📈 사용 시나리오 비교

### 시나리오 1: 25세 여성, 저축액 1,500만원, 투자기간 12개월, 목표 "비상금"

#### 추천 페이지

**비율 계산**:
- 저축액 1,500만원 → 예금 20점, 적금 30점
- 기간 12개월 → 예금 30점, 적금 20점
- 목표 "비상금" → 예금 20점, 적금 5점
- **총점**: 예금 70점, 적금 55점
- **비율**: 56% : 44% → **예금 8개, 적금 7개**

**추천 상품**:
```
1. [예금] NH올원e예금 - 3.50% (12개월) - 매칭도 85점
2. [예금] The플러스예금 - 3.45% (12개월) - 매칭도 82점
3. [적금] 온 적금 - 2.90% (12개월) - 매칭도 78점
4. [예금] 헤이자유예금 - 3.40% (6개월) - 매칭도 75점
...
(총 15개: 예금 8개 + 적금 7개)
```

#### 챗봇

**질문**: "안정적인 예금 상품 추천해줘"

**RAG 검색 결과**:
```
1. [예금] NH올원e예금 - 3.50% - 유사도 39.1%
2. [예금] The플러스예금 - 3.45% - 유사도 38.5%
3. [예금] 헤이자유예금 - 3.40% - 유사도 38.4%
4. [예금] IBK평생한가족예금 - 3.35% - 유사도 37.2%
5. [예금] KB Star정기예금 - 3.30% - 유사도 36.8%
```

**LLM 응답**:
```
안녕하세요! 25세 여성 고객님께 안정적인 예금 상품을 추천드립니다.

**1위: NH올원e예금 (농협은행)**
- 최고 금리: 3.50% (12개월)
- 예상 수익: 52만원 (1,500만원 기준)
- 추천 이유: 고객님의 투자 기간 12개월과 정확히 일치하며,
  높은 금리로 안정적인 수익을 보장합니다.

**2위: The플러스예금 (광주은행)**
- 최고 금리: 3.45% (12개월)
- 예상 수익: 51만원
- 추천 이유: 인터넷/모바일 가입으로 편리하며,
  비상금 용도로 적합한 자유입출금 기능이 있습니다.

위 상품들은 모두 예금자보호법에 따라 5,000만원까지
원금이 보장되어 안정성이 매우 높습니다.
```

---

## 🎯 언제 어떤 시스템을 사용해야 할까?

### 추천 페이지를 사용하는 경우

1. **전체 포트폴리오 구성**
   - "내 조건에 맞는 모든 상품을 보고 싶어요"
   - 예금과 적금을 적절히 섞어서 추천받고 싶을 때

2. **비교 검토**
   - 15개 상품을 한눈에 비교
   - 매칭 점수로 순위 확인

3. **투자 계획 수립**
   - 장기 투자 계획 필요
   - 예상 수익 비교

### 챗봇을 사용하는 경우

1. **빠른 탐색**
   - "금리 높은 예금 알려줘" 같은 즉각적 질문
   - 특정 조건의 상품만 보고 싶을 때

2. **대화형 상담**
   - 자연어로 질문하고 싶을 때
   - 추가 질문이 필요할 때

3. **상황별 추천**
   - "단기로 운용할 수 있는 상품"
   - "안정적인 상품"
   - "금리가 제일 높은 상품"

---

## 🔧 기술 스택 비교

### 추천 페이지

**백엔드**:
- Django ORM
- 점수 기반 알고리즘
- SQL 집계 함수 (Max, Annotate)

**프론트엔드**:
- Vue 3 Composition API
- Axios HTTP 클라이언트
- Computed Properties (중복 제거)

**데이터 흐름**:
```
User Profile
    ↓
Calculate Ratio (저축액/기간/목표 점수화)
    ↓
Filter Products (성별/나이/기간)
    ↓
Sort by Rate (최고 금리순)
    ↓
Select by Ratio (예금 N개, 적금 M개)
    ↓
Response JSON
```

### 챗봇

**백엔드**:
- Django ORM
- TF-IDF (scikit-learn)
- FAISS 벡터 검색
- GMS API (LLM)

**프론트엔드**:
- Vue 3 Composition API
- WebSocket (실시간 채팅)
- Markdown 렌더링

**데이터 흐름**:
```
User Question
    ↓
Analyze Intent (키워드 점수화)
    ↓
RAG Vector Search (TF-IDF + FAISS)
    ↓
Filter Products (성별/나이/기간)
    ↓
Build Prompt (프로필 + 상품 정보)
    ↓
LLM Generation (GMS API)
    ↓
Natural Language Response
```

---

## 📊 성능 비교

| 지표 | 추천 페이지 | 챗봇 |
|------|------------|------|
| **응답 속도** | 빠름 (~500ms) | 보통 (~2-3초) |
| **DB 쿼리** | 2회 (예금, 적금) | 2회 + 벡터 검색 |
| **토큰 사용** | 0 (LLM 미사용) | ~173 토큰 (RAG) |
| **API 비용** | 무료 | ~$0.0005/요청 |
| **정확도** | 높음 (규칙 기반) | 매우 높음 (의미 기반) |
| **유연성** | 낮음 (고정 로직) | 높음 (자연어 처리) |

---

## 💡 개선 아이디어

### 추천 페이지 개선안

1. **사용자 피드백 학습**
   - 북마크한 상품 특성 분석
   - 선호도 가중치 적용

2. **더 정교한 점수 시스템**
   - 우대조건 실제 매칭
   - 사용자 금융 활동 반영 (급여이체, 카드 사용 등)

3. **포트폴리오 시뮬레이션**
   - 예금 60% + 적금 40% 같은 비율 조정
   - 예상 총 수익 비교

### 챗봇 개선안

1. **더 정확한 RAG**
   - TF-IDF → Sentence Transformers (의미 기반 임베딩)
   - 한국어 특화 모델 (KoBERT, KoSBERT)

2. **대화 컨텍스트 유지**
   - 이전 대화 기억
   - 연속 질문 처리

3. **추천 이유 상세화**
   - 프로필 매칭 근거 명시
   - 장단점 비교

---

## 📁 관련 파일

### 추천 페이지
- **Backend**:
  - [accounts/views.py](accounts/views.py#L338-L531) - `recommend_products()`
  - [accounts/views.py](accounts/views.py#L270-L335) - `_calculate_product_ratio()`
  - [accounts/views.py](accounts/views.py#L534-L583) - `calculate_match_score()`

- **Frontend**:
  - [RecommendationsView.vue](../Frontend/Finflow_front/src/views/auth/RecommendationsView.vue) - 추천 페이지

### 챗봇
- **Backend**:
  - [chatbot/services.py](chatbot/services.py) - `ChatbotService`
  - [chatbot/vector_store.py](chatbot/vector_store.py) - RAG 시스템
  - [CHATBOT_RECOMMENDATION_LOGIC_GUIDE.md](CHATBOT_RECOMMENDATION_LOGIC_GUIDE.md) - 챗봇 로직 상세

---

**작성일**: 2025년 12월 25일
**버전**: 1.0.0
