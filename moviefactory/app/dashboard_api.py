# ======================================================
# moviefactory/app/dashboard_api.py
# ======================================================
"""
MovieFactory Dashboard API

변경 원칙 (중요):
- 기존 코드/라우트/로직 삭제 ❌
- 기존 동작 의미 변경 ❌
- ADD ONLY
- 신규 기능은 의도와 책임을 주석으로 명시

추가 내용:
- Engine Comparison 전용 API
  (쿼리 기반 TF-IDF / SBERT / CLIP similarity)
- 기존 search_hybrid 경로와 완전히 분리
"""

from flask import Blueprint, jsonify, request, render_template
import os
import tempfile

from moviefactory.engine.engine_provider import get_runtime_engine

bp = Blueprint("dashboard_pages", __name__)

# ======================================================
# Dashboard About
# ======================================================
@bp.route("/dashboard/about", methods=["GET"])
def dashboard_about():
    return render_template(
        "dashboard_about.html",
        streamlit_url="http://127.0.0.1:8501"
    )


# ======================================================
# Dataset Overview
# ======================================================
@bp.route("/dashboard/overview", methods=["GET"])
def dashboard_overview():
    runtime_engine = get_runtime_engine()
    df = runtime_engine.df

    if df is None or df.empty:
        return jsonify({
            "total_movies": 0,
            "avg_rating": None,
            "avg_popularity": None,
            "top20_avg_rating": None,
            "recent_10y_ratio": None,
            "year_distribution": {},
        })

    total_movies = len(df)

    avg_rating = float(df["vote_average"].mean())
    avg_popularity = float(df["popularity"].mean())

    threshold = df["vote_average"].quantile(0.8)
    top20 = df[df["vote_average"] >= threshold]
    top20_avg_rating = float(top20["vote_average"].mean())

    year_series = df["release_date"].astype(str).str.slice(0, 4)
    year_series = year_series[year_series.str.isdigit()].astype(int)

    current_year = year_series.max() if not year_series.empty else 0
    recent_10y = year_series >= (current_year - 9) if current_year else year_series >= 0
    recent_10y_ratio = round(float(recent_10y.sum() / total_movies * 100), 1) if total_movies else 0.0

    year_distribution = year_series.value_counts().sort_index().to_dict()

    return jsonify({
        "total_movies": total_movies,
        "avg_rating": round(avg_rating, 2),
        "avg_popularity": round(avg_popularity, 2),
        "top20_avg_rating": round(top20_avg_rating, 2),
        "recent_10y_ratio": recent_10y_ratio,
        "year_distribution": year_distribution,
    })


# ======================================================
# Recommendation Analysis (Dummy)
# ======================================================
@bp.route("/dashboard/recommendation_analysis", methods=["GET"])
def dashboard_recommendation_analysis():
    return jsonify({
        "engine_contribution": {
            "TF-IDF": 0.30,
            "SBERT": 0.40,
            "CLIP": 0.15,
            "CF-SVD": 0.15
        },
        "ranker_comparison": {
            "TF-IDF": {"off": 0.62, "on": 0.71},
            "SBERT": {"off": 0.68, "on": 0.78},
            "CLIP": {"off": 0.55, "on": 0.63},
            "CF-SVD": {"off": 0.58, "on": 0.66}
        }
    })


# ======================================================
# 내부 유틸: movie_id → title 보강
# ======================================================
def _attach_title(runtime_engine, movies):
    """
    Dashboard View-Model 생성 책임
    engine 결과(movie_id, score)에 title을 붙인다

    주의:
    - score는 '검색 결과 score'일 뿐
      엔진별 similarity를 의미하지 않는다.
    """
    df = runtime_engine.df
    if df is None or df.empty:
        return []

    title_map = dict(zip(df["movie_id"], df["title"]))

    results = []
    for m in movies:
        movie_id = m.get("movie_id")
        try:
            movie_id_int = int(movie_id)
        except Exception:
            movie_id_int = movie_id

        results.append({
            "title": title_map.get(movie_id_int, "Unknown"),
            "score": round(float(m.get("score", 0) or 0.0), 4),
        })

    return results


