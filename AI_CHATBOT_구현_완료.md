# 🤖 Finflow AI 챗봇 구현 완료

## 📋 구현 개요

GMS API를 활용하여 사용자의 투자 성향에 맞는 금융 상품을 추천하는 AI 챗봇을 성공적으로 구현했습니다.

---

## ✅ 구현 완료 기능

### 1. 백엔드 (Django)

#### **새로 추가된 앱: `chatbot`**

**위치:** `c:\Users\SSAFY\Desktop\pjt\-with-\Backend\chatbot\`

#### **모델 (models.py)**
- **ChatMessage**: 사용자와 AI의 대화 내용 저장
  - user (ForeignKey): 사용자
  - user_message (TextField): 사용자 메시지
  - ai_response (TextField): AI 응답
  - recommended_products (JSONField): 추천 상품 목록 (JSON)
  - created_at (DateTimeField): 생성 시간

- **ChatSession**: 채팅 세션 관리 (선택사항)
  - user (ForeignKey): 사용자
  - title (CharField): 세션 제목
  - is_active (BooleanField): 활성 상태
  - created_at, updated_at (DateTimeField)

#### **서비스 로직 (services.py)**
- **ChatbotService 클래스**
  - `get_user_profile_context()`: 사용자 투자 프로필 정보 추출
  - `get_financial_products_context()`: DB에서 예적금, 주식 상품 데이터 조회
  - `build_system_prompt()`: GMS API에 전달할 시스템 프롬프트 생성
  - `chat()`: GMS API 호출하여 AI 응답 생성
  - `extract_recommended_products()`: AI 응답에서 상품 코드 파싱

**GMS API 통합:**
- 엔드포인트: `https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions`
- 모델: `gpt-4o`
- 사용자 프로필 + 금융 상품 DB를 컨텍스트로 활용
- 최근 5개 대화 히스토리를 컨텍스트로 전달

#### **API 엔드포인트 (views.py + urls.py)**
| 메소드 | 경로 | 설명 |
|--------|------|------|
| POST | `/chatbot/chat/` | 챗봇에게 메시지 전송 |
| GET | `/chatbot/history/` | 대화 히스토리 조회 (limit 파라미터) |
| DELETE | `/chatbot/history/` | 전체 대화 히스토리 삭제 |
| DELETE | `/chatbot/messages/{id}/` | 특정 메시지 삭제 |
| GET | `/chatbot/avatar/` | 사용자 성향별 챗봇 아바타 정보 |

#### **Admin 통합 (admin.py)**
- ChatMessage, ChatSession 모델 Django Admin에 등록
- 메시지 미리보기, 필터링, 검색 기능 포함

---

### 2. 프론트엔드 (Vue 3)

#### **새로 추가된 컴포넌트**

**위치:** `c:\Users\SSAFY\Desktop\pjt\-with-\Frontend\Finflow_front\src\components\common\ChatbotWidget.vue`

#### **주요 기능**
1. **플로팅 버튼**
   - 우측 하단 고정 위치
   - 투자 성향에 따른 아바타 이미지 표시
   - 새로운 추천 상품이 있을 때 알림 배지 표시
   - 펄스 애니메이션 효과

2. **채팅 창 (400x600px 팝업)**
   - **헤더**:
     - 챗봇 아바타 + 사용자 투자 성향 표시
     - 닫기 버튼 (회전 애니메이션)

   - **메시지 영역**:
     - 초기 환영 메시지 + 빠른 질문 버튼 3개
     - 사용자 메시지 (우측, 그라데이션 보라색)
     - AI 메시지 (좌측, 흰색 배경)
     - 타이핑 인디케이터 (로딩 중)
     - 자동 스크롤

   - **추천 상품 카드**:
     - 상품 타입 배지 (예금/적금/주식)
     - 상품명, 은행명 표시
     - ❤️ 좋아요 버튼 (기존 북마크 API 연동)
     - "상세보기 →" 버튼 (상품 상세 페이지 이동)

   - **입력 영역**:
     - Textarea (Enter 전송, Shift+Enter 줄바꿈)
     - 전송 버튼 (➤ 아이콘)
     - "대화 내역 삭제" 버튼
     - "AI 답변은 참고용입니다" 안내 문구

3. **투자 성향별 아바타**
   - **Timid (안정형)**: `timid-avatar.png` (파란색 계열)
   - **Normal (중립형)**: `normal-avatar.png` (보라색 계열)
   - **Speculative (공격형)**: `speculative-avatar.png` (주황색 계열)
   - 이미지 없으면 🤖 이모지로 폴백

4. **기존 시스템 통합**
   - 북마크 기능: 기존 `/accounts/recommendations/{code}/bookmark/` API 활용
   - 북마크 상태: Set 자료구조로 실시간 동기화
   - 상품 상세 페이지로 라우팅

#### **메인 페이지 통합**
**위치:** `c:\Users\SSAFY\Desktop\pjt\-with-\Frontend\Finflow_front\src\views\main\MainView.vue`

- `<ChatbotWidget v-if="auth.isLogin" />` 추가
- 로그인한 사용자만 챗봇 표시

---

## 🎨 UI/UX 특징

### 디자인 시스템
- **색상**: 보라색 그라데이션 (`#667eea` → `#764ba2`)
- **애니메이션**:
  - Bounce-in/out (버튼 등장/퇴장)
  - Slide-up (채팅창 등장/퇴장)
  - Pulse (새 추천 알림)
  - Typing indicator (AI 응답 대기)
