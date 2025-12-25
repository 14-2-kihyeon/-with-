# 🏗️ Finflow 프로젝트 구조

## 📋 프로젝트 개요

**프로젝트명**: Finflow
**아키텍처**: Monorepo (Backend: Django REST API + Frontend: Vue.js SPA)
**타입**: PBTI 기반 맞춤형 금융 추천 플랫폼
**위치**: `c:\Users\정승현\Desktop\-with-\`

---

## 📁 루트 디렉토리 구조

```
-with-/
├── Backend/                          # Django REST API
├── Frontend/Finflow_front/           # Vue.js SPA
├── .git/                             # Git 저장소
├── .claude/                          # Claude AI 설정
├── README.md                         # 프로젝트 문서
├── ERD.md                            # 데이터베이스 ERD
├── PROJECT_STRUCTURE.md              # 이 문서
├── .gitignore
├── .gitattributes
├── 14기 관통 프로젝트 기획서.docx
├── AI_CHATBOT_구현_완료.md
├── 마이페이지_및_관심상품_기능_완성.md
├── 버그수정_완료.md
├── 최종_업데이트_완료.md
├── 투자성향분석_개선사항.md
└── README전용 picture/               # 문서 이미지
```

---

## 🔧 Backend 구조 (Django)

### 프로젝트 설정

**프로젝트명**: Finflow
**데이터베이스**: SQLite3 (db.sqlite3 - 39MB)
**Python 버전**: 3.x

### 주요 설정 (Backend/Finflow/settings.py)

- **인증**: JWT (dj-rest-auth, django-allauth)
- **CORS**: localhost:5173, 5174 허용
- **토큰 수명**:
  - Access Token: 50분
  - Refresh Token: 7일 (회전 방식)
- **커스텀 User 모델**: `accounts.User`
- **시간대**: Asia/Seoul
- **언어**: ko-kr

---

## 📦 Django 앱 구조 (9개)

### 1. 🔐 accounts - 사용자 관리 & PBTI 시스템

**목적**: 사용자 인증, 투자 성향 프로필, 설문 시스템, 북마크 관리

```
accounts/
├── models.py (21KB)                  # 13개 모델
│   ├── User (AbstractUser 확장)
│   ├── InvestmentProfile (PBTI 타입)
│   ├── SurveyQuestion, SurveyChoice, SurveyResponse
│   ├── ProductRecommendation (금융상품 추천)
│   ├── StockRecommendation (주식 추천)
│   ├── UserNewsBookmark
│   ├── UserYouTubeSubscription
│   ├── UserWatchLater
│   └── RecommendationLog
├── views.py (32KB)                   # 포괄적 사용자 엔드포인트
├── urls.py (3.8KB)                   # 20+ 엔드포인트
├── serializers.py (2KB)
├── migrations/
│   ├── 0001_initial.py
│   ├── 0002_usernewsbookmark_userwatchlater_and_more.py
│   └── 0003_stockrecommendation.py
└── admin.py
```

**주요 URL 엔드포인트** (20+):
- **설문**: `/survey/questions/`, `/survey/submit/`
- **프로필**: `/investment-profile/`
- **추천**: `/recommendations/`, `/recommendations/<code>/bookmark/`
- **주식**: `/stocks/<code>/bookmark/`, `/stocks/bookmarks/`
- **뉴스**: `/news/<id>/bookmark/`, `/news/bookmarks/`
- **YouTube**: `/youtube/channels/<id>/subscribe/`, `/youtube/watch-later/`
- **마이페이지**: `/mypage/` (통합 데이터)

**PBTI 투자 성향 타입** (6가지):
- `timid_male`, `timid_female` (안정형)
- `normal_male`, `normal_female` (중립형)
- `speculative_male`, `speculative_female` (공격형)

---

### 2. 🤖 chatbot - AI 챗봇 서비스

**목적**: Google Gemini 기반 금융 상담 챗봇

```
chatbot/
├── services.py (63KB)                # 메인 챗봇 로직, 모드 분류
├── mode_classifier.py (7.5KB)        # 의도 분류 (상품추천/주식분석/일반대화)
├── stock_alias.py (3.6KB)            # 주식명 매핑 (삼성전자 → 005930)
├── models.py (1.7KB)
│   ├── ChatMessage (대화 내역 + JSON 추천)
│   └── ChatSession (대화 세션)
├── views.py (5KB)
├── urls.py                           # 4개 엔드포인트
├── serializers.py (1.4KB)
└── migrations/
    └── 0001_initial.py
