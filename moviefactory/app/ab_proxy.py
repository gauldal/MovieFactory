# ============================================================
# moviefactory/app/ab_proxy.py
# - Offline proxy A/B (Ranker OFF vs ON)
# - ✅ ON: RuntimeEngine.search_hybrid(text) 그대로 사용 (hybrid_rerank 경로)
# - ✅ OFF: search_hybrid(text) 로직을 "그대로 복제"하되,
#          ranked source만 TF-IDF 점수로 대체 (hybrid_rerank 제거)
# - 결과는 Dashboard의 ranker_comparison에 바로 꽂을 수 있는 형태로 반환
# ============================================================

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# RuntimeEngine이 실제로 사용하는 모듈/함수들을 그대로 import
from moviefactory.engine.runtime_engine import (
    _normalize_space,
    _looks_like_gibberish,
    _tokenize,
)
from moviefactory.engine.tfidf_engine import tfidf_engine


# -----------------------------
# Proxy metric helpers
# -----------------------------
def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default


def _jaccard(a: List[str], b: List[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    inter = len(sa & sb)
    uni = len(sa | sb)
    return inter / uni if uni else 0.0


def _entropy(labels: List[str]) -> float:
    if not labels:
        return 0.0
    total = len(labels)
    cnt: Dict[str, int] = {}
    for x in labels:
        cnt[x] = cnt.get(x, 0) + 1
    ent = 0.0
    for c in cnt.values():
        p = c / total
        ent -= p * math.log(p + 1e-12)
    return ent


def _weighted_rating(vote_average: float, vote_count: float, C: float, m: float) -> float:
    # IMDb-style weighted rating
    v = max(vote_count, 0.0)
    R = vote_average
    denom = v + m
    if denom <= 0:
        return C
    return (v / denom) * R + (m / denom) * C


# -----------------------------
# OFF path (TF-IDF only) that matches RuntimeEngine.search_hybrid(text)
# -----------------------------
def _search_text_tfidf_only_like_search_hybrid(
    runtime_engine,
    *,
    query: str,
    sort: str = "popular",
    candidate_k: int = 700,
) -> List[Dict]:
    """
    RuntimeEngine.search_hybrid(text)와 "후처리/필터/타이틀부스트/merge 정책"을 완전히 동일하게 적용하되,
    ranked source만 TF-IDF 점수로 만든다.

    반환: List[card_dict]  (RuntimeEngine.search_hybrid 계약과 동일)
    """
    q = _normalize_space(query or "")
    if not q or _looks_like_gibberish(q):
        return []

    tokens = _tokenize(q)

    # 1) title_boost (search_hybrid와 동일)
    q_low = q.lower().strip()
    title_hits: List[Dict] = []
    try:
        mask = runtime_engine.df["title"].astype(str).str.lower().str.contains(q_low, regex=False)
        if mask.any():
            for _, r in runtime_engine.df[mask].head(10).iterrows():
                card0 = runtime_engine._row_to_card(r)
                card0["score"] = 1.0
                card0["_title_boost"] = True
                title_hits.append(card0)
    except Exception:
        title_hits = []

    # 2) TF-IDF scoring (search_hybrid와 동일한 호출 파라미터)
    tfidf_scores = tfidf_engine.score(q, top_k=int(candidate_k), min_score=0.0) or {}
    if not tfidf_scores:
        return title_hits if title_hits else []

    # 3) ranked_items 형태를 search_hybrid(text) 루프에 맞추기
    #    search_hybrid는 item={"movie_id":..., "score":...}를 순회하므로 그 형태로 맞춘다.
    ranked_pairs = sorted(tfidf_scores.items(), key=lambda x: x[1], reverse=True)
    ranked_items = [{"movie_id": mid, "score": sc} for (mid, sc) in ranked_pairs]

    movies: List[Dict] = []
    for item in ranked_items:
        try:
            mid = int(item.get("movie_id"))
        except Exception:
            continue

        score = float(item.get("score", 0.0))

        # ✅ search_hybrid(text)와 동일: score<0.12면 break
        if score < 0.12:
            break

        row = runtime_engine.df[runtime_engine.df["movie_id"] == mid]
        if row.empty:
            continue

        card = runtime_engine._row_to_card(row.iloc[0])
        card["score"] = score

        # ✅ search_hybrid(text)와 동일: 토큰 포함 or score>=0.35만 통과
        title = str(card.get("title", "")).lower()
        overview = str(card.get("overview", "")).lower()
        hay = title + " " + overview

        if any(t in hay for t in tokens):
            movies.append(card)
            continue

        if score >= 0.35:
            movies.append(card)

    # ✅ search_hybrid(text)와 동일: sort 옵션이 있으면 정렬 재적용
    if sort in ("latest", "rating", "popular") and movies:
        try:
            temp_df = pd.DataFrame(movies)
            temp_df = runtime_engine._apply_sort(temp_df, sort)
            movies = temp_df.to_dict(orient="records")
        except Exception:
            pass

    # ✅ search_hybrid(text)와 동일: title_hits를 맨 앞에 합치고 중복 제거
    if title_hits:
        seen = set()
        merged: List[Dict] = []
        for m in title_hits + movies:
            mid0 = m.get("movie_id")
            if mid0 in seen:
                continue
            seen.add(mid0)
            merged.append(m)
        movies = merged

    return movies


# -----------------------------
# A/B proxy runner
# -----------------------------
def run_ab_proxy_metrics(
    runtime_engine,
    *,
    n_seeds: int = 120,
    top_k: int = 20,
    seed: int = 42,
    sort: str = "popular",
    candidate_k: int = 700,
) -> Dict[str, Any]:
    """
    Offline A/B proxy evaluation

    session:
      - seed movie 1개
      - query = seed title

    A (OFF):
      - TF-IDF only ranking
      - BUT post-processing identical to RuntimeEngine.search_hybrid(text)

    B (ON):
      - RuntimeEngine.search_hybrid(text) 그대로 호출 (hybrid_rerank 경로)

    metrics (5):
      - Weighted Rating@K
      - Popularity(log1p)@K
      - VoteCount(log1p)@K
      - Genre Coherence@K (seed vs rec Jaccard avg)
      - Intra-list Genre Diversity@K (entropy)
    """
    df = runtime_engine.df
    if df is None or df.empty:
        return {"ok": False, "error": "empty dataset"}

    # genres cache는 RuntimeEngine이 이미 구축함
    genres_cache: Dict[int, List[str]] = getattr(runtime_engine, "_genres_cache", {}) or {}

    # global stats for weighted rating
    va = pd.to_numeric(df["vote_average"], errors="coerce").fillna(0.0)
    vc = pd.to_numeric(df["vote_count"], errors="coerce").fillna(0.0)
    C = float(va.mean())
    m = float(vc.quantile(0.70))

    ids = df["movie_id"].dropna().astype(int).tolist()
    if not ids:
        return {"ok": False, "error": "no movie_id"}

    random.seed(seed)
    seeds = random.sample(ids, k=min(n_seeds, len(ids)))

    df_idx = df.set_index("movie_id", drop=False)

    def _metric_for(seed_id: int, rec_ids: List[int]) -> Dict[str, float]:
        seed_genres = genres_cache.get(int(seed_id), [])

        wrs: List[float] = []
        pops: List[float] = []
        vclogs: List[float] = []
        coher: List[float] = []
        flat_genres: List[str] = []

        for mid in rec_ids:
            if mid not in df_idx.index:
                continue
            row = df_idx.loc[mid]

            vote_avg = _safe_float(row.get("vote_average", 0.0))
            vote_cnt = _safe_float(row.get("vote_count", 0.0))
            pop = _safe_float(row.get("popularity", 0.0))

            wrs.append(_weighted_rating(vote_avg, vote_cnt, C, m))
            pops.append(math.log1p(max(pop, 0.0)))
            vclogs.append(math.log1p(max(vote_cnt, 0.0)))

            g = genres_cache.get(int(mid), [])
            flat_genres.extend(g)
            coher.append(_jaccard(seed_genres, g))

        def mean(xs: List[float]) -> float:
            return float(sum(xs) / len(xs)) if xs else 0.0

        return {
            "wr": mean(wrs),
            "pop_log": mean(pops),
            "votecount_log": mean(vclogs),
            "genre_coherence": mean(coher),
            "genre_diversity": _entropy(flat_genres),
        }

    off_sessions: List[Dict[str, float]] = []
    on_sessions: List[Dict[str, float]] = []

    for sid in seeds:
        if sid not in df_idx.index:
            continue
        title = str(df_idx.loc[sid].get("title", "") or "").strip()
        if not title:
            continue

        # OFF: TF-IDF only + 동일 후처리
        off_cards = _search_text_tfidf_only_like_search_hybrid(
            runtime_engine,
            query=title,
            sort=sort,
            candidate_k=candidate_k,
        )
        off_ids = [int(c.get("movie_id")) for c in (off_cards or []) if c.get("movie_id") is not None][:top_k]

        # ON: RuntimeEngine.search_hybrid(text) 그대로
        on_cards = runtime_engine.search_hybrid(
            query=title,
            search_type="text",
            sort=sort,
        )
        on_ids = [int(c.get("movie_id")) for c in (on_cards or []) if c.get("movie_id") is not None][:top_k]

        off_sessions.append(_metric_for(sid, off_ids))
        on_sessions.append(_metric_for(sid, on_ids))

    if not off_sessions:
        return {"ok": False, "error": "no sessions produced"}

    def agg(sessions: List[Dict[str, float]]) -> Dict[str, float]:
        keys = sessions[0].keys()
        out: Dict[str, float] = {}
        for k in keys:
            xs = [s.get(k, 0.0) for s in sessions]
            out[k] = float(sum(xs) / len(xs)) if xs else 0.0
        return out

    off = agg(off_sessions)
    on = agg(on_sessions)

    meta = {
        "wr": {"label": "Weighted Rating@K", "higher_is_better": True},
        "pop_log": {"label": "Popularity(log1p)@K", "higher_is_better": True},
        "votecount_log": {"label": "VoteCount(log1p)@K", "higher_is_better": True},
        "genre_coherence": {"label": "Genre Coherence@K", "higher_is_better": True},
        "genre_diversity": {"label": "Intra-list Genre Diversity@K", "higher_is_better": True},
    }

    metrics: Dict[str, Any] = {}
    for k, m0 in meta.items():
        off_v = float(off.get(k, 0.0))
        on_v = float(on.get(k, 0.0))
        metrics[k] = {**m0, "off": off_v, "on": on_v, "delta": on_v - off_v}

    return {
        "ok": True,
        "n_sessions": len(off_sessions),
        "top_k": top_k,
        "seed_count_requested": n_seeds,
        "sort": sort,
        "candidate_k": candidate_k,
        "metrics": metrics,
    }