- **반응형**: 모바일에서 전체 화면 크기 조정
- **그림자**: 고급스러운 box-shadow 효과

### 사용성
- 빠른 질문 버튼으로 쉬운 시작
- 대화 히스토리 자동 저장 및 로드
- 상품 추천 시 즉시 북마크 가능
- 한 번의 클릭으로 상품 상세 페이지 이동

---

## 📁 파일 구조

### 백엔드
```
-with-/Backend/
├── chatbot/                    # 새로 추가된 앱
│   ├── models.py              # ChatMessage, ChatSession
│   ├── services.py            # ChatbotService (GMS API 연동)
│   ├── serializers.py         # ChatMessageSerializer 등
│   ├── views.py               # chat, history, avatar API
│   ├── urls.py                # /chatbot/* 라우팅
│   ├── admin.py               # Django Admin 설정
│   └── migrations/
│       └── 0001_initial.py    # DB 마이그레이션
├── Finflow/
│   ├── settings.py            # 'chatbot' 앱 추가
│   └── urls.py                # path('chatbot/', include('chatbot.urls'))
└── .env                       # GMS_KEY 설정됨
```

### 프론트엔드
```
-with-/Frontend/Finflow_front/
├── src/
│   ├── components/
│   │   └── common/
│   │       └── ChatbotWidget.vue    # AI 챗봇 위젯 (새로 생성)
│   └── views/
│       └── main/
│           └── MainView.vue         # 챗봇 통합 (수정됨)
└── public/
    └── assets/
        └── chatbot/
            ├── README.md            # 이미지 가이드
            ├── timid-avatar.png     # (사용자가 추가 필요)
            ├── normal-avatar.png    # (사용자가 추가 필요)
            └── speculative-avatar.png # (사용자가 추가 필요)
```

---

## 🚀 사용 방법

### 1. 백엔드 실행
```bash
cd "c:\Users\SSAFY\Desktop\pjt\-with-\Backend"
python manage.py runserver
```

### 2. 프론트엔드 실행
```bash
cd "c:\Users\SSAFY\Desktop\pjt\-with-\Frontend\Finflow_front"
npm run dev
```

### 3. 챗봇 사용
1. 로그인 후 메인 페이지로 이동
2. 우측 하단의 챗봇 플로팅 버튼 클릭
3. 환영 메시지와 빠른 질문 확인
4. 메시지 입력 또는 빠른 질문 클릭
5. AI 응답과 추천 상품 확인
6. 상품 카드의 ❤️ 버튼으로 관심상품 추가
7. "상세보기" 버튼으로 상품 페이지 이동

---

## 🔧 추가 설정 필요 사항

### 1. 챗봇 아바타 이미지 추가
**경로:** `public/assets/chatbot/`

다음 3개의 이미지 파일을 준비하여 추가해주세요:
- `timid-avatar.png` - 안정형 투자자용 (파란색 계열)
- `normal-avatar.png` - 중립형 투자자용 (보라색 계열)
- `speculative-avatar.png` - 공격형 투자자용 (주황색 계열)

