"""
Hybrid Engine
=============
- 책임:
  1) 개별 엔진 결과(SBERT / TF-IDF / CF / CLIP)를 결합한 하이브리드 유사도 행렬 생성
  2) 하이브리드 기반 검색 제공
- 입력 기준:
  project_root/
    ├─ data/movie_clean_data.csv
    ├─ .cache/sbert_embeddings.pkl
    ├─ .cache/tfidf_matrix.pkl
    ├─ .cache/synthetic_cf.pkl        (movie x movie similarity)
    └─ .cache/hybrid_similarity.pkl   (movie x movie similarity)
"""

from pathlib import Path
import pickle
import numpy as np
import pandas as pd

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

from moviefactory.engines.sbert_engine import (
    load_sbert_embeddings,
    search_sbert,
)
from moviefactory.engines.tfidf_engine import load_tfidf
from moviefactory.engines.meta_engine import load_cf_matrix


# --------------------------------------------------
# CONST
# --------------------------------------------------

CACHE_FILENAME = "hybrid_similarity.pkl"

# 합의된 가중치 (합 = 1.0)
WEIGHTS = {
    "sbert": 0.45,
    "tfidf": 0.25,
    "cf": 0.30,
}

# --------------------------------------------------
# INTERNAL UTILS
# --------------------------------------------------

def _load_movies(project_root: Path) -> pd.DataFrame:
    data_path = project_root / "data" / "movie_clean_data.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"movie_clean_data.csv not found: {data_path}")
    return pd.read_csv(data_path)


def _cache_path(project_root: Path) -> Path:
    cache_dir = project_root / ".cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / CACHE_FILENAME


# --------------------------------------------------
# BUILD / ENSURE
# --------------------------------------------------

def run_hybrid(project_root: Path) -> None:
    """
    Ensure hybrid similarity matrix exists.
    Called by runtime_engine / builder.
    """
    project_root = Path(project_root)
    cache_path = _cache_path(project_root)

    if cache_path.exists():
        return

    # --- SBERT similarity ---
    sbert_emb = load_sbert_embeddings(project_root)
    sim_sbert = cosine_similarity(sbert_emb)

    # --- TF-IDF similarity ---
    _, tfidf_matrix = load_tfidf(project_root)
    sim_tfidf = cosine_similarity(tfidf_matrix)

    # --- CF similarity (already similarity matrix) ---
    sim_cf = load_cf_matrix(project_root)

    # --- Normalize all similarities to comparable scale ---
    sim_sbert = normalize(sim_sbert, norm="l2")
    sim_tfidf = normalize(sim_tfidf, norm="l2")
    sim_cf = normalize(sim_cf, norm="l2")

    # --- Weighted sum ---
    hybrid_sim = (
        WEIGHTS["sbert"] * sim_sbert
        + WEIGHTS["tfidf"] * sim_tfidf
        + WEIGHTS["cf"] * sim_cf
    )

    # Final normalization for safety
    hybrid_sim = normalize(hybrid_sim, norm="l2")

    with open(cache_path, "wb") as f:
        pickle.dump(hybrid_sim, f)


def load_hybrid_matrix(project_root: Path) -> np.ndarray:
    """
    Load cached hybrid similarity matrix.
    """
    project_root = Path(project_root)
    cache_path = _cache_path(project_root)

    if not cache_path.exists():
        raise FileNotFoundError(
            "Hybrid cache not found. run_hybrid() must be called first."
        )

    with open(cache_path, "rb") as f:
        return pickle.load(f)


# --------------------------------------------------
# SEARCH
# --------------------------------------------------

def search_hybrid(
    project_root: Path,
    query: str | None = None,
    movie_id: int | None = None,
    top_k: int = 200,
):
    """
    Hybrid search entrypoint.

    - query 기반: SBERT 검색 결과를 hybrid matrix로 재랭킹
    - movie_id 기반: 해당 영화의 hybrid 유사도 행 사용
    """
    project_root = Path(project_root)
    df = _load_movies(project_root)
    hybrid_sim = load_hybrid_matrix(project_root)

    if "movie_id" not in df.columns:
        raise KeyError("movie_id column missing in movie_clean_data.csv")

    id_to_index = {
        int(mid): idx
        for idx, mid in enumerate(df["movie_id"].values)
        if not pd.isna(mid)
    }

    # --------------------------------------------------
    # Case 1: movie_id 기반
    # --------------------------------------------------
    if movie_id is not None:
        if movie_id not in id_to_index:
            return []

        idx = id_to_index[movie_id]
        scores = hybrid_sim[idx]

        ranked_idx = np.argsort(scores)[::-1][:top_k]

        results = []
        for i in ranked_idx:
            if i == idx:
                continue
            row = df.iloc[i].to_dict()
            row["hybrid_score"] = float(scores[i])
            results.append(row)

        return results

    # --------------------------------------------------
    # Case 2: query 기반
    # --------------------------------------------------
    if query:
        # 1차: SBERT semantic candidate
        sbert_results = search_sbert(project_root, query, top_k=top_k)

        results = []
        for row in sbert_results:
            mid = row.get("movie_id")
            if mid is None or int(mid) not in id_to_index:
                continue

            idx = id_to_index[int(mid)]
            row["hybrid_score"] = float(hybrid_sim[idx].max())
            results.append(row)

        # hybrid_score 기준 재정렬
        results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return results[:top_k]

    return []
