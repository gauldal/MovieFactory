# moviefactory/engine/clip_engine.py

from __future__ import annotations

import os

import numpy as np
import torch
import clip
from PIL import Image

from moviefactory.utils.engine_utils import (
    load_metadata,
    load_clip_embeddings,
)


class CLIPEngine:
    """
    CLIP Encoder
    - image -> embedding
    - text  -> embedding
    """

    def __init__(self):
        self.device = "cpu"
        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)

    def encode_image(self, image_path: str) -> np.ndarray | None:
        if not image_path:
            return None
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            print("[CLIP] Image.open failed:", e)
            return None

        image_input = self.preprocess(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            emb = self.model.encode_image(image_input)

        emb = emb.cpu().numpy().squeeze().astype(np.float32)
        norm = float(np.linalg.norm(emb))
        if norm < 1e-9:
            return None
        return emb / norm

    def encode_text(self, texts: list[str]) -> np.ndarray | None:
        if not texts:
            return None
        try:
            tokens = clip.tokenize(texts).to(self.device)
        except Exception as e:
            print("[CLIP] tokenize failed:", e)
            return None

        with torch.no_grad():
            emb = self.model.encode_text(tokens)

        emb = emb.cpu().numpy().astype(np.float32)
        denom = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-9
        return emb / denom


class CLIPScorer:
    """
    - score(image): image vs poster embeddings -> {movie_id: score}
    - score_prompts(image, prompts): image vs text prompts -> {prompt: score}
    """

    def __init__(self):
        self.is_ready = False
        self.metadata = None
        self.embeddings: np.ndarray | None = None
        self.movie_ids: list[int] = []
        self.encoder: CLIPEngine | None = None

        try:
            self.metadata = load_metadata() or {}

            # ✅ 1) clip_embeddings.npz를 우선 사용 (npz 안의 movie_ids가 "진짜 매핑 키")
            #    경로: moviefactory/.cache/full_working/clip/clip_embeddings.npz
            base_dir = os.path.dirname(os.path.dirname(__file__))  # moviefactory/
            npz_path = os.path.join(base_dir, ".cache", "full_working", "clip", "clip_embeddings.npz")

            embeddings = None
            movie_ids = None

            if os.path.exists(npz_path):
                z = np.load(npz_path)
                if "embeddings" not in z.files or "movie_ids" not in z.files:
                    raise RuntimeError(f"Invalid npz format: {npz_path} (need embeddings + movie_ids)")

                embeddings = z["embeddings"]
                movie_ids = z["movie_ids"].tolist()
            else:
                # ✅ 2) fallback: 기존 로더 사용 (하지만 이 경우도 movie_ids 매핑은 매우 위험)
                embeddings = load_clip_embeddings()
                if embeddings is None:
                    raise RuntimeError("CLIP embeddings missing")

                if "movie_ids" not in self.metadata:
                    raise RuntimeError("metadata.json missing 'movie_ids'")
                movie_ids = self.metadata["movie_ids"]

            self.embeddings = np.asarray(embeddings, dtype=np.float32)
            self.movie_ids = [int(x) for x in movie_ids]

            # ✅ 길이 불일치는 '자르기' 금지 (자르면 매핑이 틀어진 채로 굳어짐)
            n_emb = int(self.embeddings.shape[0])
            n_ids = int(len(self.movie_ids))
            if n_emb == 0 or n_ids == 0:
                raise RuntimeError("CLIP assets empty")

            if n_emb != n_ids:
                raise RuntimeError(
                    f"CLIP mapping mismatch: embeddings={n_emb}, movie_ids={n_ids}. "
                    f"Delete and rebuild CLIP cache (npz/metadata)."
                )

            # row normalize (cosine 안정화)
            denom = np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-9
            self.embeddings = (self.embeddings / denom).astype(np.float32)

            self.encoder = CLIPEngine()
            self.is_ready = True

            print(f"[CLIP] ready: n={n_emb} source={'npz' if os.path.exists(npz_path) else 'legacy'}")

        except Exception as e:
            print("[CLIP] scorer disabled:", e)
            self.is_ready = False
            self.metadata = None
            self.embeddings = None
            self.movie_ids = []
            self.encoder = None

    def score(
        self,
        image_path: str,
        *,
        top_k: int | None = None,
        min_score: float = -1.0,
    ) -> dict[int, float]:
        if not self.is_ready or not image_path or self.embeddings is None or self.encoder is None:
            return {}

        img_emb = self.encoder.encode_image(image_path)
        if img_emb is None:
            return {}

        scores = self.embeddings @ img_emb  # cosine
        n = int(scores.shape[0])
        if n == 0:
            return {}

        if top_k is not None:
            k = max(1, min(int(top_k), n))
            idx = np.argpartition(-scores, k - 1)[:k]
            idx = idx[np.argsort(-scores[idx])]
        else:
            idx = np.argsort(-scores)

        out: dict[int, float] = {}
        for i in idx:
            s = float(scores[int(i)])
            if s >= float(min_score):
                out[int(self.movie_ids[int(i)])] = s
        return out

    def score_prompts(self, image_path: str, prompts: list[str]) -> dict[str, float]:
        if not self.is_ready or not image_path or not prompts or self.encoder is None:
            return {}

        img_emb = self.encoder.encode_image(image_path)
        if img_emb is None:
            return {}

        txt_embs = self.encoder.encode_text(prompts)
        if txt_embs is None:
            return {}

        scores = txt_embs @ img_emb
        return {prompts[i]: float(scores[i]) for i in range(len(prompts))}


clip_engine = CLIPScorer()
