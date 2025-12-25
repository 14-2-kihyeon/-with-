# Finflow AI 챗봇 모드 분류 시스템 구현 완료 가이드

## 🎯 해결된 문제

### 1. 인사말에 과도한 추천 응답
**문제:** "안녕", "고마워" 같은 단순 인사/감사에도 포트폴리오 분석 + 상품 추천 제공

**해결책:**
- `chatbot/mode_classifier.py` 모듈 생성
- CHAT_MODE vs SERVICE_MODE 2단계 분류
- CHAT 모드는 DB 조회 생략, 간단한 응답만 제공

---

### 2. 응답 길이 및 가독성 문제
**문제:** 답변이 너무 길고 빽빽함 (10줄 이상, 불필요한 반복)

**해결책:**
- `format_response_by_mode()` 함수 추가
- CHAT 모드: 최대 300자, 2~3문장
- SERVICE 모드: 최대 1200자, 3~7줄, 불릿 포인트 정리

---

## 📁 신규/수정 파일 목록

### 신규 파일
1. **`chatbot/mode_classifier.py`**
   - CHAT_KEYWORDS: 인사/감정/일상 키워드 사전
   - SERVICE_KEYWORDS: 주식/예적금/기능 키워드 사전
   - `classify_chat_mode()`: 4단계 규칙 기반 분류
   - `classify_mode_with_llm()`: LLM 기반 2차 분류 (선택)

### 수정된 파일
2. **`chatbot/services.py`**
   - Line 13: `from .mode_classifier import classify_chat_mode` 추가
   - Lines 559-591: `build_system_prompt()` - CHAT 모드 전용 프롬프트 추가
   - Lines 730-787: `chat()` - 모드 분류 우선 실행, CHAT 모드 가드 추가
   - Lines 860-969: `format_response_by_mode()` - 모드별 응답 포맷팅
   - Lines 971-1016: `post_process_response()` - mode 파라미터 추가

---

## 🧪 테스트 케이스 및 예상 결과

### A. CHAT 모드 테스트

| 입력 | 예상 모드 | 예상 응답 특징 | 예상 응답 예시 |
|------|----------|--------------|--------------|
| "안녕" | CHAT | 짧은 인사 (1문장) | "안녕하세요! Finflow AI 상담사입니다. 무엇을 도와드릴까요?" |
| "고마워" | CHAT | 감사 응답 (1~2문장) | "천만에요! 언제든지 도와드릴게요 😊" |
| "ㅋㅋㅋ" | CHAT | 가볍게 반응 (1문장) | "무슨 재밌는 일이 있으셨나요? 😄" |
| "오늘 날씨 어때?" | CHAT | 주제 전환 안내 (2문장) | "저는 금융 상담 AI라 날씨 정보는 잘 모르겠어요. 대신 금융 관련 질문이 있으시면 언제든 물어보세요!" |
| "좋아" | CHAT | 긍정 반응 (1문장) | "좋아요! 다른 궁금한 점이 있으신가요?" |
| "넌 누구야?" | CHAT | 자기소개 (2~3문장) | "저는 Finflow의 AI 재무 상담사입니다. 예금, 적금, 주식 등 금융 상품 추천과 투자 조언을 도와드려요." |

**확인 사항:**
- ✅ 상품/주식 추천 없음
- ✅ 응답 길이 300자 이내
- ✅ 2~3문장 이내
- ✅ DB 조회 실행 안 함 (로그 확인)

---

### B. SERVICE 모드 테스트

| 입력 | 예상 모드 | 예상 응답 특징 | 필수 포함 요소 |
|------|----------|--------------|--------------|
| "삼전 어때?" | SERVICE | 주식 정보 제공 (3~7줄) | 삼성전자 최근 주가, 수익률, 뉴스 (예금/적금 ❌) |
| "예금 추천해줘" | SERVICE | 예금 상품 추천 (3~7줄) | 은행명, 상품명, 금리 (주식 ❌) |
| "금리 좋은 적금" | SERVICE | 적금 상품 추천 (3~7줄) | 상위 3개 적금, 금리 비교 |
| "북마크 어디서 봐?" | SERVICE | 기능 안내 (2~5줄) | 마이페이지 경로, 사용법 |
| "삼성전자 뉴스 알려줘" | SERVICE | 종목 뉴스 제공 (3~7줄) | 최근 3~5개 뉴스 제목, 날짜 |
| "주식 추천" | SERVICE | 주식 종목 추천 (3~7줄) | 사용자 성향 기반 종목, DART 링크 |

