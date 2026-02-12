from flask import Blueprint, request, jsonify

from moviefactory.llm.mock_llm import MockLLMClient, FallbackLLMClient

bp = Blueprint("explain_api", __name__)

# Mock LLM 인스턴스 (서버 시작 시 1회 생성)
mock_llm = MockLLMClient()


@bp.route("/explain", methods=["POST"])
def explain():
    """
    Movie Detail – Recommendation Explanation API
    - mock_llm 기반
    - POST only
    - 절대 예외로 서버를 죽이지 않음
    """

    data = request.get_json(silent=True) or {}

    title = data.get("title", "")
    genres = data.get("genres", "")
    year = data.get("year", "")

    # prompt는 형식만 맞추면 됨 (mock은 내용 사용 안 함)
    prompt = (
        f"Title: {title}\n"
        f"Genres: {genres}\n"
        f"Year: {year}\n"
        "Explain why this movie is recommended."
    )

    try:
        explanation = mock_llm.generate_explanation(prompt)
    except Exception:
        # 최후 안전망 (이론상 거의 안 탐)
        fallback = FallbackLLMClient(reason="mock_error")
        explanation = fallback.generate_explanation(prompt)

    return jsonify({
        "explanation": explanation
    })
