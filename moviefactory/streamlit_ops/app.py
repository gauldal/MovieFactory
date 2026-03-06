# moviefactory/streamlit_ops/app.py
from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st


# ===========================
# Shared state (Language / Learning mode)
# ===========================
def _init_shared_state() -> None:
    if "ui_lang" not in st.session_state:
        st.session_state["ui_lang"] = "ko"  # "ko" | "en"
    if "learning_mode" not in st.session_state:
        st.session_state["learning_mode"] = True


def _t() -> Dict[str, str]:
    lang = st.session_state.get("ui_lang", "ko")

    if lang == "en":
        return {
            "app_title": "MovieFactory Ops Console",
            "app_subtitle": (
                "A learning-friendly console for running hybrid search experiments "
                "in Query Lab and monitoring search quality / latency / failures "
                "in Quality Monitor."
            ),
            "lang_label": "Language",
            "learning_label": "Learning mode",
            "learning_help": (
                "Turn this on to show more explanations, purpose notes, and glossary-style hints. "
                "This is especially useful while you are still learning the Streamlit dashboard structure."
            ),
            "section_guide": "Quick Start (3 steps)",
            "guide_intro": (
                "Think of this console as a small operating room for your search system.\n"
                "You first **run and inspect** experiments in Query Lab,\n"
                "then **save** runs as JSON logs,\n"
                "and finally **monitor trends** in Quality Monitor."
            ),
            "card1_title": "1) Run a search in Query Lab",
            "card1_body": (
                "Enter a text query or upload an image, then run the search.\n"
                "Use the inspector tabs to see engine retrieval, candidate pool, fusion, "
                "and contribution."
            ),
            "card2_title": "2) Save the run as JSON",
            "card2_body": (
                "When you press Save run, the current experiment is stored as a JSON file "
                "in the runs folder. This JSON becomes the source of truth for later analysis."
            ),
            "card3_title": "3) Monitor trends and reasons",
            "card3_body": (
                "Quality Monitor aggregates saved runs into Eval Trend, Ops Trend, "
                "and Failure Analysis so you can see what changed and why."
            ),
            "open_pages": "Open pages",
            "open_query_lab": "Go to Query Lab",
            "open_quality_monitor": "Go to Quality Monitor",
            "why_this": "What this console is for",
            "why_this_body": (
                "You built a run-log driven operations console for search quality.\n"
                "It supports both experimentation and monitoring:\n"
                "- Query Lab = run / inspect / compare\n"
                "- Quality Monitor = aggregate / trend / diagnose"
            ),
            "data_health": "Data health (runs folder)",
            "runs_dir": "runs dir",
            "total_files": "Total run files",
            "eval_files": "Eval runs",
            "lab_files": "Lab runs",
            "latest_run": "Latest run",
            "schema": "Run JSON schema (compact)",
            "schema_body": (
                "- **suite**: `eval` (accuracy) or `lab` (ops / experiment)\n"
                "- **created_at**: run timestamp (ISO)\n"
                "- **engine_name**: engine identifier\n"
                "- **query_text**: input query\n"
                "- **accuracy metrics**: `hit@1`, `hit@5`, `hit@10`, `mean_rank` (mainly eval)\n"
                "- **ops metrics**: `latency_ms`, `result_count` (mainly lab)\n"
                "- **failures**: list of `{session_id, tags, reasons}`\n"
                "  - `reasons` explain which rule/threshold/evidence triggered the tag"
            ),
            "tips": "Tips",
            "tips_body": (
                "- If pages look empty, check whether `RUNS_DIR` points to the actual runs folder.\n"
                "- The first run can be slow because models and caches may still be loading.\n"
                "- Use Learning mode ON while understanding the system, then switch to EN mode "
                "for cleaner portfolio screenshots."
            ),
            "portfolio_tip": (
                "Portfolio tip: a pair of screenshots works well — "
                "Learning mode ON (to show intent and design thinking) and "
                "EN mode (for a cleaner product-style screenshot)."
            ),
        }

    return {
        "app_title": "MovieFactory 운영 콘솔 (Streamlit)",
        "app_subtitle": (
            "하이브리드 검색을 실험하는 Query Lab과, "
            "검색 품질 / 속도 / 실패 유형을 모니터링하는 Quality Monitor를 "
            "한 곳에서 연결해 보는 학습 친화형 운영 화면입니다."
        ),
        "lang_label": "언어",
        "learning_label": "학습 모드",
        "learning_help": (
            "학습 모드를 켜면 각 화면이 왜 필요한지, 무엇을 보면 되는지, "
            "용어가 무엇을 뜻하는지까지 더 자세한 설명을 보여줍니다."
        ),
        "section_guide": "빠른 사용법 (3단계)",
        "guide_intro": (
            "이 콘솔은 검색 시스템을 운영하는 작은 통제실이라고 생각하면 돼요.\n"
            "먼저 Query Lab에서 **실행하고 확인**하고,\n"
            "그다음 Save run으로 **기록을 남기고**,\n"
            "마지막으로 Quality Monitor에서 **추세와 원인**을 봅니다."
        ),
        "card1_title": "1) Query Lab에서 검색 실행",
        "card1_body": (
            "텍스트 검색어를 넣거나 이미지를 업로드한 뒤 Run을 눌러요.\n"
            "그다음 Inspector 탭에서 엔진별 retrieval / candidate pool / fusion / "
            "contribution을 확인해요."
        ),
        "card2_title": "2) Save run으로 실행 기록 저장",
        "card2_body": (
            "Save run을 누르면 현재 실험이 runs 폴더에 JSON으로 저장돼요.\n"
            "이 JSON이 나중에 품질 추이와 문제 분석의 원천 데이터가 됩니다."
        ),
        "card3_title": "3) Quality Monitor에서 추세와 근거 확인",
        "card3_body": (
            "Quality Monitor는 저장된 run을 집계해서\n"
            "- 정확도 변화(Eval Trend)\n"
            "- 속도 / 결과 수 변화(Ops Trend)\n"
            "- 실패 태그와 근거(Failure Analysis)\n"
            "를 보여줍니다."
        ),
        "open_pages": "페이지 열기",
        "open_query_lab": "Query Lab로 이동",
        "open_quality_monitor": "Quality Monitor로 이동",
        "why_this": "이 콘솔이 하는 일",
        "why_this_body": (
            "내가 만든 것은 단순한 대시보드가 아니라,\n"
            "**run 로그 기반 검색 운영 콘솔**입니다.\n"
            "즉,\n"
            "- Query Lab = 실험하고 검증하는 곳\n"
            "- Quality Monitor = 누적된 run을 관찰하고 해석하는 곳\n"
            "으로 역할이 나뉘어 있어요."
        ),
        "data_health": "데이터 상태 (runs 폴더)",
        "runs_dir": "runs 폴더",
        "total_files": "전체 run 파일 수",
        "eval_files": "Eval 실행 수",
        "lab_files": "Lab 실행 수",
        "latest_run": "가장 최근 run",
        "schema": "Run JSON 스키마 (요약)",
        "schema_body": (
            "- **suite**: `eval`(정확도) / `lab`(운영·실험)\n"
            "- **created_at**: 실행 시각(ISO)\n"
            "- **engine_name**: 엔진 이름\n"
            "- **query_text**: 입력 쿼리\n"
            "- **정확도 지표**: `hit@1`, `hit@5`, `hit@10`, `mean_rank` (주로 eval)\n"
            "- **운영 지표**: `latency_ms`, `result_count` (주로 lab)\n"
            "- **failures**: `{session_id, tags, reasons}` 리스트\n"
            "  - `reasons`에는 어떤 규칙/임계치/증거 때문에 태그가 붙었는지가 들어가요."
        ),
        "tips": "팁",
        "tips_body": (
            "- 화면이 비면 `RUNS_DIR`이 실제 runs 폴더를 가리키는지 먼저 확인하세요.\n"
            "- 첫 실행은 모델 로딩 / 캐시 준비 때문에 느릴 수 있어요.\n"
            "- 학습 모드 ON으로 구조를 이해한 뒤, EN 모드로 바꿔서 포트폴리오 스크린샷을 가져가면 좋아요."
        ),
        "portfolio_tip": (
            "포트폴리오 팁: 학습 모드 ON 스크린샷(설계 의도 설명)과 "
            "EN 모드 스크린샷(깔끔한 UI)을 둘 다 넣으면 이해도와 제품성이 함께 보입니다."
        ),
    }