```

**주요 기능**:
- 모드 분류 (상품추천, 주식분석, 일반대화)
- InvestmentProfile 기반 맞춤 추천
- Google Gemini API 통합
- 대화 히스토리 관리

**URL 엔드포인트**:
- `/chat/` - 채팅 인터페이스
- `/history/` - GET/DELETE 대화 내역
- `/messages/<id>/` - 특정 메시지 삭제
- `/avatar/` - 챗봇 아바타 정보

---

### 3. 💰 finances - 금융 상품 (예금 & 적금)

**목적**: 금융감독원 API 기반 예적금 상품 관리

```
finances/
├── apps.py (7KB)                     # 앱 시작 시 fixture 자동 로드
├── views.py (9KB)                    # 상품 목록 & 상세
├── models.py (2.5KB)
│   ├── DepositProducts + DepositOptions (1:N)
│   └── SavingProducts + SavingOptions (1:N)
├── serializers.py (3.5KB)            # 중첩 시리얼라이저
├── urls.py                           # 7개 엔드포인트
├── utils.py (2.2KB)                  # 금융감독원 API 클라이언트
├── fixtures/                         # 사전 로드 데이터
│   ├── deposit_products.json (18KB)
│   ├── deposit_options.json (26KB)
│   ├── saving_products.json (40KB)
│   └── saving_options.json (48KB)
└── migrations/
    └── 0001_initial.py
```

**URL 엔드포인트**:
- `/deposits/`, `/deposits/<code>/`
- `/savings/`, `/savings/<code>/`
- `/banks/`, `/savings/banks/`
- `/deposits/sync/`, `/savings/sync/` (관리자용)

---

### 4. 📈 stocks - 주식 시장 데이터 & 분석

**목적**: 주가 추적, 뉴스, 시장 지수, 추천 엔진

```
stocks/
├── views.py (46KB)                   # 종합 주식 엔드포인트
├── models.py (9.7KB)                 # 8개 모델
│   ├── Stock (종목 마스터)
│   ├── DailyPrice (일별 OHLCV)
│   ├── FeatureDaily (기술 지표: 수익률, 변동성, 낙폭, 뉴스 스코어)
│   ├── StockNews (종목별 뉴스)
│   ├── MarketIndex + MarketIndexDaily (KOSPI/KOSDAQ)
│   ├── FxRateDaily (환율: USD/KRW)
│   └── UpdateLog (데이터 동기화 로그)
├── urls.py (1.2KB)                   # 14+ 엔드포인트
├── admin.py (1KB)
├── management/commands/              # Django 관리 명령
│   ├── build_features.py (5.9KB)            # 기술 지표 계산
│   ├── daily_update.py (4.7KB)              # 일일 전체 업데이트
│   ├── sync_fx_rates.py (2.6KB)             # 환율 동기화
│   ├── sync_index_prices.py (2.5KB)         # 시장 지수 동기화
│   ├── sync_prices.py (5.2KB)               # 주가 동기화
│   └── sync_stock_news.py (4.8KB)           # 주식 뉴스 크롤링
├── services/                         # 비즈니스 로직
│   ├── yfinance_client.py (11KB)            # Yahoo Finance 통합
│   ├── recommender.py (9.3KB)               # 주식 추천 엔진
│   ├── stock_api_client.py (7KB)            # 주식 API 클라이언트
│   ├── news_on_demand.py (5KB)              # 실시간 뉴스 수집
│   ├── explain.py (3.3KB)                   # 종목 설명 생성기
│   ├── news_bundle.py (2.5KB)               # 뉴스 집계
│   ├── naver_news_client.py (1.8KB)         # 네이버 뉴스 API
│   ├── llm_client.py (1.2KB)                # LLM 통합
│   └── reco_utils.py (626B)                 # 추천 유틸리티
└── migrations/
    ├── 0001_initial.py
    ├── 0002_marketindex_marketindexdaily.py
    └── 0003_fxratedaily.py
