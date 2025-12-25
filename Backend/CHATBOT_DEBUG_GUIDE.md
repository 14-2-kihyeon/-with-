# Finflow AI 챗봇 디버깅 완료 가이드

## 🎯 해결된 문제

### 1. 종목 별명/Alias 미인식 문제
**문제:** "삼전", "005930" 등 다양한 표현으로 종목을 검색하면 DB 조회 실패

**해결책:**
- `chatbot/stock_alias.py` 모듈 생성 - 주요 종목 별명 사전 구축
- `find_stock_by_alias()` 함수로 사용자 입력 정규화 및 매핑
- `analyze_user_question()` 함수에 Alias 검색 우선 적용

**테스트 케이스:**
```python
# ✅ 모두 "삼성전자"로 인식되어야 함
"삼전 어때?"
"삼성전자 어때?"
"005930 어때?"
"samsung 주가는?"
```

---

### 2. 내부 구현 문구 노출 문제
**문제:** AI 응답에 "내 DB기준", "DB에서 조회한" 등 내부 용어 포함

**해결책:**
- `build_system_prompt()` 함수의 시스템 프롬프트에서 내부 문구 제거
- `post_process_response()` 함수 추가하여 응답 후처리로 금지 문구 제거
- 사용자 친화적 표현으로 변경 (예: "최종 확인일: 2025-12-25")

**테스트 케이스:**
```python
# ❌ 응답에 아래 문구가 포함되면 안 됨
"DB기준"
"DB에서 조회한"
"내 DB"
"실제 DB"

# ✅ 대신 이런 표현 사용
"최종 확인일: 2025년 12월 25일 기준"
"2025년 12월 25일 기준으로"
```

---

### 3. 주식 질문에 예금/적금 추천 문제
**문제:** "삼성전자 어때?" 같은 주식 질문에 예금/적금 상품 리스트 출력

**해결책:**
- `analyze_user_question()` 함수에 의도 분류 로직 추가
  - `STOCK` 의도: 주식 관련 키워드 감지
  - `PRODUCT` 의도: 예금/적금 키워드 감지
  - `NEWS` 의도: 뉴스 키워드 감지
  - `GENERAL` 의도: 일반 대화
- `build_system_prompt()` 함수에 의도별 맞춤 프롬프트 생성
  - STOCK 의도 → 주식 데이터만 포함, 예금/적금 제외
  - PRODUCT 의도 → 예금/적금만 포함, 주식 제외

**테스트 케이스:**
```python
# STOCK 의도 (주식만 추천해야 함)
"삼성전자 어때?"
"지금 삼전 사도 돼?"
"SK하이닉스 전망은?"
"주식 추천해줘"

# PRODUCT 의도 (예금/적금만 추천해야 함)
"예금 상품 추천해줘"
"금리 좋은 적금 알려줘"
"은행 상품 추천"

# NEWS 의도
"삼성전자 뉴스 알려줘"
"경제 뉴스 검색"
```

---

## 📁 수정된 파일 목록

### 신규 파일
1. **`chatbot/stock_alias.py`**
   - 종목 별명 사전 및 정규화 함수
   - `STOCK_ALIASES`: 주요 종목 별명 매핑
   - `find_stock_by_alias()`: 사용자 입력에서 종목 추출
   - `normalize_stock_query()`: 쿼리 정규화

### 수정된 파일
2. **`chatbot/services.py`**
   - `analyze_user_question()`: Alias 검색 + 의도 분류 추가
   - `build_system_prompt()`: 의도별 맞춤 프롬프트 생성
   - `chat()`: intent 파라미터 전달
   - `post_process_response()`: 응답 후처리 추가

---

## 🧪 테스트 방법

### A. 종목 Alias 테스트

```bash
cd /path/to/Backend
python manage.py shell
```

```python
from chatbot.stock_alias import find_stock_by_alias

# 테스트 케이스
test_queries = [
    "삼전 어때?",
    "삼성전자 주가는?",
    "005930 분석해줘",
    "sk텔 좋아?",
    "하이닉스 전망은?",
    "네이버 어때?",
]

for query in test_queries:
    result = find_stock_by_alias(query)
    print(f"{query:30s} → {result}")

# 예상 출력:
# 삼전 어때?                      → ['삼성전자']
# 삼성전자 주가는?                 → ['삼성전자']
# 005930 분석해줘                 → ['삼성전자']
# sk텔 좋아?                      → ['SK텔레콤']
# 하이닉스 전망은?                 → ['SK하이닉스']
# 네이버 어때?                     → ['NAVER']
```

### B. 의도 분류 테스트

```python
from chatbot.services import ChatbotService
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()  # 테스트용 사용자
chatbot = ChatbotService(user)

test_cases = [
    ("삼전 어때?", "STOCK"),
    ("예금 추천해줘", "PRODUCT"),
    ("삼성전자 뉴스 알려줘", "NEWS"),
    ("안녕하세요", "GENERAL"),
]

for query, expected_intent in test_cases:
    result = chatbot.analyze_user_question(query)
    actual_intent = result['intent']
    status = "✅" if actual_intent == expected_intent else "❌"
    print(f"{status} {query:30s} → {actual_intent:10s} (기대: {expected_intent})")
```

### C. 실제 챗봇 응답 테스트 (Postman/Thunder Client)

**엔드포인트:** `POST http://localhost:8000/chatbot/chat/`

**헤더:**
```json
{
  "Authorization": "Bearer YOUR_JWT_TOKEN",
  "Content-Type": "application/json"
}
```

**테스트 케이스 1: 종목 Alias**
```json
{
  "message": "삼전 어때?"
}
```
**예상 결과:** 삼성전자 주가 정보 응답, 예금/적금 추천 ❌