# ======================================================
# Search Controls — TEXT (Hybrid Search)
# ======================================================
@bp.route("/dashboard/search/text", methods=["POST"])
def dashboard_search_text():
    payload = request.get_json(silent=True) or {}
    query = (payload.get("query") or "").strip()

    if not query:
        return jsonify({"results": []})

    runtime_engine = get_runtime_engine()

    # ✅ RuntimeEngine.search_hybrid() CONTRACT:
    #    returns List[Dict] ONLY (tuple 반환 금지)
    movies = runtime_engine.search_hybrid(
        query=query,
        search_type="text",
        sort="popular",
    )

    # 대시보드는 상위 5개만 표시
    results = _attach_title(runtime_engine, (movies or [])[:5])
    return jsonify({"results": results})


# ======================================================
# Search Controls — IMAGE (Hybrid CLIP)
# ======================================================
@bp.route("/dashboard/search/image", methods=["POST"])
def dashboard_search_image():
    if "image" not in request.files:
        return jsonify({"results": []})

    image = request.files["image"]
    if image.filename == "":
        return jsonify({"results": []})

    tmp_dir = tempfile.gettempdir()
    tmp_path = os.path.join(tmp_dir, "dashboard_clip_query.jpg")
    image.save(tmp_path)

    runtime_engine = get_runtime_engine()

    # ✅ RuntimeEngine.search_hybrid() CONTRACT:
    #    returns List[Dict] ONLY (tuple 반환 금지)
    movies = runtime_engine.search_hybrid(
        image_path=tmp_path,
        search_type="image",
        sort="popular",
    )

    results = _attach_title(runtime_engine, (movies or [])[:5])
    return jsonify({"results": results})


# ======================================================
# Search Controls — CF-SVD (Stateless Listing)
# ======================================================
@bp.route("/dashboard/search/cf", methods=["POST"])
def dashboard_search_cf():
    runtime_engine = get_runtime_engine()

    movies, _, _ = runtime_engine.get_popular_movies(limit=5)
    results = _attach_title(runtime_engine, movies)

    return jsonify({"results": results})


# ======================================================
# ADD ONLY
# Engine Comparison — Query-based Similarity
# ======================================================
@bp.route("/dashboard/engine_comparison/text", methods=["POST"])
def dashboard_engine_comparison_text():
    """
    Engine Comparison 전용 API

    책임:
    - 검색(hybrid) 결과를 재사용하지 않는다
    - '쿼리 기준 similarity'를 직접 계산한다

    반환 의미:
    - TF-IDF / SBERT / CLIP : cosine similarity
    - CF-SVD : 쿼리 기반 similarity 정의 불가 → 빈 리스트
    """
    payload = request.get_json(silent=True) or {}
    query = (payload.get("query") or "").strip()

    if not query:
        return jsonify({"results": {}})

    runtime_engine = get_runtime_engine()

    # RuntimeEngine 구현 상태에 따라 해당 메서드가 없을 수 있으므로 안전 호출
    tfidf_fn = getattr(runtime_engine, "get_query_tfidf_similarity", None)
    sbert_fn = getattr(runtime_engine, "get_query_sbert_similarity", None)

    tfidf = tfidf_fn(query, top_k=5) if callable(tfidf_fn) else []
    sbert = sbert_fn(query, top_k=5) if callable(sbert_fn) else []

    # CLIP은 image-query 전용 엔진
    # text-query 기준 similarity는 정의하지 않는다
    clip = []

    return jsonify({
        "results": {
            "TF-IDF": tfidf,
            "SBERT": sbert,
            "CLIP": clip,
            "CF-SVD": [],  # 명시적 N/A
        }
    })
