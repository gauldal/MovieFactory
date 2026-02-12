import requests
import re
from urllib.parse import quote_plus
import ast
import re
print("[movie_api] LOADED:", __file__)

# ======================================================
# Movie Normalization (GLOBAL – 핵심 / 최종)
# ======================================================
def normalize_movie(movie: dict) -> dict:
    if not movie:
        return movie

    # ============================
    # GENRES
    # ============================
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

    # ❌ genres 원본은 이제 절대 제거하지 않음
    # movie.pop("genres", None)  <-- 제거

    # ============================
    # RELEASE YEAR (✅ 추가)
    # ============================
    release_date = movie.get("release_date")
    if release_date:
        try:
            year = str(release_date)[:4]
            if year.isdigit():
                movie["release_year"] = year
        except Exception:
            pass

    # ============================
    # RATING
    # ============================
    vote_average = movie.get("vote_average")

    if vote_average is not None:
        try:
            vote_average = float(vote_average)
            movie["rating_display"] = f"{vote_average:.1f}"
            movie["vote_average"] = vote_average
        except (TypeError, ValueError):
            pass

    vote_count = movie.get("vote_count")
    if vote_count is not None:
        try:
            movie["vote_count_display"] = f"{int(vote_count):,}"
        except Exception:
            pass

    # ============================
    # RUNTIME (✅ 조건 안정화)
    # ============================
    runtime = movie.get("runtime")
    if runtime is not None:
        try:
            runtime = int(runtime)
            if runtime > 0:
                movie["runtime_display"] = f"{runtime} min"
                movie["runtime"] = runtime
        except Exception:
            pass

    return movie


# ======================================================
# YouTube Trailer Search (NO API KEY)
# ======================================================
def search_youtube_trailers(query: str, max_items: int = 3):
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
            )
        }

        resp = requests.get(search_url, headers=headers, timeout=5)
        if resp.status_code != 200:
            return []

        html = resp.text

        video_ids = list(dict.fromkeys(
            re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
        ))

        results = []
        for vid in video_ids[:max_items]:
            results.append({
                "title": query,
                "url": f"https://www.youtube.com/watch?v={vid}",
                "thumbnail": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
            })

        return results

    except Exception as e:
        print(f"[YouTube Search Error] {e}")
        return []
