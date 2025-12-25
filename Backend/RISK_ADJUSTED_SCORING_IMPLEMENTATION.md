# 투자 성향별 가중치 적용 추천 시스템 구현 완료

## 📋 개요

RecommendationsView 맞춤 추천 페이지에 투자 성향별 가중치 로직을 추가하여, 동일한 금융 상품이라도 사용자의 투자 성향(안정형/중립형/공격형)에 따라 다른 점수를 부여하고 순위를 매기도록 개선했습니다.

**구현 일자**: 2025년 12월 25일
**버전**: v1.2.0
**상태**: ✅ 완료 및 테스트 통과

---

## 🎯 문제 정의

### 기존 시스템의 한계

**문제점**: RecommendationsView에서 예금/적금 상품을 추천할 때, 단순히 `max_rate` (최고금리)만으로 정렬하여 추천했습니다.

```python
# 기존 코드 (문제)
all_recommendations.sort(key=lambda x: x['max_rate'], reverse=True)
```

이 방식의 문제:
- **안정형 사용자**에게도 우대조건이 복잡한 고금리 상품이 최우선 추천됨
- **공격형 사용자**에게도 조건 단순한 저금리 상품이 섞여서 추천됨
- 사용자의 투자 성향이 전혀 반영되지 않음

### 사용자 요구사항

```
안정형: 실현가능금리(기본금리 비중↑) 중시, 우대조건 단순, 가입 편의성 중요
중립형: 기본금리와 최고금리 균형, 모든 요소 균형있게 평가
공격형: 최고금리(우대금리 비중↑) 중시, 복잡한 조건 수용 가능, 편의성 덜 중요
```

---

## ✅ 구현 내용

### 1. 새로 추가된 함수 (accounts/views.py)

#### `_evaluate_condition_complexity(spcl_cnd)` (라인 268-290)

우대조건의 복잡도를 'low', 'medium', 'high'로 평가합니다.

```python
def _evaluate_condition_complexity(spcl_cnd):
    """
    우대조건 복잡도 평가

    Returns:
        str: 'low' (조건 1~2개), 'medium' (3~4개), 'high' (5개 이상)
    """
    if not spcl_cnd or len(spcl_cnd.strip()) < 10:
        return 'low'

    condition_markers = ['\n', '1.', '2.', '3.', '4.', '5.', '-', '•']
    condition_count = sum(spcl_cnd.count(marker) for marker in condition_markers)

    if condition_count <= 2:
        return 'low'
    elif condition_count <= 4:
        return 'medium'
    else:
        return 'high'
```

**로직**:
- 조건 구분 마커(`\n`, `1.`, `2.` 등)의 개수를 세어 복잡도 판단
- 조건이 없거나 10자 미만이면 'low'
- 2개 이하: 'low', 3~4개: 'medium', 5개 이상: 'high'

---

#### `_evaluate_join_convenience(join_way)` (라인 293-318)

가입 방법의 편의성을 0~10점으로 평가합니다.

```python
def _evaluate_join_convenience(join_way):
    """
    가입 방법 편의성 평가

    Returns:
        int: 편의성 점수 (0~10점)
    """
    if not join_way:
        return 0

    join_way_lower = join_way.lower()
    score = 0

    if '인터넷' in join_way or '모바일' in join_way or '스마트폰' in join_way or 'app' in join_way_lower:
        score += 10  # 비대면 가입 가능
    elif '영업점' in join_way or '창구' in join_way:
        score += 3   # 방문 필요
    else:
        score += 5   # 기타

    return min(score, 10)
```

**로직**:
- 인터넷/모바일 가입: 10점 (최고 편의성)
- 영업점 방문: 3점 (불편)
- 기타: 5점 (중간)

---

#### `_calculate_risk_adjusted_score(profile, product, option)` (라인 321-437)

**핵심 함수**: 투자 성향에 따라 상품에 대한 가중치 점수(0~100점)를 계산합니다.

```python
def _calculate_risk_adjusted_score(profile, product, option):
    """
    투자 성향에 따른 가중치 적용 점수 계산

    안정형 (timid_male, timid_female):
    - 기본금리 가중치 높음 (70%)
    - 우대조건 간단할수록 가산점
    - 가입 편의성 중요

    중립형 (normal_male, normal_female):
    - 기본금리 + 우대금리 균형 (50% / 50%)
    - 모든 요소 균형있게 평가

    공격형 (speculative_male, speculative_female):
    - 최고금리 가중치 높음 (70%)
    - 우대조건 복잡해도 OK
    - 가입 편의성 덜 중요

    Returns:
        float: 위험 조정 점수 (0~100)
    """
```

