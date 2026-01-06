"""
TF-IDF Engine
=============
- 책임:
  1) TF-IDF 벡터라이저 + 문서 행렬 생성 및 캐시 저장 (offline/build & runtime ensure)
  2) TF-IDF 기반 키워드 검색 (online)
- 입력 기준:
  - project_root/
      ├─ data/movie_clean_data.csv
      └─ .cache/tfidf_vectorizer.pkl
      └─ .cache/tfidf_matrix.pkl
"""

from pathlib import Path
import pickle
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# --------------------------------------------------
# CONST
# --------------------------------------------------

VECTORIZER_FILENAME = "tfidf_vectorizer.pkl"
MATRIX_FILENAME = "tfidf_matrix.pkl"

TFIDF_KWARGS = dict(
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.9,
    stop_words="english",
    sublinear_tf=True,
    norm="l2",
)


# --------------------------------------------------
# INTERNAL UTILS
# --------------------------------------------------

def _load_movies(project_root: Path) -> pd.DataFrame:
    data_path = project_root / "data" / "movie_clean_data.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"movie_clean_data.csv not found: {data_path}")
    return pd.read_csv(data_path)


def _cache_dir(project_root: Path) -> Path:
    d = project_root / ".cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _vectorizer_path(project_root: Path) -> Path:
    return _cache_dir(project_root) / VECTORIZER_FILENAME


def _matrix_path(project_root: Path) -> Path:
    return _cache_dir(project_root) / MATRIX_FILENAME


def _combined_text(df: pd.DataFrame) -> pd.Series:
    return (
        df["title"].fillna("").astype(str)
        + " "
        + df["overview"].fillna("").astype(str)
    )


# --------------------------------------------------
# BUILD / ENSURE
# --------------------------------------------------

def run_tfidf(project_root: Path) -> None:
    """
    Ensure TF-IDF vectorizer & matrix cache exist.
    Called by builder / runtime_engine.
    """
    project_root = Path(project_root)
    vec_path = _vectorizer_path(project_root)
    mat_path = _matrix_path(project_root)

    if vec_path.exists() and mat_path.exists():
        return

    df = _load_movies(project_root)
    texts = _combined_text(df).tolist()

    vectorizer = TfidfVectorizer(**TFIDF_KWARGS)
    matrix = vectorizer.fit_transform(texts)

    with open(vec_path, "wb") as f:
        pickle.dump(vectorizer, f)

    with open(mat_path, "wb") as f:
        pickle.dump(matrix, f)


def load_tfidf(project_root: Path):
    """
    Load cached TF-IDF vectorizer and matrix.
    """
    project_root = Path(project_root)
    vec_path = _vectorizer_path(project_root)
    mat_path = _matrix_path(project_root)

    if not vec_path.exists() or not mat_path.exists():
        raise FileNotFoundError(
            "TF-IDF cache not found. run_tfidf() must be called first."
        )

    with open(vec_path, "rb") as f:
        vectorizer = pickle.load(f)

    with open(mat_path, "rb") as f:
        matrix = pickle.load(f)

    return vectorizer, matrix


# --------------------------------------------------
# SEARCH
# --------------------------------------------------

def search_tfidf(project_root: Path, query: str, top_k: int = 200):
    """
    TF-IDF keyword search.
    Returns ranked list of movie dicts.
    """
    project_root = Path(project_root)

    df = _load_movies(project_root)
    vectorizer, matrix = load_tfidf(project_root)

    q_vec = vectorizer.transform([query])
    scores = cosine_similarity(q_vec, matrix)[0]

    ranked_idx = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in ranked_idx:
        row = df.iloc[idx].to_dict()
        row["tfidf_score"] = float(scores[idx])
        results.append(row)

    return results
