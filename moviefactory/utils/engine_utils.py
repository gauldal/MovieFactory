# moviefactory/utils/engine_utils.py
"""
MovieFactory utils/engine_utils.py

엔진 공통 유틸 (SAFE MODE)

정책:
- full_working 캐시를 기본으로 사용
- 파일이 없으면 엔진 비활성(빈 값 반환)
- 서버 500 절대 발생 ❌ (가능한 범위에서 안전 처리)
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import json
import numpy as np
import pickle
import os
from scipy.sparse import load_npz

from moviefactory.utils.cache_loader import resolve_cache_root


# ==================================================
# Cache Root
# ==================================================
def _get_cache_root() -> Path:
    """
    캐시 루트는 full_working을 기본으로 한다.
    (사용자 요구: 캐시 루트 폴더명은 full_working)
    """
    # auto는 full_working 우선
    mode = os.environ.get("MOVIEFACTORY_CACHE_MODE", "AUTO").strip().lower()
    if mode in ("full", "full_working"):
        return resolve_cache_root("full")
    if mode in ("fast",):
        # 남겨두되, 기본은 full_working
        return resolve_cache_root("fast")
    return resolve_cache_root("auto")


# ==================================================
# Metadata (OPTIONAL)
# ==================================================
def load_metadata() -> Optional[Dict[str, Any]]:
    """
    Root metadata.json 로드 (OPTIONAL)

    주의:
    - metadata.json의 movie_ids 길이와 특정 엔진 캐시(예: CLIP npz)의 movie_ids 길이가
      다를 수 있다.
    - 이 함수는 원본 metadata.json을 그대로 반환한다.
    - 개별 엔진 로더는 필요 시 자체적으로 정렬/정합을 맞춘다.
    """
    root = _get_cache_root()
    meta_path = root / "metadata.json"
    if not meta_path.exists():
        return None
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# ==================================================
# Internal safe loaders
# ==================================================
def _safe_load_numpy(path: Path):
    try:
        return np.load(path) if path.exists() else None
    except Exception:
        return None


def _safe_load_pickle(path: Path):
    try:
        if not path.exists():
            return None
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None


# ==================================================
# SBERT
# ==================================================
def load_sbert_embeddings():
    """
    Returns:
        np.ndarray | None
        shape: (N, 384)
    """
    root = _get_cache_root()
    path = root / "sbert" / "sbert_embeddings.npy"
    return _safe_load_numpy(path)


# ==================================================
# TFIDF
# ==================================================
def load_tfidf_matrix():
    root = _get_cache_root()
    path = root / "tfidf" / "tfidf_matrix.npz"
    try:
        return load_npz(path) if path.exists() else None
    except Exception:
        return None



def load_tfidf_vectorizer():
    """
    Returns:
        sklearn TfidfVectorizer | None
    """
    root = _get_cache_root()
    path = root / "tfidf" / "tfidf_vectorizer.pkl"
    return _safe_load_pickle(path)


# ==================================================
# CLIP
# ==================================================
def _load_clip_npz() -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """
    clip_embeddings.npz 로드

    Returns:
        (movie_ids, embeddings) or None
    """
    root = _get_cache_root()
    path = root / "clip" / "clip_embeddings.npz"
    if not path.exists():
        return None

    try:
        z = np.load(path)
        if not isinstance(z, np.lib.npyio.NpzFile):
            return None

        if "embeddings" not in z.files:
            return None

        emb = z["embeddings"]
        mids = z["movie_ids"] if "movie_ids" in z.files else None
        return (mids, emb)
    except Exception:
        return None


def load_clip_embeddings():
    """
    CLIP scorer가 사용하는 임베딩 행렬을 반환한다.

    중요:
    - 기존 프로젝트에서는 root/metadata.json의 movie_ids(예: 18901) 길이와
      clip_embeddings.npz의 movie_ids(예: 2234) 길이가 다를 수 있다.
    - clip_engine은 metadata["movie_ids"]를 인덱싱에 사용하므로,
      여기서 임베딩을 metadata 길이에 맞춰 "정렬/확장"해준다.
    - 결과: scores 계산은 정상이며, 실제로 존재하는 포스터 영화만 양수 점수를 갖게 된다.

    Returns:
        np.ndarray | None
        shape: (N_meta, 512)  또는 (N_clip, 512) (metadata 없을 때)
    """
    meta = load_metadata()
    clip_npz = _load_clip_npz()
    if clip_npz is None:
        return None

    clip_movie_ids, clip_embeddings = clip_npz

    # metadata가 없거나, movie_ids가 없으면 clip embeddings 그대로 반환
    if not meta or "movie_ids" not in meta:
        return clip_embeddings

    try:
        meta_ids = [int(x) for x in meta["movie_ids"]]
    except Exception:
        return clip_embeddings

    # clip npz에 movie_ids가 없으면(구버전), 길이가 같을 때만 그대로 사용
    if clip_movie_ids is None:
        if len(meta_ids) == len(clip_embeddings):
            return clip_embeddings
        # 불일치면 안전하게 비활성
        return None

    try:
        clip_ids = [int(x) for x in clip_movie_ids.tolist()]
    except Exception:
        return None

    # 이미 길이가 맞으면 그대로 사용
    if len(meta_ids) == len(clip_embeddings) and len(clip_ids) == len(meta_ids):
        return clip_embeddings

    # metadata 길이에 맞춰 0-패딩 행렬 생성 후 clip subset만 삽입
    n_meta = len(meta_ids)
    try:
        out = np.zeros((n_meta, clip_embeddings.shape[1]), dtype=clip_embeddings.dtype)
    except Exception:
        return None

    index_map = {mid: i for i, mid in enumerate(meta_ids)}

    for j, mid in enumerate(clip_ids):
        i = index_map.get(mid)
        if i is None:
            continue
        if j >= clip_embeddings.shape[0]:
            break
        out[i] = clip_embeddings[j]

    return out


# ==================================================
# CF (optional)
# ==================================================
def load_cf_item_factors():
    """
    Returns:
        np.ndarray | None
    """
    root = _get_cache_root()
    path = root / "cf" / "cf_item_factors.npy"
    return _safe_load_numpy(path)
