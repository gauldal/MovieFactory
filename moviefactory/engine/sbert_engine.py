"""
SBERT Engine
============
- 책임:
  1) SBERT 임베딩 생성 및 캐시 저장 (offline/build & runtime ensure)
  2) SBERT 기반 텍스트 검색 (online)
- 입력 기준:
  - project_root/
      ├─ data/movie_clean_data.csv
      └─ .cache/sbert_embeddings.pkl
"""

from pathlib import Path
import pickle
import numpy as np
import pandas as pd
from tqdm import tqdm

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# --------------------------------------------------
# CONST
# --------------------------------------------------

SBERT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CACHE_FILENAME = "sbert_embeddings.pkl"


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

def run_sbert(project_root: Path) -> None:
    """
    Ensure SBERT embeddings cache exists.
    Called by builder / runtime_engine.
    """
    project_root = Path(project_root)
    cache_path = _cache_path(project_root)

    if cache_path.exists():
        return

    df = _load_movies(project_root)

    texts = (
        df["title"].fillna("").astype(str)
        + " "
        + df["overview"].fillna("").astype(str)
    ).tolist()

    model = SentenceTransformer(SBERT_MODEL_NAME)

    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    with open(cache_path, "wb") as f:
        pickle.dump(embeddings, f)


def load_sbert_embeddings(project_root: Path) -> np.ndarray:
    """
    Load cached SBERT embeddings.
    """
    cache_path = _cache_path(project_root)
    if not cache_path.exists():
        raise FileNotFoundError(
            "SBERT cache not found. run_sbert() must be called first."
        )

    with open(cache_path, "rb") as f:
        return pickle.load(f)


# --------------------------------------------------
# SEARCH
# --------------------------------------------------

def search_sbert(project_root: Path, query: str, top_k: int = 200):
    """
    SBERT semantic search.
    Returns ranked list of movie dicts.
    """
    project_root = Path(project_root)

    df = _load_movies(project_root)
    embeddings = load_sbert_embeddings(project_root)

    model = SentenceTransformer(SBERT_MODEL_NAME)
    q_emb = model.encode(
        [query],
        normalize_embeddings=True
    )

    scores = cosine_similarity(q_emb, embeddings)[0]

    ranked_idx = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in ranked_idx:
        row = df.iloc[idx].to_dict()
        row["sbert_score"] = float(scores[idx])
        results.append(row)

    return results
