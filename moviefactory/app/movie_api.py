from flask import Blueprint, render_template, abort
import requests
import re
from urllib.parse import quote_plus

print("[movie_api] LOADED:", __file__)

bp = Blueprint("movie", __name__)

# ======================================================
# Movie Normalization
# ======================================================
def normalize_movie(movie: dict) -> dict:
    if not movie:
        return movie

    # ----------------------------
    # GENRES
    # ----------------------------
    genres_display = ""
    genres = movie.get("genres")

    if isinstance(genres, list):
        names = [
            g["name"] for g in genres
            if isinstance(g, dict) and "name" in g
        ]
        genres_display = ", ".join(names)

    elif isinstance(genres, str):
        if "name" in genres and "id" in genres:
            names = re.findall(r"'name':\s*'([^']+)'", genres)
            genres_display = ", ".join(names)
        else:
            genres_display = genres.replace("|", ", ")

    if genres_display:
        movie["genres_display"] = genres_display

    # ----------------------------
    # RELEASE YEAR
    # ----------------------------
    release_date = movie.get("release_date")
    if release_date:
        year = str(release_date)[:4]
        if year.isdigit():
            movie["release_year"] = year

    # ----------------------------
    # RATING
    # ----------------------------
    vote_average = movie.get("vote_average")
    if vote_average is not None:
        try:
            vote_average = float(vote_average)
            movie["rating_display"] = f"{vote_average:.1f}"
            movie["vote_average"] = vote_average
        except:
            pass

    vote_count = movie.get("vote_count")
    if vote_count is not None:
        try:
            movie["vote_count_display"] = f"{int(vote_count):,}"
        except:
            pass

    # ----------------------------
    # RUNTIME
    # ----------------------------
    runtime = movie.get("runtime")
    if runtime is not None:
        try:
            runtime = int(runtime)
            if runtime > 0:
                movie["runtime_display"] = f"{runtime} min"
                movie["runtime"] = runtime
        except:
            pass

    return movie


# ======================================================
# YouTube Trailer Search
# ======================================================
def search_youtube_trailers(query: str, max_items: int = 4):
    if not query:
        return []

    try:
        search_url = (
            "https://www.youtube.com/results?search_query="
            + quote_plus(f"{query} official trailer")
        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
        }

        resp = requests.get(search_url, headers=headers, timeout=8, allow_redirects=True)
        if resp.status_code != 200:
            return []

        html = resp.text

        # 1차: 기본 videoId 패턴
        video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)

        # 2차: 혹시 1차가 너무 적으면 다른 패턴도 한 번 더 시도(보조)
        if len(video_ids) < max_items:
            video_ids += re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', html)

        # 중복 제거 + 순서 유지
        uniq = []
        seen = set()
        for vid in video_ids:
            if vid in seen:
                continue
            seen.add(vid)
            uniq.append(vid)

        # 최대 max_items까지
        uniq = uniq[:max_items]

        results = [{
            "title": query,
            "url": f"https://www.youtube.com/watch?v={vid}",
            "thumbnail": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
        } for vid in uniq]

        return results

    except Exception as e:
        print("[YouTube Search Error]", e)
        return []



# ======================================================
# MOVIE DETAIL ROUTE
# ======================================================
@bp.route("/movie/<int:movie_id>")
def movie_detail(movie_id):

    from moviefactory.engine.engine_provider import get_runtime_engine

    engine = get_runtime_engine()
    movie = engine.get_movie_by_id(movie_id)

    if not movie:
        abort(404)

    movie = normalize_movie(movie)

    # ----------------------------
    # Trailers → 4개
    # ----------------------------
    trailers = search_youtube_trailers(
        f"{movie.get('title', '')} {movie.get('release_year', '')}",
        max_items=4
    )

    # ----------------------------
    # Similar → 6개 유지
    # ----------------------------
    similar_movies = engine.get_similar_movies(movie_id, limit=6)

    similar_movies = [
        normalize_movie(m) for m in similar_movies
    ]

    return render_template(
        "movie_detail_mobile.html",
        movie=movie,
        trailers=trailers,
        similar_movies=similar_movies
    )
