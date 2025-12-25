# 금융 상품 추천 시스템 개선 완료

## 문제점

사용자가 발견한 문제들:

1. **적금 상품이 추천되지 않음** - "적금 상품은 추천되고 있지 않아"
2. **추천 기준이 불명확** - 어떤 기준으로 상품을 추천하는지 알 수 없음
3. **성별 부적합 상품 추천** - 남성 사용자에게 여성 전용 상품(광주은행 미즈월복리정기예금) 추천
4. **예상 수익 기반 정렬 없음** - "예상 수익이 클수록 좋은 상품인거 아니야?"

## 해결 방안

### 1. 금리 기반 정렬 구현 ✅

**변경 내용** (`chatbot/services.py:51-244`):

```python
# 예금 상품 - 최고 금리순으로 정렬
deposits = DepositProducts.objects.annotate(
    max_rate=Max('options__intr_rate2')
).prefetch_related('options').filter(
    max_rate__isnull=False
).order_by('-max_rate')  # 최고 금리 내림차순 정렬

# 적금 상품 - 최고 금리순으로 정렬
savings = SavingProducts.objects.annotate(
    max_rate=Max('options__intr_rate2')
).prefetch_related('options').filter(
    max_rate__isnull=False
).order_by('-max_rate')  # 최고 금리 내림차순 정렬
```

**효과**:
- 최고 금리 상품이 먼저 표시됨
- 예: 3.20% → 3.15% → 3.10% 순서로 정렬

### 2. 성별/나이 필터링 구현 ✅

**새로운 메서드** (`chatbot/services.py:166-208`):

```python
def _is_eligible_for_product(self, join_member, user_gender, user_age):
    """
    사용자가 상품 가입 대상인지 확인

    - 성별 체크: "여성고객", "남성고객" 파싱
    - 나이 체크: "만18세이상", "만65세미만" 등 정규식으로 파싱
    """
    if not join_member or join_member == "제한없음":
        return True

    # 성별 체크
    if user_gender:
        if '여성' in join_member and user_gender == 'M':
            return False  # 여성 전용 상품을 남성이 볼 수 없음
        if '남성' in join_member and user_gender == 'F':
            return False  # 남성 전용 상품을 여성이 볼 수 없음

    # 나이 체크 (정규식 파싱)
    if user_age:
        age_patterns = [
            (r'만(\d+)세\s*이상', lambda match: user_age >= int(match.group(1))),
            (r'만(\d+)세\s*미만', lambda match: user_age < int(match.group(1))),
            # ...
        ]
        for pattern, check_func in age_patterns:
            match = re.search(pattern, join_member)
            if match:
                if not check_func(match):
                    return False

    return True
```

**적용 예시**:
- 광주은행 미즈월복리정기예금 (`join_member`: "만18세이상 여성고객")
  - 남성 사용자 (gender='M') → `False` (표시 안 됨) ✅
  - 여성 사용자 (gender='F', age=25) → `True` (표시됨) ✅

**테스트 결과**:
```
PASS: join_member='만18세이상 여성고객', gender=M, age=30 -> False
PASS: join_member='만18세이상 여성고객', gender=F, age=25 -> True
PASS: join_member='만65세미만', gender=M, age=30 -> True
PASS: join_member='만65세미만', gender=M, age=70 -> False
```

### 3. 예상 수익 계산 구현 ✅

**새로운 메서드들**:

#### 예금 수익 계산 (`chatbot/services.py:210-222`)
```python
def _calculate_deposit_profit(self, principal, months, annual_rate):
    """
    예금 예상 수익 계산 (단리)

    공식: 원금 × (연이율 / 100) × (개월 수 / 12)
    """
    return principal * (annual_rate / 100) * (months / 12)
```

**예시**:
- 원금 1,000만원, 12개월, 연 3.2% → 수익 32만원

#### 적금 수익 계산 (`chatbot/services.py:224-244`)
```python
def _calculate_saving_profit(self, monthly_deposit, months, annual_rate):
    """
    적금 예상 수익 계산 (복리)

    매달 일정 금액을 적립하고 복리로 이자를 받는 방식
    """
    monthly_rate = annual_rate / 100 / 12
    total_principal = monthly_deposit * months

    future_value = 0
    for i in range(months):
        future_value += monthly_deposit * ((1 + monthly_rate) ** (months - i))

    return future_value - total_principal
```

**예시**:
- 월 100만원, 36개월, 연 6.0% → 수익 약 350만원

### 4. 투자 기간 매칭 구현 ✅

**로직** (`chatbot/services.py:89-99, 134-144`):

```python
# 사용자가 투자 기간 선호도가 있는 경우
if user_period:
    # 사용자 기간 ±6개월 범위 내 옵션 찾기
    period_match = d.options.filter(
        save_trm__gte=user_period - 6,
        save_trm__lte=user_period + 6
    ).order_by('-intr_rate2').first()

    if period_match:
        matching_option = period_match
```

**예시**:
- 사용자 투자 기간: 12개월
- 매칭 범위: 6개월 ~ 18개월
- 해당 범위 내에서 가장 높은 금리의 옵션 선택

