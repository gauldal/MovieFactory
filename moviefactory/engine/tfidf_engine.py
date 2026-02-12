# moviefactory/engine/tfidf_engine.py

from __future__ import annotations

import numpy as np

from moviefactory.utils.engine_utils import (
    load_metadata,
    load_tfidf_matrix,
    load_tfidf_vectorizer,
)


class TFIDFScorer:
    """
    TF-IDF Scorer (Hybrid Engine Component)

    역할:
    - 텍스트 query → TF-IDF cosine score 생성
    - Top-K 결정 ❌ (단, Runtime에서 쓰기 좋게 top_k 옵션은 제공)
    - 검색 결과 반환 ❌
    - RuntimeEngine 내부에서만 사용 ⭕
    """

    def __init__(self):
        self.is_ready = False
        self.metadata = None
        self.matrix = None  # scipy sparse matrix expected
        self.vectorizer = None
        self.movie_ids: list[int] = []

        try:
            self.metadata = load_metadata() or {}
            self.matrix = load_tfidf_matrix()
            self.vectorizer = load_tfidf_vectorizer()

            if self.matrix is None or self.vectorizer is None:
                raise RuntimeError("TF-IDF assets missing")

            if "movie_ids" not in self.metadata:
                raise RuntimeError("metadata.json missing 'movie_ids'")

            self.movie_ids = [int(x) for x in self.metadata["movie_ids"]]

            # ✅ 길이 불일치 방어 (행 수 vs movie_ids)
            n_mat = int(self.matrix.shape[0])
            n_ids = int(len(self.movie_ids))
            n = min(n_mat, n_ids)

            if n == 0:
                raise RuntimeError("TF-IDF assets empty")

            if n_mat != n_ids:
                print(
                    f"[TFIDF] WARNING: length mismatch "
                    f"(matrix_rows={n_mat}, movie_ids={n_ids}) -> using n={n}"
                )
                self.matrix = self.matrix[:n]
                self.movie_ids = self.movie_ids[:n]

            self.is_ready = True

        except Exception as e:
            print("[TFIDF] scorer disabled:", e)
            self.is_ready = False
            self.metadata = None
            self.matrix = None
            self.vectorizer = None
            self.movie_ids = []

    def score(
        self,
        query: str,
        *,
        top_k: int | None = None,
        min_score: float = 0.0,
    ) -> dict[int, float]:
        """
        Generate TF-IDF lexical scores

        Returns:
            {movie_id: score}

        Notes:
            - 기존 코드 호환을 위해 기본값(top_k=None, min_score=0.0)은 "기존과 동일"하게 동작
            - RuntimeEngine이 후보 제한이 필요하면 top_k를 넘겨 사용
        """
        if not self.is_ready:
            return {}

        query = (query or "").strip()
        if not query:
            return {}

        if self.matrix is None or self.vectorizer is None or not self.movie_ids:
            return {}

        try:
            query_vec = self.vectorizer.transform([query])

            # ✅ 차원 불일치 방어
            if int(self.matrix.shape[1]) != int(query_vec.shape[1]):
                print(
                    "[TFIDF] WARNING: dimension mismatch "
                    f"(matrix_cols={self.matrix.shape[1]}, query_dim={query_vec.shape[1]})"
                )
                return {}

            scores = (self.matrix @ query_vec.T).toarray().ravel()

        except Exception as e:
            print("[TFIDF] score() failed:", e)
            return {}

        n = min(len(self.movie_ids), int(scores.shape[0]))
        if n <= 0:
            return {}

        # ✅ top_k 적용(선택)
        if top_k is not None:
            k = max(1, min(int(top_k), n))
            idx = np.argpartition(-scores[:n], k - 1)[:k]
            idx = idx[np.argsort(-scores[idx])]
        else:
            idx = range(n)

        out: dict[int, float] = {}
        for i in idx:
            s = float(scores[int(i)])
            if s > float(min_score):
                out[int(self.movie_ids[int(i)])] = s

        return out


# ==================================================
# Singleton instance (RuntimeEngine import target)
# ==================================================
tfidf_engine = TFIDFScorer()
