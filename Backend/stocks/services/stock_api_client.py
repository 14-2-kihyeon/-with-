import os
import time
import requests
from datetime import datetime
from typing import Any, Dict, List, Optional


def _to_int(value: Any) -> Optional[int]:
    """
    API 숫자 문자열(콤마 포함)을 int로 변환.
    '-', None, '' 같은 값은 None 처리.
    """
    if value is None:
        return None
    s = str(value).strip()
    if s in ("", "-", "null", "None"):
        return None
    s = s.replace(",", "")
    try:
        return int(s)
    except ValueError:
        return None


def _to_date_yyyymmdd(value: Any):
    """
    basDt: 'YYYYMMDD' -> date 객체
    """
    s = str(value).strip()
    return datetime.strptime(s, "%Y%m%d").date()


class StockPriceAPIClient:
    """
    금융위원회 주식시세정보 계열 API 호출 클라이언트.
    - response 구조가 (data.go.kr 표준 response/body/items) 인 경우를 우선 지원
    - 일부 odcloud 스타일(data: [...])도 fallback 지원
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        service_key: Optional[str] = None,
        timeout: int = 20,
    ):
        self.base_url = base_url or os.getenv("STOCK_PRICE_API_URL", "").strip()
        self.service_key = service_key or os.getenv("STOCK_PRICE_API_KEY", "").strip()
        self.timeout = timeout

        if not self.base_url:
            raise RuntimeError("STOCK_PRICE_API_URL 환경변수가 비어있습니다.")
        if not self.service_key:
            raise RuntimeError("STOCK_PRICE_API_KEY 환경변수가 비어있습니다.")

    def fetch_by_date(self, bas_dt: str, rows: int = 1000, sleep_sec: float = 0.1) -> List[Dict[str, Any]]:
        """
        basDt(YYYYMMDD) 하루치 스냅샷을 페이지네이션으로 전부 가져와서
        표준화된 dict 리스트로 반환.
        """
        all_items: List[Dict[str, Any]] = []
        page_no = 1
        total_count = None

        while True:
            payload = self._request(bas_dt=bas_dt, page_no=page_no, rows=rows)
            items, total = self._extract_items(payload)

            if total_count is None and total is not None:
                total_count = total

            if not items:
                break

            all_items.extend(items)

            # 끝 조건(1): totalCount 기반
            if total_count is not None and len(all_items) >= total_count:
                break

            # 끝 조건(2): 현재 페이지가 rows보다 적게 왔으면 마지막 페이지
            if len(items) < rows:
                break

            page_no += 1
            time.sleep(sleep_sec)

        # 표준화(필드 매핑)해서 반환
        normalized = []
        for raw in all_items:
            norm = self._normalize_item(raw)
            if norm is not None:
                normalized.append(norm)

        return normalized

    def _request(self, bas_dt: str, page_no: int, rows: int) -> Dict[str, Any]:
        params = {
            "serviceKey": self.service_key,
            "resultType": "json",
            "basDt": bas_dt,
            "pageNo": page_no,
            "numOfRows": rows,
        }
        r = requests.get(self.base_url, params=params, timeout=self.timeout)
        r.raise_for_status()

        try:
            return r.json()
        except Exception as e:
            # JSON이 아닌 응답(XML 등)이면 여기서 바로 잡힘
            raise RuntimeError(f"API 응답이 JSON이 아닙니다. URL/params 확인 필요. 원인: {e}")

    def _extract_items(self, payload: Dict[str, Any]) -> (List[Dict[str, Any]], Optional[int]):
        """
        1) data.go.kr 표준 구조:
           { response: { body: { items: { item: [...] }, totalCount: ... } } }
        2) odcloud 구조(케이스별):
           { data: [...], totalCount: ... }
        """
        # 1) 표준 response/body/items 구조
        if isinstance(payload, dict) and "response" in payload:
            body = payload.get("response", {}).get("body", {}) or {}
            total = body.get("totalCount")
            total_int = _to_int(total)

            items_container = body.get("items", {}) or {}
            items = items_container.get("item", [])

            if isinstance(items, dict):
                items = [items]
            if not isinstance(items, list):
                items = []

            return items, total_int

        # 2) odcloud 구조 fallback
        if isinstance(payload, dict) and "data" in payload:
            data = payload.get("data", [])
            if isinstance(data, dict):
                data = [data]
            total_int = _to_int(payload.get("totalCount"))
            return data if isinstance(data, list) else [], total_int

        # 알 수 없는 구조
        raise RuntimeError(f"알 수 없는 API 응답 구조입니다: keys={list(payload.keys())}")

    def _normalize_item(self, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        raw 1건(종목 1개)의 키를 표준화해서 반환.
        최소 필드(코드/이름/날짜/가격/거래량) 없으면 None
        """
        # 필드명은 API마다 약간 다를 수 있어 key fallback을 둠
        code = raw.get("srtnCd") or raw.get("stockCode") or raw.get("itmsNo")
        name = raw.get("itmsNm") or raw.get("stockName") or raw.get("itmsNmKor")
        bas_dt = raw.get("basDt") or raw.get("date")

        if not code or not name or not bas_dt:
            return None

        date_obj = _to_date_yyyymmdd(bas_dt)

        # OHLCV
        close = _to_int(raw.get("clpr"))
        open_ = _to_int(raw.get("mkp"))
        high = _to_int(raw.get("hipr"))
        low = _to_int(raw.get("lopr"))
        volume = _to_int(raw.get("trqu"))

        if close is None or open_ is None or high is None or low is None or volume is None:
            # 일시적으로 결측이 섞이면 저장하지 않음(데이터 품질)
            return None

        # 거래대금: API에 따라 trPrc / trprc / trPrc 등 다르게 올 수 있어 optional
        amount = _to_int(raw.get("trPrc") or raw.get("trprc") or raw.get("trPrc"))

        market = raw.get("mrktCtg") or raw.get("mrktCls") or ""

        market_cap = _to_int(raw.get("mrktTotAmt"))
        listed_shares = _to_int(raw.get("lstgStCnt"))

        return {
            "code": str(code).strip(),
            "name": str(name).strip(),
            "market": str(market).strip(),
            "date": date_obj,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "amount": amount,
            "market_cap": market_cap,
            "listed_shares": listed_shares,
        }

    def has_data(self, bas_dt: str) -> bool:
        """
        해당 날짜 데이터가 존재하는지만 빠르게 확인(numOfRows=1)
        """
        payload = self._request(bas_dt=bas_dt, page_no=1, rows=1)
        items, total = self._extract_items(payload)
        if total is not None:
            return total > 0
        return len(items) > 0