# 챗봇 개선 작업 완료 보고서

## 📋 작업 개요

**목표**: 챗봇이 "안정적인 예금 상품 추천"을 요청받았을 때 주식을 추천하는 버그 수정 및 적금 북마크 기능 추가

**완료 날짜**: 2025-12-25

**테스트 결과**: ✅ 6/6 테스트 통과 (100% 성공)

---

## 1. 수정된 파일 목록 및 변경 요약

### 1.1 Backend 파일

#### 📄 `chatbot/services.py` (핵심 수정)

**변경 위치**: 457-514줄 (약 60줄 추가/수정)

**변경 사유**:
- 기존: 단순 키워드 매칭으로 인한 오분류 (`'추천해'`가 주식/예금 양쪽에 모두 매칭)
- 개선: 점수 기반 의도 분류 시스템 도입

**주요 변경 내용**:
```python
# 개선 전 (문제 코드)
stock_keywords = ['주가', '시세', '종목', '주식', '전망', '어때', '분석', '상승', '하락', '추천해', '매수', '매도']
if result['stock_names'] or any(kw in user_message for kw in stock_keywords):
    result['intent'] = 'STOCK'  # ❌ "예금 추천해" → STOCK으로 오분류!

# 개선 후 (점수 기반 시스템)
stock_core_keywords = ['주가', '시세', '종목', '주식', '매수', '매도', '차트', '상장', '코스피', '코스닥', '거래량']
product_core_keywords = ['예금', '적금', '금리', '이자', '은행', '저축', '원금', '만기', '가입']
stability_keywords = ['안정', '안전', '보장', '확정', '원금보장']

# 점수 계산
stock_score = 0
product_score = 0

if result['stock_names']:
    stock_score += 10  # 종목명 발견 시 강력한 주식 신호

for kw in product_core_keywords:
    if kw in user_message:
        product_score += 3  # 예금/적금 키워드마다 +3점

for kw in stability_keywords:
    if kw in user_message:
        product_score += 5  # 안정성 키워드는 +5점 (더 강력한 예금 신호)

# 점수 기반 의도 결정
if stock_score > product_score:
    result['intent'] = 'STOCK'
elif product_score > stock_score:
    result['intent'] = 'PRODUCT'  # ✅ "안정적인 예금" → product_score=8 → PRODUCT
else:
    result['intent'] = 'PRODUCT'  # 동점 시 안전하게 PRODUCT
```

**개선 효과**:
- "안정적인 예금 추천" → `product_score = 8` (예금 3점 + 안정 5점) → ✅ PRODUCT로 정확히 분류
- "삼성전자 주가" → `stock_score = 13` (종목명 10점 + 주가 3점) → ✅ STOCK으로 정확히 분류
- "추천해줘" (애매한 경우) → 기본값 PRODUCT (안전)

---

#### 📄 `accounts/models.py`

**변경 위치**: 210-243줄 (34줄 추가)

**변경 사유**:
- 기존: `ProductRecommendation` 모델이 예금만 지원 (적금 북마크 불가)
- 개선: `SavingRecommendation` 모델 추가

**추가된 코드**:
```python
class SavingRecommendation(models.Model):
    """사용자별 적금 상품 추천 기록"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saving_recommendations'
    )
    product = models.ForeignKey(
        'finances.SavingProducts',  # ✅ 적금 상품 지원
        on_delete=models.CASCADE
    )

    # 추천 근거
    match_score = models.FloatField(help_text="매칭 점수 (0~100)")
    recommended_reason = models.TextField(help_text="추천 이유")

    # 사용자 액션
    is_viewed = models.BooleanField(default=False)
    is_bookmarked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'saving_recommendation'
        ordering = ['-match_score', '-created_at']
        unique_together = ('user', 'product')
```

---

#### 📄 `accounts/views.py`

**변경 위치**: 705-768줄 (기존 32줄 → 64줄로 확장)

**변경 사유**:
- 기존: 예금만 북마크 가능
- 개선: 예금/적금 모두 북마크 가능 + 명확한 에러 메시지