**점수 구성 (총 100점)**:

| 항목 | 안정형 | 중립형 | 공격형 | 배점 |
|------|--------|--------|--------|------|
| **금리 점수** | 기본 70% + 우대 30% | 기본 50% + 우대 50% | 기본 30% + 우대 70% | 50점 |
| **우대조건 복잡도** | 간단할수록 선호 | 적당한 조건 선호 | 복잡해도 OK | 20점 |
| **가입 편의성** | 1.5배 가중 | 1.0배 가중 | 0.8배 가중 | 15점 |
| **투자 기간 일치도** | 일치도에 따라 | 일치도에 따라 | 일치도에 따라 | 15점 |

**코드 예시 - 금리 점수 계산**:

```python
# risk_type을 일반 카테고리로 매핑
if 'timid' in risk_type:
    risk_category = 'conservative'
elif 'speculative' in risk_type:
    risk_category = 'aggressive'
else:  # 'normal' in risk_type
    risk_category = 'moderate'

# 금리 점수 계산
basic_rate = float(option.intr_rate) if option.intr_rate else 0
max_rate = float(option.intr_rate2) if option.intr_rate2 else 0

if risk_category == 'conservative':
    weighted_rate = (basic_rate * 0.7 + max_rate * 0.3)
elif risk_category == 'aggressive':
    weighted_rate = (basic_rate * 0.3 + max_rate * 0.7)
else:
    weighted_rate = (basic_rate * 0.5 + max_rate * 0.5)

rate_score = weighted_rate * 10
base_score += min(rate_score, 50)
```

---

### 2. 수정된 recommend_products 함수

#### 예금 추천 루프 (라인 567-595)

```python
# 투자 성향 기반 가중치 점수 계산
risk_adjusted_score = _calculate_risk_adjusted_score(profile, d, matching_option)

deposit_recommendations.append({
    'type': 'deposit',
    'product': {...},
    'option': {...},
    'expected_profit': expected_profit,
    'max_rate': rate,
    'risk_adjusted_score': risk_adjusted_score,  # ✅ 추가
})
```

#### 적금 추천 루프 (라인 625-653)

```python
# 투자 성향 기반 가중치 점수 계산
risk_adjusted_score = _calculate_risk_adjusted_score(profile, s, matching_option)

saving_recommendations.append({
    'type': 'saving',
    'product': {...},
    'option': {...},
    'expected_profit': expected_profit,
    'max_rate': rate,
    'risk_adjusted_score': risk_adjusted_score,  # ✅ 추가
})
```

#### 정렬 로직 변경 (라인 672-673)

```python
# ❌ 기존 (max_rate로 정렬)
all_recommendations.sort(key=lambda x: x['max_rate'], reverse=True)

# ✅ 수정 (risk_adjusted_score로 정렬)
all_recommendations.sort(key=lambda x: x['risk_adjusted_score'], reverse=True)
```

#### match_score 계산 변경 (라인 681)

```python
# ❌ 기존 (max_rate * 10)
'match_score': rec['max_rate'] * 10

# ✅ 수정 (risk_adjusted_score 사용)
'match_score': rec['risk_adjusted_score']
```

---

## 📊 테스트 결과

### 테스트 스크립트: `test_risk_adjusted_recommendations.py`

3가지 투자 성향(안정형/중립형/공격형) 사용자에 대해 동일 조건으로 추천 상품을 조회하고 점수 차이를 비교합니다.

### 실행 결과

```bash
python test_risk_adjusted_recommendations.py
```

#### 1. 안정형 (에겐소심남) - 상위 5개

| 순위 | 상품명 | 기본금리 | 최고금리 | 점수 |
|------|--------|----------|----------|------|
| 1 | The파트너예금 | 2.75% | 3.15% | 78.70 |
| 2 | MZ 플랜적금 | 2.95% | 4.95% | 75.50 |
| 3 | 헤이(Hey)정기예금 | 3.00% | 3.00% | 73.00 |
| 4 | 카카오뱅크 정기예금 | 2.95% | 2.95% | 72.50 |
| 5 | e-그린세이브예금 | 2.90% | 3.20% | 69.90 |

