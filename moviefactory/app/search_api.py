# moviefactory/app/search_api.py
print("[search_api] LOADED:", __file__)
import os
import uuid
from pathlib import Path
from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    url_for,
    session,
)

from moviefactory.engine.engine_provider import get_runtime_engine
from moviefactory.utils.device import is_mobile_request

bp = Blueprint("search", __name__, url_prefix="/search")
runtime_engine = get_runtime_engine()

_MOVIEFACTORY_ROOT = Path(__file__).resolve().parents[1]  # moviefactory/
UPLOAD_DIR = str(_MOVIEFACTORY_ROOT / "static" / "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

WEB_PAGE_SIZE = 14
MOBILE_PAGE_SIZE = 10


def paginate(items, page, per_page):
    total_count = len(items)
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], total_pages, total_count, page


def _clear_image_session():
    session.pop("image_search_path", None)
    session.pop("image_search_preview", None)


@bp.route("", methods=["GET", "POST"])
def search():
    # ---- common params
    q = request.args.get("q")
    genre = request.args.get("genre")
    sort = request.args.get("sort", "popular")
    page = int(request.args.get("page", 1))

    # ✅ 강제 리셋 옵션: /search?reset=1
    reset = request.args.get("reset")
    if reset in ("1", "true", "yes", "on"):
        _clear_image_session()
        return redirect(url_for("index"))

    is_mobile = is_mobile_request()
    per_page = MOBILE_PAGE_SIZE if is_mobile else WEB_PAGE_SIZE
    template = "search_list_mobile.html" if is_mobile else "search_list.html"

    # ==================================================
    # IMAGE SEARCH (POST)
    # ==================================================
    if request.method == "POST" and "image" in request.files:
        image = request.files["image"]
        if image and image.filename:
            filename = f"{uuid.uuid4().hex}.jpg"
            filepath = os.path.join(UPLOAD_DIR, filename)
            image.save(filepath)

            preview = f"/static/uploads/{filename}"
            session["image_search_path"] = filepath   # ✅ 절대경로
            session["image_search_preview"] = preview

            full_results = runtime_engine.search_hybrid(
                image_path=filepath,
                search_type="image",
                sort=sort,
            )

            movies, total_pages, total_count, page = paginate(full_results, 1, per_page)

            return render_template(
                template,
                movies=movies,
                total_pages=total_pages,
                total_count=total_count,
                page=page,
                q=None,
                genre=None,
                sort=sort,
                image_mode=True,
                search_image_preview=preview,
            )

    # ==================================================
    # ✅ GET 우선순위: genre/text → 이미지 세션 해제 후 처리
    # ==================================================
    q = q.strip() if q else None
    genre = genre.strip() if genre else None

    # (1) GENRE SEARCH
    if request.method == "GET" and genre:
        _clear_image_session()
        full_results = runtime_engine.search_hybrid(
            query=genre,
            search_type="genre",
            sort=sort,
        )
        movies, total_pages, total_count, page = paginate(full_results, page, per_page)
        return render_template(
            template,
            movies=movies,
            total_pages=total_pages,
            total_count=total_count,
            page=page,
            q=None,
            genre=genre,
            sort=sort,
            image_mode=False,
            search_image_preview=None,
        )

    # (2) TEXT SEARCH
    if request.method == "GET" and q:
        _clear_image_session()
        full_results = runtime_engine.search_hybrid(
            query=q,
            search_type="text",
            sort=sort,
        )
        movies, total_pages, total_count, page = paginate(full_results, page, per_page)
        return render_template(
            template,
            movies=movies,
            total_pages=total_pages,
            total_count=total_count,
            page=page,
            q=q,
            genre=None,
            sort=sort,
            image_mode=False,
            search_image_preview=None,
        )

    # ==================================================
    # (3) IMAGE SEARCH (GET session) — 마지막
    # ==================================================
    if request.method == "GET" and "image_search_path" in session:
        image_path = session.get("image_search_path")
        preview = session.get("image_search_preview")

        # 파일이 실제로 없으면 세션 정리 후 홈으로
        if not image_path or not os.path.exists(image_path):
            _clear_image_session()
            return redirect(url_for("index"))

        full_results = runtime_engine.search_hybrid(
            image_path=image_path,
            search_type="image",
            sort=sort,
        )
        movies, total_pages, total_count, page = paginate(full_results, page, per_page)
        return render_template(
            template,
            movies=movies,
            total_pages=total_pages,
            total_count=total_count,
            page=page,
            q=None,
            genre=None,
            sort=sort,
            image_mode=True,
            search_image_preview=preview,
        )

    # ==================================================
    # ✅ 아무것도 없으면: 이미지 세션도 끊고 홈으로
    # (여기가 없으면, /search 로만 들어오는 케이스에서 계속 꼬일 수 있음)
    # ==================================================
    _clear_image_session()
    return redirect(url_for("index"))

@bp.route("/api/explain/<int:movie_id>")
def api_explain(movie_id):
    from moviefactory.engine.explanation_engine import ExplanationEngine
    from moviefactory.engine.engine_provider import get_runtime_engine

    runtime_engine = get_runtime_engine()
    explanation_engine = ExplanationEngine(runtime_engine)
    explanation = explanation_engine.explain(movie_id)

    return {
        "movie_id": movie_id,
        "explanation": explanation
    }
