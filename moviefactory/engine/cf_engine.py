# moviefactory/engine/cf_engine.py

import numpy as np
import pickle
from pathlib import Path


class CFSVDScorer:
    """
    CF-SVD Scorer (Hybrid Engine Component)

    역할:
    - 가상 사용자 ID → 영화 선호도 점수 생성
    - 검색 / 랭킹 / 결과 결정 ❌
    - RuntimeEngine 내부에서만 사용 ⭕️
    """

    def __init__(self, model_path: Path):
        """
        Args:
            model_path: SVD 모델 + movie_id mapping pickle
        """
        self.model_path = model_path
        self.model = None
        self.movie_ids = None

        self._load_model()

    def _load_model(self):
        try:
            with open(self.model_path, "rb") as f:
                payload = pickle.load(f)

            self.model = payload["model"]          # surprise SVD or equivalent
            self.movie_ids = payload["movie_ids"]  # index → movie_id

            # 안전 타입 정규화
            self.movie_ids = [int(x) for x in self.movie_ids]

        except Exception as e:
            raise RuntimeError(f"CF-SVD model load failed: {e}")

    def score_by_user(self, user_id: int) -> dict[int, float]:
        """
        Generate CF preference scores for a virtual user

        Returns:
            {movie_id: score}
        """
        if self.model is None or not self.movie_ids:
            return {}

        try:
            user_id = int(user_id)
        except Exception:
            return {}

        scores: dict[int, float] = {}
        for movie_id in self.movie_ids:
            try:
                est = self.model.predict(user_id, movie_id).est
                scores[int(movie_id)] = float(est)
            except Exception:
                continue

        return scores
