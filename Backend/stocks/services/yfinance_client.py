"""
yfinance를 사용한 실시간 주가 및 인트라데이 데이터 조회 서비스
"""
import os
import sys
import shutil
from pathlib import Path

# curl_cffi의 한글 경로 문제 해결
# Windows 환경에서 사용자 이름에 한글이 포함되어 있으면 SSL 인증서를 찾지 못하는 문제 발생
# 해결: certifi의 인증서를 프로젝트 내 안전한 경로로 자동 복사
def setup_ssl_cert():
    """SSL 인증서를 한글이 없는 경로로 설정"""
    try:
        import certifi
        import tempfile

        # Windows의 경우 시스템 임시 폴더 사용 (보통 C:\Windows\Temp 또는 C:\Temp)
        # 한글이 없는 안전한 경로
        if sys.platform == 'win32':
            # ProgramData는 보통 C:\ProgramData로 한글이 없음
            cert_dir = Path(os.environ.get('PROGRAMDATA', 'C:/ProgramData')) / 'finflow_ssl'
        else:
            # Linux/Mac은 /tmp 사용
            cert_dir = Path('/tmp/finflow_ssl')

        cert_file = cert_dir / 'cacert.pem'

        # 디렉토리가 없으면 생성
        cert_dir.mkdir(exist_ok=True, parents=True)

        # 인증서가 없으면 복사
        if not cert_file.exists():
            original_cert = Path(certifi.where())
            shutil.copy(original_cert, cert_file)
            # 첫 실행 시에만 로그 출력 (Django 환경에서 logger 사용)
            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"SSL 인증서를 안전한 경로로 복사했습니다: {cert_file}")
            except:
                pass  # 로깅 실패해도 계속 진행

        # 환경변수 설정 (절대 경로, forward slash 사용)
        cert_path_str = str(cert_file.absolute()).replace('\\', '/')
        os.environ['CURL_CA_BUNDLE'] = cert_path_str
        os.environ['SSL_CERT_FILE'] = cert_path_str

    except Exception as e:
        print(f"[YFinance] SSL 인증서 설정 실패: {e}")
        # 실패해도 yfinance는 시도해볼 수 있으므로 계속 진행

# 모듈 로드 시 자동 실행
setup_ssl_cert()

import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd


class YFinanceClient:
    """
    yfinance를 활용한 주식 데이터 조회 클라이언트
    - 실시간에 가까운 주가 정보 조회
    - 인트라데이 차트 데이터 조회 (1분, 5분, 15분, 30분, 1시간)
    """

    # 한국 주식은 .KS (KOSPI) 또는 .KQ (KOSDAQ) 접미사 필요
    KOSPI_SUFFIX = ".KS"
    KOSDAQ_SUFFIX = ".KQ"

    @staticmethod
    def _get_ticker_symbol(code: str, market: str = "KOSPI") -> str:
        """
        주식/암호화폐 코드를 yfinance 티커 심볼로 변환

        Examples:
            '005930', 'KOSPI' -> '005930.KS' (한국 주식)
            'AAPL', 'US' -> 'AAPL' (미국 주식)
            'BTC-USD', 'CRYPTO' -> 'BTC-USD' (암호화폐)

        Args:
            code: 주식/암호화폐 코드
            market: 시장 구분 ('KOSPI', 'KOSDAQ', 'US', 'CRYPTO' 등)

        Returns:
            yfinance 티커 심볼
        """
        # 이미 점(.)이나 하이픈(-)이 있으면 그대로 사용 (미국 주식 또는 암호화폐)
        if "." in code or "-" in code:
            return code

        # 한국 주식만 접미사 추가
        if market == "KOSPI":
            return f"{code}{YFinanceClient.KOSPI_SUFFIX}"
        elif market == "KOSDAQ":
            return f"{code}{YFinanceClient.KOSDAQ_SUFFIX}"
        else:
            # US, CRYPTO 등은 그대로 사용
            return code

    @staticmethod
    def get_realtime_price(code: str, market: str = "KOSPI") -> Optional[Dict[str, Any]]:
        """
        실시간 주가 정보 조회 (15-20분 지연)

        Args:
            code: 주식 코드 (예: '005930')
            market: 시장 구분 ('KOSPI' 또는 'KOSDAQ')

        Returns:
            {
                'code': '005930',
                'name': '삼성전자',
                'current_price': 70000,
                'previous_close': 69500,
                'open': 69800,
                'high': 70500,
                'low': 69300,
                'volume': 12345678,
                'change': 500,
                'change_percent': 0.72,
                'market_cap': 1234567890000,
                'updated_at': '2025-12-24 15:30:00',
                'market_state': 'REGULAR' or 'CLOSED' or 'PRE' or 'POST'
            }
        """
        try:
            ticker_symbol = YFinanceClient._get_ticker_symbol(code, market)
            ticker = yf.Ticker(ticker_symbol)

            # 기본 정보
            info = ticker.info

            # 실시간 가격 데이터 (최근 1일)
            hist = ticker.history(period="1d", interval="1m")

            if hist.empty:
                return None

            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            previous_close = info.get('previousClose') or info.get('regularMarketPreviousClose')

            # 최신 데이터에서 가격 정보 추출
            latest = hist.iloc[-1]

            if current_price is None:
                current_price = latest['Close']

            change = current_price - previous_close if previous_close else 0
            change_percent = (change / previous_close * 100) if previous_close else 0

            # 시장 상태 확인
            market_state = info.get('marketState', 'CLOSED')

            return {
                'code': code,
                'name': info.get('longName') or info.get('shortName', ''),
                'current_price': int(current_price) if current_price else None,
                'previous_close': int(previous_close) if previous_close else None,
                'open': int(latest['Open']) if not pd.isna(latest['Open']) else None,
                'high': int(latest['High']) if not pd.isna(latest['High']) else None,
                'low': int(latest['Low']) if not pd.isna(latest['Low']) else None,
                'volume': int(latest['Volume']) if not pd.isna(latest['Volume']) else None,
                'change': int(change),
                'change_percent': round(change_percent, 2),
                'market_cap': info.get('marketCap'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'market_state': market_state,
            }

        except Exception as e:
            print(f"Error fetching realtime price for {code}: {str(e)}")
            return None

    @staticmethod
    def get_intraday_prices(
        code: str,
        market: str = "KOSPI",
        interval: str = "5m",
        days: int = 1
    ) -> List[Dict[str, Any]]:
        """
        인트라데이 차트 데이터 조회

        Args:
            code: 주식 코드 (예: '005930')
            market: 시장 구분 ('KOSPI' 또는 'KOSDAQ')
            interval: 시간 간격 ('1m', '5m', '15m', '30m', '1h')
            days: 조회 일수 (1, 5, 30, 60)

        Returns:
            [
                {
                    'datetime': '2025-12-24 09:00:00',
                    'open': 69800,
                    'high': 70000,
                    'low': 69700,
                    'close': 69900,
                    'volume': 123456
                },
                ...
            ]
        """
        try:
            ticker_symbol = YFinanceClient._get_ticker_symbol(code, market)
            ticker = yf.Ticker(ticker_symbol)

            # 기간 설정
            if days == 1:
                period = "1d"
            elif days <= 5:
                period = "5d"
            elif days <= 30:
                period = "1mo"
            else:
                period = "3mo"

            # 인트라데이 데이터 조회
            hist = ticker.history(period=period, interval=interval)

            if hist.empty:
                return []

            # DataFrame을 딕셔너리 리스트로 변환
            result = []
            for idx, row in hist.iterrows():
                result.append({
                    'datetime': idx.strftime('%Y-%m-%d %H:%M:%S'),
                    'open': int(row['Open']) if not pd.isna(row['Open']) else None,
                    'high': int(row['High']) if not pd.isna(row['High']) else None,
                    'low': int(row['Low']) if not pd.isna(row['Low']) else None,
                    'close': int(row['Close']) if not pd.isna(row['Close']) else None,
                    'volume': int(row['Volume']) if not pd.isna(row['Volume']) else None,
                })

            return result

        except Exception as e:
            print(f"Error fetching intraday prices for {code}: {str(e)}")
            return []

    @staticmethod
    def validate_interval(interval: str) -> bool:
        """
        유효한 interval 값인지 확인
        """
        valid_intervals = ['1m', '5m', '15m', '30m', '1h', '1d']
        return interval in valid_intervals

    @staticmethod
    def get_market_hours_status() -> Dict[str, Any]:
        """
        한국 증시 개장 시간 확인 (09:00 ~ 15:30 KST)

        Returns:
            {
                'is_open': True/False,
                'current_time': '2025-12-24 14:30:00',
                'next_open': '2025-12-25 09:00:00',
                'next_close': '2025-12-24 15:30:00'
            }
        """
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        current_weekday = now.weekday()  # 0=Monday, 6=Sunday

        # 주말 체크
        if current_weekday >= 5:  # Saturday or Sunday
            is_open = False
            # 다음 월요일 계산
            days_until_monday = 7 - current_weekday
            next_open = now + timedelta(days=days_until_monday)
            next_open = next_open.replace(hour=9, minute=0, second=0, microsecond=0)
        else:
            # 장 시간 체크 (09:00 ~ 15:30)
            market_start = 9 * 60  # 09:00 in minutes
            market_end = 15 * 60 + 30  # 15:30 in minutes
            current_minutes = current_hour * 60 + current_minute

            is_open = market_start <= current_minutes < market_end

            if current_minutes < market_start:
                # 오늘 개장 전
                next_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
                next_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
            elif current_minutes >= market_end:
                # 오늘 장 마감 후
                next_open = now + timedelta(days=1)
                next_open = next_open.replace(hour=9, minute=0, second=0, microsecond=0)
                next_close = None
            else:
                # 장 중
                next_open = None
                next_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

        return {
            'is_open': is_open,
            'current_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'next_open': next_open.strftime('%Y-%m-%d %H:%M:%S') if next_open else None,
            'next_close': next_close.strftime('%Y-%m-%d %H:%M:%S') if next_close else None,
        }