**특징**:
- "헤이(Hey)정기예금"과 "카카오뱅크 정기예금"은 우대조건이 없거나 단순함
- 기본금리가 높은 상품들이 상위권

---

#### 2. 중립형 (보통남) - 상위 5개

| 순위 | 상품명 | 기본금리 | 최고금리 | 점수 |
|------|--------|----------|----------|------|
| 1 | MZ 플랜적금 | 2.95% | 4.95% | 79.50 |
| 2 | NH1934월복리적금 | 2.30% | 5.80% | 73.50 |
| 3 | e-그린세이브예금 | 2.90% | 3.20% | 70.50 |
| 4 | KB 특★한 적금 | 2.00% | 6.00% | 66.00 |
| 5 | The든든예금(시즌2) | 2.00% | 3.15% | 65.75 |

**특징**:
- 기본금리와 최고금리의 균형이 좋은 "MZ 플랜적금"이 1위
- 최고금리가 높은 적금 상품들이 상위권 진입

---

#### 3. 공격형 (테토투기남) - 상위 5개

| 순위 | 상품명 | 기본금리 | 최고금리 | 점수 |
|------|--------|----------|----------|------|
| 1 | NH1934월복리적금 | 2.30% | 5.80% | 85.50 |
| 2 | KB 특★한 적금 | 2.00% | 6.00% | 79.00 |
| 3 | MZ 플랜적금 | 2.95% | 4.95% | 76.50 |
| 4 | 카카오뱅크 한달적금 | 0.50% | 6.00% | 70.50 |
| 5 | JB 123 정기예금 | 2.60% | 3.10% | 67.50 |

**특징**:
- 최고금리가 가장 높은 "KB 특★한 적금" (6.00%)이 2위
- "NH1934월복리적금" (5.80%)이 1위 - 복잡한 조건이지만 고금리
- "카카오뱅크 한달적금"처럼 기본금리 0.50%여도 최고금리 6.00%이면 추천됨

---

### 동일 상품 점수 비교

| 상품명 | 안정형 | 중립형 | 공격형 |
|--------|--------|--------|--------|
| The파트너예금 | 78.70 | 62.50 | 58.30 |
| MZ 플랜적금 | 75.50 | 79.50 | 76.50 |
| 헤이(Hey)정기예금 | 73.00 | 56.00 | 51.00 |

**분석**:
1. **The파트너예금**: 안정형에서 78.70점으로 1위, 공격형에서는 58.30점으로 크게 하락
   - 이유: 기본금리 2.75%로 준수하지만, 최고금리 3.15%로 공격형 선호도↓

2. **MZ 플랜적금**: 모든 성향에서 고르게 높은 점수 (75.50 → 79.50 → 76.50)
   - 이유: 기본금리 2.95%, 최고금리 4.95%로 균형적

3. **헤이(Hey)정기예금**: 안정형 73.00점, 공격형 51.00점
   - 이유: 우대조건 없고 기본금리=최고금리=3.00%, 안정형에게 매력적

---

## 🎯 핵심 성과

### 1. 투자 성향별 맞춤 추천 실현

- **안정형**: 우대조건 단순하고 기본금리 높은 상품 우선 추천
- **중립형**: 균형잡힌 금리 구조의 상품 추천
- **공격형**: 최고금리 높은 상품 우선 추천 (조건 복잡해도 OK)

### 2. 정량적 차별화

동일 상품이라도 투자 성향에 따라 **최대 22점 차이** 발생:
- "헤이(Hey)정기예금": 안정형 73.00점 vs 공격형 51.00점 (차이: 22.00점)
- "The파트너예금": 안정형 78.70점 vs 공격형 58.30점 (차이: 20.40점)

### 3. 순위 변동

| 상품 | 안정형 순위 | 중립형 순위 | 공격형 순위 |
|------|-------------|-------------|-------------|
| The파트너예금 | 1위 | 순위권 외 | 순위권 외 |
| NH1934월복리적금 | 순위권 외 | 2위 | 1위 |
| KB 특★한 적금 | 순위권 외 | 4위 | 2위 |

---

## 📁 파일 변경 사항

### 수정된 파일

