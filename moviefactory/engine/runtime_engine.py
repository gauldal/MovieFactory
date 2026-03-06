# ============================================================
# moviefactory/engine/runtime_engine.py
# - Image Search: CLIP candidates + prompt-derived pseudo_query + SBERT + RRF fusion
# - Tuned: SBERT restricted to CLIP rank pool to reduce noise
# - Text Search: TF-IDF + SBERT hybrid + Title Boost safety for exact-title queries
#
# ✅ PATCH:
#   - search_hybrid(..., debug=True) -> {"results": [...], "debug": {...}}
#   - enabled_engines로 ablation 지원 (tfidf/sbert/clip/cf)
#   - Engine Contribution:
#       * text(score fusion): contrib = w * normalized_score
#       * image(RRF): contrib = term = w/(k+rank)
#   - Flask main.py 호환 메서드 복구:
#       * get_popular_movies()
#       * get_movie_by_id()
#       * get_similar_movies()
# ============================================================

from __future__ import annotations

import os
import re
from typing import Optional, List, Dict, Any, Union

import pandas as pd

from moviefactory.engine.hybrid_engine import hybrid_rerank, _normalize  # type: ignore
from moviefactory.config.hybrid_weights import HYBRID_WEIGHTS
from moviefactory.engine.tfidf_engine import tfidf_engine
from moviefactory.engine.sbert_engine import sbert_engine
from moviefactory.engine.clip_engine import get_clip_engine


def _normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _tokenize(q: str) -> list[str]:
    q = (q or "").lower()
    tokens = re.findall(r"[a-z0-9가-힣]+", q)
    return [t for t in tokens if len(t) >= 2]


def _looks_like_gibberish(q: str) -> bool:
    s = (q or "").strip()
    if not s:
        return True
    if re.fullmatch(r"[\W_]+", s):
        return True
    if len(s) <= 2:
        return True
    if re.fullmatch(r"[ㄱ-ㅎㅏ-ㅣ]+", s):
        return True
    if len(set(s)) == 1 and len(s) >= 3:
        return True
    return False


def _parse_genres_cell(cell: str) -> list[str]:
    s = str(cell or "").strip()
    if not s:
        return []

    if s.startswith("[") and "name" in s:
        import ast

        try:
            obj = ast.literal_eval(s)
            if isinstance(obj, list):
                names = []
                for it in obj:
                    if isinstance(it, dict) and it.get("name"):
                        names.append(str(it["name"]).strip().lower())
                return [n for n in names if n]
        except Exception:
            pass

    parts = re.split(r"[,\|/]+", s)
    return [p.strip().lower() for p in parts if p.strip()]


def _engine_enabled(
    enabled_engines: Optional[Dict[str, bool]],
    name: str,
    default: bool = True,
) -> bool:
    if not enabled_engines:
        return default
    return bool(enabled_engines.get(name, default))


def _safe_top_items(scores: Dict[int, float], top_k: int = 10) -> List[Dict[str, Any]]:
    if not scores:
        return []

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    out: List[Dict[str, Any]] = []

    for r, (mid, sc) in enumerate(ranked, start=1):
        try:
            mid_int = int(mid)
        except Exception:
            continue
        out.append(
            {
                "rank": r,
                "movie_id": mid_int,
                "score": float(sc),
            }
        )
    return out


