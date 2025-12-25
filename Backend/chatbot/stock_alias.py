# chatbot/stock_alias.py
"""
주식 종목 별명/alias 매핑 모듈
사용자가 "삼전", "sk텔", "005930" 등 다양한 표현으로 검색해도
정확한 종목명으로 변환
"""

# 종목 별명 사전 (canonical name: [aliases])
STOCK_ALIASES = {
    # 삼성그룹
    "삼성전자": ["삼전", "삼성", "005930", "samsung"],
    "삼성전자우": ["삼전우", "005935"],
    "삼성물산": ["삼물", "028260"],
    "삼성SDI": ["삼디", "006400"],
    "삼성바이오로직스": ["삼바", "207940"],

    # SK그룹
    "SK하이닉스": ["하이닉스", "sk하닉", "000660"],
    "SK텔레콤": ["sk텔", "sk통신", "017670"],
    "SK이노베이션": ["sk이노", "096770"],
    "SK바이오팜": ["sk바팜", "326030"],

    # 현대그룹
    "현대차": ["현차", "005380"],
    "기아": ["기아차", "000270"],
    "현대모비스": ["모비스", "012330"],

    # 네이버/카카오
    "NAVER": ["네이버", "035420"],
    "카카오": ["kakao", "035720"],
    "카카오뱅크": ["카뱅", "323410"],
    "카카오페이": ["카페이", "377300"],

    # LG그룹
    "LG전자": ["엘지", "lg", "066570"],
    "LG화학": ["엘화", "051910"],
    "LG에너지솔루션": ["엘솔", "373220"],

    # 포스코
    "POSCO홀딩스": ["포스코", "posco", "005490"],
    "포스코퓨처엠": ["포퓨엠", "003670"],

    # 금융
    "KB금융": ["국민은행", "105560"],
    "신한지주": ["신한", "055550"],
    "하나금융지주": ["하나", "086790"],
    "우리금융지주": ["우리", "316140"],

    # 기타 주요 종목
    "셀트리온": ["셀", "068270"],
    "삼성생명": ["삼생", "032830"],
    "NAVER": ["네이버", "035420"],
    "LG유플러스": ["lg유플", "032640"],
    "한국전력": ["한전", "015760"],
}

def normalize_stock_query(query: str) -> str:
    """
    사용자 입력을 정규화
    - 공백 제거
    - 소문자 변환
    - 특수문자 제거
    """
    import re
    # 공백 제거
    normalized = query.strip()
    # 조사 제거 (간단한 버전)
    normalized = re.sub(r'(은|는|이|가|을|를|의|에|도|만|부터|까지|로|으로)', '', normalized)
    # 공백/특수문자 제거
    normalized = re.sub(r'[\s\-_.,]', '', normalized)
    return normalized.lower()

def find_stock_by_alias(query: str) -> list:
    """
    사용자 쿼리에서 종목명 추출

    Args:
        query: 사용자 입력 문자열

    Returns:
        list: 매칭된 정식 종목명 리스트
    """
    normalized_query = normalize_stock_query(query)
    matched_stocks = []

    # Alias 사전에서 검색
    for canonical_name, aliases in STOCK_ALIASES.items():
        # 정식 명칭 확인
        if normalize_stock_query(canonical_name) in normalized_query:
            if canonical_name not in matched_stocks:
                matched_stocks.append(canonical_name)
            continue

        # Alias 확인
        for alias in aliases:
            if normalize_stock_query(alias) in normalized_query:
                if canonical_name not in matched_stocks:
                    matched_stocks.append(canonical_name)
                break

    return matched_stocks

def expand_stock_search_terms(stock_name: str) -> list:
    """
    종목명을 모든 가능한 검색어로 확장

    Args:
        stock_name: 정식 종목명

    Returns:
        list: 검색에 사용할 수 있는 모든 용어 (종목명 + aliases)
    """
    search_terms = [stock_name]

    if stock_name in STOCK_ALIASES:
        search_terms.extend(STOCK_ALIASES[stock_name])

    return search_terms
