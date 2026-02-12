# ============================================================
# moviefactory/dashboard/metrics_contract.py
# ============================================================
"""
MovieFactory v1.3  → v1.4 (ADD ONLY)
metrics_contract.py — Dashboard Overview 계약 유지 + Engine Comparison 계약 추가

기존 정책:
- 계산 로직 ❌
- 데이터 로딩 ❌
- 엔진 호출 ❌
- 읽기 전용 계약 객체만 제공

변경 원칙:
- 기존 코드/필드 1바이트도 삭제 ❌
- ADD ONLY
"""

from typing import TypedDict, Dict, List, Literal, Optional


class DashboardMetrics(TypedDict):
    """
    DashboardMetrics Contract (v1.3)

    Dashboard Overview 섹션에서 사용하는
    모든 지표의 단일 계약 정의
    """

    # 기본 규모 지표
    total_movies: int

    # 평균 지표
    avg_rating: float
    avg_popularity: float

    # 분포/비율 지표
    top20_avg_rating: float
    recent_10y_ratio: float

    # 연도 분포
    year_distribution: Dict[int, int]


# ------------------------------------------------------------------
# Engine Comparison (ADD ONLY)
# ------------------------------------------------------------------
EngineName = Literal["TF-IDF", "SBERT", "CLIP", "CF-SVD"]


class EngineComparisonItem(TypedDict):
    rank: int
    movie_id: int
    title: str
    score: Optional[float]  # CF-SVD는 None 허용


class EngineComparisonResult(TypedDict):
    engine: EngineName
    basis: Literal["query"]          # 기준 고정
    score_type: Literal["cosine"]    # 의미 고정
    items: List[EngineComparisonItem]


class EngineComparison(TypedDict):
    query: str
    results: List[EngineComparisonResult]


# ------------------------------------------------------------------
# Fixed Contract Metadata
# ------------------------------------------------------------------
CONTRACT_VERSION = "v1.4"

CONTRACT_FIELDS = [
    "total_movies",
    "avg_rating",
    "avg_popularity",
    "top20_avg_rating",
    "recent_10y_ratio",
    "year_distribution",
    # ADD
    "engine_comparison",
]