**주요 변경 내용**:
```python
# 개선 전
try:
    product = DepositProducts.objects.get(fin_prdt_cd=fin_prdt_cd)  # ❌ 예금만
except DepositProducts.DoesNotExist:
    return Response({'detail': '상품을 찾을 수 없습니다.'}, status=404)

# 개선 후
# 1. 먼저 예금 상품인지 확인
deposit_product = DepositProducts.objects.filter(fin_prdt_cd=fin_prdt_cd).first()
if deposit_product:
    # 예금 상품 북마크 처리
    recommendation, created = ProductRecommendation.objects.get_or_create(...)
    return Response({
        'bookmarked': recommendation.is_bookmarked,
        'product_type': 'deposit',  # ✅ 상품 타입 명시
        'message': '예금 상품이 관심상품에 추가되었습니다.'
    })

# 2. 적금 상품인지 확인
saving_product = SavingProducts.objects.filter(fin_prdt_cd=fin_prdt_cd).first()
if saving_product:
    # 적금 상품 북마크 처리
    recommendation, created = SavingRecommendation.objects.get_or_create(...)
    return Response({
        'bookmarked': recommendation.is_bookmarked,
        'product_type': 'saving',  # ✅ 상품 타입 명시
        'message': '적금 상품이 관심상품에 추가되었습니다.'
    })

# 3. 둘 다 아니면 명확한 에러
return Response({'detail': '상품을 찾을 수 없습니다. (예금/적금 모두 확인)'}, status=404)
```

**`get_bookmarked_products()` 함수 개선** (773-814줄):
```python
# 개선 전: 예금만 반환
bookmarks = ProductRecommendation.objects.filter(user=request.user, is_bookmarked=True)

# 개선 후: 예금 + 적금 통합 반환
deposit_bookmarks = ProductRecommendation.objects.filter(user=request.user, is_bookmarked=True)
saving_bookmarks = SavingRecommendation.objects.filter(user=request.user, is_bookmarked=True)

# 두 목록을 합쳐서 최신순 정렬
data = deposit_list + saving_list
data.sort(key=lambda x: x['bookmarked_at'], reverse=True)
```

---

#### 📄 데이터베이스 마이그레이션

**파일**: `accounts/migrations/0004_savingrecommendation.py`

**내용**:
```bash
$ python manage.py makemigrations accounts
Migrations for 'accounts':
  accounts\migrations\0004_savingrecommendation.py
    + Create model SavingRecommendation

$ python manage.py migrate accounts
Operations to perform:
  Apply all migrations: accounts
Running migrations:
  Applying accounts.0004_savingrecommendation... OK
```

**생성된 테이블**:
- `saving_recommendation` (적금 추천 북마크 저장)

---

## 2. 핵심 코드 개선 사항 요약

### 2.1 의도 분류 로직 개선

| 항목 | 개선 전 | 개선 후 |
|------|---------|---------|
| **분류 방법** | 단순 키워드 매칭 | 점수 기반 시스템 |
| **주식 키워드** | `'추천해'` 포함 (❌ 오분류 원인) | `'주가', '종목', '매수'` 등 명확한 키워드만 |
| **예금 키워드** | `'예금', '적금', '상품'` | `'예금', '적금', '금리', '이자', '원금'` |
| **안정성 키워드** | 없음 | `'안정', '안전', '보장'` (+5점 가산) |
| **기본값** | GENERAL | PRODUCT (더 안전) |
| **예시 입력** | "안정적인 예금 추천" → STOCK ❌ | "안정적인 예금 추천" → PRODUCT ✅ |

### 2.2 북마크 기능 개선

| 항목 | 개선 전 | 개선 후 |
|------|---------|---------|
| **지원 상품** | 예금만 | 예금 + 적금 |
| **모델** | ProductRecommendation 1개 | ProductRecommendation + SavingRecommendation |
| **에러 메시지** | "상품을 찾을 수 없습니다" | "예금/적금 모두 확인했으나 존재하지 않음" |
| **응답 정보** | `bookmarked` 필드만 | `bookmarked`, `product_type`, `message` |
| **북마크 목록** | 예금만 반환 | 예금 + 적금 통합 반환 (최신순 정렬) |