**이미지 가이드:**
- 권장 크기: 200x200px 이상
- 파일 형식: PNG (투명 배경 권장)
- 스타일: 친근하고 심플한 캐릭터 또는 아이콘
- 이미지가 없으면 🤖 이모지로 대체됨

### 2. GMS API 키 확인
**.env 파일 확인:** `c:\Users\SSAFY\Desktop\pjt\-with-\Backend\.env`
```
GMS_KEY='S14P02EB02-5aebd3b1-c69f-46d9-930a-6bb05baff2e2'
```
✅ 이미 설정되어 있음

---

## 📊 데이터 흐름

### 챗봇 대화 프로세스
1. **사용자**: 메시지 입력 → Frontend
2. **Frontend**: `POST /chatbot/chat/` → Backend
3. **Backend**:
   - 사용자 투자 프로필 조회 (InvestmentProfile)
   - 금융 상품 DB 조회 (DepositProducts, SavingProducts, Stock)
   - 시스템 프롬프트 생성 (사용자 정보 + 상품 정보)
   - GMS API 호출 (`gpt-4o` 모델)
   - AI 응답에서 상품 코드 파싱
   - ChatMessage에 대화 내용 저장
4. **Frontend**: AI 응답 + 추천 상품 표시
5. **사용자**: 상품 좋아요 클릭 → `POST /accounts/recommendations/{code}/bookmark/`
6. **Backend**: ProductRecommendation 테이블에 북마크 저장
7. **Frontend**: 마이페이지 관심상품에 즉시 반영

---

## 🎯 핵심 기술 스택

### Backend
- Django 5.2.8
- Django REST Framework
- GMS API (OpenAI GPT-4o)
- JWT Authentication

### Frontend
- Vue 3 (Composition API)
- Pinia (상태 관리)
- Axios (HTTP 클라이언트)
- CSS Animations & Transitions

---

## 💡 추가 개선 아이디어

현재 구현이 완료되었지만, 다음과 같은 기능을 추가로 고려할 수 있습니다:

1. **대화 세션 관리**
   - ChatSession 모델 활용하여 여러 대화 스레드 관리
   - 대화 제목 자동 생성 (첫 메시지 기반)

2. **음성 입력**
   - Web Speech API 활용하여 음성 메시지 입력

3. **상품 비교**
   - 여러 상품을 한눈에 비교하는 UI

4. **챗봇 피드백**
   - AI 응답에 대한 사용자 평가 (좋아요/싫어요)

5. **추천 알림**
   - 새로운 상품이 등록되면 자동으로 알림

6. **다국어 지원**
   - i18n을 활용한 영어/한국어 지원

7. **챗봇 성격 커스터마이징**
   - 사용자가 챗봇의 말투나 성격 선택

---

## 🐛 알려진 제한사항

1. **GMS API 의존성**
   - GMS 서버가 다운되면 챗봇 사용 불가
   - API 키 만료 시 갱신 필요

2. **이미지 미제공**
   - 챗봇 아바타 이미지를 직접 준비해야 함
   - 현재는 🤖 이모지로 폴백

3. **대화 컨텍스트 제한**
   - 최근 5개 메시지만 컨텍스트로 사용
   - 긴 대화에서는 초기 내용 누락 가능

4. **상품 코드 파싱**
   - AI 응답에서 정확한 상품 코드를 언급해야 추출 가능
   - 파싱 실패 시 추천 상품 카드 미표시

---

## ✅ 테스트 체크리스트

- [x] Django 마이그레이션 완료
- [x] Django 서버 정상 실행
- [x] ChatMessage 모델 DB 생성 확인
- [x] GMS API 키 설정 확인
- [x] 챗봇 API 엔드포인트 생성
- [x] Vue 컴포넌트 생성
- [x] 메인 페이지 통합
- [x] 플로팅 버튼 표시
- [ ] 실제 대화 테스트 (서버 실행 후)
- [ ] 상품 추천 기능 테스트
- [ ] 좋아요 버튼 동작 테스트
- [ ] 북마크 연동 테스트
- [ ] 대화 히스토리 저장/로드 테스트
- [ ] 아바타 이미지 추가 (사용자 작업)

---

## 📞 문의 및 지원

구현 중 발생한 이슈나 추가 기능 요청은 언제든지 말씀해주세요!

**구현 완료 일시:** 2025-12-23
**개발자:** Claude Code (Sonnet 4.5)
