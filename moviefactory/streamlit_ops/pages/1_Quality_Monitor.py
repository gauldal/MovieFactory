# pages/1_Quality_Monitor.py
from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st


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
        "title": "품질 모니터 (운영 대시보드)",
        "subtitle": "저장된 run을 바탕으로 **정확도(품질)** / **속도(운영)** / **문제 유형(실패 태그)** 을 한 화면에서 봅니다.",
        "data": "데이터",
        "runs_dir": "runs 폴더",
        "include_lab": "실험(lab) 실행 기록 포함",
        "include_lab_help": "기본은 lab run 숨김. 체크하면 lab도 함께 표시합니다.",
        "filter_eval_by_engine": "정확도 탭에서 엔진 필터 적용",
        "filter_eval_by_engine_help": "eval run은 engine 정보가 없을 수 있어 기본 OFF가 안전합니다.",
        "filters": "필터",
        "suite": "실행 종류(suite)",
        "suite_help": "eval=정확도 평가 기록, lab=운영·실험 기록",
        "engine": "엔진(engine)",
        "engine_help": "엔진/모델/설정 이름. eval run은 없을 수 있어 (unknown)로 표시됩니다.",
        "trend": "📈 변화 추이(Trend)",
        "eval_tab": "① 정확도 변화(Accuracy)",
        "ops_tab": "② 속도·결과 변화(Ops)",
        "kpi": "보고 싶은 지표(KPI)",
        "kpi_help_eval": "hit@k / mean_rank 같은 정확도 지표를 선택합니다.",
        "kpi_help_ops": "latency_ms / result_count 같은 운영 지표를 선택합니다.",
        "rolling_window": "이동평균(rolling mean) window",
        "rolling_help": "그래프가 들쭉날쭉할 때 평균선을 같이 그려 추이를 보기 쉽게 합니다.",
        "eval_explain": (
            "이 탭은 **정확도 지표**를 시간 순서로 보는 화면입니다.\n\n"
            "- **hit@1 / hit@5 / hit@10**: 정답이 상위 K개 안에 포함되는 비율\n"
            "- **mean_rank**: 정답이 평균 몇 번째에 위치했는지\n\n"
            "즉, 모델 / 가중치 / 필터를 바꾼 뒤 검색 품질이 좋아졌는지 확인하는 용도입니다."
        ),
        "ops_explain": (
            "이 탭은 **운영 지표**를 시간 순서로 보는 화면입니다.\n\n"
            "- **latency_ms**: 검색 1회 수행 시간\n"
            "- **result_count**: 결과 개수\n\n"
            "즉, 너무 느려졌는지, 결과가 갑자기 줄었는지 같은 운영 이상을 확인하는 용도입니다."
        ),
        "recent_eval": "최근 eval 실행 기록",
        "recent_lab": "최근 lab 실행 기록",
        "no_eval": "eval 실행 기록이 없어.",
        "no_lab": "lab 실행 기록이 없어. (Query Lab에서 Save run으로 lab run을 만들어줘)",
        "empty_kpi": "선택한 KPI 데이터가 비어 있어.",
        "fail_title": "🚨 자동 문제 유형 분석(Failure Analysis)",
        "fail_explain": (
            "실행 중 발생한 문제를 **태그(tag)** 로 자동 분류한 결과를 집계합니다.\n"
            "최근 어떤 문제가 늘었는지 보고, 클릭해서 근거(reasons)까지 확인할 수 있습니다."
        ),
        "drilldown": "태그별 상세 보기(drill-down)",
        "drilldown_help": "태그를 선택하면 해당 태그가 붙은 세션만 필터링해서 보여줍니다.",
        "fail_list": "실패 세션 리스트",
        "fail_detail": "실패 상세(근거 보기)",
        "file": "파일(file)",
        "file_help": "실패가 기록된 run JSON 파일",
        "session_id": "세션 ID(session_id)",
        "session_help": "한 번의 run 안에서도 여러 session이 있을 수 있어 식별용으로 저장됩니다.",
        "reasons_full": "근거(reasons) 전체",
        "raw_failure": "failure 원본",
        "raw_run": "run 원본",
        "warn_no_runs": "runs 폴더에 *.json 이 없거나 로딩에 실패했어. RUNS_DIR 경로를 확인해줘.",
        "glossary_title": "용어 풀이 (Glossary)",
        "glossary_body": (
            "- **suite**: 실행 기록 종류 (eval=정확도 평가, lab=운영·실험 측정)\n"
            "- **run**: 한 번 실행한 기록(JSON 파일 1개)\n"
            "- **KPI**: 보고 싶은 핵심 지표\n"
            "- **Trend**: 시간 흐름에 따른 변화\n"
            "- **drill-down**: 항목을 눌러 상세로 내려가 보기\n"
        ),
        "ops_reason_title": "운영 지표가 필요한 이유",
        "ops_reason_body": (
            "- 정확도(hit@k)가 좋아도 **너무 느리면** 실제 서비스에서는 불만이 생겨요.\n"
            "- 결과 개수(result_count)가 갑자기 줄면 **필터/인덱스/데이터 문제**일 수 있어요.\n"
            "- 그래서 Ops Trend는 ‘서비스 건강 상태’를 보는 용도예요."
        ),
    }

    en = {
        "title": "Quality Monitor",
        "subtitle": "Review saved runs to monitor **accuracy**, **latency**, and **failure tags** in one place.",
        "data": "Data",
        "runs_dir": "runs dir",
        "include_lab": "Include lab runs",
        "include_lab_help": "Lab runs are hidden by default.",
        "filter_eval_by_engine": "Filter Eval Trend by engine",
        "filter_eval_by_engine_help": "Eval runs may not have engine metadata, so OFF is safer by default.",
        "filters": "Filters",
        "suite": "suite",
        "suite_help": "eval=accuracy runs, lab=ops / experiment runs",
        "engine": "engine",
        "engine_help": "Engine / model / setting identifier. Eval runs may show (unknown).",
        "trend": "📈 Trend",
        "eval_tab": "① Accuracy Trend",
        "ops_tab": "② Ops Trend",
        "kpi": "KPI",
        "kpi_help_eval": "Choose an accuracy metric such as hit@k or mean_rank.",
        "kpi_help_ops": "Choose an ops metric such as latency_ms or result_count.",
        "rolling_window": "Rolling mean window",
        "rolling_help": "Adds a smoothed line when the chart is noisy.",
        "eval_explain": (
            "This tab shows **accuracy metrics** over time.\n\n"
            "- **hit@1 / hit@5 / hit@10**: whether the correct answer appears within top K\n"
            "- **mean_rank**: the average position of the correct answer\n\n"
            "Use this to see whether quality improved or regressed after a model / weight / filter change."
        ),
        "ops_explain": (
            "This tab shows **operational metrics** over time.\n\n"
            "- **latency_ms**: time taken per search\n"
            "- **result_count**: number of retrieved results\n\n"
            "Use this to see whether the system became slower or started returning fewer results."
        ),
        "recent_eval": "Recent eval runs",
        "recent_lab": "Recent lab runs",
        "no_eval": "No eval runs found.",
        "no_lab": "No lab runs found. Save a run in Query Lab first.",
        "empty_kpi": "Selected KPI is empty.",
        "fail_title": "🚨 Failure Analysis",
        "fail_explain": (
            "This section aggregates automatically tagged failure cases.\n"
            "You can see which issue types increased recently and inspect the reasons behind each tag."
        ),
        "drilldown": "Tag drill-down",
        "drilldown_help": "Select a tag to filter only sessions that contain it.",
        "fail_list": "Failure sessions",
        "fail_detail": "Failure detail",
        "file": "file",
        "file_help": "Run JSON file that contains the failure record",
        "session_id": "session_id",
        "session_help": "Identifier for a session inside a run",
        "reasons_full": "reasons (full)",
        "raw_failure": "failure object (raw)",
        "raw_run": "run json (raw)",
        "warn_no_runs": "No run JSON files were found or loading failed. Check RUNS_DIR.",
        "glossary_title": "Glossary",
        "glossary_body": (
            "- **suite**: type of run (`eval` = accuracy evaluation, `lab` = ops / experiment)\n"
            "- **run**: one execution record stored as JSON\n"
            "- **KPI**: the key metric you want to inspect\n"
            "- **Trend**: how a metric changes over time\n"
            "- **drill-down**: click or filter to inspect details"
        ),
        "ops_reason_title": "Why ops metrics matter",
        "ops_reason_body": (
            "- Even if accuracy is good, the product feels broken when latency becomes too high.\n"
            "- If result_count suddenly drops, there may be a filtering, indexing, or data issue.\n"
            "- So Ops Trend is used to monitor overall service health."
        ),
    }

    return ko if lang == "ko" else en


