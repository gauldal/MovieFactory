from __future__ import annotations

import os
import json
import time
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import streamlit as st

from ops.auto_tagging import auto_tag_failure, compute_rolling_latency_baseline


# ===========================
# Shared state
# ===========================
def _ensure_shared_state() -> None:
    if "ui_lang" not in st.session_state:
        st.session_state["ui_lang"] = "ko"
    if "learning_mode" not in st.session_state:
        st.session_state["learning_mode"] = True


def _copy(lang: str) -> Dict[str, str]:
    ko = {
        "title": "Hybrid Search Inspector (Query Lab)",
        "subtitle": "검색을 직접 실행하면서 **엔진별 retrieval / candidate pool / fusion / contribution**을 단계별로 확인하는 실험 화면입니다.",
        "why_title": "이 화면의 목적",
        "why_body": (
            "1) 하이브리드 검색이 실제로 어떻게 동작하는지 눈으로 확인\n"
            "2) 엔진별 후보 / fusion 방식 / contribution 구조를 검증\n"
            "3) 실행 결과를 저장해서 나중에 Quality Monitor에서 추세로 다시 보기\n"
        ),
        "guide_title": "이 화면을 보는 순서",
        "guide_body": (
            "권장 순서:\n"
            "① Run 실행 → ② Explain → ③ Engine Retrieval → ④ Candidate Pool → "
            "⑤ Fusion → ⑥ Contribution → ⑦ Save run\n\n"
            "즉, 먼저 결과를 만들고, 그다음 그 결과가 왜 나왔는지를 단계적으로 해석하면 됩니다."
        ),
        "settings": "설정",
        "runs_dir": "runs 폴더",
        "runs_dir_tip": "Save run을 누르면 여기에 JSON이 저장되고, Quality Monitor가 이 폴더를 읽어 통계/그래프를 만듭니다.",
        "mode": "검색 모드",
        "mode_help": "text = TF-IDF + SBERT 점수 결합 / image = CLIP + SBERT RRF 결합",
        "query": "검색어 입력",
        "query_help": "text 모드에서 사용하는 검색어입니다.",
        "image": "이미지 업로드",
        "image_help": "image 모드에서 사용할 포스터/이미지를 업로드합니다.",
        "run": "실행(Run)",
        "run_help": "현재 설정으로 검색을 1회 실행합니다.",
        "run_ablation": "Ablation 비교 실행",
        "run_ablation_help": "같은 입력으로 엔진 조합을 바꿔서 자동 비교 실행합니다.",
        "results": "최종 결과",
        "latency": "응답 시간(latency_ms)",
        "count": "결과 개수(result_count)",
        "preview_k": "미리보기 Top K (UI용)",
        "preview_help": "표에 몇 개까지 보여줄지(UI만 영향). 저장되는 result_count는 전체 결과 개수입니다.",
        "engine_toggles": "Engine ON/OFF (단일 Run 기준)",
        "engine_toggles_help": "이 토글은 단일 Run에서만 사용됩니다. Ablation 비교는 미리 정의된 조합으로 자동 실행됩니다.",
        "tfidf": "TF-IDF",
        "sbert": "SBERT",
        "clip": "CLIP",
        "candidate_k": "candidate_k (후보 풀 크기)",
        "candidate_k_help": "text 모드에서 TF-IDF / SBERT가 점수 계산할 후보 수입니다.",
        "debug_top_k": "debug_top_k (Inspector 상위 K)",
        "debug_top_k_help": "엔진별 결과 / contribution 표에서 몇 개까지 볼지 정합니다.",
        "warn_query": "검색어를 입력해줘.",
        "warn_image": "이미지를 업로드해줘.",
        "tabs_explain": "Explain",
        "tabs_retrieval": "Engine Retrieval",
        "tabs_pool": "Candidate Pool",
        "tabs_fusion": "Fusion",
        "tabs_contrib": "Contribution",
        "tabs_final": "Final",
        "tabs_ablation": "Ablation",
        "save_title": "실험 기록 저장(Save run)",
        "save_help": "현재 실험 결과를 JSON으로 저장하고, 자동 태깅까지 함께 기록합니다.",
        "notes": "메모(선택)",
        "notes_help": "관찰 / 가설 / 이상 징후 / 느낀 점 등을 적어두면 나중에 추세를 해석하기 쉬워집니다.",
        "save": "저장(Save run)",
        "saved": "저장 완료",
        "no_results": "아직 실행 결과가 없거나 결과가 비어 있어.",
        "rules": "자동 태그 규칙(고급)",
        "rules_tip": "학습 단계에서는 기본값을 유지하고, 익숙해진 뒤 조정하는 걸 추천합니다.",
        "low_results_threshold": "LOW_RESULTS 임계치",
        "low_results_help": "result_count가 이 값보다 작으면 결과 부족 태그가 붙을 수 있습니다.",
        "slow_absolute_ms": "SLOW_ABSOLUTE 임계치(ms)",
        "slow_help": "latency_ms가 이 값보다 크면 느림 태그가 붙을 수 있습니다.",
        "clip_weak_threshold": "CLIP_WEAK_INPUT 임계치",
        "clip_help": "입력 신호가 약하다고 판단될 때 사용하는 임계치입니다.",
        "rolling_title": "Rolling latency baseline",
        "rolling_help": "최근 lab run 기준 latency baseline입니다.",
        "auto_tag_tip": "Save run 시점에 tags / reasons가 함께 저장됩니다.",
        "explain_empty": "실행 후 결과가 있으면 여기서 Why #1 설명을 볼 수 있어.",
        "retrieval_empty": "실행 후 엔진별 retrieval 결과가 표시됩니다.",
        "fusion_empty": "실행 후 fusion 정보가 표시됩니다.",
        "contrib_empty": "실행 후 contribution 정보가 표시됩니다.",
        "ablation_empty": "Ablation 비교를 실행하면 여기서 결과 차이와 시각화를 확인할 수 있습니다.",
        "quick_charts": "Quick Charts",
        "runs": "Runs",
        "comparisons": "Comparisons (vs base)",
        "trend": "Trend (from saved lab runs)",
        "trend_help": "Save run으로 누적된 ablation_summary를 기반으로 조합별 latency 추이를 시각화합니다.",
        "raw_debug": "Raw debug payload (advanced)",
        "raw_trend_rows": "Raw trend rows",
        "latency_by_variant": "조합별 latency (ms)",
        "count_by_variant": "조합별 result count",
        "purpose_explain": "이 탭은 최종 1위 결과가 왜 선택되었는지 설명합니다.",
        "purpose_retrieval": "이 탭은 각 엔진이 어떤 후보를 가져왔는지 보여줍니다.",
        "purpose_pool": "이 탭은 union / overlap / cut policy 등 후보 풀 구조를 보여줍니다.",
        "purpose_fusion": "이 탭은 score fusion 또는 RRF 결합 구조를 보여줍니다.",
        "purpose_contrib": "이 탭은 최종 결과에 어떤 엔진이 얼마나 기여했는지 보여줍니다.",
        "purpose_final": "이 탭은 최종 결과 미리보기와 raw debug payload를 보여줍니다.",
        "purpose_ablation": "이 탭은 엔진 조합별 결과 차이와 trend를 비교합니다.",
        "glossary_title": "용어 풀이 (Glossary)",
        "glossary_body": (
            "- **retrieval**: 엔진이 후보를 가져오는 단계\n"
            "- **candidate pool**: 여러 엔진 결과를 합친 후보 집합\n"
            "- **fusion**: 여러 신호를 결합해 최종 순위를 만드는 단계\n"
            "- **contribution**: 최종 결과를 밀어올린 엔진별 기여도\n"
            "- **ablation**: 엔진 일부를 끄고 결과가 얼마나 달라지는지 비교하는 실험\n"
        ),
    }

    en = {
        "title": "Hybrid Search Inspector (Query Lab)",
        "subtitle": "An experiment page where you run hybrid search and inspect **retrieval / candidate pool / fusion / contribution** step by step.",
        "why_title": "Purpose of this page",
        "why_body": (
            "1) Verify how the hybrid search pipeline actually works\n"
            "2) Inspect engine-level candidates, fusion behavior, and contribution\n"
            "3) Save experiments now and review long-term trends later in Quality Monitor\n"
        ),
        "guide_title": "Suggested reading order",
        "guide_body": (
            "Recommended order:\n"
            "① Run → ② Explain → ③ Engine Retrieval → ④ Candidate Pool → "
            "⑤ Fusion → ⑥ Contribution → ⑦ Save run\n\n"
            "In other words, first produce results, then interpret why they appeared in that order."
        ),
        "settings": "Settings",
        "runs_dir": "runs dir",
        "runs_dir_tip": "Saved runs are written here as JSON files. Quality Monitor reads them later for charts and analysis.",
        "mode": "Search mode",
        "mode_help": "text = TF-IDF + SBERT score fusion / image = CLIP + SBERT RRF fusion",
        "query": "Query",
        "query_help": "Search query used in text mode.",
        "image": "Upload image",
        "image_help": "Upload a poster/image for image mode.",
        "run": "Run",
        "run_help": "Run one search with current settings.",
        "run_ablation": "Run Ablation Compare",
        "run_ablation_help": "Automatically compare predefined engine combinations with the same input.",
        "results": "Final results",
        "latency": "latency_ms",
        "count": "result_count",
        "preview_k": "Preview Top K (UI only)",
        "preview_help": "Controls how many rows are shown in the UI. Stored result_count remains the full count.",
        "engine_toggles": "Engine ON/OFF (single run)",
        "engine_toggles_help": "These toggles are only used for the single Run action. Ablation compare uses predefined variants.",
        "tfidf": "TF-IDF",
        "sbert": "SBERT",
        "clip": "CLIP",
        "candidate_k": "candidate_k",
        "candidate_k_help": "Candidate pool size for TF-IDF / SBERT in text mode.",
        "debug_top_k": "debug_top_k",
        "debug_top_k_help": "How many top rows to show in inspector tables.",
        "warn_query": "Please enter a query.",
        "warn_image": "Please upload an image.",
        "tabs_explain": "Explain",
        "tabs_retrieval": "Engine Retrieval",
        "tabs_pool": "Candidate Pool",
        "tabs_fusion": "Fusion",
        "tabs_contrib": "Contribution",
        "tabs_final": "Final",
        "tabs_ablation": "Ablation",
        "save_title": "Save run",
        "save_help": "Save the current experiment as JSON together with auto-generated tags.",
        "notes": "Notes (optional)",
        "notes_help": "Write observations, hypotheses, suspicious behavior, or anything you want to remember later.",
        "save": "Save run",
        "saved": "Saved",
        "no_results": "No results yet.",
        "rules": "Auto-tag rules (advanced)",
        "rules_tip": "Keep the defaults while learning, then tune them later if needed.",
        "low_results_threshold": "LOW_RESULTS threshold",
        "low_results_help": "If result_count is lower than this, a low-results tag may be applied.",
        "slow_absolute_ms": "SLOW_ABSOLUTE threshold (ms)",
        "slow_help": "If latency_ms is higher than this, a slow tag may be applied.",
        "clip_weak_threshold": "CLIP_WEAK_INPUT threshold",
        "clip_help": "Threshold used when CLIP input is considered weak.",
        "rolling_title": "Rolling latency baseline",
        "rolling_help": "Latency baseline from recent lab runs.",
        "auto_tag_tip": "When you save a run, tags and reasons are stored together.",
        "explain_empty": "Run a query first to see the Why #1 explanation.",
        "retrieval_empty": "Run a query first to see engine retrieval results.",
        "fusion_empty": "Run a query first to see fusion details.",
        "contrib_empty": "Run a query first to see contribution details.",
        "ablation_empty": "Run ablation compare to inspect differences and charts here.",
        "quick_charts": "Quick Charts",
        "runs": "Runs",
        "comparisons": "Comparisons (vs base)",
        "trend": "Trend (from saved lab runs)",
        "trend_help": "Visualize latency trends by variant from saved ablation summaries.",
        "raw_debug": "Raw debug payload (advanced)",
        "raw_trend_rows": "Raw trend rows",
        "latency_by_variant": "Latency by variant (ms)",
        "count_by_variant": "Result count by variant",
        "purpose_explain": "This tab explains why the top-ranked result became #1.",
        "purpose_retrieval": "This tab shows what each engine retrieved as candidates.",
        "purpose_pool": "This tab shows union / overlap / cut-policy details for the candidate pool.",
        "purpose_fusion": "This tab shows score fusion or RRF combination behavior.",
        "purpose_contrib": "This tab shows how much each engine contributed to the final ranking.",
        "purpose_final": "This tab shows final preview results and the raw debug payload.",
        "purpose_ablation": "This tab compares engine variants and visualizes their trends.",
        "glossary_title": "Glossary",
        "glossary_body": (
            "- **retrieval**: the stage where an engine fetches candidates\n"
            "- **candidate pool**: the merged set of candidates across engines\n"
            "- **fusion**: the stage where multiple signals are combined into a final ranking\n"
            "- **contribution**: how much each engine pushed a result upward\n"
            "- **ablation**: an experiment where some engines are removed to observe changes"
        ),
    }

    return ko if lang == "ko" else en


