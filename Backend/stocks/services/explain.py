# stocks/services/explain.py
from __future__ import annotations

from typing import Any


LABELS = {
    "r1": "1일 수익률",
    "r5": "5일 수익률",
    "r20": "20일 수익률",
    "r60": "60일 수익률",
    "vol10": "10일 변동성",
    "vol20": "20일 변동성",
    "vol60": "60일 변동성",
    "mdd10": "10일 최대낙폭",
    "mdd20": "20일 최대낙폭",
    "mdd60": "60일 최대낙폭",

    # ✅ build_features가 만드는 실제 필드
    "vz5": "5일 거래량 급증",
    "vz20": "20일 거래량 급증",

    # (혹시 다른 프로젝트에서 쓰는 이름도 함께 유지)
    "volume_z5": "5일 거래량 급증",
    "volume_z20": "20일 거래량 급증",

    "news3": "최근 3일 뉴스 강도",
    "news7": "최근 7일 뉴스 강도",
    "news30": "최근 30일 뉴스 강도",
}


def _fmt(v: Any) -> str:
    if v is None:
        return "-"
    # 숫자 예쁘게 (너무 길면 가독성 나쁨)
    if isinstance(v, float):
        return f"{v:.4f}".rstrip("0").rstrip(".")
    return str(v)


def build_explain_messages(
    *,
    code: str,
    name: str,
    as_of: str,
    question: str,
    feature: dict | None,
    weights: dict | None,
    components: dict | None,
    news_topk: list[dict] | None,
) -> list[dict]:
    news_topk = news_topk or []

    # ✅ 컨텍스트를 “한국어 라벨”로만 구성 (r20/vol 같은 키 노출 금지)
    lines = []
    lines.append(f"종목: {name} ({code})")
    lines.append(f"기준일: {as_of}")
    lines.append("")

    lines.append("[지표 요약]")
    if not feature:
        lines.append("- 지표 데이터가 없어 지표 기반 설명은 제한됨")
    else:
        for k, v in feature.items():
            label = LABELS.get(k, None)
            if not label:
                # 라벨 없는 키는 아예 숨겨버림(내부 키 노출 방지)
                continue
            lines.append(f"- {label}: {_fmt(v)}")

    lines.append("")
    lines.append("[뉴스 TOP]")
    if not news_topk:
        lines.append("- 최근 뉴스 데이터 없음(뉴스 근거 제한)")
    else:
        for i, n in enumerate(news_topk[:3], 1):
            title = n.get("title") or "-"
            link = n.get("link") or n.get("originallink") or "-"
            published = n.get("published_at") or n.get("pub_date") or "-"
            lines.append(f"{i}. ({published}) {title} / {link}")

    context = "\n".join(lines)

    developer = (
        "너는 금융/주식 '교육용 분석' 도우미다. "
        "절대로 매수/매도/수익보장/미래가격 예측을 단정하지 마라. "
        "반드시 제공된 [지표 요약]과 [뉴스 TOP] 범위 내에서만 근거를 제시하라. "
        "지표 변수명(r20, vol, mdd, z-score 등)이나 괄호 표기를 절대 쓰지 말고 "
        "반드시 한국어로 풀어서 말하라.\n\n"

        "출력 형식은 아래 구조를 반드시 지켜라(줄바꿈 포함):\n"
        "[한줄 요약]\n"
        "- (1문장)\n"
        "[지표 근거]\n"
        "- (2~4개, 숫자는 %/건/배 등 단위 포함)\n"
        "[뉴스 근거]\n"
        "- (1~3개, 뉴스가 없으면 '최근 뉴스 근거 부족' 1줄)\n"
        "[리스크/주의]\n"
        "- (2~3개)\n"
        "[확인 체크리스트]\n"
        "1) (1줄)\n"
        "2) (1줄)\n"
        "3) (1줄)\n\n"

        "각 항목은 간결하게, 전체는 10~18줄 정도로 작성하라."
    )


    user = (
        f"질문: {question}\n\n"
        f"아래 컨텍스트만 근거로 설명해줘.\n\n"
        f"{context}"
    )

    return [
        {"role": "system", "content": developer},
        {"role": "user", "content": user},
    ]
