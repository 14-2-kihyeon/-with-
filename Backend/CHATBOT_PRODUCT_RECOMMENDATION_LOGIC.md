# 챗봇 예금/적금 추천 로직 상세 가이드

## 📋 개요

챗봇이 사용자에게 예금/적금 상품을 추천할 때 사용하는 로직을 **사용자 맞춤 추천 페이지 형식**에 맞춰 정리한 문서입니다.

**파일 위치**: `chatbot/services.py`
**주요 함수**:
- `get_financial_products_context()` - 전체 상품 로드 (기존 모드)
- `get_rag_products_context()` - 질문 관련 상품만 검색 (RAG 모드)

---

## 🎯 챗봇 추천 로직 (맞춤 추천 페이지 형식)

### 1. 성별/나이 필터링

**함수**: `_is_eligible_for_product(join_member, user_gender, user_age)`

```python
# 상품의 가입 대상 확인
if not self._is_eligible_for_product(d.join_member, user_gender, user_age):
    continue
```

**로직**:
- 사용자 프로필에서 성별(`gender`)과 나이(`age`) 추출
- 상품의 `join_member` 필드와 비교하여 가입 가능 여부 확인
- 예: "청년 전용" 상품은 만 19~34세만 추천
- 예: "여성 전용" 상품은 여성 사용자에게만 추천