# ===========================
# Paths / IO
# ===========================
def _default_runs_dir() -> Path:
    env = os.getenv("RUNS_DIR")
    if env:
        return Path(env)

    p = Path("moviefactory") / "eval" / "eval_reports" / "runs"
    if p.exists():
        return p

    p2 = Path("moviefactory") / "eval" / "runs"
    if p2.exists():
        return p2

    return Path("runs")


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _slug(s: str, max_len: int = 40) -> str:
    s = (s or "").strip().lower()
    keep = []
    for ch in s:
        if ch.isalnum():
            keep.append(ch)
        elif ch in (" ", "-", "_"):
            keep.append("-")
    out = "".join(keep)
    while "--" in out:
        out = out.replace("--", "-")
    out = out.strip("-")
    return out[:max_len] if out else "run"


def load_runs(runs_dir: Path) -> List[Dict[str, Any]]:
    if not runs_dir.exists():
        return []

    runs: List[Dict[str, Any]] = []
    for fp in sorted(runs_dir.glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            data["_file"] = str(fp)
            runs.append(data)
        except Exception:
            continue

    def key_fn(r: Dict[str, Any]) -> str:
        return str(r.get("created_at") or r.get("meta", {}).get("created_at") or r.get("run_at") or "")

    runs.sort(key=key_fn)
    return runs


def save_run(run: Dict[str, Any], runs_dir: Path) -> Path:
    _ensure_dir(runs_dir)
    created = run.get("created_at") or _now_iso()
    ts = created.replace(":", "").replace("-", "").replace("Z", "")
    engine = _slug(str(run.get("engine_name") or "engine"), 20)
    q = _slug(str(run.get("query_text") or run.get("image_name") or ""), 30)
    fn = f"{ts}__{run.get('suite','lab')}__{engine}__{q}.json"
    fp = runs_dir / fn
    fp.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    return fp


# ===========================
# Engine singleton
# ===========================
_ENGINE_SINGLETON = None


def _get_runtime_engine():
    global _ENGINE_SINGLETON
    if _ENGINE_SINGLETON is None:
        from moviefactory.engine.engine_provider import get_runtime_engine  # type: ignore
        _ENGINE_SINGLETON = get_runtime_engine()
    return _ENGINE_SINGLETON


def _save_uploaded_image_to_temp(uploaded) -> Tuple[str, str]:
    suffix = ""
    if uploaded and uploaded.name and "." in uploaded.name:
        suffix = "." + uploaded.name.split(".")[-1].lower()
        if suffix not in (".jpg", ".jpeg", ".png", ".webp"):
            suffix = ".png"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix or ".png") as f:
        f.write(uploaded.getbuffer())
        return f.name, (uploaded.name or "uploaded_image")