---

## 3. 테스트 시나리오 및 결과

### 테스트 파일: `test_chatbot_intent_classification.py`

#### 테스트 1: 의도 분류 정확도 (10개 케이스)

| 입력 메시지 | 예상 의도 | 실제 의도 | 결과 |
|-------------|----------|-----------|------|
| "안정적인 예금 상품 추천해줘" | PRODUCT | PRODUCT | ✅ PASS |
| "금리 높은 적금 알려줘" | PRODUCT | PRODUCT | ✅ PASS |
| "원금보장되는 상품 찾아줘" | PRODUCT | PRODUCT | ✅ PASS |
| "은행 적금 추천" | PRODUCT | PRODUCT | ✅ PASS |
| "삼성전자 주가 어때?" | STOCK | STOCK | ✅ PASS |
| "카카오 주식 전망은?" | STOCK | STOCK | ✅ PASS |
| "005930 종목 분석해줘" | STOCK | STOCK | ✅ PASS |
| "코스피 상승세는?" | STOCK | STOCK | ✅ PASS |
| "저축 상품 추천해줘" | PRODUCT | PRODUCT | ✅ PASS |
| "투자 상품 알려줘" | PRODUCT | PRODUCT | ✅ PASS |

**결과**: 10/10 통과 (100%)

---

#### 테스트 2: 핵심 케이스 - "안정적인 예금 상품 추천"

**입력**: `"안정적인 예금 상품 추천해줘"`

**분석 과정**:
```
[DEBUG] 금융상품 핵심 키워드 '예금' 감지 → product_score +3
[DEBUG] 안정성 키워드 '안정' 감지 → product_score +5
[DEBUG] 최종 점수 - stock_score: 0, product_score: 8
[DEBUG] 의도 분류: PRODUCT (점수 우위)
```

**결과**: ✅ PASS - 예금/적금 추천 의도로 정확히 분류됨

---

#### 테스트 3: 애매한 입력 → 기본값 PRODUCT

| 입력 | 의도 | 결과 |
|------|------|------|
| "추천해줘" | PRODUCT | ✅ PASS (기본값 적용) |
| "뭐가 좋아?" | PRODUCT | ✅ PASS (기본값 적용) |
| "도와줘" | PRODUCT | ✅ PASS (기본값 적용) |

**결과**: 3/3 통과

---

#### 테스트 4: 예금 북마크 (기존 기능 유지)

**테스트 대상**: WON플러스예금 (코드: WR0001B)

**API 응답**:
```json
{
  "bookmarked": true,
  "product_type": "deposit",
  "message": "예금 상품이 관심상품에 추가되었습니다."
}
```

**결과**: ✅ PASS - 예금 북마크 성공

---

#### 테스트 5: 적금 북마크 (신규 기능)

**테스트 대상**: 우리SUPER청년도약적금 (코드: WR0001F)

**API 응답**:
```json
{
  "bookmarked": true,
  "product_type": "saving",
  "message": "적금 상품이 관심상품에 추가되었습니다."
}
```

**결과**: ✅ PASS - 적금 북마크 성공

---

#### 테스트 6: 북마크 토글 (추가 → 제거 → 추가)

**토글 결과**:
- 1회차: True (추가)
- 2회차: False (제거)
- 3회차: True (추가)

**결과**: ✅ PASS - 북마크 토글 정상 작동

---

### 📊 최종 테스트 결과

```
[PASS]: 의도 분류
[PASS]: 핵심 케이스 (안정적인 예금)
[PASS]: 애매한 입력 기본값
[PASS]: 예금 북마크
[PASS]: 적금 북마크
[PASS]: 북마크 토글

================================================================================
전체 결과: 6/6 성공
[SUCCESS] 모든 테스트 통과! 챗봇 개선 성공!
================================================================================
```

---

## 4. 개선 효과

### 4.1 의도 분류 개선

