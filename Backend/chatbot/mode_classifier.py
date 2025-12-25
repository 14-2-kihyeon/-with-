# chatbot/mode_classifier.py
"""
챗봇 모드 분류기
CHAT_MODE: 일반 대화 (인사/잡담/감정)
SERVICE_MODE: Finflow 기능 질문 (주식/예적금/뉴스/북마크 등)
"""

import re

# ===== 모드 분류 키워드 사전 =====
CHAT_KEYWORDS = {
    # 인사
    '안녕', '하이', '헬로', 'hello', 'hi', '반가워', '처음', '만나서',

    # 감정/반응
    'ㅋㅋ', 'ㅎㅎ', 'ㅋ', 'ㅎ', '하하', '웃기', '재밌', '좋아', '싫어', '슬퍼', '기뻐',
    '짜증', '화나', '속상', '우울', '행복', '최고', '굿', 'good', 'nice', '멋져',

    # 감사/인정
    '고마워', '감사', '땡큐', 'thank', '고맙', '수고', '잘했어', '잘해',

    # 일상 대화
    '어때', '뭐해', '심심', '배고파', '졸려', '피곤', '힘들', '바빠',
    '날씨', '시간', '오늘', '내일', '어제', '주말', '월요일',

    # 짧은 반응어
    '오', '아', '음', '네', '응', '그래', '알겠', '오케이', 'ok', 'okay',
    '예', '아니', '노', 'no', 'yes', '맞아', '틀려',

    # 기타
    '누구', '뭐', '어디', '언제', '왜', '어떻게',  # 추상적 질문
}

SERVICE_KEYWORDS = {
    # 주식 관련
    '주식', '주가', '시세', '종목', '전망', '분석', '매수', '매도', '투자',
    '삼성전자', '삼전', 'sk하이닉스', '하이닉스', 'sk텔레콤', 'sk텔', '네이버',
    '카카오', '현대차', '삼성', '엘지', 'lg', 'posco', '포스코', '셀트리온',
    '상승', '하락', '등락', '시가', '종가', '거래량', '차트', '기술적', '펀더멘털',

    # 금융상품
    '예금', '적금', '금리', '이자', '저축', '은행', '상품', '투자상품',
    '우리은행', '국민은행', 'kb', '신한', '하나', '농협', 'nh',
    '정기예금', '자유적금', '정기적금', '파킹통장', 'cma',

    # Finflow 기능
    '추천', '조회', '검색', '찾아', '알려줘', '보여줘', '확인',
    '북마크', '즐겨찾기', '관심', '저장', '담기',
    '마이페이지', '내정보', '프로필', '성향', '포트폴리오',
    '나중에', '구독', '채널', '영상', '유튜브', '뉴스', '기사',
    '목록', '리스트', '내역', '기록', '히스토리',

    # 질문 패턴
    '어디서', '어떻게', '방법', '어떡', '뭐가', '무엇',
}

# 패턴 기반 규칙
CHAT_PATTERNS = [
    r'^(ㅋ|ㅎ){1,10}$',  # ㅋㅋㅋ, ㅎㅎㅎ
    r'^(안녕|하이|헬로|hi|hello)[\?!~]*$',  # 단순 인사
    r'^(네|응|ㅇㅇ|오케이|ok)[\?!~]*$',  # 단순 긍정
    r'^(아니|노|ㄴㄴ|no)[\?!~]*$',  # 단순 부정
]

SERVICE_PATTERNS = [
    r'\d{6}',  # 종목 코드 (6자리 숫자)
    r'(어때|추천|분석|조회|알려|보여)',  # 서비스 요청 동사
    r'(북마크|구독|저장|담기|나중에)',  # 기능 명사
]


def normalize_query(text: str) -> str:
    """입력 텍스트 정규화"""
    # 공백 정리
    normalized = re.sub(r'\s+', ' ', text.strip())
    # 소문자 변환
    normalized = normalized.lower()
    return normalized


