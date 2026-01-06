"""
CLIP Engine
-----------
- Poster image embedding (offline preprocessing)
- Single image embedding (online inference)
- CLIP-based image similarity search for service

This module intentionally separates:
1) build_clip_embeddings()  -> offline
2) embed_single_image()     -> online
3) search_by_clip_embedding -> online

No Flask code here.
No hybrid logic here.
"""

from pathlib import Path
from typing import Union, List
import pickle

import numpy as np
import torch
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity

import clip  # OpenAI CLIP


# ============================================================
# PATH CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
CACHE_DIR = BASE_DIR / ".cache"
POSTER_DIR = BASE_DIR / "data" / "posters"

CACHE_DIR.mkdir(exist_ok=True)


# ============================================================
# MODEL LOAD (ONCE)
# ============================================================

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL, PREPROCESS = clip.load("ViT-B/32", device=DEVICE)


# ============================================================
# OFFLINE: BUILD ALL POSTER EMBEDDINGS
# ============================================================

def build_clip_embeddings(
    poster_paths: List[Path],
    output_path: Path = CACHE_DIR / "clip_embeddings.pkl",
) -> np.ndarray:
    """
    Build CLIP embeddings for all poster images (offline).

    Args:
        poster_paths: list of poster image Paths
        output_path : where to save pickle

    Returns:
        embeddings (N, D)
    """
    embeddings = []

    for path in poster_paths:
        if not path.exists():
            # keep index alignment
            embeddings.append(None)
            continue

        try:
            image = Image.open(path).convert("RGB")
            image_tensor = PREPROCESS(image).unsqueeze(0).to(DEVICE)

            with torch.no_grad():
                emb = MODEL.encode_image(image_tensor)
                emb = emb / emb.norm(dim=-1, keepdim=True)

            embeddings.append(emb.cpu().numpy()[0])

        except Exception:
            embeddings.append(None)

    # replace None with zeros (safe similarity)
    dim = embeddings[0].shape[0]
    embeddings = [
        e if e is not None else np.zeros(dim, dtype=np.float32)
        for e in embeddings
    ]

    matrix = np.vstack(embeddings)

    with open(output_path, "wb") as f:
        pickle.dump(matrix, f)

    return matrix


# ============================================================
# ONLINE: SINGLE IMAGE EMBEDDING
# ============================================================

def embed_single_image(
    image_input: Union[str, Path, Image.Image]
) -> np.ndarray:
    """
    Embed a single image using CLIP (online inference).

    Args:
        image_input:
          - file path (str or Path)
          - PIL Image

    Returns:
        embedding (D,)
    """
    if isinstance(image_input, (str, Path)):
        image = Image.open(image_input).convert("RGB")
    elif isinstance(image_input, Image.Image):
        image = image_input.convert("RGB")
    else:
        raise ValueError("Unsupported image input type")

    image_tensor = PREPROCESS(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        emb = MODEL.encode_image(image_tensor)
        emb = emb / emb.norm(dim=-1, keepdim=True)

    return emb.cpu().numpy()[0]


# ============================================================
# ONLINE: CLIP IMAGE SEARCH
# ============================================================

def search_by_clip_embedding(
    query_embedding: np.ndarray,
    clip_matrix: np.ndarray,
    top_k: int = 10
) -> List[int]:
    """
    CLIP-based image similarity search.

    Args:
        query_embedding : (D,)
        clip_matrix    : (N, D)
        top_k           : number of results

    Returns:
        list of indices (movie indices)
    """
    if query_embedding.ndim == 1:
        query_embedding = query_embedding.reshape(1, -1)

    sims = cosine_similarity(query_embedding, clip_matrix)[0]
    ranked = np.argsort(sims)[::-1]

    return ranked[:top_k].tolist()


# ============================================================
# UTIL: LOAD CACHED MATRIX
# ============================================================

def load_clip_matrix(
    path: Path = CACHE_DIR / "clip_embeddings.pkl"
) -> np.ndarray:
    """
    Load precomputed CLIP embedding matrix.
    """
    if not path.exists():
        raise FileNotFoundError("clip_embeddings.pkl not found")

    with open(path, "rb") as f:
        return pickle.load(f)