```

**주요 URL 엔드포인트** (14+):
- **시장**: `/market/summary/`, `/market/prices/`, `/market/fx/`, `/market/index/snapshot/`
- **종목**: `/<code>/`, `/<code>/prices/`, `/<code>/news/`, `/<code>/explain/`, `/<code>/realtime/`, `/<code>/intraday/`
- **추천**: `/recommendations/`, `/recommendations/history/`
- **검색**: `/search/`
- **헬스체크**: `/status/`, `/health/`

**관리 명령어** (6개):
```bash
python manage.py sync_prices          # 일별 주가 동기화
python manage.py sync_fx_rates        # 환율 동기화
python manage.py sync_index_prices    # 시장 지수 동기화
python manage.py sync_stock_news      # 주식 뉴스 크롤링
python manage.py build_features       # 기술 지표 계산
python manage.py daily_update         # 전체 업데이트 실행
```

---

### 5. 📝 posts - 커뮤니티 게시판

**목적**: 사용자 생성 콘텐츠 및 토론

```
posts/
├── models.py (715B)
│   ├── Post (게시글)
│   └── Comment (댓글)
├── views.py (2KB)                    # CRUD 작업
├── serializers.py (1.3KB)
├── urls.py (471B)                    # 5개 엔드포인트
├── permissions.py (860B)             # IsOwnerOrReadOnly
├── forms.py (267B)
└── migrations/
    ├── 0001_initial.py
    └── 0002_rename_post_comment_post.py
```

---

### 6. 📰 naversearch - 네이버 뉴스 검색

**목적**: 네이버 API 기반 뉴스 검색 및 표시

```
naversearch/
├── views.py (4.8KB)                  # 뉴스 검색 & 상세
├── utils.py (4.2KB)                  # 네이버 API 클라이언트
├── models.py (477B)
│   └── News (뉴스 기사 + 북마크 상태)
├── serializers.py (267B)
├── urls.py (336B)                    # 3개 엔드포인트
└── migrations/
    └── 0001_initial.py
