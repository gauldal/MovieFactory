"""
MovieFactory Web Application (UI Layer)
======================================
- 책임: 라우팅 + 템플릿 렌더링
- 엔진 직접 호출 금지
- 모든 검색은 API(Blueprint) 경유
- Streamlit Dashboard URL 환경변수 분기 지원
"""

import os
from pathlib import Path
from urllib.parse import urlencode

from flask import Flask, request, render_template, abort

# --------------------------------------------------
# PATH
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
CLEAN_CSV = DATA_DIR / "movie_clean_data.csv"

# --------------------------------------------------
# APP
# --------------------------------------------------

app = Flask(__name__)

# --------------------------------------------------
# ENV (Streamlit)
# --------------------------------------------------

STREAMLIT_URL = os.getenv("STREAMLIT_URL", "http://localhost:8501")

# --------------------------------------------------
# Blueprint 등록
# --------------------------------------------------

from moviefactory.app.search_api import search_bp
from moviefactory.app.movie_api import movie_bp
from moviefactory.app.dashboard_api import dashboard_bp

app.register_blueprint(search_bp)
app.register_blueprint(movie_bp)
app.register_blueprint(dashboard_bp)

# --------------------------------------------------
# UTIL
# --------------------------------------------------

def normalize_movie(row: dict) -> dict:
    youtube_key = row.get("youtube_key")
    if not youtube_key and row.get("title"):
        youtube_key = row["title"].replace(" ", "+") + "+trailer"

    return {
        "movie_id": int(row.get("movie_id")),
        "title": row.get("title"),
        "overview": row.get("overview"),
        "poster_url": row.get("poster_url"),
        "genres_text": row.get("genres_text") or row.get("genres"),
        "release_year": (
            row.get("release_date", "")[:4]
            if row.get("release_date") else None
        ),
        "youtube_key": youtube_key,
    }


def build_page_urls(base: str, params: dict, page: int, total_pages: int):
    prev_url = None
    next_url = None

    if page > 1:
        prev_url = f"{base}?{urlencode(params | {'page': page - 1})}"

    if page < total_pages:
        next_url = f"{base}?{urlencode(params | {'page': page + 1})}"

    return prev_url, next_url

# --------------------------------------------------
# ROUTES
# --------------------------------------------------

@app.route("/")
def index():
    if not CLEAN_CSV.exists():
        abort(500, "movie_clean_data.csv not found. Run builder first.")

    hero_summary = {
        "title": "MovieFactory",
        "desc": "AI-powered movie discovery platform",
        "details": [
            "Text · Image · Hybrid Search",
            "SBERT · CLIP · TF-IDF · CF",
            "Visualization-first Analytics",
        ],
    }

    return render_template(
        "index.html",
        hero_summary=hero_summary,
        featured_movies=[],
    )


@app.route("/search", methods=["GET", "POST"])
def search():
    q = request.values.get("q", "").strip()
    genre = request.values.get("genre", "").strip()
    page = request.values.get("page", default=1, type=int)
    per_page = 24

    search_type = "idle"
    api_endpoint = None
    api_method = None
    api_params = {}

    # --------------------------------------------------
    # IMAGE SEARCH (CLIP)
    # --------------------------------------------------
    if request.method == "POST" and "image" in request.files:
        image_file = request.files["image"]
        if image_file and image_file.filename:
            search_type = "image"
            api_endpoint = "/api/search/image"
            api_method = "POST"

            data = {
                "page": page,
                "per_page": per_page,
                "image": image_file,
            }

            with app.test_client() as client:
                resp = client.post(
                    api_endpoint,
                    data=data,
                    content_type="multipart/form-data",
                )

            if resp.status_code != 200:
                abort(resp.status_code, resp.get_data(as_text=True))

            data = resp.get_json()
            movies = [normalize_movie(m) for m in data.get("movies", [])]
            total_pages = data.get("total_pages", 1)

            prev_url, next_url = build_page_urls(
                base="/search",
                params={},
                page=page,
                total_pages=total_pages,
            )

            return render_template(
                "search_list.html",
                movies=movies,
                query="",
                genre="",
                total_pages=total_pages,
                current_page=page,
                prev_page_url=prev_url,
                next_page_url=next_url,
                search_type=search_type,
            )

    # --------------------------------------------------
    # TEXT / GENRE SEARCH
    # --------------------------------------------------
    if q:
        search_type = "text"
        api_endpoint = "/api/search/text"
        api_method = "GET"
        api_params = {"q": q}

    elif genre:
        search_type = "genre"
        api_endpoint = "/api/search/genre"
        api_method = "GET"
        api_params = {"genre": genre}

    else:
        return render_template(
            "search_list.html",
            movies=[],
            query="",
            genre="",
            total_pages=1,
            current_page=1,
            prev_page_url=None,
            next_page_url=None,
            search_type="idle",
        )

    # --------------------------------------------------
    # API CALL (TEXT / GENRE)
    # --------------------------------------------------
    with app.test_client() as client:
        resp = client.get(
            api_endpoint,
            query_string=api_params | {
                "page": page,
                "per_page": per_page,
            },
        )

    if resp.status_code != 200:
        abort(resp.status_code, resp.get_data(as_text=True))

    data = resp.get_json()
    movies = [normalize_movie(m) for m in data.get("movies", [])]
    total_pages = data.get("total_pages", 1)

    prev_url, next_url = build_page_urls(
        base="/search",
        params=api_params,
        page=page,
        total_pages=total_pages,
    )

    return render_template(
        "search_list.html",
        movies=movies,
        query=q,
        genre=genre,
        total_pages=total_pages,
        current_page=page,
        prev_page_url=prev_url,
        next_page_url=next_url,
        search_type=search_type,
    )


@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id: int):
    with app.test_client() as client:
        resp = client.get(f"/api/movie/{movie_id}")

    if resp.status_code != 200:
        abort(resp.status_code)

    movie_raw = resp.get_json()
    movie = normalize_movie(movie_raw)

    with app.test_client() as client:
        sim_resp = client.post(
            "/api/search/hybrid",
            data={
                "q": movie["title"],
                "page": 1,
                "per_page": 12,
            },
        )

    similar_movies = []
    if sim_resp.status_code == 200:
        sim_data = sim_resp.get_json()
        similar_movies = [
            normalize_movie(m)
            for m in sim_data.get("movies", [])
            if int(m["movie_id"]) != movie_id
        ]

    return render_template(
        "movie_detail.html",
        movie=movie,
        similar_movies=similar_movies,
    )


@app.route("/dashboard")
def dashboard():
    return render_template(
        "dashboard.html",
        streamlit_url=STREAMLIT_URL,
    )

# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