class RuntimeEngine:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))  # moviefactory/
        data_dir = os.path.join(base_dir, "data")

        env_csv = os.environ.get("MOVIEFACTORY_CANONICAL_CSV", "").strip()

        candidate_paths: List[str] = []
        if env_csv:
            if os.path.isabs(env_csv):
                candidate_paths.append(env_csv)
            else:
                candidate_paths.append(os.path.join(data_dir, env_csv))

        candidate_paths.append(os.path.join(data_dir, "movie_clean_data_poster.csv"))
        candidate_paths.append(os.path.join(data_dir, "movie_clean_data.csv"))

        csv_path = None
        for p in candidate_paths:
            if os.path.exists(p):
                csv_path = p
                break

        if csv_path is None:
            raise FileNotFoundError(
                "Canonical CSV not found. Checked: " + ", ".join(candidate_paths)
            )

        self.csv_path = csv_path
        self.df = pd.read_csv(self.csv_path)
        print(f"[RuntimeEngine] canonical csv = {self.csv_path} rows={len(self.df)}")

        required_cols = [
            "movie_id",
            "title",
            "original_title",
            "overview",
            "tagline",
            "genres",
            "tmdb_poster_url",
            "poster_path",
            "vote_average",
            "vote_count",
            "popularity",
            "release_date",
            "runtime",
        ]
        for c in required_cols:
            if c not in self.df.columns:
                self.df[c] = None

        self.df.fillna(
            {
                "title": "",
                "original_title": "",
                "overview": "",
                "tagline": "",
                "genres": "",
                "tmdb_poster_url": "",
                "poster_path": "",
                "vote_average": 0.0,
                "vote_count": 0,
                "popularity": 0.0,
                "release_date": "",
                "runtime": 0,
            },
            inplace=True,
        )

        tmdb_img_base = os.environ.get("TMDB_IMG_BASE", "https://image.tmdb.org/t/p/w500")
        self.df["tmdb_poster_url"] = self.df["tmdb_poster_url"].astype(str).fillna("").str.strip()
        self.df["poster_path"] = self.df["poster_path"].astype(str).fillna("").str.strip()

        mask = (self.df["tmdb_poster_url"] == "") & (self.df["poster_path"] != "")
        if mask.any():
            pp = self.df.loc[mask, "poster_path"].apply(
                lambda x: x if str(x).startswith("/") else "/" + str(x)
            )
            self.df.loc[mask, "tmdb_poster_url"] = tmdb_img_base + pp

        # 포스터 없는 영화 제외
        self.df = self.df[
            (self.df["tmdb_poster_url"].astype(str).str.strip() != "")
            | (self.df["poster_path"].astype(str).str.strip() != "")
        ].copy()

        try:
            self.df["movie_id"] = self.df["movie_id"].astype(int)
        except Exception:
            pass

        for col in ["vote_average", "popularity"]:
            try:
                self.df[col] = self.df[col].astype(float)
            except Exception:
                pass

        for col in ["vote_count", "runtime"]:
            try:
                self.df[col] = self.df[col].astype(int)
            except Exception:
                pass

        # 장르 파싱 캐시
        self._genres_cache: dict[int, list[str]] = {}
        try:
            for _, r in self.df[["movie_id", "genres"]].iterrows():
                mid = int(r["movie_id"])
                self._genres_cache[mid] = _parse_genres_cell(r["genres"])
        except Exception:
            self._genres_cache = {}

    def _apply_sort(self, df: pd.DataFrame, sort: str) -> pd.DataFrame:
        if sort == "latest":
            return df.sort_values("release_date", ascending=False, na_position="last")
        if sort == "rating":
            return df.sort_values("vote_average", ascending=False)
        return df.sort_values("popularity", ascending=False)

    def _row_to_card(self, row) -> Dict[str, Any]:
        movie_id = row.get("movie_id", 0)
        try:
            movie_id = int(movie_id)
        except Exception:
            movie_id = 0

        def _to_float(x, default=0.0):
            try:
                return float(x)
            except Exception:
                return default

        def _to_int(x, default=0):
            try:
                return int(x)
            except Exception:
                return default

        tmdb_poster_url = str(row.get("tmdb_poster_url", "") or "").strip()

        return {
            "movie_id": movie_id,
            "title": row.get("title", ""),
            "original_title": row.get("original_title", ""),
            "overview": row.get("overview", ""),
            "tagline": row.get("tagline", ""),
            "genres": row.get("genres", ""),
            "tmdb_poster_url": tmdb_poster_url,
            "poster_url": tmdb_poster_url,
            "poster_path": row.get("poster_path", ""),
            "vote_average": _to_float(row.get("vote_average", 0.0), 0.0),
            "vote_count": _to_int(row.get("vote_count", 0), 0),
            "popularity": _to_float(row.get("popularity", 0.0), 0.0),
            "release_date": row.get("release_date", ""),
            "runtime": _to_int(row.get("runtime", 0), 0),
        }

    # ============================================================
    # Flask main.py compatibility methods
    # ============================================================
    def get_popular_movies(self, limit: int = 21, sort: str = "popular"):
        df = self._apply_sort(self.df.copy(), sort)

        if limit and limit > 0:
            df = df.head(int(limit))

        movies = [self._row_to_card(row) for _, row in df.iterrows()]
        total_count = len(self.df)
        total_pages = 1
        return movies, total_pages, total_count

    def get_movie_by_id(self, movie_id: int):
        try:
            movie_id = int(movie_id)
        except Exception:
            return None

        row = self.df[self.df["movie_id"] == movie_id]
        if row.empty:
            return None

        movie = self._row_to_card(row.iloc[0])

        # 상세 화면 편의 필드
        genres_list = self._genres_cache.get(movie_id, [])
        movie["genres_list"] = genres_list
        movie["genres_display"] = ", ".join([g.title() for g in genres_list]) if genres_list else ""

        return movie

    def get_similar_movies(self, movie_id: int, limit: int = 14):
        try:
            movie_id = int(movie_id)
        except Exception:
            return []

        target = self.df[self.df["movie_id"] == movie_id]
        if target.empty:
            return []

        target_row = target.iloc[0]
        target_genres = set(self._genres_cache.get(movie_id, []))
        target_title = str(target_row.get("title", "")).strip().lower()

        candidates = []

        for _, row in self.df.iterrows():
            try:
                mid = int(row.get("movie_id", 0))
            except Exception:
                continue

            if mid == movie_id:
                continue

            row_title = str(row.get("title", "")).strip().lower()
            if row_title == target_title:
                continue

            genres = set(self._genres_cache.get(mid, []))
            genre_overlap = len(target_genres & genres)

            try:
                popularity = float(row.get("popularity", 0.0) or 0.0)
            except Exception:
                popularity = 0.0

            try:
                vote_average = float(row.get("vote_average", 0.0) or 0.0)
            except Exception:
                vote_average = 0.0

            try:
                vote_count = float(row.get("vote_count", 0.0) or 0.0)
            except Exception:
                vote_count = 0.0

            # 장르 겹침 우선 + 대중성/평점 보조
            score = (
                genre_overlap * 10.0
                + popularity * 0.05
                + vote_average * 0.5
                + min(vote_count, 5000) * 0.0002
            )

            if genre_overlap <= 0:
                continue

            candidates.append((score, row))

        candidates.sort(key=lambda x: x[0], reverse=True)

        out = []
        for _, row in candidates[: int(limit)]:
            out.append(self._row_to_card(row))

        return out

    # ============================================================
    # Hybrid Search
    # ============================================================
    def search_hybrid(
        self,
        *,
        query: Optional[str] = None,
        image_path: Optional[str] = None,
        search_type: str = "text",
        sort: str = "popular",
        candidate_k: int = 700,
        debug: bool = False,
        enabled_engines: Optional[Dict[str, bool]] = None,
        debug_top_k: int = 20,
    ) -> Union[List[Dict], Dict[str, Any]]:
        query = _normalize_space(query or "")
        has_query = bool(query)
        has_image = bool(image_path)

        debug_payload: Dict[str, Any] = {
            "search_type": search_type,
            "sort": sort,
            "candidate_k": int(candidate_k),
            "enabled_engines": enabled_engines or {},
        }

        # ------------------------------
        # IMAGE SEARCH (RRF)
        # ------------------------------
        if search_type == "image" and image_path:
            if not _engine_enabled(enabled_engines, "clip", True):
                if not debug:
                    return []
                debug_payload["fusion_method"] = "rrf"
                debug_payload["error"] = "CLIP disabled (image search requires CLIP)."
                return {"results": [], "debug": debug_payload}

            clip_scores = get_clip_engine().score(image_path, top_k=None, min_score=-1.0) or {}
            if not clip_scores:
                if not debug:
                    return []
                debug_payload["fusion_method"] = "rrf"
                debug_payload["clip_scores_n"] = 0
                return {"results": [], "debug": debug_payload}

            prompts = [
                "action",
                "adventure",
                "animation",
                "comedy",
                "crime",
                "drama",
                "fantasy",
                "horror",
                "romance",
                "science fiction",
                "thriller",
                "war",
                "superhero",
                "vigilante",
                "batman",
                "dark",
                "gritty",
                "noir",
                "mystery",
                "city",
                "night",
                "explosion",
                "fire",
                "violence",
                "revenge",
            ]
            prompt_scores = get_clip_engine().score_prompts(image_path, prompts) or {}
            top_prompts = sorted(prompt_scores.items(), key=lambda x: x[1], reverse=True)[:6]
            pseudo_query = " ".join([p for p, s in top_prompts if s > 0]).strip()

            use_sbert = _engine_enabled(enabled_engines, "sbert", True)
            clip_rank_pool = 600

            if pseudo_query and use_sbert:
                sbert_all = sbert_engine.score(pseudo_query) or {}
                clip_sorted_for_sbert = sorted(
                    clip_scores.items(), key=lambda x: x[1], reverse=True
                )[:clip_rank_pool]
                candidate_set = {int(mid) for mid, _ in clip_sorted_for_sbert}
                sbert_scores = {
                    int(mid): float(sc)
                    for mid, sc in sbert_all.items()
                    if int(mid) in candidate_set
                }
            else:
                sbert_scores = {}

            # RRF params
            k = 40
            w_clip = 1.0
            w_sbert = 0.9

            clip_rank_pool = 600
            sbert_rank_pool = 800

            clip_sorted = sorted(
                clip_scores.items(), key=lambda x: x[1], reverse=True
            )[:clip_rank_pool]
            clip_rank: dict[int, int] = {
                int(mid): r for r, (mid, _) in enumerate(clip_sorted, start=1)
            }

            sbert_rank: dict[int, int] = {}
            if sbert_scores:
                sbert_sorted = sorted(
                    sbert_scores.items(), key=lambda x: x[1], reverse=True
                )[:sbert_rank_pool]
                sbert_rank = {
                    int(mid): r for r, (mid, _) in enumerate(sbert_sorted, start=1)
                }

            pool_ids = set(clip_rank.keys()) | set(sbert_rank.keys())

            fused: list[tuple[int, float, float, float]] = []
            # (mid, rrf_score, clip_term, sbert_term)
            for mid in pool_ids:
                rc = clip_rank.get(mid, 10**9)
                rs = sbert_rank.get(mid, 10**9)

                clip_term = (w_clip / (k + rc)) if rc < 10**8 else 0.0
                sbert_term = (w_sbert / (k + rs)) if rs < 10**8 else 0.0
                score = clip_term + sbert_term
                fused.append((mid, score, clip_term, sbert_term))

            fused.sort(key=lambda x: x[1], reverse=True)

            # cut policy
            max_results = 600
            min_results = 120

            try:
                clip_best = float(max(clip_scores.values())) if clip_scores else 0.0
            except Exception:
                clip_best = 0.0

            fused = fused[:max_results]

            if clip_best < 0.55:
                fused = fused[:min_results]
                cut_policy = {
                    "mode": "weak_input_min_cap",
                    "clip_best": clip_best,
                    "kept": len(fused),
                }
            else:
                target_anchor = 220
                if not fused:
                    fused = []
                    cut_policy = {"mode": "empty"}
                else:
                    anchor_idx = min(len(fused) - 1, max(min_results - 1, target_anchor - 1))
                    anchor_score = fused[anchor_idx][1]
                    anchor_ratio = 0.70
                    threshold = anchor_score * anchor_ratio
                    filtered = [t for t in fused if t[1] >= threshold]
                    if len(filtered) < min_results:
                        filtered = fused[:min_results]
                    fused = filtered
                    cut_policy = {
                        "mode": "anchor_ratio",
                        "anchor_idx": anchor_idx + 1,
                        "anchor_score": float(anchor_score),
                        "anchor_ratio": float(anchor_ratio),
                        "threshold": float(threshold),
                        "kept": len(fused),
                    }

            movies: list[dict] = []
            contrib_rows: List[Dict[str, Any]] = []

            for i, (mid, rrf_score, clip_term, sbert_term) in enumerate(fused, start=1):
                row = self.df[self.df["movie_id"] == int(mid)]
                if row.empty:
                    continue

                card = self._row_to_card(row.iloc[0])

                card["rrf_score"] = float(rrf_score)
                card["clip_rank"] = int(clip_rank.get(int(mid), 10**9))
                card["sbert_rank"] = int(sbert_rank.get(int(mid), 10**9)) if sbert_rank else None
                card["clip_term"] = float(clip_term)
                card["sbert_term"] = float(sbert_term)
                card["dominant_engine"] = "clip" if clip_term >= sbert_term else "sbert"
                card["_pseudo_query"] = pseudo_query

                movies.append(card)

                if i <= min(debug_top_k, 50):
                    contrib_rows.append(
                        {
                            "final_rank": i,
                            "movie_id": int(mid),
                            "title": card.get("title"),
                            "rrf_score": float(rrf_score),
                            "clip_rank": int(card.get("clip_rank")),
                            "sbert_rank": card.get("sbert_rank"),
                            "clip_term": float(clip_term),
                            "sbert_term": float(sbert_term),
                            "dominant_engine": card.get("dominant_engine"),
                            "present_clip": int(mid) in clip_rank,
                            "present_sbert": int(mid) in sbert_rank,
                        }
                    )

            if not debug:
                return movies

            debug_payload["fusion_method"] = "rrf"
            debug_payload["rrf_params"] = {"k": k, "w_clip": w_clip, "w_sbert": w_sbert}
            debug_payload["pseudo_query"] = pseudo_query
            debug_payload["clip_best"] = clip_best
            debug_payload["cut_policy"] = cut_policy

            debug_payload["engine_counts"] = {
                "clip_scores_total": len(clip_scores),
                "clip_rank_pool": len(clip_rank),
                "sbert_scores_restricted": len(sbert_scores),
                "sbert_rank_pool": len(sbert_rank),
                "union_pool_ids": len(pool_ids),
            }

            debug_payload["engine_top"] = {
                "clip_top": _safe_top_items(
                    {int(k0): float(v) for k0, v in clip_scores.items()},
                    top_k=min(debug_top_k, 30),
                ),
                "prompt_top": [
                    {"rank": i + 1, "prompt": p, "score": float(s)}
                    for i, (p, s) in enumerate(top_prompts)
                ],
                "sbert_top": _safe_top_items(
                    {int(k0): float(v) for k0, v in sbert_scores.items()},
                    top_k=min(debug_top_k, 30),
                ),
                "fused_top": [
                    {
                        "rank": i + 1,
                        "movie_id": int(mid),
                        "rrf_score": float(sc),
                        "clip_term": float(ct),
                        "sbert_term": float(st),
                    }
                    for i, (mid, sc, ct, st) in enumerate(fused[: min(debug_top_k, 50)])
                ],
                "contrib_top": contrib_rows,
            }

            debug_payload["result_count"] = len(movies)
            return {"results": movies, "debug": debug_payload}

        # ------------------------------
        # TEXT SEARCH (score fusion)
        # ------------------------------
        if search_type == "text" and has_query:
            if _looks_like_gibberish(query):
                if not debug:
                    return []
                debug_payload["fusion_method"] = "score_fusion"
                debug_payload["error"] = "gibberish_query"
                return {"results": [], "debug": debug_payload}

            tokens = _tokenize(query)
            if not tokens:
                if not debug:
                    return []
                debug_payload["fusion_method"] = "score_fusion"
                debug_payload["error"] = "no_tokens"
                return {"results": [], "debug": debug_payload}

            q_low = query.lower().strip()
            title_hits: List[Dict] = []
            try:
                mask = self.df["title"].astype(str).str.lower().str.contains(q_low, regex=False)
                if mask.any():
                    for _, r in self.df[mask].head(10).iterrows():
                        card0 = self._row_to_card(r)
                        card0["score"] = 1.0
                        card0["_title_boost"] = True
                        title_hits.append(card0)
            except Exception:
                title_hits = []

            use_tfidf = _engine_enabled(enabled_engines, "tfidf", True)
            use_sbert = _engine_enabled(enabled_engines, "sbert", True)

            tfidf_scores: Dict[int, float] = {}
            sbert_scores: Dict[int, float] = {}

            if use_tfidf:
                raw = tfidf_engine.score(query, top_k=int(candidate_k), min_score=0.0) or {}
                tfidf_scores = {int(mid): float(sc) for mid, sc in raw.items()}

            if use_sbert:
                raw = sbert_engine.score(query, top_k=int(candidate_k), min_score=0.10) or {}
                sbert_scores = {int(mid): float(sc) for mid, sc in raw.items()}

            base_w = dict(HYBRID_WEIGHTS.get("text", {}) or {})
            w = {
                "tfidf": float(base_w.get("tfidf", 0.0)) if use_tfidf else 0.0,
                "sbert": float(base_w.get("sbert", 0.0)) if use_sbert else 0.0,
                "clip": 0.0,
                "cf": 0.0,
            }

            ranked_items = hybrid_rerank(
                tfidf_results=tfidf_scores if use_tfidf else None,
                sbert_results=sbert_scores if use_sbert else None,
                clip_results=None,
                cf_results=None,
                weights=w,
            )

            if not ranked_items:
                movies = title_hits if title_hits else []
                if not debug:
                    return movies

                debug_payload["fusion_method"] = "score_fusion"
                debug_payload["weights"] = w
                debug_payload["engine_counts"] = {
                    "tfidf_n": len(tfidf_scores),
                    "sbert_n": len(sbert_scores),
                    "union_ids": len(set(tfidf_scores.keys()) | set(sbert_scores.keys())),
                    "overlap_tfidf_sbert": len(set(tfidf_scores.keys()) & set(sbert_scores.keys())),
                }
                debug_payload["result_count"] = len(movies)
                return {"results": movies, "debug": debug_payload}

            movies: List[Dict] = []
            for item in ranked_items:
                try:
                    mid = int(item.get("movie_id"))
                except Exception:
                    continue

                score = float(item.get("score", 0.0))
                if score < 0.12:
                    break

                row = self.df[self.df["movie_id"] == mid]
                if row.empty:
                    continue

                card = self._row_to_card(row.iloc[0])
                card["score"] = score

                title = str(card.get("title", "")).lower()
                overview = str(card.get("overview", "")).lower()
                hay = title + " " + overview

                if any(t in hay for t in tokens):
                    movies.append(card)
                    continue

                if score >= 0.35:
                    movies.append(card)

            if sort in ("latest", "rating", "popular") and movies:
                try:
                    temp_df = pd.DataFrame(movies)
                    temp_df = self._apply_sort(temp_df, sort)
                    movies = temp_df.to_dict(orient="records")
                except Exception:
                    pass

            if title_hits:
                seen = set()
                merged: List[Dict] = []
                for m in title_hits + movies:
                    mid = m.get("movie_id")
                    if mid in seen:
                        continue
                    seen.add(mid)
                    merged.append(m)
                movies = merged

            if not debug:
                return movies

            tfidf_norm = _normalize(tfidf_scores) if tfidf_scores else {}
            sbert_norm = _normalize(sbert_scores) if sbert_scores else {}

            union_ids = set(tfidf_scores.keys()) | set(sbert_scores.keys())
            overlap = set(tfidf_scores.keys()) & set(sbert_scores.keys())

            debug_payload["fusion_method"] = "score_fusion"
            debug_payload["weights"] = w
            debug_payload["engine_counts"] = {
                "tfidf_n": len(tfidf_scores),
                "sbert_n": len(sbert_scores),
                "union_ids": len(union_ids),
                "overlap_tfidf_sbert": len(overlap),
            }

            contrib_rows: List[Dict[str, Any]] = []
            for i, m in enumerate(movies[: min(debug_top_k, 50)], start=1):
                mid = int(m.get("movie_id", 0))
                tf = float(tfidf_norm.get(mid, 0.0))
                sb = float(sbert_norm.get(mid, 0.0))
                tf_c = tf * float(w.get("tfidf", 0.0))
                sb_c = sb * float(w.get("sbert", 0.0))
                dom = "tfidf" if tf_c >= sb_c else "sbert"

                m["tfidf_norm"] = tf
                m["sbert_norm"] = sb
                m["tfidf_contrib"] = tf_c
                m["sbert_contrib"] = sb_c
                m["dominant_engine"] = dom

                contrib_rows.append(
                    {
                        "final_rank": i,
                        "movie_id": mid,
                        "title": m.get("title"),
                        "final_score": float(m.get("score", 0.0)),
                        "tfidf_norm": tf,
                        "sbert_norm": sb,
                        "tfidf_contrib": tf_c,
                        "sbert_contrib": sb_c,
                        "dominant_engine": dom,
                        "present_tfidf": mid in tfidf_scores,
                        "present_sbert": mid in sbert_scores,
                    }
                )

            debug_payload["engine_top"] = {
                "tfidf_top": _safe_top_items(tfidf_scores, top_k=min(debug_top_k, 30)),
                "sbert_top": _safe_top_items(sbert_scores, top_k=min(debug_top_k, 30)),
                "contrib_top": contrib_rows,
            }
            debug_payload["result_count"] = len(movies)
            return {"results": movies, "debug": debug_payload}

        if not debug:
            return []

        debug_payload["fusion_method"] = "none"
        debug_payload["result_count"] = 0
        return {"results": [], "debug": debug_payload}