```

**URL 엔드포인트**:
- `/search/` - 뉴스 검색
- `/news/<id>/` - 뉴스 상세
- `/bookmark/<id>/` - 북마크 토글

---

### 7. 🗺️ kakaomap - 은행 위치 서비스

**목적**: 카카오 맵 API 기반 은행 위치 표시

```
kakaomap/
├── views.py (3KB)                    # 은행 검색 엔드포인트
├── urls.py (121B)                    # 1개 엔드포인트
├── models.py (empty)
└── migrations/
```

**URL 엔드포인트**:
- `/search/` - 주변 은행 검색

---

### 8. 🥇 gold_silver - 귀금속 시세

**목적**: 금/은 가격 정보 제공

```
gold_silver/
├── views.py (1.5KB)                  # 가격 데이터 엔드포인트
├── urls.py (141B)                    # 1개 엔드포인트
├── data/
│   ├── Gold_prices.xlsx (22KB)
│   └── Silver_prices.xlsx (22KB)
└── migrations/
```

**URL 엔드포인트**:
- `/price/` - 금/은 가격 조회

---

### 9. 📺 youtube - YouTube 통합

**목적**: YouTube 동영상 검색 및 관리

```
youtube/
├── utils.py                          # 유틸리티 함수
├── views.py (771B)                   # 동영상 검색
├── urls.py (162B)                    # 1개 엔드포인트
└── migrations/
```

**URL 엔드포인트**:
- `/search/` - YouTube 동영상 검색

---

## 📚 Backend 추가 파일

### 루트 레벨
```
Backend/
├── manage.py                         # Django 관리 스크립트
├── requirements.txt (1.6KB)          # 70+ 의존성
├── .env                              # 환경 변수 (API 키)
├── .gitignore
├── db.sqlite3 (39MB)                 # SQLite 데이터베이스
├── venv/                             # Python 가상 환경
├── init_survey_data.py (1.8KB)       # 설문 초기화
├── check_product_fields.py (1.5KB)   # 상품 검증
└── test_*.py (18개 테스트 파일)      # 종합 테스트 스위트
```

### 문서
- `CHATBOT_FINAL_SUMMARY.md` (12KB)
- `CHATBOT_MODE_CLASSIFICATION_GUIDE.md` (14KB)
- `CHATBOT_DEBUG_GUIDE.md` (9.5KB)
- `CHATBOT_REQUIREMENTS_SUMMARY.md` (6.8KB)
- `CHATBOT_CLOSING_IMPROVEMENT.md` (5.5KB)
- `PRODUCT_RECOMMENDATION_IMPROVEMENTS.md` (9KB)
- `README.md` (3.3KB)

### 주요 의존성 (requirements.txt)
```
Django==5.2.8
djangorestframework==3.16.1
djangorestframework_simplejwt==5.5.1
dj-rest-auth==7.0.1
django-allauth==65.13.1
django-cors-headers==4.9.0
django-environ==0.12.0
yfinance==1.0
pandas==2.3.3
numpy==2.3.3
beautifulsoup4==4.14.2
requests==2.32.5
selenium==4.38.0
matplotlib==3.10.7
plotly==6.5.0
```

---

## 🎨 Frontend 구조 (Vue.js)

### 프로젝트 설정

**프로젝트명**: Finflow_front
**프레임워크**: Vue 3 + Vite
**상태 관리**: Pinia
**라우팅**: Vue Router
**UI 프레임워크**: Bootstrap 5
**차트**: Chart.js

### 디렉토리 구조

```
Frontend/Finflow_front/
├── public/                           # 정적 자산
│   ├── assets/
│   └── favi.ico
├── src/                              # 소스 코드
│   ├── api/                          # API 클라이언트 (9개 파일)
│   ├── assets/                       # 이미지, 스타일, 데이터
│   ├── components/                   # 재사용 컴포넌트 (27개)
│   ├── composables/                  # Composition API 유틸리티
│   ├── layouts/                      # 레이아웃 컴포넌트 (4개)
│   ├── router/                       # Vue Router 설정
│   ├── stores/                       # Pinia 스토어 (5개)
│   ├── views/                        # 페이지 컴포넌트 (24개)
│   ├── App.vue                       # 루트 컴포넌트
│   └── main.js                       # 진입점
├── package.json                      # 의존성
├── vite.config.js                    # Vite 설정
├── jsconfig.json                     # JavaScript 설정
├── index.html                        # HTML 템플릿
├── .env.local                        # 환경 변수
├── .gitignore
└── README.md
```

---

## 📡 src/api/ - Backend API 클라이언트

```
api/
├── axios.js (1.8KB)                  # Axios 인스턴스 + JWT 인터셉터
├── finances.js (1.8KB)               # 예적금 엔드포인트
├── stocks.js (2.5KB)                 # 주식 엔드포인트
├── market.js (1.1KB)                 # 시장 데이터 엔드포인트
├── youtube.js (997B)                 # YouTube 엔드포인트
├── naver.js (584B)                   # 네이버 뉴스 엔드포인트
├── news.js (363B)                    # 뉴스 엔드포인트
├── gold_silver.js (802B)             # 금/은 엔드포인트
└── kakao.js (190B)                   # 카카오 맵 엔드포인트
```

**핵심 기능**:
- JWT 액세스 토큰 자동 주입
- 자동 토큰 갱신
- 요청/응답 인터셉터

---

## 🎨 src/assets/ - 정적 리소스

```
assets/
├── styles/                           # CSS 파일
│   ├── base.css                      # 전역 스타일
│   ├── table.css                     # 테이블 스타일
│   └── font.css                      # 타이포그래피
├── banks/                            # 은행 로고
├── character/                        # 캐릭터 이미지 (PBTI 아바타)
├── flag/                             # 국가 국기
├── main/                             # 메인 페이지 자산
│   ├── chatbot/
│   ├── finances/
│   ├── icon/                         # 투자성향별 아이콘 (6개)
│   ├── kakaomap/
│   ├── news/
│   ├── pbti/                         # PBTI 타입 이미지
│   ├── posts/
│   ├── stock/
│   └── youtube/
├── navbar/                           # 내비게이션 자산
├── video/                            # 비디오 파일
└── data/                             # 정적 데이터 파일
```

---

## 🧩 src/components/ - 재사용 컴포넌트 (27개)

### 공통 컴포넌트 (5개)
```
components/common/
├── BaseTable.vue (1KB)               # 재사용 테이블
├── ChatbotWidget.vue (38KB)          # AI 챗봇 위젯 (최대 규모)
├── NavBar.vue (12.8KB)               # 메인 내비게이션
├── PopUp.vue (8.9KB)                 # 모달/팝업
└── ScrollToTop.vue (3KB)             # 맨 위로 버튼
```

### 메인 페이지 컴포넌트 (3개)
```
components/main/
├── FeatureSection.vue (11KB)         # 기능 쇼케이스
├── HeroSection.vue (5.6KB)           # 랜딩 히어로 섹션
└── ScreenshotCarousel.vue (5.3KB)    # 이미지 캐러셀
```

### 주식 컴포넌트 (10개)
```
components/stocks/
├── StocksMarketDashboard.vue (21KB)  # 시장 개요
├── IntradayChart.vue (11KB)          # 당일 가격 차트
├── RealtimeStockPrice.vue (9KB)      # 실시간 가격 표시
├── CryptoMarketDashboard.vue (7.9KB) # 암호화폐 시장
├── GlobalMarketDashboard.vue (7.9KB) # 글로벌 시장
├── TopVolumeList.vue (4.4KB)         # 거래량 상위 종목
├── StocksSearchSection.vue (3KB)     # 종목 검색
├── StocksMarketTab.vue (1.5KB)       # 시장 탭
├── StockChart.vue (1.2KB)            # 가격 차트
└── StockNewsList.vue (1.1KB)         # 종목 뉴스 목록
```

### 뉴스 컴포넌트 (4개)
```
components/news/
├── NewsDetail.vue
├── NewsHeader.vue
├── NewsList.vue
└── NewsSummary.vue
```

### 네이버 컴포넌트 (4개)
```
components/naver/
├── NewsDetail.vue
├── NewsList.vue
├── NewsSearchBar.vue
└── NewsSummary.vue
```

### YouTube 컴포넌트 (1개)
```
components/youtube/
└── VideoCard.vue
```

---

## 📄 src/views/ - 페이지 컴포넌트 (24개)

### 인증 뷰 (5개)
```
views/auth/
├── LoginView.vue                     # 로그인
├── SignupView.vue                    # 회원가입
├── MyPageView.vue                    # 마이페이지 & 북마크
├── InvestmentSurveyView.vue          # PBTI 설문
└── RecommendationsView.vue           # 상품 추천
```

### 금융 뷰 (4개)
```
views/finances/
├── FinHomeView.vue                   # 금융 대시보드
├── deposits/
│   └── DepositDetailView.vue         # 예금 상세
├── savings/
│   └── SavingDetailView.vue          # 적금 상세
└── gold_silvers/
    └── Gold_SilverView.vue           # 금/은 가격
