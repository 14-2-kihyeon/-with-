# stocks/services/recommender.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import QuerySet

from stocks.models import FeatureDaily  # FeatureDaily(stock FK, date, r1/r5/..., vol.., mdd.., volume_z.., news..)


# -------------------------
# date parsing
# -------------------------
def parse_date_any(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    s = s.strip()
    try:
        # YYYYMMDD
        if len(s) == 8 and s.isdigit():
            return datetime.strptime(s, "%Y%m%d").date()
        # YYYY-MM-DD
        if len(s) == 10 and s[4] == "-" and s[7] == "-":
            return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None
    return None


# -------------------------
# configs
# -------------------------
FEATURE_CONFIG = {
    "SHORT": {
        "trend_windows": [1, 5],
        "trend_weights": [0.4, 0.6],
        "volume_z_field_candidates": ["vz5", "volume_z5", "volume_z"],
        "vol_field_candidates": ["vol10", "vol"],
        "mdd_field_candidates": ["mdd10", "mdd"],
        "news_field": "news3",
    },
    "MID": {
        "trend_windows": [5, 20],
        "trend_weights": [0.6, 0.4],
        "volume_z_field_candidates": ["vz20", "volume_z20", "vz5", "volume_z5", "volume_z"],
        "vol_field_candidates": ["vol20", "vol"],
        "mdd_field_candidates": ["mdd20", "mdd"],
        "news_field": "news7",
    },
    "LONG": {
        "trend_windows": [20, 60],
        "trend_weights": [0.3, 0.7],
        "volume_z_field_candidates": ["vz20", "volume_z20", "vz5", "volume_z5", "volume_z"],
        "vol_field_candidates": ["vol60", "vol"],
        "mdd_field_candidates": ["mdd60", "mdd"],
        "news_field": "news30",
    },
}

WEIGHTS_CONFIG = {
    # OPTIMIZE: 뉴스 포함
    "OPTIMIZE": {
        "LOW":  {"w_T": 0.30, "w_U": 0.10, "w_N": 0.10, "w_V": 0.25, "w_D": 0.25},
        "MID":  {"w_T": 0.35, "w_U": 0.15, "w_N": 0.15, "w_V": 0.20, "w_D": 0.15},
        "HIGH": {"w_T": 0.40, "w_U": 0.20, "w_N": 0.20, "w_V": 0.10, "w_D": 0.10},
    },
    # SIMPLE: 뉴스 제거
    "SIMPLE": {
        "LOW":  {"w_T": 0.35, "w_U": 0.10, "w_N": 0.00, "w_V": 0.30, "w_D": 0.25},
        "MID":  {"w_T": 0.40, "w_U": 0.15, "w_N": 0.00, "w_V": 0.25, "w_D": 0.20},
        "HIGH": {"w_T": 0.45, "w_U": 0.25, "w_N": 0.00, "w_V": 0.15, "w_D": 0.15},
    },
}


RISK_FILTERS = {
    "LOW":  {"max_mdd": 0.25, "max_vol_pct": 0.80},  # 변동성 상위 20% 제외
    "MID":  {"max_mdd": 0.35, "max_vol_pct": 0.90},
    "HIGH": {"max_mdd": 0.50, "max_vol_pct": 0.98},
}


def _norm_key(x: str, allowed: Tuple[str, ...], default: str) -> str:
    x = (x or "").upper().strip()
    return x if x in allowed else default


def _safe_get(obj: Any, field: str, default: float = 0.0) -> float:
    if not field:
        return default
    if not hasattr(obj, field):
        return default
    v = getattr(obj, field)
    if v is None:
        return default
    try:
        return float(v)
    except Exception:
        return default


def _first_existing(obj: Any, fields: List[str]) -> str:
    for f in fields:
        if hasattr(obj, f):
            return f
    return ""


def to_percentile(values: List[float]) -> List[float]:
    """
    values -> 0~1 퍼센타일(순위) 변환
    """
    n = len(values)
    if n <= 1:
        return [0.5] * n

    # 동점은 단순 rank(정렬 순서)로 처리
    order = sorted(range(n), key=lambda i: values[i])
    rank = [0] * n
    for r, i in enumerate(order):
        rank[i] = r

    denom = (n - 1)
    return [rank[i] / denom for i in range(n)]


@dataclass
class RawRow:
    code: str
    name: str
    T_raw: float
    U_raw: float
    N_raw: float
    V_raw: float
    D_raw: float


def _trend_raw(feature: Any, windows: List[int], weights: List[float]) -> float:
    """
    r{window} 필드 조합. 없으면 0으로 처리.
    ex) SHORT: 0.4*r1 + 0.6*r5
    """
    out = 0.0
    for w, a in zip(windows, weights):
        field = f"r{w}"
        out += a * _safe_get(feature, field, 0.0)
    return out


def _pick_news_raw(feature: Any, horizon: str) -> float:
    cfg = FEATURE_CONFIG[horizon]
    return _safe_get(feature, cfg["news_field"], 0.0)


def recommend_stocks(
    *,
    as_of: date,
    risk: str = "MID",
    horizon: str = "MID",
    top_n: int = 20,
    include_news: bool = True,
    effort: str = "OPTIMIZE",
) -> Dict[str, Any]:
    """
    FeatureDaily(date=as_of) 기반 추천.
    - include_news=False면 N_raw=0으로 두고 추천(TopK 후보 뽑을 때 사용)
    """
    risk = _norm_key(risk, ("LOW", "MID", "HIGH"), "MID")
    horizon = _norm_key(horizon, ("SHORT", "MID", "LONG"), "MID")
    effort = _norm_key(effort, ("SIMPLE", "OPTIMIZE"), "OPTIMIZE")

    # include_news=False면 사실상 SIMPLE처럼 동작하게 w_N을 0으로 만드는 게 안전
    weights = dict(WEIGHTS_CONFIG[effort][risk])
    if not include_news:
        weights["w_N"] = 0.0

    cfg = FEATURE_CONFIG[horizon]

    qs: QuerySet = FeatureDaily.objects.select_related("stock").filter(date=as_of)
    if not qs.exists():
        return {"detail": f"FeatureDaily 데이터가 없습니다: date={as_of}"}

    # Raw 만들기
    rows: List[RawRow] = []
    features = list(qs)

    # vol/mdd 필드 후보 중 실제 존재하는 필드 선택(첫 레코드 기준)
    any_fd = features[0]
    vol_field = _first_existing(any_fd, cfg["vol_field_candidates"])
    mdd_field = _first_existing(any_fd, cfg["mdd_field_candidates"])
    volz_field = _first_existing(any_fd, cfg["volume_z_field_candidates"])

    for f in features:
        stock = f.stock
        code = getattr(stock, "code", "")
        name = getattr(stock, "name", "")

        T_raw = _trend_raw(f, cfg["trend_windows"], cfg["trend_weights"])
        U_raw = _safe_get(f, volz_field, 0.0)
        V_raw = _safe_get(f, vol_field, 0.0)
        D_raw = _safe_get(f, mdd_field, 0.0)

        N_raw = 0.0
        if include_news and weights.get("w_N", 0.0) > 0:
            N_raw = _pick_news_raw(f, horizon)

        rows.append(RawRow(code=code, name=name, T_raw=T_raw, U_raw=U_raw, N_raw=N_raw, V_raw=V_raw, D_raw=D_raw))

    # 1차: MDD 하드컷(리스크별)
    max_mdd = RISK_FILTERS[risk]["max_mdd"]
    filtered = [r for r in rows if (r.D_raw <= max_mdd or r.D_raw == 0.0)]
    if not filtered:
        filtered = rows  # 전부 날아가면 fallback

    # 퍼센타일 정규화(0~1)
    T_list = [r.T_raw for r in filtered]
    U_list = [r.U_raw for r in filtered]
    N_list = [r.N_raw for r in filtered]
    V_list = [r.V_raw for r in filtered]
    D_list = [r.D_raw for r in filtered]

    T_pct = to_percentile(T_list)  # 클수록 좋음
    U_pct = to_percentile(U_list)
    N_pct = to_percentile(N_list) if include_news and weights.get("w_N", 0.0) > 0 else [0.0] * len(filtered)

    V_raw_pct = to_percentile(V_list)  # 클수록 위험(변동성 큼)
    D_raw_pct = to_percentile(D_list)  # 클수록 위험(낙폭 큼)

    # 안정성 점수로 뒤집기(작을수록 좋은 지표 → 1 - percentile)
    V_stab = [1.0 - x for x in V_raw_pct]
    D_stab = [1.0 - x for x in D_raw_pct]

    # 2차: 변동성 퍼센타일 컷(리스크별)
    max_vol_pct = RISK_FILTERS[risk]["max_vol_pct"]
    tmp = []
    for i, r in enumerate(filtered):
        # V_raw_pct가 max_vol_pct보다 크면(상위권 변동성) 제외
        if V_raw_pct[i] > max_vol_pct:
            continue
        tmp.append((i, r))
    if tmp:
        keep_indices = [i for i, _ in tmp]
    else:
        keep_indices = list(range(len(filtered)))  # 전부 날아가면 fallback

    # 점수 계산
    recs = []
    for i in keep_indices:
        r = filtered[i]
        score = (
            weights["w_T"] * T_pct[i]
            + weights["w_U"] * U_pct[i]
            + weights["w_N"] * N_pct[i]
            + weights["w_V"] * V_stab[i]
            + weights["w_D"] * D_stab[i]
        )

        recs.append({
            "code": r.code,
            "name": r.name,
            "score": round(float(score), 6),
            "components": {
                "T": round(float(T_pct[i]), 6),
                "U": round(float(U_pct[i]), 6),
                "N": round(float(N_pct[i]), 6),
                "V": round(float(V_stab[i]), 6),
                "D": round(float(D_stab[i]), 6),
            },
            "raw": {
                "T_raw": round(float(r.T_raw), 6),
                "U_raw": round(float(r.U_raw), 6),
                "N_raw": round(float(r.N_raw), 6),
                "V_raw": round(float(r.V_raw), 6),
                "D_raw": round(float(r.D_raw), 6),
            }
        })

    recs.sort(key=lambda x: x["score"], reverse=True)
    recs = recs[: max(1, int(top_n))]

    return {
        "as_of": str(as_of),
        "profile": {"risk": risk, "horizon": horizon, "effort": effort},
        "include_news": bool(include_news),
        "weights": weights,
        "feature_fields_used": {
            "trend": [f"r{w}" for w in cfg["trend_windows"]],
            "volume_z": volz_field or "(none)",
            "vol": vol_field or "(none)",
            "mdd": mdd_field or "(none)",
            "news": cfg["news_field"],
        },
        "count": len(recs),
        "recommendations": recs,
    }
