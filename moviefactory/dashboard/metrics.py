# moviefactory/app/metrics.py

import pandas as pd
from datetime import datetime


def _get_year_series(df: pd.DataFrame) -> pd.Series:
    """
    release_date 우선, 없으면 release_year 사용
    최종적으로 int year Series 반환 (결측 제거)
    """
    if "release_date" in df.columns:
        years = (
            df["release_date"]
            .astype(str)
            .str.slice(0, 4)
            .apply(lambda x: int(x) if x.isdigit() else None)
        )
    elif "release_year" in df.columns:
        years = pd.to_numeric(df["release_year"], errors="coerce")
    else:
        years = pd.Series([], dtype="int")

    years = years.dropna().astype(int)
    return years


def get_dataset_overview(runtime_engine):
    """
    Dataset Overview 카드용 메트릭
    """
    df = runtime_engine.df.copy()

    total_movies = int(len(df))

    avg_vote = (
        float(df["vote_average"].mean())
        if "vote_average" in df.columns and len(df) > 0
        else 0.0
    )

    avg_popularity = (
        float(df["popularity"].mean())
        if "popularity" in df.columns and len(df) > 0
        else 0.0
    )

    if "vote_average" in df.columns and len(df) > 0:
        threshold = df["vote_average"].quantile(0.8)
        top20 = df[df["vote_average"] >= threshold]
        top20_avg_vote = (
            float(top20["vote_average"].mean()) if len(top20) > 0 else 0.0
        )
    else:
        top20_avg_vote = 0.0

    years = _get_year_series(df)
    if len(years) > 0:
        current_year = datetime.now().year
        recent_10_ratio = float((years >= current_year - 10).mean()) * 100.0
    else:
        recent_10_ratio = 0.0

    return {
        "total_movies": total_movies,
        "avg_rating": round(avg_vote, 2),
        "avg_popularity": round(avg_popularity, 2),
        "top20_avg_rating": round(top20_avg_vote, 2),
        "recent_10y_ratio": round(recent_10_ratio, 1),
    }


def get_release_year_distribution(runtime_engine):
    """
    Release Year Distribution 차트용
    """
    df = runtime_engine.df.copy()
    years = _get_year_series(df)

    if len(years) == 0:
        return {}

    year_counts = years.value_counts().sort_index()

    return year_counts.to_dict()


# ADDED: search_mode별 집계 (대시보드 표시용)
def get_search_mode_metrics(search_mode: str, results: list | None):
    return {
        "search_mode": search_mode,
        "result_count": len(results) if results else 0,
    }