```

### 주식 뷰 (4개)
```
views/stocks/
├── StocksHomeView.vue                # 주식 시장 홈 (KOSPI/KOSDAQ)
├── StocksGlobalView.vue              # 글로벌 시장
├── StocksCryptoView.vue              # 암호화폐
└── StockDetailView.vue               # 종목 상세
```

### 커뮤니티 뷰 (4개)
```
views/posts/
├── PostListView.vue                  # 게시판 목록
├── PostDetailView.vue                # 게시글 상세
├── PostCreateView.vue                # 게시글 작성
└── PostEditView.vue                  # 게시글 수정
```

### 뉴스 뷰 (1개)
```
views/news/
└── NaverNewsView.vue                 # 네이버 뉴스 검색
```

### 지도 뷰 (1개)
```
views/kakaomap/
└── BankMapView.vue                   # 은행 위치 지도
```

### YouTube 뷰 (4개)
```
views/youtube/
├── SearchView.vue                    # 동영상 검색
├── VideoDetailView.vue               # 동영상 플레이어
├── SavedVideosView.vue               # 나중에 볼 영상
└── ChannelsView.vue                  # 구독 채널
```

### 메인 뷰 (1개)
```
views/main/
└── MainView.vue                      # 랜딩 페이지
```

---

## 🏗️ src/layouts/ - 레이아웃 래퍼 (4개)

```
layouts/
├── MainLayout.vue (4KB)              # 메인 앱 레이아웃 (NavBar + Footer)
├── FinLayout.vue (165B)              # 금융 섹션 레이아웃
├── KakaoMapLayout.vue (182B)         # 지도 레이아웃
└── YoutubeLayout.vue (246B)          # YouTube 레이아웃
```

**레이아웃 계층**:
```
MainLayout (전역)
├── MainView
├── Auth 페이지들
├── Posts 페이지들
├── FinLayout (스코프)
│   ├── FinHomeView
│   ├── DepositDetailView
│   ├── SavingDetailView
│   └── Gold_SilverView
├── KakaoMapLayout
│   └── BankMapView
├── YoutubeLayout
│   ├── SearchView
│   ├── VideoDetailView
│   ├── SavedVideosView
│   └── ChannelsView
└── Stocks 페이지들
```

---

## 🛣️ src/router/ - Vue Router 설정

```
router/
└── index.js (6.5KB)                  # 라우트 정의 & 가드
```

**라우트 구조**:
```javascript
/ (MainLayout)
├── / → MainView
├── /login → LoginView
├── /signup → SignupView
├── /mypage → MyPageView (인증 필요)
├── /investment-survey → InvestmentSurveyView (인증 필요)
├── /recommendations → RecommendationsView (인증 필요)
├── /posts
│   ├── / → PostListView
│   ├── /create → PostCreateView (인증 필요)
│   ├── /:pk → PostDetailView
│   └── /:pk/edit → PostEditView (인증 필요)
├── /finances (FinLayout)
│   ├── / → FinHomeView
│   ├── /deposits/:fin_prdt_cd → DepositDetailView
│   ├── /savings/:fin_prdt_cd → SavingDetailView
│   └── /gold_silver → Gold_SilverView
├── /naver → NaverNewsView
├── /kakaomap (KakaoMapLayout)
│   └── / → BankMapView
├── /youtube (YoutubeLayout)
│   ├── /search → SearchView
│   ├── /video/:id → VideoDetailView
│   ├── /saved → SavedVideosView
│   └── /channels → ChannelsView
└── /stocks
    ├── / → StocksHomeView
    ├── /global → StocksGlobalView
    ├── /crypto → StocksCryptoView
    └── /:code → StockDetailView
