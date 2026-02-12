# moviefactory/engine/sbert_engine.py

from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

from moviefactory.utils.engine_utils import (
    load_metadata,
    load_sbert_embeddings,
)


class SBERTEncoder:
    """
    SBERT Encoder (Embedding Generator)

    역할:
    - 텍스트 → SBERT embedding 생성
    - 점수 계산 ❌ (encoder 책임 아님)
    """

    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def encode(self, text: str) -> np.ndarray | None:
        text = (text or "").strip()
        if not text:
            return None
        # normalize_embeddings=True → cosine dot-product에 안전
        return self.model.encode(text, normalize_embeddings=True)


class SBERTScorer:
    """
    SBERT Scorer (Hybrid Engine Component)

    역할:
    - 텍스트 query → cosine similarity score 생성
    - Top-K 결정 ❌ (단, Runtime에서 쓰기 좋게 top_k 옵션 제공)
    - 검색 결과 반환 ❌
    - RuntimeEngine 내부에서만 사용 ⭕
    """

    def __init__(self):
        self.is_ready = False
        self.metadata = None
        self.embeddings: np.ndarray | None = None
        self.movie_ids: list[int] = []
        self.encoder: SBERTEncoder | None = None

        try:
            self.metadata = load_metadata() or {}
            self.embeddings = load_sbert_embeddings()

            if self.embeddings is None:
                raise RuntimeError("SBERT embeddings missing")

            if "movie_ids" not in self.metadata:
                raise RuntimeError("metadata.json missing 'movie_ids'")

            self.movie_ids = [int(x) for x in self.metadata["movie_ids"]]

            # ✅ 길이 불일치 방어
            n_emb = int(self.embeddings.shape[0])
            n_ids = int(len(self.movie_ids))
            n = min(n_emb, n_ids)

            if n == 0:
                raise RuntimeError("SBERT assets empty")

            if n_emb != n_ids:
                print(
                    f"[SBERT] WARNING: length mismatch "
                    f"(embeddings={n_emb}, movie_ids={n_ids}) -> using n={n}"
                )
                self.embeddings = self.embeddings[:n]
                self.movie_ids = self.movie_ids[:n]

            self.encoder = SBERTEncoder()
            self.is_ready = True

        except Exception as e:
            print("[SBERT] scorer disabled:", e)
            self.is_ready = False
            self.metadata = None
            self.embeddings = None
            self.movie_ids = []
            self.encoder = None

    def score(
        self,
        query: str,
        *,
        top_k: int | None = None,
        min_score: float = 0.0,
    ) -> dict[int, float]:
        """
        Generate SBERT semantic scores

        Returns:
            {movie_id: score}

        Notes:
            - 기본 동작은 기존과 동일(양수 점수만 dict로)
            - RuntimeEngine이 후보 제한이 필요하면 top_k를 넘겨 사용
        """
        if not self.is_ready:
            return {}

        query = (query or "").strip()
        if not query:
            return {}

        if self.embeddings is None or self.encoder is None or not self.movie_ids:
            return {}

        q_emb = self.encoder.encode(query)
        if q_emb is None:
            return {}

        n = min(int(self.embeddings.shape[0]), len(self.movie_ids))
        if n <= 0:
            return {}

        try:
            scores = self.embeddings[:n] @ q_emb  # (n,)
        except Exception as e:
            print("[SBERT] score() failed:", e)
            return {}

        # ✅ top_k 적용(선택)
        if top_k is not None:
            k = max(1, min(int(top_k), n))
            idx = np.argpartition(-scores, k - 1)[:k]
            idx = idx[np.argsort(-scores[idx])]
        else:
            idx = range(int(scores.shape[0]))

        out: dict[int, float] = {}
        for i in idx:
            s = float(scores[int(i)])
            if s > float(min_score):
                out[int(self.movie_ids[int(i)])] = s
        return out


# ==================================================
# Singleton instance (RuntimeEngine import target)
# ==================================================
sbert_engine = SBERTScorer()
