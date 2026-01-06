"""
Movie Domain API
================
- 단건 영화 조회 전용
- movie_id 기준 1건 반환
"""

from pathlib import Path
from flask import Blueprint, jsonify, abort

from moviefactory.engine.runtime_engine import RuntimeEngine

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
CLEAN_CSV = DATA_DIR / "movie_clean_data.csv"
CACHE_DIR = DATA_DIR.parent / ".cache"

movie_bp = Blueprint("movie_api", __name__, url_prefix="/api/movie")

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = RuntimeEngine(
            data_path=str(CLEAN_CSV),
            cache_dir=str(CACHE_DIR),
        )
    return _engine


@movie_bp.route("/<int:movie_id>", methods=["GET"])
def get_movie(movie_id: int):
    engine = get_engine()
    movie = engine.get_movie_by_id(movie_id)

    if not movie:
        abort(404, "Movie not found")

    return jsonify(movie)