**확인 사항:**
- ✅ 구체적인 데이터 포함 (금리, 주가, 날짜 등)
- ✅ 응답 길이 1200자 이내
- ✅ 3~7줄 구조화된 포맷
- ✅ 불릿 포인트 사용
- ✅ DB 조회 실행됨 (로그 확인)

---

## 🔬 단위 테스트 방법

### 1. 모드 분류 테스트

```bash
cd /path/to/Backend
python chatbot/mode_classifier.py
```

**예상 출력:**
```
============================================================
챗봇 모드 분류 테스트
============================================================
✅ '안녕                            ' → CHAT       (기대: CHAT)
✅ 'ㅋㅋㅋ                          ' → CHAT       (기대: CHAT)
✅ '고마워                          ' → CHAT       (기대: CHAT)
✅ '좋아                            ' → CHAT       (기대: CHAT)
✅ '오늘 날씨 어때?                  ' → CHAT       (기대: CHAT)
✅ '넌 누구야?                      ' → CHAT       (기대: CHAT)
✅ '삼전 어때?                      ' → SERVICE    (기대: SERVICE)
✅ '삼성전자 주가 알려줘              ' → SERVICE    (기대: SERVICE)
✅ '예금 추천해줘                    ' → SERVICE    (기대: SERVICE)
✅ '금리 좋은 적금                   ' → SERVICE    (기대: SERVICE)
✅ '북마크 어디서 봐?                ' → SERVICE    (기대: SERVICE)
✅ '나중에 볼 영상 목록              ' → SERVICE    (기대: SERVICE)
✅ '005930 분석                     ' → SERVICE    (기대: SERVICE)
✅ '마이페이지 조회                  ' → SERVICE    (기대: SERVICE)
============================================================
정확도: 14/14 (100.0%)
```

---

### 2. 응답 포맷팅 테스트

```python
from chatbot.services import ChatbotService
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()
chatbot = ChatbotService(user)

# CHAT 모드 포맷팅 테스트
long_chat_response = """안녕하세요! Finflow AI 상담사입니다. 무엇을 도와드릴까요?
저희는 예금, 적금, 주식 등 다양한 금융 상품을 추천해드리고 있으며,
사용자님의 투자 성향에 맞는 포트폴리오를 구성해드립니다.
언제든지 편하게 질문해주세요."""

formatted = chatbot.format_response_by_mode(long_chat_response, 'CHAT')
print(f"원본 길이: {len(long_chat_response)}자")
print(f"CHAT 모드 길이: {len(formatted)}자")
print(f"응답: {formatted}")
# 예상: 300자 이내로 잘림, 간결한 문장만 남음

# SERVICE 모드 포맷팅 테스트
long_service_response = """=== 예금 상품 추천 ===
1. 우리은행 - WON플러스예금
   - 기본금리: 3.20%, 최고금리: 3.50%

2. 신한은행 - 쏠편한 정기예금
   - 기본금리: 3.10%, 최고금리: 3.40%

3. 국민은행 - KB Star 정기예금
   - 기본금리: 3.00%, 최고금리: 3.30%

추천 이유: 사용자님의 안정형 투자 성향에 적합한 상품들입니다."""

formatted = chatbot.format_response_by_mode(long_service_response, 'SERVICE')
print(f"\nSERVICE 모드 줄 수: {len([l for l in formatted.split('\\n') if l.strip()])}줄")
print(f"응답:\n{formatted}")
# 예상: 3~7줄로 정리됨
```

---

### 3. 실제 챗봇 API 테스트 (Postman/Thunder Client)

**엔드포인트:** `POST http://localhost:8000/chatbot/chat/`

**헤더:**
```json
{
  "Authorization": "Bearer YOUR_JWT_TOKEN",
  "Content-Type": "application/json"
}
```

#### 테스트 케이스 1: CHAT 모드 - 인사
```json
{
  "message": "안녕"
}
```

**예상 응답:**
```json
{
  "id": 123,
  "user_message": "안녕",
  "ai_response": "안녕하세요! Finflow AI 상담사입니다. 무엇을 도와드릴까요?",
  "recommended_products": null,
  "created_at": "2025-12-25T10:30:00Z"
}
```

