# moviefactory/engine/clip_engine.py
from __future__ import annotations

import os
from typing import Optional

import numpy as np
from PIL import Image

from moviefactory.utils.engine_utils import (
    load_metadata,
    load_clip_embeddings,
)


class CLIPEngine:
    """
    CLIP Encoder (lazy heavy imports inside __init__)
    - image -> embedding
    - text  -> embedding
    """

    def __init__(self):
        # Heavy imports are intentionally inside __init__ (Render Free 안정화)
        import torch  # noqa: WPS433
        import open_clip  # noqa: WPS433

        self._torch = torch
        self._open_clip = open_clip

        self.device = "cpu"
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32",
            pretrained="openai",
        )
        self.model = self.model.to(self.device)
        self.model.eval()

    def encode_image(self, image_path: str) -> Optional[np.ndarray]:
        if not image_path:
            return None
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            print("[CLIP] Image.open failed:", e)
            return None

        torch = self._torch
        image_input = self.preprocess(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            emb = self.model.encode_image(image_input)

        emb = emb.cpu().numpy().squeeze().astype(np.float32)
        norm = float(np.linalg.norm(emb))
        if norm < 1e-9:
            return None
        return emb / norm

    def encode_text(self, texts: list[str]) -> Optional[np.ndarray]:
        if not texts:
            return None

        torch = self._torch
        open_clip = self._open_clip

        try:
            tokens = open_clip.tokenize(texts).to(self.device)
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
        # Render에서 완전히 끄고 싶으면 환경변수로 제어
        # Render Dashboard > Environment Variables: DISABLE_CLIP=1
        if os.getenv("DISABLE_CLIP", "").strip().lower() in {"1", "true", "yes", "y"}:
            print("[CLIP] disabled by DISABLE_CLIP env")
            self.is_ready = False
            self.metadata = None
            self.embeddings = None
            self.movie_ids = []
            self.encoder = None
            return

        self.is_ready = False
        self.metadata = None
        self.embeddings: Optional[np.ndarray] = None
        self.movie_ids: list[int] = []
        self.encoder: Optional[CLIPEngine] = None

        try:
            self.metadata = load_metadata() or {}

            # ✅ 1) clip_embeddings.npz 우선 사용
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
                # ✅ 2) fallback: 기존 로더
                embeddings = load_clip_embeddings()
                if embeddings is None:
                    raise RuntimeError("CLIP embeddings missing")
                if "movie_ids" not in self.metadata:
                    raise RuntimeError("metadata.json missing 'movie_ids'")
                movie_ids = self.metadata["movie_ids"]

            self.embeddings = np.asarray(embeddings, dtype=np.float32)
            self.movie_ids = [int(x) for x in movie_ids]

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

            # ✅ encoder는 여기서 만들지 않는다 (진짜 중요!)
            self.encoder = None
            self.is_ready = True

            print(f"[CLIP] ready (encoder lazy): n={n_emb} source={'npz' if os.path.exists(npz_path) else 'legacy'}")

        except Exception as e:
            print("[CLIP] scorer disabled:", e)
            self.is_ready = False
            self.metadata = None
            self.embeddings = None
            self.movie_ids = []
            self.encoder = None

    def _get_encoder(self) -> Optional[CLIPEngine]:
        if not self.is_ready:
            return None
        if self.encoder is not None:
            return self.encoder

        try:
            self.encoder = CLIPEngine()
            return self.encoder
        except Exception as e:
            # 모델 로딩 실패하면 이후 요청도 계속 실패하므로 disable 처리
            print("[CLIP] encoder init failed; disabling CLIP:", e)
            self.encoder = None
            self.is_ready = False
            return None

    def score(
        self,
        image_path: str,
        *,
        top_k: Optional[int] = None,
        min_score: float = -1.0,
    ) -> dict[int, float]:
        if not self.is_ready or not image_path or self.embeddings is None:
            return {}

        enc = self._get_encoder()
        if enc is None:
            return {}

        img_emb = enc.encode_image(image_path)
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
        if not self.is_ready or not image_path or not prompts:
            return {}

        enc = self._get_encoder()
        if enc is None:
            return {}

        img_emb = enc.encode_image(image_path)
        if img_emb is None:
            return {}

        txt_embs = enc.encode_text(prompts)
        if txt_embs is None:
            return {}

        scores = txt_embs @ img_emb
        return {prompts[i]: float(scores[i]) for i in range(len(prompts))}


_clip_engine_instance: Optional[CLIPScorer] = None


def get_clip_engine() -> CLIPScorer:
    """
    Global accessor (lazy singleton)
    - CLIPScorer is created only when first requested
    - encoder/model is created only when score() is called
    """
    global _clip_engine_instance
    if _clip_engine_instance is None:
        _clip_engine_instance = CLIPScorer()
    return _clip_engine_instance