```

**내비게이션 가드**:
- JWT 토큰 검증
- 새로고침 시 사용자 정보 복원
- 보호된 라우트 인증 확인

---

## 🗄️ src/stores/ - Pinia 상태 관리 (5개)

```
stores/
├── auth.js (2.9KB)                   # 인증 상태 (로그인, 사용자, 토큰)
├── stocks.js (7.9KB)                 # 주식 시장 상태
├── market.js (4.3KB)                 # 시장 데이터 상태
├── finSync.js (2.7KB)                # 금융 동기화 상태
└── posts.js (1.1KB)                  # 게시글 상태
```

**auth.js 기능**:
- 로그인/로그아웃
- 토큰 관리
- 사용자 프로필 조회
- 영구 로그인 상태

**stocks.js 기능**:
- 종목 검색
- 가격 데이터
- 시장 지수
- 실시간 업데이트

**market.js 기능**:
- 시장 요약
- 환율
- 지수 가격

**finSync.js 기능**:
- 예적금 데이터 동기화
- 캐시 관리

---

## 🔧 Frontend 설정 파일

### package.json - 의존성

```json
{
  "dependencies": {
    "vue": "^3.5.25",
    "vue-router": "^4.6.3",
    "pinia": "^3.0.4",
    "axios": "^1.13.2",
    "bootstrap": "^5.3.8",
    "bootstrap-icons": "^1.13.1",
    "chart.js": "^4.5.1",
    "chartjs-adapter-date-fns": "^3.0.0",
    "@popperjs/core": "^2.11.8"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^6.0.2",
    "vite": "^7.2.4",
    "vite-plugin-vue-devtools": "^8.0.5"
  }
}
```

### vite.config.js - Vite 설정

- Vue 플러그인
- DevTools 플러그인
- 경로 별칭: `@` → `./src`

### jsconfig.json - JavaScript 설정

- import를 위한 경로 매핑

---

## 🏛️ 전체 아키텍처 패턴

### 아키텍처 타입: **Monorepo (Backend/Frontend 분리)**

```
아키텍처 개요:
┌─────────────────────────────────────────────────────────┐
│                   클라이언트 레이어                       │
│  Vue 3 SPA (포트 5173) - Bootstrap 5 UI                 │
│  - Pinia 상태 관리                                       │
│  - Vue Router (SPA 라우팅)                               │
│  - Axios (JWT 포함 HTTP 클라이언트)                      │
└─────────────────────────────────────────────────────────┘
                         ↓ HTTP/REST API