# ===========================
# Path / IO
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
        return str(
            r.get("created_at")
            or r.get("run_at")
            or r.get("timestamp")
            or r.get("ts")
            or r.get("meta", {}).get("created_at")
            or ""
        )

    runs.sort(key=key_fn)
    return runs


# ===========================
# Robust extraction
# ===========================
def _dig(d: Dict[str, Any], path: str) -> Any:
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _first_non_null(d: Dict[str, Any], keys: List[str]) -> Any:
    for k in keys:
        v = _dig(d, k) if "." in k else d.get(k)
        if v is not None:
            return v
    return None


def _infer_suite(r: Dict[str, Any]) -> str:
    suite = _first_non_null(r, ["suite", "meta.suite", "kind"])
    if isinstance(suite, str) and suite.strip():
        s = suite.strip().lower()
        if s in ("eval", "intent", "regression"):
            return "eval"
        if s == "lab":
            return "lab"

    hit_candidates = [
        "hit@1", "hit@5", "hit@10",
        "hit_1", "hit_5", "hit_10",
        "hit1", "hit5", "hit10",
        "hit_at_1", "hit_at_5", "hit_at_10",
        "metrics.hit@1", "metrics.hit@5", "metrics.hit@10",
        "metrics.hit_1", "metrics.hit_5", "metrics.hit_10",
        "metrics.hit1", "metrics.hit5", "metrics.hit10",
    ]
    for k in hit_candidates:
        if _first_non_null(r, [k]) is not None:
            return "eval"

    if _first_non_null(r, ["latency_ms", "latency", "result_count", "results_count", "metrics.latency_ms"]) is not None:
        return "lab"

    return "eval"