**위치**: [chatbot/services.py:74-76](c:\Users\kint_\Desktop\pjt\-with-\Backend\chatbot\services.py#L74-L76) (예금), [chatbot/services.py:122-124](c:\Users\kint_\Desktop\pjt\-with-\Backend\chatbot\services.py#L122-L124) (적금)

---

### 2. 투자 기간 매칭

**로직**: 사용자의 희망 투자 기간(`investment_period`)과 유사한 옵션 우선 선택

```python
# 사용자 투자 기간과 유사한 옵션 찾기 (있다면)
matching_option = best_option  # 기본값: 최고금리 옵션
if user_period:
    period_match = d.options.filter(
        save_trm__gte=user_period - 6,  # -6개월
        save_trm__lte=user_period + 6   # +6개월
    ).order_by('-intr_rate2').first()

    if period_match:
        matching_option = period_match  # 기간 일치 옵션으로 교체
```

**예시**:
- 사용자 희망 기간: 12개월
- 검색 범위: 6~18개월
- 해당 범위 내에서 최고 금리 옵션 선택
- 범위 내 옵션이 없으면 전체 옵션 중 최고 금리 선택

**위치**: [chatbot/services.py:81-89](c:\Users\kint_\Desktop\pjt\-with-\Backend\chatbot\services.py#L81-L89) (예금), [chatbot/services.py:129-137](c:\Users\kint_\Desktop\pjt\-with-\Backend\chatbot\services.py#L129-L137) (적금)

---

### 3. ~~예금/적금 비율 계산~~ (챗봇에는 없음)

**챗봇에서는 예금/적금 비율 계산 없음**

대신:
- **기존 모드**: 예금 15개 + 적금 15개를 모두 AI에게 전달
- **RAG 모드**: 사용자 질문과 유사한 상위 5개 상품만 전달

**차이점**:
| 항목 | 맞춤 추천 페이지 | 챗봇 |
|------|------------------|------|
| 예금/적금 비율 | ✅ 계산함 (저축액/기간/목표 기반) | ❌ 계산 안 함 |
| 추천 개수 | 15개 (비율에 맞춰) | 기존: 30개, RAG: 5개 |
| 선택 방법 | 알고리즘 선택 | AI가 자유롭게 선택 |

---

### 4. 최고 금리순 정렬

**로직**: DB 쿼리 단계에서 최고 금리(`intr_rate2`) 내림차순 정렬

```python
# 예금 상품 - 최고 금리순으로 정렬하여 가져오기
deposits = DepositProducts.objects.annotate(
    max_rate=Max('options__intr_rate2')  # 옵션들 중 최고 금리 계산
).prefetch_related('options').filter(
    max_rate__isnull=False
).order_by('-max_rate')  # 최고 금리 내림차순 ⭐

# 적금 상품도 동일
savings = SavingProducts.objects.annotate(
    max_rate=Max('options__intr_rate2')
).prefetch_related('options').filter(
    max_rate__isnull=False
).order_by('-max_rate')  # 최고 금리 내림차순 ⭐
```

**특징**:
- 각 상품의 모든 옵션 중 **최고 금리**를 기준으로 정렬
- 상위 15개 예금, 15개 적금만 선택 (총 30개)
- RAG 모드에서는 이미 벡터 유사도로 정렬되어 있음

**위치**: [chatbot/services.py:65-70](c:\Users\kint_\Desktop\pjt\-with-\Backend\chatbot\services.py#L65-L70) (예금), [chatbot/services.py:114-118](c:\Users\kint_\Desktop\pjt\-with-\Backend\chatbot\services.py#L114-L118) (적금)

---

### 5. ~~투자 성향별 가중치 계산~~ (챗봇에는 없음)

**챗봇에서는 투자 성향별 가중치 계산 없음**

대신:
- 사용자 프로필 정보를 AI 프롬프트에 포함
- AI가 투자 성향(`risk_type`)을 고려하여 자연어로 추천

**차이점**:
| 항목 | 맞춤 추천 페이지 | 챗봇 |
|------|------------------|------|
| 가중치 계산 | ✅ `_calculate_risk_adjusted_score()` 함수 | ❌ 없음 |
| 성향별 차별화 | ✅ 정량적 점수 (최대 22점 차이) | ✅ AI 판단 (정성적) |
| 우대조건 고려 | ✅ 복잡도 평가 함수 | ❌ AI에게 텍스트로 전달만 |
| 가입 편의성 | ✅ 편의성 점수 (0~10점) | ❌ AI에게 텍스트로 전달만 |

**AI 프롬프트 예시**:
```
사용자 투자 프로필:
- 투자 성향: timid_male (에겐소심남)
- 나이: 30세
- 투자 기간: 12개월
- 투자 목표: stable_income

위 사용자에게 적합한 예금/적금 상품을 추천해주세요.
안정형 투자자이므로 기본금리가 높고 우대조건이 단순한 상품을 추천하세요.
```

---

## 🔄 챗봇의 두 가지 모드

### 모드 1: 기존 모드 (전체 상품 로드)

**사용 시점**: RAG 시스템이 비활성화된 경우 또는 PRODUCT 의도가 아닌 경우

**함수**: `get_financial_products_context()`

**프로세스**:
1. 전체 예금 상품을 최고 금리순으로 조회
2. 성별/나이 필터링
3. 투자 기간 매칭
4. 상위 15개 선택
5. 전체 적금 상품도 동일하게 처리
6. 총 30개 상품을 AI에게 전달

**장점**: 다양한 상품 정보 제공
**단점**: 토큰 사용량 많음 (3,000~5,000 토큰)

---

### 모드 2: RAG 모드 (관련 상품만 검색) ⭐ 현재 기본값

**사용 시점**: 사용자 의도가 'PRODUCT'인 경우 (기본값)

**함수**: `get_rag_products_context(user_message, top_k=5)`

**프로세스**:
1. 사용자 질문을 TF-IDF 벡터로 변환
2. FAISS 벡터 스토어에서 유사한 상품 검색
3. 유사도 상위 5개 상품만 선택
4. DB에서 상세 정보 조회
5. 5개 상품만 AI에게 전달

**장점**:
- 토큰 93.9% 절감 (162 토큰)
- 질문과 관련성 높은 상품만 추천
- 응답 속도 빠름

**단점**:
- 벡터 검색 품질에 의존
- 다양성 낮음 (최대 5개)

**예시**:
```
사용자 질문: "안정적인 예금 상품 추천해줘"

RAG 검색 결과 (유사도순):
1. NH올원e예금 (유사도 95.2%)
2. The플러스예금 (유사도 93.8%)
3. 헤이(Hey)자유예금 (유사도 91.5%)
4. 카카오뱅크 정기예금 (유사도 89.3%)
5. e-그린세이브예금 (유사도 87.1%)

→ 이 5개만 AI에게 전달
```

**위치**: [chatbot/services.py:167-251](c:\Users\kint_\Desktop\pjt\-with-\Backend\chatbot\services.py#L167-L251)

---

## 📊 맞춤 추천 페이지 vs 챗봇 비교표

| 단계 | 맞춤 추천 페이지 | 챗봇 (기존 모드) | 챗봇 (RAG 모드) |
|------|------------------|------------------|-----------------|
| **1. 성별/나이 필터링** | ✅ 있음 | ✅ 있음 | ✅ 있음 |
| **2. 투자 기간 매칭** | ✅ ±0개월 정확 매칭 | ✅ ±6개월 유연 매칭 | ✅ ±6개월 유연 매칭 |
| **3. 예금/적금 비율** | ✅ 알고리즘 계산 | ❌ 없음 (AI 판단) | ❌ 없음 (AI 판단) |
| **4. 최고 금리순 정렬** | ~~최고 금리순~~ → 가중치 점수순 | ✅ 최고 금리순 | ❌ 유사도순 |
| **5. 투자 성향별 가중치** | ✅ 정량적 점수 계산 | ❌ AI 판단 | ❌ AI 판단 |
| **최종 추천 개수** | 15개 | AI가 선택 (보통 3~5개) | AI가 선택 (보통 3~5개) |
| **토큰 사용량** | N/A (API 미사용) | 3,000~5,000 토큰 | 162 토큰 |

---

## 🎯 챗봇 로직 상세 (5단계 형식)

### 1️⃣ 성별/나이 필터링

```python
# 위치: chatbot/services.py:74-76 (예금), 122-124 (적금)

if not self._is_eligible_for_product(d.join_member, user_gender, user_age):
    continue
```

**적용 방식**:
- ✅ 맞춤 추천과 동일
- 상품의 `join_member` 필드 검사
- 부적격 상품은 목록에서 제외

---

### 2️⃣ 투자 기간 매칭

```python
# 위치: chatbot/services.py:81-89 (예금), 129-137 (적금)

matching_option = best_option  # 기본: 최고금리 옵션
if user_period:
    period_match = d.options.filter(
        save_trm__gte=user_period - 6,
        save_trm__lte=user_period + 6
    ).order_by('-intr_rate2').first()

    if period_match:
        matching_option = period_match
```

**차이점**:
| 항목 | 맞춤 추천 페이지 | 챗봇 |
|------|------------------|------|
| 매칭 범위 | 정확히 일치하는 옵션만 | ±6개월 유연 매칭 |
| 없을 때 | 다음 우선순위 옵션 | 최고금리 옵션 선택 |

**더 유연한 매칭**: 챗봇은 사용자 질문이 다양하므로 유연하게 대응

---

### 3️⃣ ~~예금/적금 비율 계산~~ → **없음**

**챗봇에서는 예금/적금 비율을 계산하지 않습니다.**

**대신**:
- 기존 모드: 예금 15개 + 적금 15개 = 총 30개를 AI에게 전달
- RAG 모드: 상위 5개 (예금+적금 혼합)만 전달
- AI가 사용자 질문에 맞춰 적절한 개수 선택

**예시**:
```
사용자: "장기 적금 추천해줘"
→ AI가 적금 위주로 3~5개 추천

사용자: "예금과 적금을 골고루 추천해줘"
→ AI가 예금 2개 + 적금 2개 추천
```

---

### 4️⃣ 최고 금리순 정렬

```python
# 위치: chatbot/services.py:65-70 (예금), 114-118 (적금)

# 예금 상품 - 최고 금리순으로 정렬
deposits = DepositProducts.objects.annotate(
    max_rate=Max('options__intr_rate2')
).order_by('-max_rate')  # 최고 금리 내림차순
```

**적용 방식**:
- ✅ 전체 상품을 최고 금리 기준으로 정렬
- ✅ 상위 15개 선택
- ❌ 투자 성향별 재정렬 없음 (AI가 판단)

**RAG 모드에서는**:
```python
# 위치: chatbot/services.py:188

similar_products = vector_store.search(user_message, top_k=5)
```
- 벡터 유사도순으로 정렬 (금리 기준 아님)
- 사용자 질문과 가장 관련성 높은 상품 우선

---

### 5️⃣ ~~투자 성향별 가중치 계산~~ → **AI 판단**

**챗봇에서는 정량적 가중치 계산을 하지 않습니다.**

**대신 AI 프롬프트에 투자 성향 정보 포함**:

```python
# 위치: chatbot/services.py:1028-1080 (프롬프트 생성 부분)

# 사용자 프로필 정보를 AI에게 전달
user_profile = self.get_user_profile_context()

system_prompt = f"""
당신은 금융 상담 전문가입니다.

사용자 프로필:
- 투자 성향: {user_profile['risk_type']} (위험점수: {user_profile['risk_score']})
- 나이: {user_profile['age']}세
- 투자 기간: {user_profile['investment_period']}개월
- 투자 목표: {user_profile['investment_goal']}

투자 성향별 추천 가이드:
- timid (안정형): 기본금리가 높고 우대조건이 단순한 상품 추천
- normal (중립형): 균형잡힌 상품 추천
- speculative (공격형): 최고금리가 높은 상품 추천 (조건 복잡해도 OK)
"""
```

**AI가 고려하는 요소**:
- ✅ 투자 성향 (risk_type)
- ✅ 우대조건 복잡도 (텍스트 분석)
- ✅ 가입 방법 (join_way)
- ❌ 정량적 점수는 계산하지 않음

---

## 🔍 투자 성향 반영 방식 비교

### 맞춤 추천 페이지: 정량적 점수 계산

```python
# _calculate_risk_adjusted_score() 함수 사용

안정형 (timid):
- 기본금리 70% + 우대금리 30%
- 우대조건 단순할수록 +20점
- 가입 편의성 1.5배 가중

중립형 (normal):
- 기본금리 50% + 우대금리 50%
- 우대조건 적당할 때 +15점
- 가입 편의성 1.0배 가중

공격형 (speculative):
- 기본금리 30% + 우대금리 70%
- 우대조건 복잡해도 +15점
- 가입 편의성 0.8배 가중
```

**결과**: 동일 상품이라도 투자 성향에 따라 최대 22점 차이

---

### 챗봇: AI 자연어 판단

**AI 프롬프트 예시** (안정형 사용자):
```
사용자는 투자 성향이 'timid_male (에겐소심남)'입니다.
안정형 투자자이므로:
1. 기본금리가 높은 상품을 우선 추천하세요
2. 우대조건이 단순한 상품을 선호합니다
3. 인터넷/모바일 가입이 가능한 편리한 상품을 추천하세요
4. 중도해지 불이익이 적은 상품을 추천하세요

추천 상품:
1. [예금] NH올원e예금 - 기본금리 3.30%, 최고금리 3.50% (12개월)
   우대조건: 인터넷뱅킹 가입 시 0.20%p (단순함 ✅)

2. [예금] 헤이(Hey)자유예금 - 기본금리 3.00%, 최고금리 3.00% (12개월)
   우대조건: 없음 (매우 단순 ✅✅)
```

**AI 응답 예시**:
```
안녕하세요! 안정적인 투자를 선호하시는 고객님께 추천드리는 예금 상품입니다.

1. 헤이(Hey)자유예금 (카카오뱅크)
   - 기본금리 3.00%로 우대조건 없이 바로 적용됩니다
   - 모바일 앱으로 간편 가입 가능합니다
   - 중도해지 시에도 일할계산 이자를 지급받을 수 있어 안전합니다

2. NH올원e예금 (농협은행)
   - 기본금리 3.30%로 높은 편입니다
   - 인터넷뱅킹 가입이라는 단순한 조건만 충족하면 최고금리 적용 가능
```

---

## 💡 핵심 차이점 요약

| 구분 | 맞춤 추천 페이지 | 챗봇 |
|------|------------------|------|
| **목적** | 포트폴리오 구성 | 질의응답 기반 추천 |
| **추천 방식** | 알고리즘 기반 | AI 자연어 기반 |
| **예금/적금 비율** | ✅ 계산함 | ❌ AI 판단 |
| **투자 성향 반영** | ✅ 정량적 점수 (최대 100점) | ✅ 정성적 판단 |
| **우대조건 평가** | ✅ 복잡도 점수 (low/medium/high) | ❌ AI 텍스트 분석 |
| **가입 편의성** | ✅ 점수화 (0~10점) | ❌ AI 텍스트 분석 |
| **정렬 기준** | risk_adjusted_score | 최고 금리 or 유사도 |
| **추천 개수** | 정확히 15개 | AI가 선택 (3~5개) |
| **응답 형식** | JSON 배열 | 자연어 설명 + 상품 목록 |

---

## 📝 챗봇 추천 로직 전체 플로우

### 기존 모드 (전체 상품 로드)

```
1. 사용자 질문 분석
   └─> 의도 분류: PRODUCT

2. 사용자 프로필 조회
   └─> 성별: 남성, 나이: 30세, 투자 기간: 12개월, 투자 성향: timid_male

3. 예금 상품 조회
   ├─> 전체 예금 상품을 최고금리순 정렬
   ├─> 성별/나이 필터링 (30세 남성 가입 가능한 상품만)
   ├─> 투자 기간 매칭 (6~18개월 옵션 우선)
   └─> 상위 15개 선택

4. 적금 상품 조회
   ├─> 전체 적금 상품을 최고금리순 정렬
   ├─> 성별/나이 필터링
   ├─> 투자 기간 매칭
   └─> 상위 15개 선택

5. AI 프롬프트 생성
   ├─> 사용자 프로필 정보 포함
   ├─> 30개 상품 정보 포함 (예금 15 + 적금 15)
   └─> 투자 성향별 추천 가이드 포함

6. AI 응답 생성
   └─> 자연어로 3~5개 상품 추천

7. 추천 상품 메타데이터 추출
   └─> AI 응답에서 상품명 파싱하여 DB 정보 첨부
```

---

### RAG 모드 (관련 상품만 검색) ⭐ 기본값

```
1. 사용자 질문 분석
   └─> 의도 분류: PRODUCT
   └─> 질문: "안정적인 예금 상품 추천해줘"

2. 벡터 유사도 검색
   ├─> 질문을 TF-IDF 벡터로 변환
   ├─> FAISS 인덱스에서 유사한 상품 검색
   └─> 상위 5개 선택
       1. NH올원e예금 (유사도 95.2%)
       2. The플러스예금 (유사도 93.8%)
       3. 헤이(Hey)자유예금 (유사도 91.5%)
       4. 카카오뱅크 정기예금 (유사도 89.3%)
       5. e-그린세이브예금 (유사도 87.1%)

3. 상품 상세 정보 조회
   ├─> 5개 상품 코드로 DB 조회
   ├─> 최고금리 옵션 선택
   └─> 예상 수익 계산

4. AI 프롬프트 생성
   ├─> 사용자 프로필 정보 포함
   ├─> 5개 상품 정보만 포함 (토큰 93.9% 절감!)
   └─> 투자 성향별 추천 가이드 포함

5. AI 응답 생성
   └─> 자연어로 3~5개 상품 추천

6. 추천 상품 메타데이터 추출
   └─> AI 응답에서 상품명 파싱하여 DB 정보 첨부
```

---

## 🎯 챗봇이 투자 성향을 반영하는 방법

### 1. 프롬프트에 성향 정보 포함

```python
# 위치: chatbot/services.py (chat 메서드)

system_prompt = f"""
당신은 친근하고 전문적인 금융 상담 전문가입니다.

사용자 프로필:
- 투자 성향: {risk_type_korean} (위험점수: {user_profile['risk_score']})
- 나이: {user_profile['age']}세
- 연 소득: {user_profile['annual_income']}만원
- 현재 저축액: {user_profile['current_savings']}만원
- 투자 목표: {user_profile['investment_goal']}
- 희망 투자 기간: {user_profile['investment_period']}개월
"""
```

### 2. 투자 성향별 가이드 제공

```python
투자 성향별 추천 원칙:
- timid (안정형):
  * 기본금리가 높은 상품 우선
  * 우대조건이 1~2개로 단순한 상품
  * 인터넷/모바일 가입 가능한 편리한 상품
  * 중도해지 불이익이 적은 상품

- normal (중립형):
  * 기본금리와 최고금리의 균형이 좋은 상품
  * 우대조건이 3~4개 정도로 적당한 상품
  * 안정성과 수익성을 모두 고려

- speculative (공격형):
  * 최고금리가 높은 상품 우선
  * 우대조건이 5개 이상이어도 OK
  * 영업점 방문이 필요해도 OK
  * 높은 수익을 위해 복잡한 조건 수용
```

### 3. AI가 자연어로 판단

AI는 상품 정보와 투자 성향 가이드를 바탕으로:
- 우대조건 텍스트를 직접 읽고 복잡도 판단
- 가입 방법 텍스트를 읽고 편의성 판단
- 기본금리 vs 최고금리 비교하여 적합성 판단

**결과**: 정량적 점수는 없지만, 자연어 설명으로 사용자 납득도↑

---

## ⚠️ 챗봇에 가중치 계산 기능이 없는 이유

### 1. 목적의 차이
- **맞춤 추천**: 정확한 포트폴리오 구성 (알고리즘 기반)
- **챗봇**: 대화형 추천 (AI 자연어 기반)

### 2. 유연성
- 챗봇은 다양한 질문에 대응해야 함
- "예금만", "적금만", "둘 다", "단기", "장기" 등
- 고정된 알고리즘보다 AI 판단이 더 유연함

### 3. 설명 가능성
- 맞춤 추천: 점수만 제시 (예: 78.70점)
- 챗봇: 자연어 설명 제공 (예: "이 상품은 우대조건이 단순해서 안정형 투자자에게 적합합니다")

---

## 🚀 챗봇에 가중치 시스템 추가 시 고려사항

만약 챗봇에도 `_calculate_risk_adjusted_score()` 기능을 추가한다면:

### 장점
- ✅ 더 정확한 투자 성향별 추천
- ✅ 일관된 추천 기준
- ✅ 맞춤 추천 페이지와 동일한 상품 추천 가능

### 단점
- ❌ 토큰 사용량 증가 (점수 정보 추가)
- ❌ 유연성 감소 (AI 판단 여지 축소)
- ❌ 복잡도 증가

### 구현 방법 (예시)
```python
# chatbot/services.py에 추가

from accounts.views import _calculate_risk_adjusted_score

def get_rag_products_context_with_scores(self, user_message, top_k=5):
    """
    RAG 검색 + 가중치 점수 계산
    """
    similar_products = vector_store.search(user_message, top_k=top_k)
    user_profile = self.user.investment_profile

    context = ""
    for item in similar_products:
        product = get_product_from_db(item['fin_prdt_cd'])
        option = product.options.order_by('-intr_rate2').first()

        # 가중치 점수 계산 ⭐
        score = _calculate_risk_adjusted_score(user_profile, product, option)

        context += f"[예금] {product.fin_prdt_nm}\n"
        context += f"  투자 성향 적합도: {score:.1f}점 / 100점\n"
        context += f"  최고 금리: {option.intr_rate2:.2f}%\n\n"

    return context
```

---

## 📝 최종 정리

### 챗봇 예금/적금 추천 로직 (5단계 형식)

1. **성별/나이 필터링** ✅
   - 맞춤 추천과 동일하게 적용

2. **투자 기간 매칭** ✅ (더 유연)
   - ±6개월 범위로 유연하게 매칭

3. **예금/적금 비율** ❌
   - 계산하지 않음
   - AI가 질문에 맞춰 자유롭게 선택

4. **최고 금리순 정렬** ✅ (기존 모드) / ❌ (RAG 모드)
   - 기존 모드: 최고 금리순
   - RAG 모드: 벡터 유사도순

5. **투자 성향별 가중치** ❌ (정량) / ✅ (정성)
   - 정량적 점수 계산은 없음
   - AI가 프롬프트 기반으로 정성적 판단

### 맞춤 추천 vs 챗봇 요약

- **맞춤 추천**: 정확한 알고리즘 기반 포트폴리오
- **챗봇**: 유연한 AI 기반 대화형 추천

두 시스템은 **서로 보완적**입니다:
- 맞춤 추천: 체계적인 자산 배분이 필요할 때
- 챗봇: 빠른 질의응답과 설명이 필요할 때

---

**작성일**: 2025년 12월 25일
**버전**: v1.0.0
**참고 문서**:
- [CHATBOT_RECOMMENDATION_LOGIC_GUIDE.md](CHATBOT_RECOMMENDATION_LOGIC_GUIDE.md)
- [RECOMMENDATIONS_VS_CHATBOT_COMPARISON.md](RECOMMENDATIONS_VS_CHATBOT_COMPARISON.md)
- [RISK_ADJUSTED_SCORING_IMPLEMENTATION.md](RISK_ADJUSTED_SCORING_IMPLEMENTATION.md)