**체크리스트:**
- [ ] `ai_response` 길이 300자 이내
- [ ] `recommended_products`가 `null`
- [ ] 응답에 금리/주가 등 구체적 데이터 없음
- [ ] 콘솔 로그에 `[MODE] CHAT 모드 - 간단한 대화 처리` 출력

---

#### 테스트 케이스 2: CHAT 모드 - 감사
```json
{
  "message": "고마워"
}
```

**예상 응답:**
```json
{
  "ai_response": "천만에요! 언제든지 도와드릴게요 😊",
  "recommended_products": null
}
```

---

#### 테스트 케이스 3: SERVICE 모드 - 주식 질문
```json
{
  "message": "삼전 어때?"
}
```

**예상 응답:**
```json
{
  "ai_response": "삼성전자는 최근 20일간 5.2% 상승했습니다.\n\n주요 포인트:\n• 현재가: 75,000원 (2025-12-25 기준)\n• 최근 뉴스: AI 반도체 투자 확대 발표\n• 변동성: 중립 (20일 변동성 2.3%)\n\n⚠️ 주식 투자에는 위험이 따를 수 있습니다. DART 전자공시에서 더 자세한 정보를 확인하세요: [링크]",
  "recommended_products": [
    {
      "type": "stock",
      "name": "삼성전자",
      "code": "005930",
      "price": "75,000원",
      "dart_link": "https://dart.fss.or.kr/..."
    }
  ]
}
```

**체크리스트:**
- [ ] `ai_response` 길이 1200자 이내
- [ ] 3~7줄 구조화된 포맷
- [ ] 불릿 포인트 사용
- [ ] 예금/적금 추천 없음 (주식만)
- [ ] `recommended_products`에 주식 정보 포함
- [ ] 콘솔 로그에 `[MODE] 챗봇 모드: SERVICE` 출력

---

#### 테스트 케이스 4: SERVICE 모드 - 예금 추천
```json
{
  "message": "예금 추천해줘"
}
```

**예상 응답:**
```json
{
  "ai_response": "사용자님의 안정형 투자 성향에 맞는 예금 상품을 추천드립니다.\n\n추천 상품:\n1. 우리은행 - WON플러스예금\n   • 최고금리: 3.50% (12개월)\n   • 가입방법: 인터넷뱅킹, 영업점\n\n2. 신한은행 - 쏠편한 정기예금\n   • 최고금리: 3.40% (12개월)\n\n⚠️ 금리는 변동될 수 있습니다.",
  "recommended_products": [
    {
      "type": "deposit",
      "name": "WON플러스예금",
      "bank": "우리은행",
      "rate": "3.50%"
    }
  ]
}
```

**체크리스트:**
- [ ] 주식 추천 없음 (예금만)
- [ ] 은행명, 상품명, 금리 포함
- [ ] 3~7줄 구조화

---

## 🔍 디버깅 팁

### 1. 로그 확인
콘솔에서 모드 분류 과정 확인:

```
[MODE] CHAT 패턴 매칭: ^(안녕|하이|헬로|hi|hello)[\?!~]*$
[MODE] 챗봇 모드: CHAT
[MODE] CHAT 모드 - 간단한 대화 처리
```

또는

```
[MODE] SERVICE 키워드 2개 매칭
[MODE] 챗봇 모드: SERVICE
[DEBUG] analyze_user_question 시작 - 사용자 메시지: '삼전 어때?'
[DEBUG] Alias 매칭 성공: ['삼성전자']
```

---

### 2. 키워드 추가/조정

#### CHAT 키워드 추가
`chatbot/mode_classifier.py`:
```python
CHAT_KEYWORDS = {
    # 기존 키워드...
    '새로운키워드1', '새로운키워드2',  # ← 추가
}
```

#### SERVICE 키워드 추가
```python
SERVICE_KEYWORDS = {
    # 기존 키워드...
    '새기능', '새상품',  # ← 추가
}
```

---

### 3. 응답 길이 조정

#### CHAT 모드 길이 변경
`chatbot/services.py` - `format_response_by_mode()`:
```python
if mode == 'CHAT':
    max_length = 500  # 기본 300 → 500으로 변경
```

#### SERVICE 모드 줄 수 변경
```python
if len(lines) > 10:  # 기본 7 → 10으로 변경
```