def run_query(
    *,
    mode: str,
    query_text: str,
    uploaded_image,
    sort: str,
    candidate_k: int,
    enabled_engines: Dict[str, bool],
    debug_top_k: int,
) -> Tuple[List[Dict[str, Any]], float, Dict[str, Any]]:
    eng = _get_runtime_engine()
    t0 = time.perf_counter()

    if mode == "text":
        payload = eng.search_hybrid(
            query=query_text,
            search_type="text",
            sort=sort,
            candidate_k=int(candidate_k),
            debug=True,
            enabled_engines=enabled_engines,
            debug_top_k=int(debug_top_k),
        )
        results = payload.get("results", [])
        debug = payload.get("debug", {})
    else:
        img_path, img_name = _save_uploaded_image_to_temp(uploaded_image)
        payload = eng.search_hybrid(
            image_path=img_path,
            search_type="image",
            sort=sort,
            candidate_k=int(candidate_k),
            debug=True,
            enabled_engines=enabled_engines,
            debug_top_k=int(debug_top_k),
        )
        results = payload.get("results", [])
        debug = payload.get("debug", {})
        if isinstance(debug, dict):
            debug["image_name"] = img_name
            debug["image_path"] = img_path

    latency_ms = (time.perf_counter() - t0) * 1000.0
    return results, latency_ms, debug


