# moviefactory/app/main.py

import os
from flask import Flask, render_template, request, session

from moviefactory.engine.engine_provider import get_runtime_engine
from moviefactory.app.movie_api import (
    search_youtube_trailers,
    normalize_movie,
)
from moviefactory.app.search_api import bp as search_bp
from moviefactory.app.dashboard_api import bp as dashboard_bp
from moviefactory.app.explain_api import bp as explain_bp
from moviefactory.utils.device import is_mobile_request


# ======================================================
# App Setup
# ======================================================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)

# 🔑 session 필수 (이미지 검색 상태 유지)
app.secret_key = os.environ.get(
    "MF_SECRET_KEY",
    "moviefactory-dev-secret"
)


# ======================================================
# Blueprints
# ======================================================
app.register_blueprint(search_bp)
app.register_blueprint(dashboard_bp, url_prefix="/api")
app.register_blueprint(explain_bp, url_prefix="/api")


# ======================================================
# Runtime Engine
# ======================================================
runtime_engine = get_runtime_engine()


# ======================================================
# Routes
# ======================================================
@app.route("/")
def index():
    sort = request.args.get("sort", "latest")

    # ✅ 홈으로 오면 이미지 검색 세션을 정리해서
    #    "어딜 가든 이미지검색 화면만 보이는" 상태를 방지
    session.pop("image_search_path", None)
    session.pop("image_search_preview", None)

    is_mobile = is_mobile_request()
    grid_limit = 20 if is_mobile else 21

    movies, total_pages, total_count = runtime_engine.get_popular_movies(
        limit=grid_limit,
        sort=sort,
    )

    movies = [normalize_movie(m) for m in movies]

    template = "index_mobile.html" if is_mobile else "index.html"

    return render_template(
        template,
        movies=movies,
        total_count=total_count,
        sort=sort,
    )


@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id):
    movie = runtime_engine.get_movie_by_id(movie_id)
    movie = normalize_movie(movie)

    print("[DETAIL-RAW]", movie_id, movie.get("release_date"), movie.get("runtime"), movie.get("genres"))
    print("[DETAIL-NORM]", movie_id, movie.get("release_year"), movie.get("runtime_display"), movie.get("genres_display"))

    trailers = search_youtube_trailers(
        movie.get("title"),
        max_items=3,
    )


    trailers = search_youtube_trailers(
        movie.get("title"),
        max_items=3,
    )

    similar_movies = runtime_engine.get_similar_movies(
        movie_id,
        limit=14,
    )
    similar_movies = [normalize_movie(m) for m in similar_movies]

    template = (
        "movie_detail_mobile.html"
        if is_mobile_request()
        else "movie_detail.html"
    )

    return render_template(
        template,
        movie=movie,
        trailers=trailers,
        similar_movies=similar_movies,
    )

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")


@app.route("/dashboard/about")
def dashboard_about_page():
    return render_template("dashboard_about.html")


# ======================================================
# Entry
# ======================================================
if __name__ == "__main__":
    app.run(debug=True)
