"""
Search API
==========
- 책임: 고급 검색 엔드포인트 제공
- 사용 엔진:
  - SBERT (text semantic)
  - CLIP (image semantic)
  - TF-IDF (keyword)
  - CF (collaborative)
  - Hybrid (weighted aggregation)
- RuntimeEngine:
  - baseline search / 단건 조회 / 유사 영화만 담당
"""

from pathlib import Path
from flask import Blueprint, request, jsonify, abort

from moviefactory.runtime.runtime_engine import RuntimeEngine
from moviefactory.engines.sbert_engine import search_sbert
from moviefactory.engines.clip_engine import search_clip
from moviefactory.engines.tfidf_engine import search_tfidf
from moviefactory.engines.meta_engine import search_cf
from moviefactory.engines.hybrid_engine import search_hybrid


# --------------------------------------------------
# INIT
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
engine = RuntimeEngine(PROJECT_ROOT)

search_bp = Blueprint(
    "search_api",
    __name__,
    url_prefix="/api/search"
)

# --------------------------------------------------
# UTIL
# --------------------------------------------------

def paginate(results, page: int, per_page: int):
    total = len(results)
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "movies": results[start:end],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page,
    }

# --------------------------------------------------
# BASELINE (TEXT / GENRE)
# --------------------------------------------------

@search_bp.route("/text", methods=["GET"])
def search_text():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", type=int, default=1)
    per_page = request.args.get("per_page", type=int, default=24)

    if not q:
        abort(400, "query(q) is required")

    result = engine.search(query=q, page=page, per_page=per_page)

    return jsonify({
        "movies": result["results"],
        "page": page,
        "per_page": per_page,
        "total": result["total"],
        "total_pages": (result["total"] + per_page - 1) // per_page,
    })


@search_bp.route("/genre", methods=["GET"])
def search_genre():
    genre = request.args.get("genre", "").strip()
    page = request.args.get("page", type=int, default=1)
    per_page = request.args.get("per_page", type=int, default=24)

    if not genre:
        abort(400, "genre is required")

    # SF → science fiction 매핑
    if genre.lower() == "sf":
        genre = "science fiction"

    result = engine.search(genre=genre, page=page, per_page=per_page)

    return jsonify({
        "movies": result["results"],
        "page": page,
        "per_page": per_page,
        "total": result["total"],
        "total_pages": (result["total"] + per_page - 1) // per_page,
    })

# --------------------------------------------------
# SBERT
# --------------------------------------------------

@search_bp.route("/sbert", methods=["GET"])
def search_sbert_api():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", type=int, default=1)
    per_page = request.args.get("per_page", type=int, default=24)

    if not q:
        abort(400, "query(q) is required")

    results = search_sbert(PROJECT_ROOT, q)
    return jsonify(paginate(results, page, per_page))

# --------------------------------------------------
# TF-IDF
# --------------------------------------------------

@search_bp.route("/tfidf", methods=["GET"])
def search_tfidf_api():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", type=int, default=1)
    per_page = request.args.get("per_page", type=int, default=24)

    if not q:
        abort(400, "query(q) is required")

    results = search_tfidf(PROJECT_ROOT, q)
    return jsonify(paginate(results, page, per_page))

# --------------------------------------------------
# CF
# --------------------------------------------------

@search_bp.route("/cf", methods=["GET"])
def search_cf_api():
    movie_id = request.args.get("movie_id", type=int)
    page = request.args.get("page", type=int, default=1)
    per_page = request.args.get("per_page", type=int, default=24)

    if movie_id is None:
        abort(400, "movie_id is required")

    results = search_cf(PROJECT_ROOT, movie_id)
    return jsonify(paginate(results, page, per_page))

# --------------------------------------------------
# IMAGE (CLIP)
# --------------------------------------------------

@search_bp.route("/image", methods=["POST"])
def search_image():
    if "image" not in request.files:
        abort(400, "image file is required")

    image = request.files["image"]
    if not image.filename:
        abort(400, "empty image file")

    page = request.form.get("page", type=int, default=1)
    per_page = request.form.get("per_page", type=int, default=24)

    results = search_clip(PROJECT_ROOT, image)
    return jsonify(paginate(results, page, per_page))

# --------------------------------------------------
# HYBRID
# --------------------------------------------------

@search_bp.route("/hybrid", methods=["POST"])
def search_hybrid_api():
    q = request.form.get("q", "").strip()
    movie_id = request.form.get("movie_id", type=int)

    page = request.form.get("page", type=int, default=1)
    per_page = request.form.get("per_page", type=int, default=24)

    if not q and movie_id is None:
        abort(400, "q or movie_id is required")

    results = search_hybrid(
        PROJECT_ROOT,
        query=q if q else None,
        movie_id=movie_id
    )

    return jsonify(paginate(results, page, per_page))