---

### 4. LLM 2차 분류 활성화 (선택)

`chatbot/services.py` - `chat()` 함수:
```python
# 규칙 기반 분류 후 LLM으로 재확인 (애매한 경우만)
chat_mode = classify_chat_mode(user_message)

# LLM 2차 확인 (선택)
if chat_mode == 'CHAT' and any(kw in user_message for kw in ['추천', '알려']):
    # 애매한 케이스: LLM으로 재분류
    from .mode_classifier import classify_mode_with_llm
    chat_mode = classify_mode_with_llm(user_message, self.api_url, self.api_key)
```

---

## ⚠️ 주의사항

1. **모드 분류 경계 케이스**
   - "삼성 좋아" → CHAT (감정 표현 우선)
   - "삼성전자 좋아?" → SERVICE (종목명 포함)
   - 애매한 경우 CHAT 모드 기본값 (과잉 응답 방지)

2. **응답 길이 제한 부작용**
   - SERVICE 모드에서 중요한 정보가 잘릴 수 있음
   - 필요시 `max_length` 늘리거나 중요도 기반 필터링 강화

3. **DB 조회 성능**
   - CHAT 모드는 DB 조회 생략으로 응답 속도 빠름 (~1초)
   - SERVICE 모드는 기존과 동일 (~3~5초)

4. **LLM 분류 비용**
   - `classify_mode_with_llm()`은 추가 API 호출 필요
   - 규칙 기반만으로도 90% 이상 정확도 달성 가능
   - 비용 절감 위해 기본적으로 비활성화

---

## 📊 재현 케이스 정리

### 문제1: 인사말에 과도한 응답

| 입력 | 기존 결과 | 수정 후 결과 |
|------|----------|-------------|
| "안녕" | ❌ 포트폴리오 분석 + 상품 3개 추천 (500자) | ✅ "안녕하세요! 무엇을 도와드릴까요?" (30자) |
| "고마워" | ❌ "감사합니다. 예금 추천드리면..." (300자) | ✅ "천만에요! 언제든지 도와드릴게요 😊" (20자) |
| "ㅋㅋㅋ" | ❌ "재밌으시군요. 주식 추천..." (200자) | ✅ "무슨 재밌는 일이 있으셨나요? 😄" (18자) |

---

### 문제2: 응답 과다 및 가독성 저하

| 입력 | 기존 결과 | 수정 후 결과 |
|------|----------|-------------|
| "예금 추천" | ❌ 15개 상품 나열 (1500자, 50줄) | ✅ 상위 3개 불릿 포인트 (400자, 7줄) |
| "삼전 어때?" | ❌ 주가+뉴스+예금+적금 혼합 (1200자) | ✅ 주가+뉴스만 (600자, 5줄) |

---

## 🚀 배포 체크리스트

- [ ] `chatbot/mode_classifier.py` 파일 추가됨
- [ ] `chatbot/services.py` 수정사항 반영됨
- [ ] 모드 분류 단위 테스트 통과 (정확도 90% 이상)
- [ ] CHAT 모드 응답 길이 300자 이내 확인
- [ ] SERVICE 모드 응답 3~7줄 확인
- [ ] 실제 챗봇 API 통합 테스트 (6개 케이스) 통과
- [ ] 로그에서 `[MODE]` 메시지 확인
- [ ] 프로덕션 환경에서 최소 5가지 케이스 테스트
- [ ] 사용자 피드백 모니터링 계획 수립

---

## 📞 추가 개선 아이디어

1. **사용자 피드백 수집**
   - 응답 하단에 "이 답변이 도움이 되었나요? 👍 👎" 버튼 추가
   - 부정 피드백 시 모드 분류 오류 로그 수집

2. **컨텍스트 기반 모드 전환**
   - 이전 대화가 SERVICE였다면 다음 "고마워"는 SERVICE 유지
   - 세션 기반 모드 히스토리 관리

3. **자동 키워드 학습**
   - 사용자 입력 패턴 분석하여 CHAT/SERVICE 키워드 자동 추가
   - 월 1회 키워드 사전 업데이트

4. **모드별 응답 템플릿**
   - CHAT: 10가지 인사 템플릿, 5가지 감사 템플릿
   - LLM 호출 없이 템플릿 매칭으로 빠른 응답

완료! 🎉
