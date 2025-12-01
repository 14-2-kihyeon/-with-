# 📰 SSAFY 뉴스 검색기
## 📌 프로젝트 개요
본 프로젝트는 네이버 뉴스 검색 Open API를 활용하여 금융/SSAFY 관련 뉴스를 검색·저장·조회·북마크·요약하는 웹 서비스를 만드는 것을 목표로 한다.
Django 기반 REST API 서버를 구축하고,
프론트엔드에서는 axios를 이용해 비동기 통신으로 뉴스를 조회 및 제어할 수 있도록 구현했다.
또한 OpenAI(GMS) API를 활용해 선택한 기사의 내용을 한눈에 볼 수 있는 요약본으로 제공한다.

## 🖼️ 실행 화면

※ 위 경로(./images/ssafy-news-finished.png)에 이 README 상단에 첨부한 스크린샷을 저장해 두면 정상적으로 표시된다.

![SSAFY 뉴스 검색기 화면](./images/capture.png)



### 🏗️ 기술 스택
Backend
Python 3
Django
Django REST Framework (DRF)
requests (Naver API 요청)
Frontend
HTML, CSS, JavaScript
axios (AJAX 통신)
DB
SQLite3 (Django 기본 DB)
기타
python-dotenv / django-environ (.env로 API KEY 관리)
OpenAI / GMS API (뉴스 요약)

## 📁 주요 기능 요약

1. 뉴스 검색 & 저장 (F01)

네이버 뉴스 검색 Open API를 이용해 키워드 기반으로 뉴스를 조회한다.
응답받은 뉴스 중 새로운 기사만 DB에 저장하여 중복 저장을 방지한다.
검색 시마다 기존 데이터는 유지하면서 새 기사만 추가한다.

2. 전체 뉴스 목록 조회 (F02)

페이지 진입 또는 검색 후, 저장된 모든 뉴스를 좌측 리스트로 출력한다.
뉴스가 없을 경우 안내 문구를 표시한다.
뉴스 리스트 영역만 스크롤 가능하도록 구현했다.

3. 뉴스 상세 보기 (F03)

좌측에서 기사를 클릭하면 우측 영역에 다음 정보를 표시한다.

제목
본문(요약/설명)
발행일
원문 링크
긴 내용도 편하게 볼 수 있도록 우측 영역에 별도 스크롤을 적용했다.

4. 북마크 토글 (F04)

각 기사마다 별(★) 아이콘으로 북마크 상태를 표시한다.
별 아이콘 클릭 시 is_bookmarked 값을 토글하여 DB에 반영한다.
응답값을 기반으로 즉시 UI에 반영되도록 axios로 비동기 요청/응답을 처리했다.

5. 전체 / 북마크 보기 전환 (F05)

상단에 [전체 보기] / [북마크 보기] 버튼을 제공한다.
전체 보기 클릭 시: DB에 저장된 모든 뉴스를 출력한다.
북마크 보기 클릭 시: is_bookmarked = True 인 기사만 필터링하여 출력한다.
선택된 탭이 시각적으로 구분되도록 스타일을 적용했다.

6. AI 요약 기능 (심화, F06)

우측 상세 영역에 [요약 보기] 버튼을 제공한다.
버튼 클릭 시:
해당 기사의 본문(또는 요약 가능한 텍스트)을 서버로 전송한다.
서버에서 OpenAI(GMS) API를 호출해 2~3문장 정도의 요약을 생성한다.
요약 결과를 상세 영역 하단에 표시한다.
호출 실패 시 에러 메시지를 보여주고, 원문은 그대로 유지한다.

🔌 API 엔드포인트 예시
- Method	URL	설명
```
GET	/api/news/	전체 뉴스 목록 조회
GET	/api/news/?bookmark=true	북마크된 뉴스 목록 조회
GET	/api/news/<id>/	특정 뉴스 상세 조회
POST	/api/news/search/	검색어 기반 Naver 검색 & 저장
POST	/api/news/<id>/bookmark/	북마크 상태 토글
POST	/api/news/<id>/summary/	AI 요약 생성 요청
실제 URL 네이밍은 프로젝트 구조에 따라 약간 달라질 수 있다.
```

🗂️ 디렉토리 구조 (예시)
```
.
├─ backend/
│  ├─ config/              # Django 프로젝트 설정
│  ├─ news/                # 뉴스 관련 앱
│  │  ├─ models.py         # News 모델 정의
│  │  ├─ serializers.py    # NewsSerializer
│  │  ├─ views.py          # 목록/상세/북마크/요약 API
│  │  ├─ urls.py           # /api/news/ 라우팅
│  │  └─ utils.py          # Naver 뉴스 API 호출 함수
│  └─ templates/
│     └─ index.html        # 메인 화면 템플릿
├─ static/
│  ├─ css/
│  │  └─ style.css         # 레이아웃 및 스타일
│  └─ js/
│     └─ app.js            # axios 요청 & DOM 조작
├─ .env                    # NAVER / OPENAI / GMS KEY
├─ requirements.txt
└─ README.md
```


## 💬 느낀 점

외부 Open API(Naver)와 생성형 AI(OpenAI/GMS)를 한 프로젝트 안에서 함께 사용하는 경험을 할 수 있었다.
DRF로 **CRUD + 상태 토글 + 추가 액션(요약)**까지 구현하면서 REST API 설계와 구현 흐름을 익혔다.
axios로 비동기 UI를 구성하며, 프론트엔드와 백엔드 간 데이터 흐름을 전체적으로 이해할 수 있었다.