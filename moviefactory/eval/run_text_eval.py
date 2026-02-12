from __future__ import annotations

import sys
import yaml
import statistics
from typing import List, Dict, Any

from moviefactory.engine.engine_provider import get_runtime_engine


# -----------------------------
# YAML 로드
# -----------------------------
def load_yaml(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("cases", [])


# -----------------------------
# 평가 실행
# -----------------------------
def main():
    # yaml 경로 선택
    if len(sys.argv) > 1:
        yaml_path = sys.argv[1]
    else:
        yaml_path = "moviefactory/eval/text_queries.yaml"

    cases = load_yaml(yaml_path)

    engine = get_runtime_engine()

    hit1 = 0
    hit5 = 0
    hit10 = 0
    ranks = []

    print(f"\n=== Running eval: {yaml_path} ===\n")

    for case in cases:
        cid = case["id"]
        query = case["query"]
        must_ids = set(case.get("must_ids", []))
        candidate_k = case.get("candidate_k", 400)

        results = engine.search_hybrid(
            query=query,
            search_type="text",
            sort="relevance",
            candidate_k=candidate_k,
        )

        # 실패(Top10 밖) 케이스는 top10을 출력해서 원인 분석
        if cid in ("I005", "I010"):
            print("  top10:")
            for j, r in enumerate(results[:10], start=1):
                print(f"    {j:02d}. {r.get('movie_id')} | {r.get('title')} | score={r.get('score')}")

        result_ids = [r["movie_id"] for r in results]

        best_rank = None
        for i, mid in enumerate(result_ids):
            if mid in must_ids:
                best_rank = i + 1
                break

        h1 = best_rank == 1
        h5 = best_rank is not None and best_rank <= 5
        h10 = best_rank is not None and best_rank <= 10

        if h1:
            hit1 += 1
        if h5:
            hit5 += 1
        if h10:
            hit10 += 1
        if best_rank is not None:
            ranks.append(best_rank)

        print(
            f"[{cid}] hit@1={h1} hit@5={h5} hit@10={h10} "
            f"best_rank={best_rank} k={candidate_k} | {query}"
        )

    print("\n================== SUMMARY ==================")
    n = len(cases)
    print(f"cases: {n}")
    print(f"hit@1 : {hit1}/{n} = {hit1/n:.3f}")
    print(f"hit@5 : {hit5}/{n} = {hit5/n:.3f}")
    print(f"hit@10: {hit10}/{n} = {hit10/n:.3f}")
    if ranks:
        print(f"mean_rank(best must): {statistics.mean(ranks):.2f} (n={len(ranks)})")
    print("============================================\n")


if __name__ == "__main__":
    main()