def _extract_created_at(r: Dict[str, Any]) -> Any:
    return _first_non_null(r, ["created_at", "run_at", "timestamp", "ts", "meta.created_at", "meta.run_at"])


def _extract_engine(r: Dict[str, Any]) -> Optional[str]:
    v = _first_non_null(r, ["engine_name", "engine", "meta.engine_name", "meta.engine", "model", "config.engine"])
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def _extract_query(r: Dict[str, Any]) -> str:
    v = _first_non_null(r, ["query_text", "query", "text", "meta.query_text", "meta.query"])
    return "" if v is None else str(v)


def _extract_metric(r: Dict[str, Any], key: str) -> Any:
    candidates = [key, f"metrics.{key}"]

    alias_map = {
        "hit@1": ["hit_1", "hit1", "hit_at_1"],
        "hit@5": ["hit_5", "hit5", "hit_at_5"],
        "hit@10": ["hit_10", "hit10", "hit_at_10"],
        "mean_rank": ["meanrank", "rank_mean"],
        "latency_ms": ["latency", "metrics.latency"],
        "result_count": ["results_count", "metrics.result_count"],
    }
    for alias in alias_map.get(key, []):
        candidates.append(alias)
        candidates.append(f"metrics.{alias}")

    return _first_non_null(r, candidates)


