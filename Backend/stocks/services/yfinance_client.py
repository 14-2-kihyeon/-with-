"""
yfinance를 사용한 실시간 주가 및 인트라데이 데이터 조회 서비스
"""
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
        한국 주식 코드를 yfinance 티커 심볼로 변환
        예: '005930' (삼성전자) -> '005930.KS'
        """
        if "." in code:
            return code

        suffix = YFinanceClient.KOSPI_SUFFIX if market == "KOSPI" else YFinanceClient.KOSDAQ_SUFFIX
        return f"{code}{suffix}"

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
