"""
Runtime Engine
==============
- 책임: Web/API/Dashboard 공통 런타임 검색 허브
- 역할:
  1) 캐시 보장 (SBERT / TF-IDF / CF / Hybrid)
  2) baseline 검색 (문자열 필터링 전용)
  3) 단건 조회 및 유사 영화 조회 지원

⚠️ 중요:
- SBERT / TF-IDF / CF / Hybrid 검색은 search_api.py에서 담당
- 본 파일의 search()는 빠른 baseline 검색 ONLY
"""

import os
import csv
from pathlib import Path
from typing import List, Dict, Optional

from moviefactory.engines.sbert_engine import run_sbert
from moviefactory.engines.tfidf_engine import run_tfidf
from moviefactory.engines.meta_engine import run_cf
from moviefactory.engines.hybrid_engine import run_hybrid


class RuntimeEngine:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / "data"
        self.cache_dir = self.project_root / ".cache"

        self.movie_csv = self.data_dir / "movie_clean_data.csv"

        self._movies: List[Dict] = []
        self._id_to_index: Dict[int, int] = {}

        self._load_movies()
        self._ensure_caches()

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _safe_float(self, v, default: float = 0.0) -> float:
        """
        Defensive float conversion.
        Prevents runtime errors caused by malformed CSV values.
        """
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def _load_movies(self):
        if not self.movie_csv.exists():
            raise FileNotFoundError(f"Movie CSV not found: {self.movie_csv}")

        with open(self.movie_csv, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            self._movies = list(reader)

        self._id_to_index = {
            int(row["movie_id"]): idx
            for idx, row in enumerate(self._movies)
            if row.get("movie_id") is not None
        }

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------
    def _is_hybrid_stale(self) -> bool:
        """
        Hybrid cache becomes stale if any dependency cache
        is newer than hybrid cache.
        """
        hybrid = self.cache_dir / "hybrid_similarity.pkl"
        deps = [
            self.cache_dir / "sbert_embeddings.pkl",
            self.cache_dir / "tfidf_matrix.pkl",
            self.cache_dir / "cf_matrix.pkl",
        ]

        if not hybrid.exists():
            return True

        for p in deps:
            if p.exists() and p.stat().st_mtime > hybrid.stat().st_mtime:
                return True

        return False

    def _ensure_caches(self):
        """
        Ensure all engine caches exist.
        Executed once at runtime engine initialization.
        """
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        run_sbert(self.project_root)
        run_tfidf(self.project_root)
        run_cf(self.project_root)

        if self._is_hybrid_stale():
            run_hybrid(self.project_root)

    # ------------------------------------------------------------------
    # Baseline Search
    # ------------------------------------------------------------------
    def search(
        self,
        query: Optional[str] = None,
        genre: Optional[str] = None,
        page: int = 1,
        per_page: int = 24,
    ) -> Dict:
        """
        Baseline search ONLY.

        - Performs fast string-based filtering on title/overview/genre
        - DOES NOT use SBERT / TF-IDF / CF / Hybrid
        - Advanced search is handled in search_api.py
        """
        results = []

        q = query.lower().strip() if query else None
        g = genre.lower().strip() if genre else None

        for row in self._movies:
            title = (row.get("title") or "").lower()
            overview = (row.get("overview") or "").lower()
            genres = (row.get("genres") or "").lower()

            if q and q not in title and q not in overview:
                continue

            if g and g not in genres:
                continue

            results.append(row)

        total = len(results)
        start = (page - 1) * per_page
        end = start + per_page

        page_items = results[start:end]

        return {
            "page": page,
            "per_page": per_page,
            "total": total,
            "results": page_items,
        }

    # ------------------------------------------------------------------
    # Single movie
    # ------------------------------------------------------------------
    def get_movie(self, movie_id: int) -> Optional[Dict]:
        idx = self._id_to_index.get(movie_id)
        if idx is None:
            return None

        row = self._movies[idx].copy()

        # Defensive numeric parsing
        row["popularity"] = self._safe_float(row.get("popularity"))
        row["vote_average"] = self._safe_float(row.get("vote_average"))
        row["vote_count"] = self._safe_float(row.get("vote_count"))

        return row

    # ------------------------------------------------------------------
    # Similar movies (Hybrid)
    # ------------------------------------------------------------------
    def similar_movies(self, movie_id: int, limit: int = 16) -> List[Dict]:
        idx = self._id_to_index.get(movie_id)
        if idx is None:
            return []

        # Hybrid similarity cache is guaranteed at init
        from moviefactory.engines.hybrid_engine import load_hybrid_matrix

        sim_matrix = load_hybrid_matrix(self.project_root)
        scores = sim_matrix[idx]

        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True
        )

        results = []
        for i, score in ranked[1:limit + 1]:
            row = self._movies[i].copy()
            row["hybrid_score"] = float(score)
            results.append(row)

        return results