┌─────────────────────────────────────────────────────────┐
│                    API 게이트웨이                         │
│  Django REST Framework (포트 8000)                       │
│  - JWT 인증                                              │
│  - CORS 미들웨어                                         │
│  - 9개 Django 앱 (마이크로서비스 스타일)                 │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                  비즈니스 로직 레이어                     │
│  ┌──────────┬──────────┬──────────┬──────────┐          │
│  │ accounts │ chatbot  │ finances │  stocks  │          │
│  │ (PBTI)   │ (AI)     │(상품)    │(시장)    │          │
│  └──────────┴──────────┴──────────┴──────────┘          │
│  ┌──────────┬──────────┬──────────┬──────────┐          │
│  │  posts   │  naver   │ kakaomap │ youtube  │          │
│  │(커뮤니티)│(뉴스)    │(위치)    │(동영상)  │          │
│  └──────────┴──────────┴──────────┴──────────┘          │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                    데이터 레이어                          │
│  SQLite3 (db.sqlite3 - 39MB)                             │
│  - 32개 테이블                                           │
│  - User 중심 스키마                                      │
│  - 시계열 데이터 (주식)                                  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                  외부 서비스                              │
│  - Google Gemini API (AI 챗봇)                          │
│  - 금융감독원 API (금융 상품)                            │
│  - Yahoo Finance (주가)                                  │
│  - 네이버 검색 API (뉴스)                                │
│  - 카카오 맵 API (위치)                                  │
│  - YouTube Data API                                      │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 주요 아키텍처 패턴

### 1. RESTful API 설계
- 리소스 기반 URL
- HTTP 메서드 (GET, POST, PATCH, DELETE)
- JWT 인증

### 2. 컴포넌트 기반 UI
- 재사용 가능한 Vue 컴포넌트
- 레이아웃 구성
- 중첩 라우팅

### 3. 상태 관리
- 중앙화된 Pinia 스토어
- 반응형 데이터 플로우
- API 통합 레이어

### 4. 서비스 레이어 패턴
- Backend: `services/` 모듈 (stocks, chatbot)
- Frontend: `api/` 클라이언트
- 관심사의 분리

### 5. 예약 작업
- Django 관리 명령
- 일일 데이터 동기화
- 기능 계산

### 6. PBTI 추천 엔진
- 설문 기반 프로파일링
- 위험도 기반 상품 매칭
- 주식 기술 분석

---

## ✨ 주요 기능 & 기능성

### 1. PBTI 투자 성향 시스템
- 6가지 투자 타입 (성별 x 위험 수준)
- 설문 기반 분류
- 맞춤형 추천

### 2. 금융 상품 추천
- 예적금 매칭
- 기술 분석 기반 주식 추천
- 매칭 스코어 계산

### 3. AI 챗봇
- Google Gemini 통합
- 모드 분류 (상품, 주식, 일반)
- 대화 히스토리
- 맞춤형 응답

### 4. 주식 시장 분석
- 실시간 가격 추적
- 기술 지표 (수익률, 변동성, 낙폭)
- 시장 지수 (KOSPI, KOSDAQ)
- 주식 뉴스 집계
- 일중 차트