def _extract_failures(r: Dict[str, Any]) -> List[Dict[str, Any]]:
    v = _first_non_null(r, ["failures", "failure", "meta.failures"])
    if isinstance(v, list):
        return [x for x in v if isinstance(x, dict)]
    if isinstance(v, dict):
        return [v]
    return []


# ===========================
# Build dataframe
# ===========================
def _runs_to_df(runs: List[Dict[str, Any]]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for r in runs:
        row = {
            "created_at": _extract_created_at(r),
            "suite": _infer_suite(r),
            "engine": _extract_engine(r) or "(unknown)",
            "query": _extract_query(r),
            "hit@1": _extract_metric(r, "hit@1"),
            "hit@5": _extract_metric(r, "hit@5"),
            "hit@10": _extract_metric(r, "hit@10"),
            "mean_rank": _extract_metric(r, "mean_rank"),
            "latency_ms": _extract_metric(r, "latency_ms"),
            "result_count": _extract_metric(r, "result_count"),
            "_file": r.get("_file"),
            "_raw": r,
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        df["created_at"] = df["created_at"].astype(str)
    return df


# ===========================
# Page UI
# ===========================
_ensure_shared_state()
lang = st.session_state["ui_lang"]
learning = st.session_state["learning_mode"]
t = _copy(lang)

st.set_page_config(page_title="Quality Monitor", layout="wide")

st.title(t["title"])
st.info(t["subtitle"])

runs_dir = _default_runs_dir()
runs = load_runs(runs_dir)

if not runs:
    st.warning(t["warn_no_runs"])

df = _runs_to_df(runs)

with st.sidebar:
    st.subheader(t["data"])
    st.caption(f"{t['runs_dir']}: `{runs_dir.as_posix()}`")

    include_lab = st.checkbox(t["include_lab"], value=False, help=t["include_lab_help"] if learning else None)
    filter_eval_by_engine = st.checkbox(
        t["filter_eval_by_engine"],
        value=False,
        help=t["filter_eval_by_engine_help"] if learning else None,
    )

    st.divider()
    st.subheader(t["filters"])

    suites_all = sorted(df["suite"].dropna().astype(str).unique().tolist()) if not df.empty else []
    suite_filter = st.multiselect(
        t["suite"],
        options=suites_all,
        default=suites_all if include_lab else [s for s in suites_all if s != "lab"],
        help=t["suite_help"] if learning else None,
    )

    engines_all = sorted(df["engine"].dropna().astype(str).unique().tolist()) if not df.empty else []
    engine_filter = st.multiselect(
        t["engine"],
        options=engines_all,
        default=engines_all,
        help=t["engine_help"] if learning else None,
    )

df_suite = df.copy()
if suite_filter:
    df_suite = df_suite[df_suite["suite"].isin(suite_filter)]

df_ops = df_suite.copy()
if engine_filter:
    df_ops = df_ops[df_ops["engine"].astype(str).isin(engine_filter)]

# ===========================
# Trend
# ===========================
st.subheader(t["trend"])
tab_eval, tab_ops = st.tabs([t["eval_tab"], t["ops_tab"]])

with tab_eval:
    if learning:
        st.markdown(t["eval_explain"])
        with st.expander(t["glossary_title"], expanded=False):
            st.markdown(t["glossary_body"])

    eval_df = df_suite[df_suite["suite"] == "eval"].copy()
    if filter_eval_by_engine and engine_filter:
        eval_df = eval_df[eval_df["engine"].astype(str).isin(engine_filter)]

    if eval_df.empty:
        st.info(t["no_eval"])
    else:
        metric = st.selectbox(
            t["kpi"],
            ["hit@1", "hit@5", "hit@10", "mean_rank"],
            index=1,
            help=t["kpi_help_eval"] if learning else None,
        )

        plot_df = eval_df[["created_at", metric]].dropna()
        if plot_df.empty:
            st.info(t["empty_kpi"])
        else:
            plot_df = plot_df.sort_values("created_at").set_index("created_at")
            st.line_chart(plot_df[metric])

        with st.expander(t["recent_eval"], expanded=False):
            st.dataframe(
                eval_df.sort_values("created_at", ascending=False)[
                    ["created_at", "engine", "query", "hit@1", "hit@5", "hit@10", "mean_rank", "_file"]
                ].head(50),
                use_container_width=True,
            )

with tab_ops:
    if learning:
        st.markdown(t["ops_explain"])
        with st.expander(t["ops_reason_title"], expanded=False):
            st.markdown(t["ops_reason_body"])

    lab_df = df_ops[df_ops["suite"] == "lab"].copy()
    if lab_df.empty:
        st.info(t["no_lab"])
    else:
        kpi = st.selectbox(
            t["kpi"],
            ["latency_ms", "result_count"],
            index=0,
            help=t["kpi_help_ops"] if learning else None,
        )
        window = st.slider(
            t["rolling_window"],
            min_value=1,
            max_value=30,
            value=10,
            step=1,
            help=t["rolling_help"] if learning else None,
        )

        plot_df = lab_df[["created_at", kpi]].dropna()
        if plot_df.empty:
            st.info(t["empty_kpi"])
        else:
            plot_df = plot_df.sort_values("created_at").set_index("created_at")
            rolling_col = f"{kpi}_rolling_mean_{window}"
            plot_df[rolling_col] = plot_df[kpi].rolling(window=window, min_periods=1).mean()
            st.line_chart(plot_df[[kpi, rolling_col]])

        with st.expander(t["recent_lab"], expanded=False):
            st.dataframe(
                lab_df.sort_values("created_at", ascending=False)[
                    ["created_at", "engine", "query", "latency_ms", "result_count", "_file"]
                ].head(50),
                use_container_width=True,
            )

st.divider()

# ===========================
# Failure Analysis
# ===========================
st.subheader(t["fail_title"])
if learning:
    st.markdown(t["fail_explain"])

fail_rows: List[Dict[str, Any]] = []
for r in runs:
    file_path = r.get("_file")
    for f in _extract_failures(r):
        tags = f.get("tags") or []
        reasons = f.get("reasons") or []
        session_id = f.get("session_id") or ""
        fail_rows.append(
            {
                "created_at": _extract_created_at(r),
                "engine": _extract_engine(r) or "(unknown)",
                "query": _extract_query(r),
                "file": file_path,
                "session_id": session_id,
                "tags": tags,
                "reasons": reasons,
                "_failure": f,
                "_run": r,
            }
        )

fail_df = pd.DataFrame(fail_rows)

if fail_df.empty:
    st.info("No failure tags found.")
else:
    all_tags: List[str] = []
    for tags in fail_df["tags"]:
        if isinstance(tags, list):
            all_tags.extend([str(x) for x in tags])

    unique_tags = sorted(set(all_tags))
    selected_tag = st.selectbox(
        t["drilldown"],
        options=["(all)"] + unique_tags,
        index=0,
        help=t["drilldown_help"] if learning else None,
    )

    show_df = fail_df.copy()
    if selected_tag != "(all)":
        show_df = show_df[show_df["tags"].apply(lambda xs: isinstance(xs, list) and selected_tag in xs)]

    st.subheader(t["fail_list"])
    st.dataframe(
        show_df[["created_at", "engine", "query", "session_id", "tags", "file"]],
        use_container_width=True,
    )

    st.subheader(t["fail_detail"])
    for _, row in show_df.head(20).iterrows():
        label = f"{row['created_at']} | {row['engine']} | {row['session_id']}"
        with st.expander(label, expanded=False):
            st.write({t["file"]: row["file"], t["session_id"]: row["session_id"]})
            st.write({"tags": row["tags"]})
            st.write({t["reasons_full"]: row["reasons"]})

            with st.expander(t["raw_failure"], expanded=False):
                st.json(row["_failure"])
            with st.expander(t["raw_run"], expanded=False):
                st.json(row["_run"])