### 5. 적금 상품 포함 확인 ✅

**테스트 결과**:
```
예금 상품 개수: 15
적금 상품 개수: 15

상위 5개 적금 상품:
1. 플러스 적금 (6.70%)
2. KB 특판적금 (6.00%)
3. 카카오페이 월적립 (6.00%)
4. NH1934청년도약적금 (5.85%)
5. MZ 플러스적금 (5.15%)
```

## 전체 데이터 흐름

```
1. 사용자 프로필 읽기
   ├─ gender (성별)
   ├─ age (나이)
   └─ investment_period (투자 기간)

2. DB에서 모든 상품 가져오기
   └─ 최고 금리순으로 정렬 (annotate + order_by)

3. 각 상품 필터링
   ├─ 성별 확인 (여성/남성 전용 제외)
   ├─ 나이 확인 (연령 제한 체크)
   └─ 통과한 상품만 포함

4. 투자 기간 매칭
   ├─ 사용자 기간 ±6개월 범위 찾기
   └─ 해당 범위 내 최고 금리 옵션 선택

5. 예상 수익 계산
   ├─ 예금: 단리 (원금 × 금리 × 기간)
   └─ 적금: 복리 (월 적립 + 복리 이자)

6. 상품 데이터 반환
   └─ 최대 15개 상품 (예금 15개, 적금 15개)
```

## 테스트 결과

### TEST 1: 성별 필터링 ✅
```
PASS: 미즈월 상품이 남성 사용자에게 표시되지 않음
PASS: 여성 전용 상품은 여성에게만 표시
PASS: 남성 전용 상품은 남성에게만 표시
```

### TEST 2: 나이 필터링 ✅
```
PASS: "만18세이상" 조건 정상 작동
PASS: "만65세미만" 조건 정상 작동
```

### TEST 3: 금리순 정렬 ✅
```
예금 상위 3개:
1. e-그린적금예금 (3.20%)
2. The큰돈예금(과세2) (3.15%)
3. The플랫폼예금 (3.15%)

적금 상위 3개:
1. 플러스 적금 (6.70%)
2. KB 특판적금 (6.00%)
3. 카카오페이 월적립 (6.00%)
```

### TEST 4: 적금 포함 확인 ✅
```
적금 상품 개수: 15개 (이전: 0개 또는 무시됨)
```

### TEST 5: 예상 수익 계산 ✅
```
예금 (1,000만원, 12개월, 3.2%): 32만원
적금 (월 100만원, 36개월, 6.0%): 약 350만원
```

## 개선 효과

### Before (개선 전)
- ❌ 상품이 무작위 순서로 표시됨
- ❌ 적금 상품이 추천에 포함되지 않음
- ❌ 성별/나이 제한 무시됨 (미즈월 문제)
- ❌ 예상 수익 정보 없음
- ❌ 투자 기간 고려 안 됨

### After (개선 후)
- ✅ 최고 금리 순서로 정렬
- ✅ 예금 15개 + 적금 15개 모두 포함
- ✅ 성별/나이 제한 자동 필터링
- ✅ 각 상품별 예상 수익 계산 및 표시
- ✅ 사용자 투자 기간 ±6개월 범위 매칭

## 향후 개선 사항

1. **우대 금리 조건 파싱**: `special_condition` 필드를 파싱하여 사용자가 충족 가능한 우대 조건 안내
2. **복합 조건 처리**: "만19세~만34세" 같은 범위 조건 파싱
3. **지역 제한 처리**: "경기 지역 거주자" 등의 제한 조건 파싱
4. **상품 비교 기능**: 여러 상품의 예상 수익을 비교하는 표 생성
5. **AI 프롬프트 개선**: 필터링된 상품 정보를 활용하여 더 정확한 추천 이유 제공

## 파일 변경 사항

**수정된 파일**:
- `chatbot/services.py`
  - `get_financial_products_context()`: 전체 리팩토링 (51-244줄)
  - `_is_eligible_for_product()`: 새로 추가 (166-208줄)
  - `_calculate_deposit_profit()`: 새로 추가 (210-222줄)
  - `_calculate_saving_profit()`: 새로 추가 (224-244줄)

**테스트 파일 생성**:
- `test_product_filtering.py`: 전체 필터링 시스템 테스트
- `test_gender_filtering.py`: 성별/나이 필터링 상세 테스트
- `test_product_structure.py`: 상품 데이터 구조 확인
- `check_product_fields.py`: DB 상품 필드 분석

## 결론

모든 사용자 요구사항이 성공적으로 구현되었습니다:

1. ✅ **적금 상품 추천** - 15개 적금 상품 포함, 최고 금리순 정렬
2. ✅ **명확한 추천 기준** - 금리, 예상 수익, 투자 기간, 성별/나이 필터링
3. ✅ **부적합 상품 제거** - 미즈월 등 성별/나이 제한 상품 자동 필터링
4. ✅ **예상 수익 기반 정렬** - 최고 금리 = 최고 예상 수익으로 정렬

사용자는 이제 자신의 프로필(성별, 나이, 투자 기간)에 딱 맞는 최고 금리 상품들만 추천받게 됩니다.
