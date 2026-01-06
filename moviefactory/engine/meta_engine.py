"""
Meta (CF) Engine
================
- 책임:
  1) Synthetic Collaborative Filtering 행렬 생성 및 캐시 저장 (offline/build & runtime ensure)
  2) CF 기반 유사 영화 검색 (online)
- 입력 기준:
  - project_root/
      ├─ data/movie_clean_data.csv
      └─ .cache/synthetic_cf.pkl
"""

from pathlib import Path
import pickle
import numpy as np
import pandas as pd

from sklearn.preprocessing import normalize
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity


# --------------------------------------------------
# CONST
# --------------------------------------------------

CACHE_FILENAME = "synthetic_cf.pkl"
CF_N_COMPONENTS = 64
RANDOM_STATE = 42


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


def _safe_float(v, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


# --------------------------------------------------
# BUILD / ENSURE
# --------------------------------------------------

def run_cf(project_root: Path) -> None:
    """
    Ensure synthetic CF matrix cache exists.
    Called by builder / runtime_engine.
    """
    project_root = Path(project_root)
    cache_path = _cache_path(project_root)

    if cache_path.exists():
        return

    df = _load_movies(project_root)

    # Guard: required columns
    for col in ("popularity", "vote_average", "vote_count"):
        if col not in df.columns:
            raise KeyError(f"Required column missing for CF: {col}")

    # Build synthetic preference matrix (movie x features)
    features = np.vstack([
        df["popularity"].apply(_safe_float).values,
        df["vote_average"].apply(_safe_float).values,
        df["vote_count"].apply(_safe_float).values,
    ]).T

    # Normalize feature scale
    features = normalize(features, norm="l2")

    # Dimensionality reduction (cold-start friendly)
    n_components = min(
        CF_N_COMPONENTS,
        max(2, features.shape[0] - 1),
        features.shape[1]
    )

    svd = TruncatedSVD(
        n_components=n_components,
        random_state=RANDOM_STATE
    )

    latent = svd.fit_transform(features)
    latent = normalize(latent, norm="l2")

    # Cosine similarity matrix (movie x movie)
    cf_matrix = cosine_similarity(latent)

    with open(cache_path, "wb") as f:
        pickle.dump(cf_matrix, f)


def load_cf_matrix(project_root: Path) -> np.ndarray:
    """
    Load cached CF similarity matrix.
    """
    project_root = Path(project_root)
    cache_path = _cache_path(project_root)

    if not cache_path.exists():
        raise FileNotFoundError(
            "CF cache not found. run_cf() must be called first."
        )

    with open(cache_path, "rb") as f:
        return pickle.load(f)


# --------------------------------------------------
# SEARCH
# --------------------------------------------------

def search_cf(project_root: Path, movie_id: int, top_k: int = 200):
    """
    CF-based similar movie search.
    Returns ranked list of movie dicts.
    """
    project_root = Path(project_root)

    df = _load_movies(project_root)
    cf_matrix = load_cf_matrix(project_root)

    if "movie_id" not in df.columns:
        raise KeyError("movie_id column missing in movie_clean_data.csv")

    id_to_index = {
        int(mid): idx
        for idx, mid in enumerate(df["movie_id"].values)
        if not pd.isna(mid)
    }

    if movie_id not in id_to_index:
        return []

    idx = id_to_index[movie_id]
    scores = cf_matrix[idx]

    ranked_idx = np.argsort(scores)[::-1][:top_k]

    results = []
    for i in ranked_idx:
        if i == idx:
            continue
        row = df.iloc[i].to_dict()
        row["cf_score"] = float(scores[i])
        results.append(row)

    return results
