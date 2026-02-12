# moviefactory/utils/cache_loader.py

from pathlib import Path
from typing import Literal

CacheMode = Literal["auto", "full", "fast"]


def resolve_cache_root(mode: CacheMode = "auto") -> Path:
    """
    Cache root resolver (MovieFactory structure)

    Base:
      moviefactory/.cache/
        ├─ full_working/   (PRIMARY)
        └─ fast/           (OPTIONAL / legacy)
    """
    moviefactory_root = Path(__file__).resolve().parents[1]
    cache_base = moviefactory_root / ".cache"

    full_dir = cache_base / "full_working"
    fast_dir = cache_base / "fast"

    if mode == "full":
        return full_dir

    if mode == "fast":
        return fast_dir

    # auto: full_working 우선
    if full_dir.exists():
        return full_dir

    return fast_dir


def resolve_tfidf_paths(mode: CacheMode = "auto") -> dict:
    root = resolve_cache_root(mode)
    tfidf_dir = root / "tfidf"

    return {
        "matrix": tfidf_dir / "tfidf_matrix.npz",
        "vectorizer": tfidf_dir / "tfidf_vectorizer.pkl",
    }


def resolve_sbert_paths(mode: CacheMode = "auto") -> Path:
    return resolve_cache_root(mode) / "sbert" / "sbert_embeddings.npy"


def resolve_clip_paths(mode: CacheMode = "auto") -> Path:
    return resolve_cache_root(mode) / "clip" / "clip_embeddings.npz"


def resolve_cf_paths(mode: CacheMode = "auto") -> dict:
    root = resolve_cache_root(mode)
    cf_dir = root / "cf"

    return {
        "item_factors": cf_dir / "cf_item_factors.npy",
        "user_factors": cf_dir / "cf_user_factors.npy",
        "metadata": cf_dir / "cf_metadata.json",
    }
