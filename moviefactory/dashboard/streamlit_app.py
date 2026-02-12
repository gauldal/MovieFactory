# ============================================================
# moviefactory/dashboard/streamlit_app.py
# ============================================================
"""
MovieFactory v1.3 → v1.4 (ADD ONLY)
streamlit_app.py — 기존 Dashboard 유지 + Engine Comparison 섹션 추가
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

from moviefactory.dashboard.metrics_contract import (
    DashboardMetrics,
    CONTRACT_VERSION,
)
from moviefactory.engine.runtime_engine import RuntimeEngine


# ------------------------------------------------------------------
# Data Loader (Read-Only)
# ------------------------------------------------------------------
_DATA_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "movie_clean_data.csv"
)

_df_cache = None


def load_df() -> pd.DataFrame:
    global _df_cache
    if _df_cache is None:
        if not _DATA_PATH.exists():
            st.error(f"Missing data file: {_DATA_PATH}")
            st.stop()
        _df_cache = pd.read_csv(_DATA_PATH)
    return _df_cache


# ------------------------------------------------------------------
# Metrics Builder (Contract-Based)
# ------------------------------------------------------------------
def build_metrics(df: pd.DataFrame) -> DashboardMetrics:
    total_movies = int(len(df))

    avg_rating = float(df["vote_average"].mean())
    avg_popularity = float(df["popularity"].mean())

    threshold = df["vote_average"].quantile(0.8)
    top20 = df[df["vote_average"] >= threshold]
    top20_avg_rating = float(top20["vote_average"].mean())

    year_series = (
        pd.to_datetime(df["release_date"], errors="coerce")
        .dt.year
        .dropna()
        .astype(int)
    )

    current_year = year_series.max()
    recent_10y = year_series >= (current_year - 9)
    recent_10y_ratio = round(
        float(recent_10y.sum() / total_movies * 100), 1
    )

    year_distribution = (
        year_series.value_counts()
        .sort_index()
        .to_dict()
    )

    metrics: DashboardMetrics = {
        "total_movies": total_movies,
        "avg_rating": round(avg_rating, 2),
        "avg_popularity": round(avg_popularity, 2),
        "top20_avg_rating": round(top20_avg_rating, 2),
        "recent_10y_ratio": recent_10y_ratio,
        "year_distribution": year_distribution,
    }
    return metrics


# ------------------------------------------------------------------
# Streamlit App
# ------------------------------------------------------------------
def main():
    st.set_page_config(
        page_title="MovieFactory Dashboard",
        layout="wide",
    )

    st.title("🎬 MovieFactory Dashboard")
    st.caption(f"Metrics Contract Version: {CONTRACT_VERSION}")

    df = load_df()
    metrics = build_metrics(df)

    # --------------------------------------------------------------
    # Top Metrics
    # --------------------------------------------------------------
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Movies", metrics["total_movies"])
    col2.metric("Average Rating", f'{metrics["avg_rating"]:.2f}')
    col3.metric("Average Popularity", f'{metrics["avg_popularity"]:.2f}')
    col4.metric("Top 20% Avg Rating", f'{metrics["top20_avg_rating"]:.2f}')
    col5.metric("Recent 10 Years (%)", f'{metrics["recent_10y_ratio"]}%')

    st.divider()

    # --------------------------------------------------------------
    # Release Year Distribution (FIXED)
    # --------------------------------------------------------------
    st.subheader("Release Year Distribution")

    year_df = (
        pd.DataFrame(
            list(metrics["year_distribution"].items()),
            columns=["Year", "Count"],
        )
        .sort_values("Year")
        .reset_index(drop=True)
    )

    fig = px.bar(
        year_df,
        x="Year",
        y="Count",
    )

    fig.update_layout(
        dragmode=False,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "scrollZoom": False,
            "displayModeBar": False,
        },
    )

    st.divider()

    # --------------------------------------------------------------
    # ADD ONLY — Engine Comparison
    # --------------------------------------------------------------
    st.subheader("Engine Comparison (Query-Based Similarity)")
    query = st.text_input("Query", value="family")

    engine = RuntimeEngine()

    tfidf = engine.get_query_tfidf_similarity(query)
    sbert = engine.get_query_sbert_similarity(query)
    clip = engine.get_query_clip_similarity(query)

    colA, colB, colC, colD = st.columns(4)

    with colA:
        st.markdown("### TF-IDF")
        for i, it in enumerate(tfidf, 1):
            st.write(f"{i}. {it['title']} ({it['score']:.3f})")

    with colB:
        st.markdown("### SBERT")
        for i, it in enumerate(sbert, 1):
            st.write(f"{i}. {it['title']} ({it['score']:.3f})")

    with colC:
        st.markdown("### CLIP")
        for i, it in enumerate(clip, 1):
            st.write(f"{i}. {it['title']} ({it['score']:.3f})")

    with colD:
        st.markdown("### CF-SVD")
        st.write("N/A (query-based similarity not defined)")


if __name__ == "__main__":
    main()