**테스트 케이스 2: 예금 추천**
```json
{
  "message": "예금 상품 추천해줘"
}
```
**예상 결과:** 예금/적금 상품 추천, 주식 추천 ❌

**테스트 케이스 3: 내부 문구 확인**
```json
{
  "message": "삼성전자 최근 주가 알려줘"
}
```
**예상 결과:** 응답에 "DB기준", "DB에서 조회한" 등 문구 ❌

### D. 응답 후처리 단위 테스트

```python
from chatbot.services import ChatbotService
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()
chatbot = ChatbotService(user)

# 내부 문구 포함된 응답 시뮬레이션
test_response = "내 DB기준으로 삼성전자의 DB에서 조회한 최근 주가는 75,000원입니다."

cleaned = chatbot.post_process_response(test_response)
print(f"원본: {test_response}")
print(f"정제: {cleaned}")

# 예상 출력:
# 원본: 내 DB기준으로 삼성전자의 DB에서 조회한 최근 주가는 75,000원입니다.
# 정제: 삼성전자의 최근 주가는 75,000원입니다.
```

---

## 🔍 디버깅 팁

### 1. 로그 확인
콘솔에 출력되는 DEBUG 로그를 확인하세요:

```
[DEBUG] analyze_user_question 시작 - 사용자 메시지: '삼전 어때?'
[DEBUG] Alias 매칭 성공: ['삼성전자']
[DEBUG] DB 검증 완료: 삼성전자
[DEBUG] 의도 분류: STOCK
[DEBUG] 최종 분석 결과: {'stock_names': ['삼성전자'], 'intent': 'STOCK', ...}
```

### 2. Alias 사전 확장
`chatbot/stock_alias.py`의 `STOCK_ALIASES`에 새로운 종목 추가:

```python
STOCK_ALIASES = {
    "삼성전자": ["삼전", "삼성", "005930", "samsung"],
    "새로운종목": ["별명1", "별명2", "종목코드"],  # ← 추가
}
```

### 3. 의도 키워드 조정
`services.py`의 `analyze_user_question()` 함수에서 키워드 수정:

```python
# 주식 관련 키워드 추가
stock_keywords = ['주가', '시세', '종목', '주식', '전망', '어때', ...]

# 금융상품 관련 키워드 추가
product_keywords = ['예금', '적금', '상품', '은행', ...]
```

### 4. 금지 문구 추가
`services.py`의 `post_process_response()` 함수에서 금지 문구 추가:

```python
forbidden_phrases = [
    "내 DB기준",
    "DB에서 조회한",
    "새로운_금지_문구",  # ← 추가
]
```

---

## ⚠️ 주의사항

1. **Alias 사전 유지보수**
   - 새로운 주요 종목 상장 시 `STOCK_ALIASES`에 추가 필요
   - 사용자 피드백 기반으로 자주 사용되는 별명 추가

2. **의도 분류 경계 케이스**
   - "삼성전자 예금"처럼 혼합된 의도는 첫 번째 매칭(STOCK) 우선
   - 필요시 `analyze_user_question()` 로직 조정

3. **응답 후처리 성능**
   - `post_process_response()`는 정규식 사용하므로 긴 응답에서 지연 가능
   - 필요시 컴파일된 정규식으로 최적화

4. **GMS API 호출 제한**
   - 대량 테스트 시 API 제한 주의
   - 단위 테스트는 실제 API 호출 없이 로직만 테스트

---

## 📊 재현 케이스 정리

### 문제1: 종목 별명 미인식
| 입력 | 기존 결과 | 수정 후 결과 |
|------|----------|-------------|
| "삼전 어때?" | ❌ 조회 실패 | ✅ 삼성전자 조회 성공 |
| "005930 분석" | ❌ 조회 실패 | ✅ 삼성전자 조회 성공 |
| "sk텔 주가" | ❌ 조회 실패 | ✅ SK텔레콤 조회 성공 |

### 문제2: 내부 문구 노출
| 응답 예시 | 기존 | 수정 후 |
|----------|------|---------|
| 기준일 표시 | "내 DB기준으로..." | "2025년 12월 25일 기준으로..." |
| 데이터 출처 | "DB에서 조회한..." | "최종 확인일: 2025-12-25..." |

### 문제3: 잘못된 상품 추천
| 입력 | 기존 결과 | 수정 후 결과 |
|------|----------|-------------|
| "삼성전자 어때?" | ❌ 예금/적금 추천 | ✅ 주식 정보만 제공 |
| "예금 추천해줘" | ⚠️ 주식도 섞여서 추천 | ✅ 예금/적금만 추천 |

---

## 🚀 배포 체크리스트

- [ ] `chatbot/stock_alias.py` 파일 추가됨
- [ ] `chatbot/services.py` 수정사항 반영됨
- [ ] 종목 Alias 단위 테스트 통과
- [ ] 의도 분류 단위 테스트 통과
- [ ] 응답 후처리 단위 테스트 통과
- [ ] 실제 챗봇 API 통합 테스트 통과
- [ ] 로그에서 DEBUG 메시지 확인
- [ ] 프로덕션 환경에서 최소 3가지 케이스 테스트
- [ ] 사용자 피드백 모니터링 계획 수립

---

## 📞 추가 지원

문제 발생 시:
1. 콘솔 로그 확인 (`[DEBUG]` 메시지)
2. `chatbot/services.py`의 `print()` 디버깅 활용
3. 위 테스트 케이스 재실행
4. 필요시 alias 사전 또는 의도 키워드 조정

완료! 🎉