### 5. 다중 소스 뉴스
- 네이버 뉴스 검색
- 종목별 뉴스
- 북마크 기능

### 6. 커뮤니티 기능
- 사용자 게시글 & 댓글
- 북마크 시스템 (상품, 주식, 뉴스, 동영상)

### 7. 위치 서비스
- 은행 위치 검색
- 카카오 맵 통합

### 8. YouTube 통합
- 동영상 검색
- 채널 구독
- 나중에 볼 영상 목록

---

## 📊 데이터 플로우 예시

### 사용자 온보딩 플로우
```
1. SignupView → POST /accounts/registration/
2. InvestmentSurveyView → GET /accounts/survey/questions/
3. 사용자 설문 완료 → POST /accounts/survey/submit/
4. 백엔드 risk_type 계산 → InvestmentProfile 생성
5. RecommendationsView → GET /accounts/recommendations/
6. 맞춤형 상품 표시
```

### 종목 상세 플로우
```
1. StocksHomeView → GET /api/stocks/market/summary/
2. 사용자 종목 검색 → GET /api/stocks/search/?q=삼성
3. StockDetailView → GET /api/stocks/005930/
4. 병렬 요청:
   - GET /api/stocks/005930/prices/
   - GET /api/stocks/005930/news/
   - GET /api/stocks/005930/realtime/
   - GET /api/stocks/005930/explain/
5. 종합 주식 정보 표시
```

### 챗봇 상호작용 플로우
```
1. 사용자 ChatbotWidget 열기
2. 사용자 메시지 입력 → POST /chatbot/chat/
3. 백엔드:
   - mode_classifier.py 의도 분류
   - services.py 응답 생성
   - InvestmentProfile 조회 (맞춤화)
4. AI 응답 + recommended_products (JSON) 반환
5. 위젯에 응답 & 상품 카드 표시
```

---

## 🚀 배포 고려사항

### Backend
- **서버**: Django 개발 서버 (포트 8000)
- **데이터베이스**: SQLite3 (프로덕션은 PostgreSQL 권장)
- **정적 파일**: Django 정적 파일
- **CORS**: localhost:5173 설정

### Frontend
- **서버**: Vite 개발 서버 (포트 5173)
- **빌드**: `npm run build` → dist/ 폴더
- **환경**: `.env.local` API 키용

### 필수 환경 변수

**Backend (.env)**:
- API_KEY (일반)
- NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
- GMS_KEY (Google Gemini)
- DJANGO_SECRET_KEY
- KAKAO_MOBILITY_REST_KEY
- YOUTUBE_API_KEY
- STOCK_PRICE_API_KEY

**Frontend (.env.local)**:
- VITE_API_BASE_URL (백엔드 URL)

---

## 📈 프로젝트 통계

### Backend
- **Django 앱**: 9개
- **데이터베이스 모델**: 32개
- **API 엔드포인트**: 70+
- **관리 명령**: 6개
- **서비스 모듈**: 9개
- **테스트 파일**: 18개

### Frontend
- **컴포넌트**: 27개
- **뷰**: 24개
- **레이아웃**: 4개
- **Pinia 스토어**: 5개
- **API 클라이언트**: 9개

### 전체
- **코드 라인**: ~15,000+ (추정)
- **외부 API 통합**: 6개
- **데이터베이스 크기**: 39MB

---

## 🎓 요약

**PBTI 기반 맞춤형 금융 추천 플랫폼**:

- **Backend**: 9개 Django 앱, 32개 데이터베이스 모델, 70+ API 엔드포인트
- **Frontend**: 27개 컴포넌트, 24개 뷰, 5개 Pinia 스토어
- **기능**: AI 챗봇, 주식 분석, 금융 상품, 커뮤니티, 뉴스, 지도
- **아키텍처**: 관심사의 명확한 분리를 갖춘 Monorepo
- **기술 스택**: Django REST + Vue 3 + Pinia + Bootstrap 5 + Chart.js

이 프로젝트는 프론트엔드와 백엔드의 적절한 분리, 포괄적인 API 설계, 여러 외부 서비스와의 통합을 통해 잘 구조화된 풀스택 애플리케이션을 보여줍니다.
