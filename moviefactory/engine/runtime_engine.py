# ============================================================
# moviefactory/engine/runtime_engine.py
# - Image Search: CLIP candidates + prompt-derived pseudo_query + SBERT + RRF fusion
# - Tuned: stronger SBERT in top ranks + limit rank pool to reduce noise
# - Text Search: TF-IDF + SBERT hybrid + (NEW) Title Boost safety for exact-title queries
# ============================================================

from __future__ import annotations

import os
import re
from typing import Optional, List, Dict

import pandas as pd

from moviefactory.engine.hybrid_engine import hybrid_rerank
from moviefactory.config.hybrid_weights import HYBRID_WEIGHTS
from moviefactory.engine.tfidf_engine import tfidf_engine
from moviefactory.engine.sbert_engine import sbert_engine
from moviefactory.engine.clip_engine import clip_engine


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

    # TMDB dict-list string like "[{'id':..,'name':'Fantasy'}, ...]"
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


class RuntimeEngine:
    """
    RuntimeEngine

    ✅ 페이지네이션 정책
    - 검색/장르/탐색 화면의 21개(7×3) prev/next는 "UI/라우트"가 담당
    - 엔진은 결과를 임의로 60개로 자르지 않는다.
    - 대신 '유효하지 않은 입력/유효하지 않은 점수'를 걸러낸다.

    ✅ 상세 페이지
    - get_similar_movies(limit=14)는 기존 그대로 사용
    """

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
            "movie_id", "title", "original_title", "overview", "tagline", "genres",
            "tmdb_poster_url", "poster_path", "vote_average", "vote_count", "popularity",
            "release_date", "runtime",
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

        TMDB_IMG_BASE = os.environ.get("TMDB_IMG_BASE", "https://image.tmdb.org/t/p/w500")

        self.df["tmdb_poster_url"] = self.df["tmdb_poster_url"].astype(str).fillna("").str.strip()
        self.df["poster_path"] = self.df["poster_path"].astype(str).fillna("").str.strip()

        mask = (self.df["tmdb_poster_url"] == "") & (self.df["poster_path"] != "")
        if mask.any():
            pp = self.df.loc[mask, "poster_path"].apply(lambda x: x if x.startswith("/") else "/" + x)
            self.df.loc[mask, "tmdb_poster_url"] = TMDB_IMG_BASE + pp

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

        # 장르 파싱 캐시 (다중 장르 포함 정확히)
        self._genres_cache: dict[int, list[str]] = {}
        try:
            for _, r in self.df[["movie_id", "genres"]].iterrows():
                mid = int(r["movie_id"])
                self._genres_cache[mid] = _parse_genres_cell(r["genres"])
        except Exception:
            self._genres_cache = {}

    # ==================================================
    # SORT
    # ==================================================
    def _apply_sort(self, df: pd.DataFrame, sort: str) -> pd.DataFrame:
        if sort == "latest":
            return df.sort_values("release_date", ascending=False, na_position="last")
        if sort == "rating":
            return df.sort_values("vote_average", ascending=False)
        return df.sort_values("popularity", ascending=False)

    # ==================================================
    # CARD / DETAIL
    # ==================================================
    def _row_to_card(self, row) -> Dict:
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

        tmdb_poster_url = (row.get("tmdb_poster_url", "") or "").strip()

        return {
            "movie_id": movie_id,
            "title": row.get("title", ""),
            "original_title": row.get("original_title", ""),
            "overview": row.get("overview", ""),
            "tagline": row.get("tagline", ""),
            "genres": row.get("genres", ""),
            "tmdb_poster_url": tmdb_poster_url,
            "poster_url": tmdb_poster_url,  # 템플릿 호환 키
            "poster_path": row.get("poster_path", ""),
            "vote_average": _to_float(row.get("vote_average", 0.0), 0.0),
            "vote_count": _to_int(row.get("vote_count", 0), 0),
            "popularity": _to_float(row.get("popularity", 0.0), 0.0),
            "release_date": row.get("release_date", ""),
            "runtime": _to_int(row.get("runtime", 0), 0),
        }

    def _row_to_detail(self, row) -> Dict:
        # ✅ 상세는 "필수 메타"를 항상 포함해야 함
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

        if hasattr(row, "to_dict"):
            raw = row.to_dict()
        else:
            raw = dict(row)

        tmdb_poster_url = (raw.get("tmdb_poster_url", "") or "").strip()

        d = {
            "movie_id": _to_int(raw.get("movie_id", 0), 0),
            "title": raw.get("title", "") or "",
            "original_title": raw.get("original_title", "") or "",
            "overview": raw.get("overview", "") or "",
            "tagline": raw.get("tagline", "") or "",
            "genres": raw.get("genres", "") or "",
            "tmdb_poster_url": tmdb_poster_url,
            "poster_url": tmdb_poster_url,
            "poster_path": raw.get("poster_path", "") or "",
            "vote_average": _to_float(raw.get("vote_average", 0.0), 0.0),
            "vote_count": _to_int(raw.get("vote_count", 0), 0),
            "popularity": _to_float(raw.get("popularity", 0.0), 0.0),
            "release_date": raw.get("release_date", "") or "",
            "runtime": _to_int(raw.get("runtime", 0), 0),
        }

        return d

    # ==================================================
    # PUBLIC API
    # ==================================================
    def get_popular_movies(self, *, limit: int = 21, sort: str = "popular"):
        df = self._apply_sort(self.df, sort)
        total_count = len(df)
        movies = [self._row_to_card(r) for _, r in df.head(limit).iterrows()]
        total_pages = 1
        return movies, total_pages, total_count

    def get_movie_by_id(self, movie_id: int) -> Dict:
        try:
            movie_id = int(movie_id)
        except Exception:
            return {}
        row = self.df[self.df["movie_id"] == movie_id]
        if row.empty:
            return {}
        return self._row_to_detail(row.iloc[0])

    def get_similar_movies(self, movie_id: int, *, limit: int = 14):
        try:
            movie_id = int(movie_id)
        except Exception:
            return []
        df = self.df[self.df["movie_id"] != movie_id]
        df = df.sort_values("popularity", ascending=False)
        return [self._row_to_card(r) for _, r in df.head(limit).iterrows()]

    # ==================================================
    # SEARCH
    # ==================================================
    def search_hybrid(
        self,
        *,
        query: Optional[str] = None,
        image_path: Optional[str] = None,
        search_type: str = "text",
        sort: str = "popular",
        candidate_k: int = 700,
    ) -> List[Dict]:

        query = _normalize_space(query or "")
        has_query = bool(query)
        has_image = bool(image_path)

        # ------------------------------
        # BROWSE
        # ------------------------------
        if not has_query and not has_image and search_type != "genre":
            df = self._apply_sort(self.df, sort)
            return [self._row_to_card(r) for _, r in df.iterrows()]

        # ------------------------------
        # GENRE SEARCH
        # ------------------------------
        if search_type == "genre" and has_query:
            q = query.lower().strip()
            genre_alias = {
                "sf": ["science fiction", "sci-fi", "sci fi", "sf"],
            }
            targets = genre_alias.get(q, [q])

            matched_ids: list[int] = []
            if self._genres_cache:
                for mid, glist in self._genres_cache.items():
                    if any(t in glist for t in targets):
                        matched_ids.append(mid)
            else:
                genres_lower = self.df["genres"].astype(str).str.lower()
                mask = pd.Series([False] * len(self.df), index=self.df.index)
                for t in targets:
                    mask = mask | genres_lower.str.contains(t, regex=False)
                df = self.df[mask]
                df = self._apply_sort(df, sort)
                return [self._row_to_card(r) for _, r in df.iterrows()]

            if not matched_ids:
                return []

            df = self.df[self.df["movie_id"].isin(matched_ids)]
            df = self._apply_sort(df, sort)
            return [self._row_to_card(r) for _, r in df.iterrows()]

        # ------------------------------
        # IMAGE SEARCH (TUNED RRF)
        # ------------------------------
        if search_type == "image" and image_path:
            # 1) CLIP 점수: 전체 대상(2234) 비교
            clip_scores = clip_engine.score(
                image_path,
                top_k=None,
                min_score=-1.0,
            )
            if not clip_scores:
                print("[IMG-RRF] clip_scores=0 (no candidates)")
                return []

            # (디버그) CLIP 전체에서 155 순위
            try:
                target_id = 155
                clip_sorted_all = sorted(clip_scores.items(), key=lambda x: x[1], reverse=True)
                clip_rank_155 = None
                for i, (mid, _) in enumerate(clip_sorted_all, start=1):
                    if int(mid) == target_id:
                        clip_rank_155 = i
                        break
                print(f"[IMG-RRF][CLIP-RANK] total={len(clip_scores)} movie_id=155 rank={clip_rank_155}")
            except Exception as e:
                print("[IMG-RRF][CLIP-RANK] failed:", e)

            # 2) prompt 기반 pseudo_query 만들기
            prompts = [
                # MovieFactory 장르 탭 + 톤/테마
                "action", "adventure", "animation", "comedy", "crime", "drama",
                "fantasy", "horror", "romance", "science fiction", "thriller", "war",
                # 히어로/범죄 힌트
                "superhero", "vigilante", "batman",
                # 분위기/공간 힌트
                "dark", "gritty", "noir", "mystery", "city", "night",
                # 사건/액션 힌트
                "explosion", "fire", "violence", "revenge",
            ]
            prompt_scores = clip_engine.score_prompts(image_path, prompts) or {}
            top_prompts = sorted(prompt_scores.items(), key=lambda x: x[1], reverse=True)[:6]
            pseudo_query = " ".join([p for p, s in top_prompts if s > 0]).strip()

            # 3) SBERT 의미 점수 (전체 -> clip 후보로 restrict)
            if pseudo_query:
                sbert_all = sbert_engine.score(pseudo_query)
                candidate_set = set(clip_scores.keys())
                sbert_scores = {mid: sc for mid, sc in sbert_all.items() if mid in candidate_set}
            else:
                sbert_scores = {}

            print(
                "[IMG-RRF] pseudo_query=", pseudo_query,
                "| candidates=", len(clip_scores),
                "| sbert_scores=", len(sbert_scores),
                "| top_prompts=", top_prompts
            )

            # 4) RRF (순위 기반 결합) - 튜닝값
            k = 40
            w_clip = 1.0
            w_sbert = 1.4

            # ✅ RRF 대상 풀 = (CLIP 상위 pool) ∪ (SBERT 상위 pool)
            CLIP_RANK_POOL = 600
            SBERT_RANK_POOL = 800

            clip_sorted = sorted(clip_scores.items(), key=lambda x: x[1], reverse=True)[:CLIP_RANK_POOL]
            clip_rank: dict[int, int] = {}
            for r, (mid, _) in enumerate(clip_sorted, start=1):
                clip_rank[int(mid)] = r

            sbert_rank: dict[int, int] = {}
            if sbert_scores:
                sbert_sorted = sorted(sbert_scores.items(), key=lambda x: x[1], reverse=True)[:SBERT_RANK_POOL]
                for r, (mid, _) in enumerate(sbert_sorted, start=1):
                    sbert_rank[int(mid)] = r

            pool_ids = set(clip_rank.keys()) | set(sbert_rank.keys())

            fused: list[tuple[int, float]] = []
            for mid in pool_ids:
                rc = clip_rank.get(mid, 10**9)
                rs = sbert_rank.get(mid, 10**9)

                score = 0.0
                if rc < 10**8:
                    score += (w_clip / (k + rc))
                if rs < 10**8:
                    score += (w_sbert / (k + rs))

                fused.append((mid, score))

            fused.sort(key=lambda x: x[1], reverse=True)

            # 결과 컷 정책 (RRF 전용: 순위 기반)
            MAX_RESULTS = 600
            MIN_RESULTS = 120

            fused = fused[:MAX_RESULTS]

            clip_best = 0.0
            try:
                clip_best = float(max(clip_scores.values())) if clip_scores else 0.0
            except Exception:
                clip_best = 0.0

            if clip_best < 0.55:
                fused = fused[:MIN_RESULTS]

            print(f"[IMG-RRF][CUT] clip_best={clip_best:.4f} kept={len(fused)}")

            # DEBUG: RRF 결과 Top20 + movie_id=155 랭크
            try:
                target_id = 155
                target_rank = None
                for i, (mid, _) in enumerate(fused, start=1):
                    if int(mid) == target_id:
                        target_rank = i
                        break
                print(f"[IMG-RRF][TARGET] movie_id={target_id} rank={target_rank} (in fused)")

                for rank, (mid, sc) in enumerate(fused[:20], start=1):
                    row = self.df[self.df["movie_id"] == int(mid)]
                    title = ""
                    if not row.empty:
                        title = str(row.iloc[0].get("title", ""))
                    print(f"[IMG-RRF][TOP20] {rank:02d} movie_id={int(mid)} score={float(sc):.6f} title={title}")
            except Exception as e:
                print("[IMG-RRF][DEBUG] failed:", e)

            # 카드 변환 (점수는 UI 미노출)
            movies: list[dict] = []
            for mid, _ in fused:
                row = self.df[self.df["movie_id"] == int(mid)]
                if row.empty:
                    continue
                movies.append(self._row_to_card(row.iloc[0]))

            return movies

        # ------------------------------
        # TEXT SEARCH (HYBRID)
        # ------------------------------
        if search_type == "text" and has_query:
            if _looks_like_gibberish(query):
                return []

            tokens = _tokenize(query)
            if not tokens:
                return []

            # ------------------------------
            # TITLE BOOST (정확 제목 검색 안전장치)
            # - query가 title에 포함되는 영화는 결과 맨 앞에 병합한다.
            # ------------------------------
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

            tfidf_scores = tfidf_engine.score(query, top_k=int(candidate_k), min_score=0.0)
            sbert_scores = sbert_engine.score(query, top_k=int(candidate_k), min_score=0.10)

            ranked_items = hybrid_rerank(
                tfidf_results=tfidf_scores,
                sbert_results=sbert_scores,
                clip_results=None,
                cf_results=None,
                weights=HYBRID_WEIGHTS.get("text", {}),
            )
            if not ranked_items:
                return title_hits if title_hits else []

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

            # ✅ title_hits를 결과 맨 앞에 합치되 중복 제거
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

            return movies

        return []
