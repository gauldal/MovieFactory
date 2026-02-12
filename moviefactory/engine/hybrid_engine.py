# moviefactory/engine/hybrid_engine.py

import numpy as np

def _normalize(scores: dict[int, float]) -> dict[int, float]:
    if not scores:
        return {}

    values = np.array(list(scores.values()), dtype=float)
    min_v, max_v = values.min(), values.max()

    if max_v - min_v < 1e-8:
        return {k: 1.0 for k in scores}

    return {k: (v - min_v) / (max_v - min_v) for k, v in scores.items()}


def hybrid_rerank(
    *,
    sbert_results: dict[int, float] | None = None,
    tfidf_results: dict[int, float] | None = None,
    clip_results: dict[int, float] | None = None,
    cf_results: dict[int, float] | None = None,
    weights: dict,
):
    """
    Hybrid Score Combiner
    - 추천 판단 로직 ❌
    - 검색 실행 ❌
    - 점수 결합 전용 함수
    모든 엔진 결과는 {movie_id: score} dict 형태
    """

    final_scores: dict[int, float] = {}

    def apply(results: dict[int, float] | None, weight: float, name: str):
        if not results or weight <= 0:
            print(f"[Hybrid][{name}] EMPTY or weight=0")
            return

        norm = _normalize(results)
        vals = list(norm.values())

        try:
            print(
                f"[Hybrid][{name}] min={min(vals):.4f} "
                f"max={max(vals):.4f} mean={np.mean(vals):.4f} (n={len(vals)})"
            )
        except Exception:
            print(f"[Hybrid][{name}] (n={len(vals)})")

        for mid, score in norm.items():
            final_scores[mid] = final_scores.get(mid, 0.0) + score * weight

    apply(sbert_results, weights.get("sbert", 0.0), "sbert")
    apply(tfidf_results, weights.get("tfidf", 0.0), "tfidf")
    apply(clip_results,  weights.get("clip", 0.0),  "clip")
    apply(cf_results,    weights.get("cf", 0.0),    "cf")

    return sorted(
        [{"movie_id": mid, "score": score} for mid, score in final_scores.items()],
        key=lambda x: x["score"],
        reverse=True,
    )