# ===========================
# Runs data health
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


def _load_runs_quick(runs_dir: Path, limit: int = 200) -> List[Dict[str, Any]]:
    if not runs_dir.exists():
        return []

    files = sorted(runs_dir.glob("*.json"))
    if len(files) > limit:
        files = files[-limit:]

    out: List[Dict[str, Any]] = []
    for fp in files:
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
            d["_file"] = str(fp)
            out.append(d)
        except Exception:
            continue
    return out


def _infer_suite(r: Dict[str, Any]) -> str:
    s = r.get("suite")
    if isinstance(s, str):
        ss = s.strip().lower()
        if ss in ("lab",):
            return "lab"
        if ss in ("eval", "intent", "regression"):
            return "eval"

    if any(k in r for k in ["latency_ms", "result_count"]):
        return "lab"
    if "metrics" in r and isinstance(r["metrics"], dict) and any(k in r["metrics"] for k in ["hit@1", "hit@5", "hit@10"]):
        return "eval"
    if any(k in r for k in ["hit@1", "hit@5", "hit@10", "mean_rank"]):
        return "eval"
    return "eval"


def _created_at_str(r: Dict[str, Any]) -> str:
    return str(
        r.get("created_at")
        or r.get("run_at")
        or r.get("timestamp")
        or r.get("ts")
        or r.get("meta", {}).get("created_at")
        or ""
    )