**문제 상황**:
```
사용자: "안정적인 예금 상품 추천해줘"
챗봇: [삼성전자 주식 추천 내용] ❌
```

**개선 후**:
```
사용자: "안정적인 예금 상품 추천해줘"
챗봇: [예금/적금 상품 추천 내용] ✅
```

### 4.2 북마크 기능 확장

**문제 상황**:
- 챗봇이 적금 상품 추천 → 사용자가 '관심상품 담기' 클릭 → ❌ 실패 (404 에러)

**개선 후**:
- 챗봇이 적금 상품 추천 → 사용자가 '관심상품 담기' 클릭 → ✅ 성공
- 명확한 성공/실패 메시지 제공
- 마이페이지에서 예금/적금 북마크 통합 조회 가능

---

## 5. 추가 개선 가능 사항 (향후 계획)

### 5.1 머신러닝 기반 의도 분류

현재는 키워드 점수 기반이지만, 사용자의 실제 클릭/선택 데이터를 학습하여 더 정확한 분류 가능:
- TF-IDF + Logistic Regression
- BERT 기반 문장 임베딩
- 사용자 피드백 학습 (클릭하지 않은 추천 = 잘못된 분류)

### 5.2 문맥 고려 의도 분류

현재는 단일 메시지만 분석하지만, 대화 문맥 고려:
```
사용자: "삼성전자 주가 어때?" (STOCK)
챗봇: [주가 정보]
사용자: "더 안정적인 거 없어?" (현재: PRODUCT, 하지만 문맥상 STOCK이 맞음)
```

### 5.3 통합 Recommendation 모델

현재는 `ProductRecommendation`(예금)과 `SavingRecommendation`(적금)이 분리되어 있지만, Django ContentType을 사용하여 통합 가능:
```python
from django.contrib.contenttypes.fields import GenericForeignKey

class UnifiedRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=50)
    product = GenericForeignKey('content_type', 'object_id')  # 예금/적금/주식 모두 지원
```

---

## 6. 기존 기능 유지 확인

✅ 모든 기존 기능 정상 작동 확인:
- 예금 추천 API (`/api/accounts/recommend-products/`)
- 주식 추천 API (챗봇 내부)
- 뉴스 검색 기능
- 사용자 프로필 기반 추천 로직 (SMART_RECOMMENDATION_LOGIC.md)
- 예금 북마크 기능 (기존 사용자 영향 없음)

---

## 7. 실행 방법

### 7.1 데이터베이스 마이그레이션 적용 (이미 완료)

```bash
cd Backend
python manage.py makemigrations accounts
python manage.py migrate accounts
```

### 7.2 테스트 실행

```bash
cd Backend
python test_chatbot_intent_classification.py
```

### 7.3 서버 재시작

```bash
python manage.py runserver
```

---

## 8. 요약

### 수정된 파일 (3개)
1. `chatbot/services.py` - 의도 분류 로직 개선 (점수 기반 시스템)
2. `accounts/models.py` - SavingRecommendation 모델 추가
3. `accounts/views.py` - 예금/적금 통합 북마크 API

### 추가된 파일 (2개)
1. `test_chatbot_intent_classification.py` - 종합 테스트
2. `accounts/migrations/0004_savingrecommendation.py` - DB 마이그레이션

### 테스트 결과
- **6/6 테스트 통과 (100%)**
- 의도 분류 정확도: 10/10
- 핵심 버그 수정 완료: "안정적인 예금 추천" → ✅ 예금 추천
- 적금 북마크 기능 추가: ✅ 정상 작동

### 핵심 개선 사항
1. ✅ "안정적인 예금 상품 추천" → 주식 추천하는 버그 수정
2. ✅ 적금 북마크 기능 추가 (예금만 가능했던 문제 해결)
3. ✅ 점수 기반 의도 분류로 정확도 향상
4. ✅ 명확한 에러 메시지 및 상품 타입 구분
5. ✅ 기존 기능 100% 유지

---

**작업 완료일**: 2025-12-25
**테스트 결과**: ✅ 모든 테스트 통과
**배포 준비**: ✅ 완료
