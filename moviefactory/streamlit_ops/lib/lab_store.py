from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

REPORT_ROOT = Path("moviefactory/eval/eval_reports")
RUNS_DIR = REPORT_ROOT / "runs"


def now_run_id(prefix: str = "QUERYLAB") -> str:
    return f"{prefix}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"


def write_run_json(obj: Dict[str, Any]) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = obj.get("run_id") or now_run_id()
    path = RUNS_DIR / f"{run_id}.json"
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def make_lab_run(
    *,
    run_id: str,
    mode: str,
    query: Optional[str],
    image_path: Optional[str],
    params: Dict[str, Any],
    results: List[Dict[str, Any]],
    compare: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:

    ts = datetime.now().isoformat(timespec="seconds")

    latency_ms = params.get("latency_ms")
    result_count = len(results) if results is not None else 0

    session = {
        "query_id": run_id,
        "query": query,
        "image_path": image_path,
        "mode": mode,
        "params": params,
        "tags": tags or [],
        "outputs": {
            "topk_preview": results[:10] if results else [],
            "result_count": result_count,
        },
    }

    if compare:
        session["compare"] = compare

    return {
        "format_version": "eval_report_v1",
        "run_id": run_id,
        "ts": ts,
        "yaml_path": "",
        "suite": "lab",
        "metrics": {
            "cases": 1,
            "latency_ms": latency_ms,
            "result_count": result_count,
            "hit@1": None,
            "hit@5": None,
            "hit@10": None,
            "mean_rank": None,
        },
        "sessions": [session],
        "failures": [],
        "signals_summary": {
            "total_cases": 1,
            "success_cases": 0,
            "failure_cases": 0,
            "tag_count": {t: 1 for t in (tags or [])},
        },
        "artifacts": {
            "raw_source": "query_lab",
            "log_path": None,
        },
    }