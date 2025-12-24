# Finflow Backend

Django 기반의 주식 추천 및 분석 서비스 백엔드

## 주요 기능

- 주식 추천 시스템
- 실시간 주가 조회 (yfinance)
- 인트라데이 차트 데이터
- 뉴스 수집 및 분석
- AI 기반 종목 설명

## 설치 및 실행

### 1. 가상환경 생성 및 활성화

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 데이터베이스 마이그레이션

```bash
python manage.py migrate
```

### 4. 개발 서버 실행

```bash
python manage.py runserver
```

## 실시간 데이터 기능 (yfinance)

### 한글 경로 문제 자동 해결

Windows 환경에서 **사용자 이름에 한글이 포함**되어 있으면 yfinance가 사용하는 `curl_cffi` 라이브러리가 SSL 인증서를 찾지 못하는 문제가 발생할 수 있습니다.

**✅ 이 문제는 완전히 자동으로 해결됩니다:**

1. **자동 감지 및 복사**
   - 첫 실행 시 시스템 경로(`C:\ProgramData\finflow_ssl\`)에 SSL 인증서 자동 복사
   - 프로젝트 폴더가 아닌 시스템 공통 폴더 사용

2. **Git과 무관**
   - 인증서는 각 PC에서 자동 생성되므로 Git 저장소에 포함되지 않음
   - `pull` 받은 후 첫 실행 시 자동으로 설정됨

3. **별도 설정 불필요**
   - 환경변수 자동 설정
   - 코드 수정 불필요
   - 관리자 권한 필요 없음 (ProgramData 폴더 쓰기 가능)

**배포 시:**
- 코드를 그대로 배포하면 모든 사용자(한글 경로 포함)가 자동으로 실시간 데이터를 받을 수 있습니다

### API 엔드포인트

#### 실시간 주가 조회
```
GET /api/stocks/{code}/realtime/
```

**응답 예시:**
```json
{
  "endpoint": "realtime",
  "code": "005930",
  "data": {
    "current_price": 70000,
    "change": 500,
    "change_percent": 0.72,
    "volume": 12345678,
    ...
  },
  "market_status": {
    "is_open": false,
    "next_open": "2025-12-25 09:00:00"
  }
}
```

#### 인트라데이 차트 데이터
```
GET /api/stocks/{code}/intraday/?interval=5m&days=1
```

**파라미터:**
- `interval`: 시간 간격 (1m, 5m, 15m, 30m, 1h)
- `days`: 조회 일수 (1, 5, 30, 60)

**응답 예시:**
```json
{
  "endpoint": "intraday",
  "code": "005930",
  "count": 78,
  "prices": [
    {
      "datetime": "2025-12-24 09:00:00",
      "open": 69800,
      "high": 70000,
      "low": 69700,
      "close": 69900,
      "volume": 123456
    },
    ...
  ]
}
```

## 기술 스택

- **Django** - 웹 프레임워크
- **Django REST Framework** - API 구축
- **yfinance** - 실시간 주가 데이터
- **pandas** - 데이터 처리
- **numpy** - 수치 계산
- **scikit-learn** - 머신러닝

## 트러블슈팅

### SSL 인증서 오류

```
curl: (77) error setting certificate verify locations
```

**원인:** 사용자 경로에 한글이 포함되어 있음

**해결:** 자동으로 처리되지만, 수동으로 확인하려면:
```bash
python -c "from stocks.services.yfinance_client import YFinanceClient; print(YFinanceClient.get_realtime_price('005930', 'KOSPI'))"
```

### 데이터가 조회되지 않음

1. 인터넷 연결 확인
2. 종목 코드가 올바른지 확인
3. 시장 개장 시간 확인 (09:00 ~ 15:30 KST)
4. yfinance 서비스 상태 확인