# ===========================
# Helpers
# ===========================
def _result_preview(results: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in results[:limit]:
        out.append(
            {
                "movie_id": r.get("movie_id") or r.get("id"),
                "title": r.get("title"),
                "score": r.get("score") or r.get("similarity"),
                "rrf_score": r.get("rrf_score"),
                "dominant_engine": r.get("dominant_engine"),
                "tfidf_contrib": r.get("tfidf_contrib"),
                "sbert_contrib": r.get("sbert_contrib"),
                "clip_term": r.get("clip_term"),
                "sbert_term": r.get("sbert_term"),
                "clip_rank": r.get("clip_rank"),
                "sbert_rank": r.get("sbert_rank"),
                "poster_url": r.get("poster_url") or r.get("tmdb_poster_url"),
            }
        )
    return out


def _dominant_ratio(contrib_rows: List[Dict[str, Any]]) -> Dict[str, float]:
    if not contrib_rows:
        return {}

    total = len(contrib_rows)
    counts: Dict[str, int] = {}
    for r in contrib_rows:
        de = str(r.get("dominant_engine") or "unknown")
        counts[de] = counts.get(de, 0) + 1
    return {k: round(v / total, 4) for k, v in counts.items()}


def _top_ids(results: List[Dict[str, Any]], k: int = 10) -> List[int]:
    ids: List[int] = []
    for r in results[:k]:
        mid = r.get("movie_id") or r.get("id")
        try:
            ids.append(int(mid))
        except Exception:
            continue
    return ids


def _jaccard(a: List[int], b: List[int]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _overlap_count(a: List[int], b: List[int]) -> int:
    return len(set(a) & set(b))


def _rank_map(ids: List[int]) -> Dict[int, int]:
    return {mid: i + 1 for i, mid in enumerate(ids)}


def _diff_table(base_ids: List[int], other_ids: List[int]) -> List[Dict[str, Any]]:
    base_rm = _rank_map(base_ids)
    oth_rm = _rank_map(other_ids)
    all_ids = list(set(base_ids) | set(other_ids))

    rows: List[Dict[str, Any]] = []
    for mid in all_ids:
        rows.append(
            {
                "movie_id": mid,
                "base_rank": base_rm.get(mid),
                "other_rank": oth_rm.get(mid),
                "delta(other-base)": (oth_rm.get(mid) - base_rm.get(mid)) if (mid in base_rm and mid in oth_rm) else None,
                "status": "both" if (mid in base_rm and mid in oth_rm) else ("only_base" if mid in base_rm else "only_other"),
            }
        )

    def key_fn(r: Dict[str, Any]):
        status = r["status"]
        if status == "both":
            return (0, r["base_rank"] or 10**9)
        if status == "only_base":
            return (1, r["base_rank"] or 10**9)
        return (2, r["other_rank"] or 10**9)

    rows.sort(key=key_fn)
    return rows


def _safe_get_contrib_top(debug: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        return (debug.get("engine_top") or {}).get("contrib_top") or []
    except Exception:
        return []


def _ablation_runs_to_chart_rows(ablation: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for r in (ablation.get("runs") or []):
        rows.append(
            {
                "label": r.get("label"),
                "latency_ms": float(r.get("latency_ms") or 0.0),
                "result_count": int(r.get("result_count") or 0),
            }
        )
    return rows


def _load_ablation_trend_from_saved_runs(runs_dir: Path, mode: str, limit: int = 60) -> List[Dict[str, Any]]:
    runs = load_runs(runs_dir)
    rows: List[Dict[str, Any]] = []

    candidates = list(reversed(runs))[: max(limit * 2, 120)]
    count = 0

    for r in candidates:
        if r.get("suite") != "lab":
            continue

        ss = (r.get("signals_summary") or {}).get("hybrid_debug") or {}
        ab = ss.get("ablation_summary")
        if not ab:
            continue
        if ab.get("mode") != mode:
            continue

        created_at = r.get("created_at") or ""
        rr = ab.get("runs") or []
        label_to_latency = {x.get("label"): float(x.get("latency_ms") or 0.0) for x in rr}

        base_all = None
        for k in label_to_latency.keys():
            if k and str(k).startswith("ALL"):
                base_all = k
                break

        row: Dict[str, Any] = {"created_at": created_at}
        if base_all:
            row["ALL_latency_ms"] = label_to_latency.get(base_all, 0.0)

        if mode == "text":
            row["TFIDF_ONLY_latency_ms"] = label_to_latency.get("TFIDF_ONLY", 0.0)
            row["SBERT_ONLY_latency_ms"] = label_to_latency.get("SBERT_ONLY", 0.0)
        else:
            row["CLIP_ONLY_latency_ms"] = label_to_latency.get("CLIP_ONLY", 0.0)

        rows.append(row)
        count += 1
        if count >= limit:
            break

    return list(reversed(rows))


# ===========================
# Explain card
# ===========================
def _render_explain_card(results: List[Dict[str, Any]], debug: Dict[str, Any], t: Dict[str, str]) -> None:
    if not results:
        st.info(t["explain_empty"])
        return

    top1 = results[0]
    title = top1.get("title", "")
    mid = top1.get("movie_id")
    fm = debug.get("fusion_method")

    st.markdown("### Why #1?")
    st.write({"movie_id": mid, "title": title, "fusion_method": fm})

    if fm == "score_fusion":
        tf_c = top1.get("tfidf_contrib")
        sb_c = top1.get("sbert_contrib")
        tf_n = top1.get("tfidf_norm")
        sb_n = top1.get("sbert_norm")
        dom = top1.get("dominant_engine")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("dominant_engine", str(dom))
        with c2:
            st.metric("tfidf_contrib", f"{float(tf_c):.4f}" if tf_c is not None else "-")
            st.caption(f"tfidf_norm={float(tf_n):.4f}" if tf_n is not None else "")
        with c3:
            st.metric("sbert_contrib", f"{float(sb_c):.4f}" if sb_c is not None else "-")
            st.caption(f"sbert_norm={float(sb_n):.4f}" if sb_n is not None else "")

        st.caption("text: contrib = weight × normalized_score")

    elif fm == "rrf":
        ct = top1.get("clip_term")
        stt = top1.get("sbert_term")
        dom = top1.get("dominant_engine")
        pseudo = debug.get("pseudo_query")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("dominant_engine", str(dom))
        with c2:
            st.metric("clip_term", f"{float(ct):.6f}" if ct is not None else "-")
            st.caption(f"clip_rank={top1.get('clip_rank')}")
        with c3:
            st.metric("sbert_term", f"{float(stt):.6f}" if stt is not None else "-")
            st.caption(f"sbert_rank={top1.get('sbert_rank')}")

        st.write({"pseudo_query": pseudo})
        st.caption("image: rrf_score = clip_term + sbert_term")

    else:
        st.info("fusion_method not available.")


# ===========================
# Ablation runner
# ===========================
def _ablation_variants(mode: str) -> List[Tuple[str, Dict[str, bool]]]:
    if mode == "text":
        return [
            ("ALL(tfidf+sbert)", {"tfidf": True, "sbert": True, "clip": False}),
            ("TFIDF_ONLY", {"tfidf": True, "sbert": False, "clip": False}),
            ("SBERT_ONLY", {"tfidf": False, "sbert": True, "clip": False}),
        ]
    return [
        ("ALL(clip+sbert)", {"tfidf": False, "sbert": True, "clip": True}),
        ("CLIP_ONLY", {"tfidf": False, "sbert": False, "clip": True}),
    ]


def run_ablation_compare(
    *,
    mode: str,
    query_text: str,
    uploaded_image,
    sort: str,
    candidate_k: int,
    debug_top_k: int,
    topk_eval: int = 10,
) -> Dict[str, Any]:
    variants = _ablation_variants(mode)

    runs: List[Dict[str, Any]] = []
    for label, engines in variants:
        results, latency_ms, dbg = run_query(
            mode=mode,
            query_text=query_text,
            uploaded_image=uploaded_image,
            sort=sort,
            candidate_k=candidate_k,
            enabled_engines=engines,
            debug_top_k=debug_top_k,
        )
        runs.append(
            {
                "label": label,
                "enabled_engines": engines,
                "latency_ms": float(latency_ms),
                "result_count": int(len(results)),
                "top_ids": _top_ids(results, k=topk_eval),
                "results_preview": _result_preview(results, limit=min(10, topk_eval)),
                "debug": dbg,
            }
        )

    base = runs[0] if runs else None
    comparisons: List[Dict[str, Any]] = []
    if base:
        base_ids = base["top_ids"]
        for r in runs[1:]:
            oth_ids = r["top_ids"]
            comparisons.append(
                {
                    "base": base["label"],
                    "other": r["label"],
                    "topk": int(topk_eval),
                    "jaccard": float(_jaccard(base_ids, oth_ids)),
                    "overlap": int(_overlap_count(base_ids, oth_ids)),
                    "top1_same": bool((base_ids[:1] == oth_ids[:1]) if base_ids and oth_ids else False),
                    "diff": _diff_table(base_ids, oth_ids),
                }
            )

    return {
        "mode": mode,
        "topk_eval": int(topk_eval),
        "runs": runs,
        "comparisons": comparisons,
    }


# ===========================
# Page UI
# ===========================
_ensure_shared_state()
lang = st.session_state["ui_lang"]
learning = st.session_state["learning_mode"]
t = _copy(lang)

st.set_page_config(page_title="Hybrid Search Inspector", layout="wide")

st.title(t["title"])
if learning:
    st.info(t["subtitle"])
    st.subheader(t["why_title"])
    st.markdown(t["why_body"])
    st.subheader(t["guide_title"])
    st.markdown(t["guide_body"])
    with st.expander(t["glossary_title"], expanded=False):
        st.markdown(t["glossary_body"])

runs_dir = _default_runs_dir()
all_runs = load_runs(runs_dir)
lab_runs = [r for r in all_runs if r.get("suite") == "lab"]
rolling = compute_rolling_latency_baseline(lab_runs, window=50)

with st.sidebar:
    st.subheader(t["settings"])
    st.caption(f"{t['runs_dir']}: `{runs_dir.as_posix()}` (env RUNS_DIR)")
    if learning:
        st.caption(t["runs_dir_tip"])

    mode = st.selectbox(t["mode"], ["text", "image"], index=0, help=t["mode_help"] if learning else None)
    sort = st.selectbox("sort", ["popular", "latest", "rating"], index=0)

    st.divider()

    st.subheader(t["engine_toggles"])
    if learning:
        st.caption(t["engine_toggles_help"])

    use_tfidf = st.checkbox(t["tfidf"], value=True, disabled=(mode == "image"))
    use_sbert = st.checkbox(t["sbert"], value=True)
    use_clip = st.checkbox(t["clip"], value=True, disabled=(mode == "text"))

    enabled_engines_single = {
        "tfidf": bool(use_tfidf),
        "sbert": bool(use_sbert),
        "clip": bool(use_clip),
    }

    st.divider()

    candidate_k = st.slider(
        t["candidate_k"],
        min_value=100,
        max_value=2000,
        value=700,
        step=100,
        help=t["candidate_k_help"] if learning else None,
    )
    debug_top_k = st.slider(
        t["debug_top_k"],
        min_value=5,
        max_value=80,
        value=20,
        step=5,
        help=t["debug_top_k_help"] if learning else None,
    )
    top_k_display = st.slider(
        t["preview_k"],
        min_value=5,
        max_value=50,
        value=10,
        step=5,
        help=t["preview_help"] if learning else None,
    )

    st.divider()

    st.subheader(t["rules"])
    if learning:
        st.caption(t["rules_tip"])

    low_results_threshold = st.number_input(
        t["low_results_threshold"],
        min_value=1,
        max_value=50,
        value=5,
        step=1,
        help=t["low_results_help"] if learning else None,
    )
    slow_absolute_ms = st.number_input(
        t["slow_absolute_ms"],
        min_value=200,
        max_value=20000,
        value=3000,
        step=100,
        help=t["slow_help"] if learning else None,
    )
    clip_weak_threshold = st.number_input(
        t["clip_weak_threshold"],
        min_value=0.0,
        max_value=1.0,
        value=0.55,
        step=0.01,
        help=t["clip_help"] if learning else None,
    )

    st.divider()

    st.subheader(t["rolling_title"])
    if learning:
        st.caption(t["rolling_help"])
    st.write(rolling)

query_text = st.text_input(
    t["query"],
    placeholder="예: 인셉션, 겨울왕국, 스파이더맨 ..." if lang == "ko" else "e.g., Inception, Frozen, Spider-Man ...",
    help=t["query_help"] if learning else None,
    disabled=(mode == "image"),
)
uploaded_image = st.file_uploader(
    t["image"],
    type=["jpg", "jpeg", "png", "webp"],
    help=t["image_help"] if learning else None,
    disabled=(mode == "text"),
)

col_btn1, col_btn2 = st.columns([1, 1])
with col_btn1:
    run_btn = st.button(t["run"], help=t["run_help"] if learning else None, use_container_width=True)
with col_btn2:
    run_ablation_btn = st.button(t["run_ablation"], help=t["run_ablation_help"] if learning else None, use_container_width=True)

if "last_results" not in st.session_state:
    st.session_state["last_results"] = []
if "last_latency_ms" not in st.session_state:
    st.session_state["last_latency_ms"] = None
if "last_error" not in st.session_state:
    st.session_state["last_error"] = None
if "last_debug" not in st.session_state:
    st.session_state["last_debug"] = {}
if "last_ablation" not in st.session_state:
    st.session_state["last_ablation"] = None


def _can_run() -> bool:
    if mode == "text":
        return bool((query_text or "").strip())
    return uploaded_image is not None


if run_btn:
    st.session_state["last_error"] = None
    if not _can_run():
        st.warning(t["warn_query"] if mode == "text" else t["warn_image"])
    else:
        try:
            results, latency_ms, dbg = run_query(
                mode=mode,
                query_text=(query_text or "").strip(),
                uploaded_image=uploaded_image,
                sort=sort,
                candidate_k=int(candidate_k),
                enabled_engines=enabled_engines_single,
                debug_top_k=int(debug_top_k),
            )
            st.session_state["last_results"] = results
            st.session_state["last_latency_ms"] = latency_ms
            st.session_state["last_debug"] = dbg
        except Exception as e:
            st.session_state["last_results"] = []
            st.session_state["last_latency_ms"] = None
            st.session_state["last_debug"] = {}
            st.session_state["last_error"] = str(e)

if run_ablation_btn:
    st.session_state["last_error"] = None
    if not _can_run():
        st.warning(t["warn_query"] if mode == "text" else t["warn_image"])
    else:
        try:
            ab = run_ablation_compare(
                mode=mode,
                query_text=(query_text or "").strip(),
                uploaded_image=uploaded_image,
                sort=sort,
                candidate_k=int(candidate_k),
                debug_top_k=int(debug_top_k),
                topk_eval=10,
            )
            st.session_state["last_ablation"] = ab
        except Exception as e:
            st.session_state["last_ablation"] = None
            st.session_state["last_error"] = str(e)

results: List[Dict[str, Any]] = st.session_state.get("last_results", [])
latency_ms = st.session_state.get("last_latency_ms", None)
err = st.session_state.get("last_error", None)
dbg: Dict[str, Any] = st.session_state.get("last_debug", {}) or {}
ablation: Optional[Dict[str, Any]] = st.session_state.get("last_ablation", None)
result_count = len(results) if results else 0

if err:
    st.error(err)

c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    st.subheader(t["results"])
with c2:
    st.metric(t["latency"], f"{latency_ms:.1f}" if latency_ms is not None else "-")
with c3:
    st.metric(t["count"], result_count)

engine_top = (dbg.get("engine_top") or {}) if isinstance(dbg, dict) else {}
fusion_method = dbg.get("fusion_method")

tabs = st.tabs(
    [
        t["tabs_explain"],
        t["tabs_retrieval"],
        t["tabs_pool"],
        t["tabs_fusion"],
        t["tabs_contrib"],
        t["tabs_final"],
        t["tabs_ablation"],
    ]
)

with tabs[0]:
    if learning:
        st.caption(t["purpose_explain"])
    _render_explain_card(results, dbg, t)

with tabs[1]:
    if learning:
        st.caption(t["purpose_retrieval"])
    st.markdown("### Engine Retrieval (Top-K)")
    st.caption(f"fusion_method = `{fusion_method}`")

    if fusion_method == "score_fusion":
        colA, colB = st.columns(2)
        with colA:
            st.markdown("**TF-IDF Top**")
            st.dataframe(engine_top.get("tfidf_top") or [], use_container_width=True)
        with colB:
            st.markdown("**SBERT Top**")
            st.dataframe(engine_top.get("sbert_top") or [], use_container_width=True)
    elif fusion_method == "rrf":
        colA, colB = st.columns(2)
        with colA:
            st.markdown("**CLIP Top**")
            st.dataframe(engine_top.get("clip_top") or [], use_container_width=True)
        with colB:
            st.markdown("**SBERT Top (restricted)**")
            st.dataframe(engine_top.get("sbert_top") or [], use_container_width=True)

        st.markdown("**Prompt → pseudo_query**")
        st.dataframe(engine_top.get("prompt_top") or [], use_container_width=True)
        st.write({"pseudo_query": dbg.get("pseudo_query")})
    else:
        st.info(t["retrieval_empty"])

with tabs[2]:
    if learning:
        st.caption(t["purpose_pool"])
    st.markdown("### Candidate Pool")
    counts = dbg.get("engine_counts") or {}
    st.write(counts)

    if "overlap_tfidf_sbert" in counts:
        cA, cB = st.columns(2)
        with cA:
            st.metric("union_ids", int(counts.get("union_ids", 0)))
        with cB:
            st.metric("overlap_tfidf_sbert", int(counts.get("overlap_tfidf_sbert", 0)))

    if dbg.get("cut_policy"):
        st.markdown("**RRF Cut Policy**")
        st.json(dbg.get("cut_policy"))

with tabs[3]:
    if learning:
        st.caption(t["purpose_fusion"])
    st.markdown("### Fusion")
    if fusion_method == "score_fusion":
        st.markdown("**Weights (after ablation)**")
        st.json(dbg.get("weights") or {})
        st.markdown("**Contribution formula**")
        st.code("contrib = weight * normalized_score", language="text")
    elif fusion_method == "rrf":
        st.markdown("**RRF Params**")
        st.json(dbg.get("rrf_params") or {})
        st.markdown("**Contribution formula**")
        st.code(
            "clip_term = w_clip/(k + clip_rank)\n"
            "sbert_term = w_sbert/(k + sbert_rank)\n"
            "rrf_score = clip_term + sbert_term",
            language="text",
        )
        st.markdown("**Fused Top**")
        st.dataframe(engine_top.get("fused_top") or [], use_container_width=True)
    else:
        st.info(t["fusion_empty"])

with tabs[4]:
    if learning:
        st.caption(t["purpose_contrib"])
    st.markdown("### Engine Contribution (Top)")
    contrib_top = _safe_get_contrib_top(dbg)
    if not contrib_top:
        st.info(t["contrib_empty"])
    else:
        ratio = _dominant_ratio(contrib_top)
        st.write({"dominant_ratio(topK)": ratio})
        st.dataframe(contrib_top, use_container_width=True)

with tabs[5]:
    if learning:
        st.caption(t["purpose_final"])
    st.markdown("### Final Results (Preview)")
    if results:
        st.dataframe(_result_preview(results, limit=int(top_k_display)), use_container_width=True)
        with st.expander(t["raw_debug"], expanded=False):
            st.json(dbg)
    else:
        st.info(t["no_results"])

with tabs[6]:
    if learning:
        st.caption(t["purpose_ablation"])
    st.markdown("### One-click Ablation Compare + Visualization")

    if not ablation:
        st.info(t["ablation_empty"])
    else:
        st.write({"mode": ablation.get("mode"), "topk_eval": ablation.get("topk_eval")})

        st.markdown(f"#### {t['quick_charts']}")
        chart_rows = _ablation_runs_to_chart_rows(ablation)
        if chart_rows:
            import pandas as pd

            df_chart = pd.DataFrame(chart_rows).set_index("label")

            cA, cB = st.columns(2)
            with cA:
                st.caption(t["latency_by_variant"])
                st.bar_chart(df_chart[["latency_ms"]])
            with cB:
                st.caption(t["count_by_variant"])
                st.bar_chart(df_chart[["result_count"]])
        else:
            st.info("No chart rows.")

        runs = ablation.get("runs") or []
        comps = ablation.get("comparisons") or []

        st.markdown(f"#### {t['runs']}")
        for r in runs:
            with st.expander(
                f"{r.get('label')}  |  latency={r.get('latency_ms'):.1f}ms  |  results={r.get('result_count')}",
                expanded=False,
            ):
                st.write({"enabled_engines": r.get("enabled_engines")})
                st.dataframe(r.get("results_preview") or [], use_container_width=True)

        st.markdown(f"#### {t['comparisons']}")
        if not comps:
            st.info("No comparisons available.")
        else:
            for c in comps:
                base = c.get("base")
                other = c.get("other")
                st.markdown(f"**{other} vs {base}**")
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("overlap(topK)", int(c.get("overlap", 0)))
                with m2:
                    st.metric("jaccard(topK)", f"{float(c.get('jaccard', 0.0)):.3f}")
                with m3:
                    st.metric("top1_same", "YES" if c.get("top1_same") else "NO")

                st.dataframe(c.get("diff") or [], use_container_width=True)

        st.divider()
        st.markdown(f"#### {t['trend']}")
        if learning:
            st.caption(t["trend_help"])

        trend_rows = _load_ablation_trend_from_saved_runs(runs_dir, mode=ablation.get("mode"), limit=50)
        if not trend_rows:
            st.info("No saved ablation_summary yet. Save a few runs first.")
        else:
            import pandas as pd

            df_trend = pd.DataFrame(trend_rows).set_index("created_at")
            st.line_chart(df_trend)

            with st.expander(t["raw_trend_rows"], expanded=False):
                st.dataframe(df_trend.reset_index(), use_container_width=True)

st.divider()
st.subheader(t["save_title"])
if learning:
    st.caption(t["save_help"])

notes = st.text_area(
    t["notes"],
    height=90,
    placeholder="관찰 / 가설 / 이상 징후 등 메모" if lang == "ko" else "Notes, observations, suspicious behavior, hypotheses...",
    help=t["notes_help"] if learning else None,
)

colA, colB = st.columns([1, 2])
with colA:
    save_btn = st.button(t["save"], type="primary", disabled=(latency_ms is None))
with colB:
    if learning:
        st.caption(t["auto_tag_tip"])

if save_btn:
    contrib_top = _safe_get_contrib_top(dbg)
    contrib_summary = {
        "dominant_ratio_topK": _dominant_ratio(contrib_top) if isinstance(contrib_top, list) else {},
        "top1": contrib_top[0] if isinstance(contrib_top, list) and len(contrib_top) > 0 else None,
    }

    ablation_summary = None
    if ablation:
        ablation_summary = {
            "mode": ablation.get("mode"),
            "topk_eval": ablation.get("topk_eval"),
            "runs": [
                {
                    "label": r.get("label"),
                    "enabled_engines": r.get("enabled_engines"),
                    "latency_ms": r.get("latency_ms"),
                    "result_count": r.get("result_count"),
                    "top_ids": r.get("top_ids"),
                }
                for r in (ablation.get("runs") or [])
            ],
            "comparisons": [
                {
                    "base": c.get("base"),
                    "other": c.get("other"),
                    "topk": c.get("topk"),
                    "jaccard": c.get("jaccard"),
                    "overlap": c.get("overlap"),
                    "top1_same": c.get("top1_same"),
                }
                for c in (ablation.get("comparisons") or [])
            ],
        }

    signals_summary = {
        "fusion_method": dbg.get("fusion_method"),
        "search_type": dbg.get("search_type"),
        "engine_counts": dbg.get("engine_counts"),
        "weights": dbg.get("weights"),
        "rrf_params": dbg.get("rrf_params"),
        "pseudo_query": dbg.get("pseudo_query"),
        "cut_policy": dbg.get("cut_policy"),
        "contrib_summary": contrib_summary,
        "ablation_summary": ablation_summary,
    }

    session = {
        "session_id": f"s_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "suite": "lab",
        "query_text": (query_text or "").strip() if mode == "text" else "",
        "image_name": dbg.get("image_name") if mode == "image" else None,
        "engine_name": "hybrid",
        "latency_ms": float(latency_ms) if latency_ms is not None else None,
        "result_count": int(result_count),
        "top_preview": _result_preview(results, limit=10),
        "signals": signals_summary,
        "error": None,
    }

    tags, reasons, summary = auto_tag_failure(
        session,
        rolling_latency=rolling,
        low_results_threshold=int(low_results_threshold),
        slow_absolute_ms=int(slow_absolute_ms),
        clip_weak_threshold=float(clip_weak_threshold),
    )

    run_json: Dict[str, Any] = {
        "suite": "lab",
        "created_at": _now_iso(),
        "engine_name": "hybrid",
        "query_text": (query_text or "").strip() if mode == "text" else "",
        "image_name": dbg.get("image_name") if mode == "image" else None,
        "notes": notes,
        "hit@1": None,
        "hit@5": None,
        "hit@10": None,
        "mean_rank": None,
        "latency_ms": float(latency_ms) if latency_ms is not None else None,
        "result_count": int(result_count),
        "sessions": [session],
        "failures": [],
        "signals_summary": {
            "tag_counts": summary.get("tag_counts", {}),
            "top_tags": summary.get("top_tags", []),
            "rolling_latency": summary.get("rolling_latency", {}),
            "hybrid_debug": signals_summary,
        },
    }

    if tags:
        run_json["failures"].append(
            {
                "session_id": session["session_id"],
                "tags": tags,
                "reasons": reasons,
            }
        )

    fp = save_run(run_json, runs_dir)
    st.success(f"{t['saved']}: {fp.as_posix()}")
    st.write({"tags": tags, "reasons": reasons})