def classify_chat_mode(user_message: str) -> str:
    """
    사용자 메시지를 CHAT_MODE 또는 SERVICE_MODE로 분류

    Args:
        user_message: 사용자 입력 문자열

    Returns:
        'CHAT' | 'SERVICE'
    """
    normalized = normalize_query(user_message)

    # ===== 1단계: 길이 기반 빠른 분류 =====
    # 너무 짧으면 (1~3자) CHAT
    if len(normalized) <= 3:
        # 예외: 종목 코드나 명령어는 SERVICE
        if any(re.search(pattern, normalized) for pattern in SERVICE_PATTERNS):
            return 'SERVICE'
        return 'CHAT'

    # ===== 2단계: 패턴 기반 분류 =====
    # CHAT 패턴 매칭
    for pattern in CHAT_PATTERNS:
        if re.search(pattern, normalized):
            print(f"[MODE] CHAT 패턴 매칭: {pattern}")
            return 'CHAT'

    # SERVICE 패턴 매칭
    for pattern in SERVICE_PATTERNS:
        if re.search(pattern, normalized):
            print(f"[MODE] SERVICE 패턴 매칭: {pattern}")
            return 'SERVICE'

    # ===== 3단계: 키워드 기반 분류 =====
    # SERVICE 키워드 우선 확인 (더 구체적)
    service_matches = sum(1 for kw in SERVICE_KEYWORDS if kw in normalized)
    if service_matches > 0:
        print(f"[MODE] SERVICE 키워드 {service_matches}개 매칭")
        return 'SERVICE'

    # CHAT 키워드 확인
    chat_matches = sum(1 for kw in CHAT_KEYWORDS if kw in normalized)
    if chat_matches > 0:
        print(f"[MODE] CHAT 키워드 {chat_matches}개 매칭")
        return 'CHAT'

    # ===== 4단계: 기본값 (안전) =====
    # 애매하면 CHAT (과잉 응답 방지)
    print(f"[MODE] 기본값: CHAT (애매한 입력)")
    return 'CHAT'


def classify_mode_with_llm(user_message: str, api_url: str, api_key: str) -> str:
    """
    LLM을 사용한 2차 분류 (선택적 사용)

    Args:
        user_message: 사용자 입력
        api_url: GMS API URL
        api_key: API 키

    Returns:
        'CHAT' | 'SERVICE'
    """
    import requests

    prompt = f"""다음 사용자 메시지가 어떤 의도인지 분류하세요.

CHAT: 일반 대화 (인사, 잡담, 감정 표현, 짧은 반응)
SERVICE: Finflow 금융 서비스 질문 (주식, 예적금, 뉴스, 북마크, 추천 등)

사용자 메시지: "{user_message}"

반드시 "CHAT" 또는 "SERVICE" 중 하나만 답변하세요.
답변:"""

    try:
        response = requests.post(
            api_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": "gpt-5-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 10,
                "temperature": 0,
            },
            timeout=5
        )

        result = response.json()
        llm_answer = result['choices'][0]['message']['content'].strip().upper()

        # "CHAT" 또는 "SERVICE" 포함 여부 확인
        if 'SERVICE' in llm_answer:
            print(f"[MODE] LLM 분류: SERVICE")
            return 'SERVICE'
        else:
            print(f"[MODE] LLM 분류: CHAT")
            return 'CHAT'

    except Exception as e:
        print(f"[MODE] LLM 분류 실패: {e}, 기본값 CHAT 사용")
        return 'CHAT'


# ===== 테스트 함수 =====
if __name__ == "__main__":
    test_cases = [
        # CHAT 예상
        ("안녕", "CHAT"),
        ("ㅋㅋㅋ", "CHAT"),
        ("고마워", "CHAT"),
        ("좋아", "CHAT"),
        ("오늘 날씨 어때?", "CHAT"),
        ("넌 누구야?", "CHAT"),

        # SERVICE 예상
        ("삼전 어때?", "SERVICE"),
        ("삼성전자 주가 알려줘", "SERVICE"),
        ("예금 추천해줘", "SERVICE"),
        ("금리 좋은 적금", "SERVICE"),
        ("북마크 어디서 봐?", "SERVICE"),
        ("나중에 볼 영상 목록", "SERVICE"),
        ("005930 분석", "SERVICE"),
        ("마이페이지 조회", "SERVICE"),
    ]

    print("=" * 60)
    print("챗봇 모드 분류 테스트")
    print("=" * 60)

    correct = 0
    for query, expected in test_cases:
        actual = classify_chat_mode(query)
        status = "✅" if actual == expected else "❌"
        if actual == expected:
            correct += 1
        print(f"{status} '{query:30s}' → {actual:10s} (기대: {expected})")

    print("=" * 60)
    print(f"정확도: {correct}/{len(test_cases)} ({correct/len(test_cases)*100:.1f}%)")
