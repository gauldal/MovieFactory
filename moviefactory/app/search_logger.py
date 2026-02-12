# moviefactory/app/search_logger.py

import json
import os
from datetime import datetime
from typing import List, Dict, Any


LOG_DIR = "logs"
LOG_FILE = "search_logs.jsonl"


class SearchLogger:
    """
    MovieFactory v1.3 — Search Logger

    책임:
    - 검색 1회당 로그 1건 기록
    - UI에 노출된 결과 순서 보존
    - 개인정보 미수집
    """

    @staticmethod
    def _ensure_log_dir():
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR, exist_ok=True)

    @staticmethod
    def log(
        *,
        search_type: str,
        query: str | None,
        genre: str | None,
        page: int,
        results: List[Dict[str, Any]],
    ) -> None:
        """
        results: UI에 실제로 노출된 결과 리스트
        """

        SearchLogger._ensure_log_dir()

        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "search_type": search_type,
            "query": query,
            "genre": genre,
            "page": page,
            "results": [
                {
                    "movie_id": r.get("movie_id"),
                    "rank": idx + 1,
                    "score": r.get("score"),
                }
                for idx, r in enumerate(results)
            ],
        }

        path = os.path.join(LOG_DIR, LOG_FILE)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