- **[accounts/views.py](accounts/views.py)**
  - `_evaluate_condition_complexity()` 함수 추가 (라인 268-290)
  - `_evaluate_join_convenience()` 함수 추가 (라인 293-318)
  - `_calculate_risk_adjusted_score()` 함수 추가 (라인 321-437)
  - `recommend_products()` 함수 수정:
    - 예금 추천 루프에 risk_adjusted_score 계산 추가 (라인 567-595)
    - 적금 추천 루프에 risk_adjusted_score 계산 추가 (라인 625-653)
    - 정렬 로직 변경: max_rate → risk_adjusted_score (라인 672-673)
    - match_score 계산 변경 (라인 681)

### 새로 생성된 파일

- **[test_risk_adjusted_recommendations.py](test_risk_adjusted_recommendations.py)**
  - 3가지 투자 성향별 추천 상품 테스트 스크립트
  - 동일 상품에 대한 점수 비교 기능
  - 순위 변동 분석 기능

- **[RISK_ADJUSTED_SCORING_IMPLEMENTATION.md](RISK_ADJUSTED_SCORING_IMPLEMENTATION.md)** (이 문서)
  - 전체 구현 내용 및 테스트 결과 문서

---

## 🚀 배포 가이드

### 1. 변경 사항 확인

```bash
cd c:\Users\kint_\Desktop\pjt\-with-\Backend
git diff accounts/views.py
```

### 2. 서버 재시작

```bash
python manage.py runserver
```

### 3. 테스트 실행

```bash
# 투자 성향별 추천 테스트
python test_risk_adjusted_recommendations.py

# 기존 챗봇 테스트도 함께 실행 (호환성 확인)
python test_quick_chatbot.py
python test_multiple_questions.py
```

---

## ⚠️ 주의 사항

### 1. 기존 기능 영향

- **영향 없음**: STOCK, NEWS, GENERAL 추천은 기존 로직 그대로 유지
- **변경됨**: PRODUCT 추천만 새로운 가중치 시스템 적용
- **호환성**: 기존 챗봇 추천과 독립적으로 작동

### 2. 투자 성향 타입

시스템은 6가지 성향 타입을 지원합니다:
- `timid_male` / `timid_female` → 안정형
- `normal_male` / `normal_female` → 중립형
- `speculative_male` / `speculative_female` → 공격형

`_calculate_risk_adjusted_score()` 함수는 자동으로 이를 3가지 카테고리로 매핑합니다.

### 3. 프론트엔드 변경 필요 여부

**변경 불필요**: API 응답 구조는 기존과 동일합니다.
- `recommendations` 배열에 `risk_adjusted_score` 필드가 추가되었지만, 기존 필드는 모두 유지됨
- `match_score`는 이제 `risk_adjusted_score` 값을 반환 (기존에는 `max_rate * 10`)

프론트엔드에서 `match_score`를 표시하고 있다면, 이제 더 의미있는 점수가 표시됩니다.

---

## 📈 향후 개선 가능 사항

### 1. 추가 요소 고려

- 은행별 신뢰도 점수
- 과거 사용자 선호 데이터 학습
- 유사 사용자 패턴 분석

### 2. 동적 가중치 조정

- 사용자가 직접 우선순위 설정 가능하도록 UI 제공
- 예: "금리 70% / 편의성 30%" 슬라이더

### 3. A/B 테스트

- 기존 max_rate 정렬 vs 새로운 risk_adjusted_score 정렬
- 사용자 만족도 및 상품 가입률 비교

---

## 🎉 최종 결과

### ✅ 완료 항목

- [x] 우대조건 복잡도 평가 함수 구현
- [x] 가입 방법 편의성 평가 함수 구현
- [x] 투자 성향별 가중치 계산 함수 구현
- [x] 예금 추천에 가중치 적용
- [x] 적금 추천에 가중치 적용
- [x] 정렬 로직 변경 (max_rate → risk_adjusted_score)
- [x] match_score 계산 변경
- [x] 테스트 스크립트 작성 및 실행
- [x] 모든 테스트 통과 (3/3)
- [x] 문서화 완료

### 📊 성능 지표

- **테스트 성공률**: 100% (3/3)
- **점수 차별화**: 최대 22점 차이 발생
- **순위 변동**: 투자 성향별로 상이한 추천 순위 확인
- **코드 품질**: 함수 분리로 가독성 및 유지보수성 향상

---

**작성일**: 2025년 12월 25일
**버전**: v1.2.0
**작성자**: Claude Sonnet 4.5
**상태**: ✅ 구현 완료 및 테스트 통과