# ===========================
# Page
# ===========================
_init_shared_state()
t = _t()
lang = st.session_state["ui_lang"]
learning = st.session_state["learning_mode"]

st.set_page_config(page_title="MovieFactory Ops Console", layout="wide")

with st.sidebar:
    st.subheader("Settings")
    lang_sel = st.selectbox(
        t["lang_label"],
        options=["ko", "en"],
        index=0 if st.session_state["ui_lang"] == "ko" else 1,
        format_func=lambda x: "한국어" if x == "ko" else "English",
    )
    st.session_state["ui_lang"] = lang_sel

    learning_sel = st.checkbox(
        t["learning_label"],
        value=st.session_state["learning_mode"],
        help=t["learning_help"],
    )
    st.session_state["learning_mode"] = learning_sel

# refresh translation after sidebar changes
t = _t()
lang = st.session_state["ui_lang"]
learning = st.session_state["learning_mode"]

st.title(t["app_title"])
st.info(t["app_subtitle"])

if learning:
    st.subheader(t["why_this"])
    st.markdown(t["why_this_body"])

    st.subheader(t["section_guide"])
    st.markdown(t["guide_intro"])

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"**{t['card1_title']}**")
        st.write(t["card1_body"])
    with c2:
        st.markdown(f"**{t['card2_title']}**")
        st.write(t["card2_body"])
    with c3:
        st.markdown(f"**{t['card3_title']}**")
        st.write(t["card3_body"])

st.divider()

st.subheader(t["open_pages"])
p1, p2 = st.columns(2)
with p1:
    st.page_link("pages/2_Query_Lab.py", label=t["open_query_lab"], icon="🔬")
with p2:
    st.page_link("pages/1_Quality_Monitor.py", label=t["open_quality_monitor"], icon="📈")

st.divider()

st.subheader(t["data_health"])
runs_dir = _default_runs_dir()
runs = _load_runs_quick(runs_dir)

total = 0
eval_n = 0
lab_n = 0
latest: Optional[Dict[str, Any]] = None

if runs_dir.exists():
    json_files = sorted(runs_dir.glob("*.json"))
    total = len(json_files)

    if runs:
        runs_sorted = sorted(runs, key=lambda r: _created_at_str(r))
        latest = runs_sorted[-1] if runs_sorted else None

    for r in runs:
        s = _infer_suite(r)
        if s == "lab":
            lab_n += 1
        else:
            eval_n += 1

m1, m2, m3, m4 = st.columns(4)
m1.metric(t["runs_dir"], runs_dir.as_posix())
m2.metric(t["total_files"], total)
m3.metric(t["eval_files"], eval_n)
m4.metric(t["lab_files"], lab_n)

if latest:
    with st.expander(t["latest_run"], expanded=False):
        st.write(
            {
                "created_at": _created_at_str(latest),
                "suite": _infer_suite(latest),
                "engine_name": latest.get("engine_name") or latest.get("engine") or "(unknown)",
                "query_text": latest.get("query_text") or latest.get("query") or latest.get("text") or "",
                "file": latest.get("_file"),
            }
        )

st.divider()

st.subheader(t["schema"])
st.markdown(t["schema_body"])

st.divider()

st.subheader(t["tips"])
st.markdown(t["tips_body"])

if learning:
    st.caption(t["portfolio_tip"])