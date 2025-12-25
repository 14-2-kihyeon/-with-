# 적금 북마크 버그 수정

## 문제 설명

챗봇에서 추천받은 금융 상품을 관심상품에 추가할 때:
- ✅ **예금 상품**: 마이페이지에 정상 표시됨
- ❌ **적금 상품**: 북마크는 되지만 마이페이지에 표시되지 않음

## 원인 분석

### 북마크 저장 (정상 작동)
`accounts/views.py` - `bookmark_recommendation()` 함수:
- 예금: `ProductRecommendation` 모델에 저장 ✅
- 적금: `SavingRecommendation` 모델에 저장 ✅

### 마이페이지 조회 (버그 위치)
`accounts/views.py` - `get_mypage_data()` 함수 (라인 1038-1056):
```python
# 기존 코드 (버그)
bookmarked_products = []
product_bookmarks = ProductRecommendation.objects.filter(
    user=user,
    is_bookmarked=True
).select_related('product')

for bookmark in product_bookmarks:
    # 예금만 조회, 적금 누락!
    ...
```

**문제**: `ProductRecommendation`만 조회하고 `SavingRecommendation`을 조회하지 않음

## 해결 방법

### 수정된 코드 (`accounts/views.py` 라인 1038-1085)

```python
# 2. 북마크한 금융 상품 (예금 + 적금)
bookmarked_products = []

# 예금 북마크
product_bookmarks = ProductRecommendation.objects.filter(
    user=user,
    is_bookmarked=True
).select_related('product')

for bookmark in product_bookmarks:
    product = bookmark.product
    best_option = product.options.order_by('-intr_rate2').first()

    bookmarked_products.append({
        'fin_prdt_cd': product.fin_prdt_cd,
        'kor_co_nm': product.kor_co_nm,
        'fin_prdt_nm': product.fin_prdt_nm,
        'product_type': 'deposit',  # 타입 명시
        'max_rate': f"{best_option.intr_rate2:.2f}%" if best_option and best_option.intr_rate2 else "정보없음",
        'bookmarked_at': bookmark.created_at,
    })

# 적금 북마크 (새로 추가)
from .models import SavingRecommendation
from finances.models import SavingOptions

saving_bookmarks = SavingRecommendation.objects.filter(
    user=user,
    is_bookmarked=True
).select_related('product')

for bookmark in saving_bookmarks:
    product = bookmark.product
    best_option = SavingOptions.objects.filter(product=product).order_by('-intr_rate2').first()

    bookmarked_products.append({
        'fin_prdt_cd': product.fin_prdt_cd,
        'kor_co_nm': product.kor_co_nm,
        'fin_prdt_nm': product.fin_prdt_nm,
        'product_type': 'saving',  # 타입 명시
        'max_rate': f"{best_option.intr_rate2:.2f}%" if best_option and best_option.intr_rate2 else "정보없음",
        'bookmarked_at': bookmark.created_at,
    })

# 북마크 시간 기준 최신순 정렬
bookmarked_products.sort(key=lambda x: x['bookmarked_at'], reverse=True)
```

### 주요 변경사항

1. **적금 북마크 조회 추가**
   - `SavingRecommendation` 모델에서 북마크 조회
   - `SavingOptions`에서 최고 금리 옵션 조회

2. **상품 타입 필드 추가**
   - `product_type`: `'deposit'` 또는 `'saving'`
   - 프론트엔드에서 예금/적금 구분 가능

3. **통합 정렬**
   - 예금과 적금을 함께 북마크 시간 기준으로 최신순 정렬

## 테스트 결과

### 테스트 1: 적금 북마크 기본 기능
```bash
python test_saving_bookmark_fix.py
```

**결과**: ✅ 성공
- 적금 상품 3개 북마크됨
- 마이페이지에서 예금 3개 + 적금 3개 = 총 6개 표시
- `product_type` 필드로 예금/적금 구분 가능

### 테스트 2: 챗봇 → 마이페이지 통합 플로우
```bash
python test_chatbot_to_mypage_integration.py
```

**시나리오**:
1. 챗봇에게 "금리 좋은 예금과 적금 상품 추천해줘" 질문
2. 추천받은 예금 1개, 적금 1개 북마크
3. 마이페이지에서 확인

**결과**: ✅ 성공
- 예금 상품 'e-그린세이브예금' 마이페이지에 표시됨
- 적금 상품 'KB 특★한 적금' 마이페이지에 표시됨
- 전체 플로우 정상 작동

## 영향 범위

### 수정된 파일
- `accounts/views.py` (1줄 수정, 29줄 추가)

### 영향받는 기능
- ✅ 마이페이지 관심상품 목록
- ✅ 챗봇 추천 상품 북마크 → 마이페이지 연동

### 프론트엔드 호환성
기존 프론트엔드 코드와 완전 호환됨:
- 기존 필드는 모두 유지 (`fin_prdt_cd`, `kor_co_nm`, `fin_prdt_nm`, `max_rate`, `bookmarked_at`)
- 새로운 필드 추가: `product_type` (선택적으로 사용 가능)

## 배포 체크리스트

- [x] 버그 원인 파악
- [x] 코드 수정
- [x] 테스트 스크립트 작성
- [x] 단위 테스트 통과
- [x] 통합 테스트 통과
- [ ] 프론트엔드 확인 (선택사항: `product_type` 필드 활용)
- [ ] 프로덕션 배포

## 관련 파일

### 백엔드
- `accounts/views.py` - `get_mypage_data()` 함수 수정
- `accounts/models.py` - `ProductRecommendation`, `SavingRecommendation` 모델
- `finances/models.py` - `SavingProducts`, `SavingOptions` 모델

### 테스트 파일
- `test_saving_bookmark_fix.py` - 적금 북마크 기본 기능 테스트
- `test_chatbot_to_mypage_integration.py` - 챗봇 → 마이페이지 통합 테스트

### 프론트엔드 (선택사항)
- `MyPageView.vue` - 마이페이지 컴포넌트
  - 필요시 `product_type` 필드를 활용하여 예금/적금 구분 표시 가능

## 기술적 노트

### 데이터베이스 구조
- **예금**: `DepositProducts` → `ProductRecommendation` (북마크)
- **적금**: `SavingProducts` → `SavingRecommendation` (북마크)

두 모델은 별도로 관리되므로, 각각 조회하여 통합해야 함.

### 옵션 조회 차이
- **예금**: `product.options.order_by('-intr_rate2').first()` (역참조)
- **적금**: `SavingOptions.objects.filter(product=product).order_by('-intr_rate2').first()` (정참조)

적금은 역참조 관계가 설정되어 있지 않아 직접 쿼리 필요.

## 결론

✅ **버그 수정 완료**: 적금 상품 북마크가 마이페이지에 정상 표시됨

이제 사용자가 챗봇에서 추천받은 예금/적금 상품을 모두 관심상품에 추가하고 마이페이지에서 확인할 수 있습니다.
