# ops/auto_tagging.py
# Failure auto-tagging (rules + rolling baseline)
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional
import math
import statistics


@dataclass
class TagDecision:
    tag: str
    confidence: float
    reason: Dict[str, Any]


def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except Exception:
        return None


def _percentile(values: List[float], p: float) -> Optional[float]:
    if not values:
        return None
    if p <= 0:
        return min(values)
    if p >= 100:
        return max(values)
    vs = sorted(values)
    k = (len(vs) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return vs[int(k)]
    d0 = vs[f] * (c - k)
    d1 = vs[c] * (k - f)
    return d0 + d1


def compute_rolling_latency_baseline(lab_runs: List[Dict[str, Any]], window: int = 50) -> Dict[str, Any]:
    """
    Returns baseline dict:
      {
        "n": int,
        "median": float|None,
        "p95": float|None,
        "p99": float|None
      }
    Uses most recent `window` lab runs (by created_at if present, else file order at load-time).
    """
    # Expect caller already sorted; still we just take tail window.
    recent = lab_runs[-window:] if len(lab_runs) > window else lab_runs[:]
    latencies: List[float] = []
    for r in recent:
        v = _safe_float(r.get("latency_ms"))
        if v is not None:
            latencies.append(v)

    if not latencies:
        return {"n": 0, "median": None, "p95": None, "p99": None}

    return {
        "n": len(latencies),
        "median": statistics.median(latencies),
        "p95": _percentile(latencies, 95),
        "p99": _percentile(latencies, 99),
    }


def auto_tag_failure(
    session: Dict[str, Any],
    *,
    rolling_latency: Optional[Dict[str, Any]] = None,
    low_results_threshold: int = 5,
    slow_absolute_ms: int = 3000,
    clip_weak_threshold: float = 0.55,
) -> Tuple[List[str], List[Dict[str, Any]], Dict[str, Any]]:
    """
    session expected (minimal):
      {
        "query_text": str,
        "latency_ms": float|int,
        "result_count": int,
        "signals": { ... optional ... }
      }

    returns: (tags, reasons, summary)
      tags: ["NO_RESULTS", ...]
      reasons: [{"tag":..., "confidence":..., "rule":..., "evidence":...}, ...]
      summary: {"tag_counts": {...}, "top_tags": [...]}
    """
    tags: List[str] = []
    reasons: List[Dict[str, Any]] = []

    q = (session.get("query_text") or "").strip()
    latency = _safe_float(session.get("latency_ms"))
    rc = session.get("result_count")
    try:
        rc_int = int(rc) if rc is not None else None
    except Exception:
        rc_int = None

    signals = session.get("signals") or {}

    decisions: List[TagDecision] = []

    # ---- Result-based ----
    if rc_int == 0:
        decisions.append(
            TagDecision(
                tag="NO_RESULTS",
                confidence=0.95,
                reason={"rule": "result_count == 0", "result_count": rc_int},
            )
        )
    elif rc_int is not None and rc_int < low_results_threshold:
        decisions.append(
            TagDecision(
                tag="LOW_RESULTS",
                confidence=0.80,
                reason={
                    "rule": f"result_count < {low_results_threshold}",
                    "result_count": rc_int,
                    "threshold": low_results_threshold,
                },
            )
        )

    # ---- Latency-based ----
    if latency is not None:
        if latency >= slow_absolute_ms:
            decisions.append(
                TagDecision(
                    tag="SLOW_ABSOLUTE",
                    confidence=0.85,
                    reason={"rule": f"latency_ms >= {slow_absolute_ms}", "latency_ms": latency, "threshold": slow_absolute_ms},
                )
            )
        # rolling p95
        if rolling_latency and rolling_latency.get("p95") is not None and rolling_latency.get("n", 0) >= 10:
            p95 = float(rolling_latency["p95"])
            if latency >= p95:
                decisions.append(
                    TagDecision(
                        tag="SLOW_P95",
                        confidence=0.75,
                        reason={"rule": "latency_ms >= rolling_p95", "latency_ms": latency, "rolling_p95": p95, "rolling_n": rolling_latency.get("n", 0)},
                    )
                )

    # ---- Input / signal based (optional) ----
    if not q:
        decisions.append(
            TagDecision(
                tag="EMPTY_QUERY",
                confidence=0.90,
                reason={"rule": "query_text.strip() == ''"},
            )
        )

    # CLIP weak input signal (if your session stores clip_best)
    clip_best = _safe_float(signals.get("clip_best"))
    if clip_best is not None and clip_best < clip_weak_threshold:
        decisions.append(
            TagDecision(
                tag="CLIP_WEAK_INPUT",
                confidence=0.70,
                reason={"rule": f"clip_best < {clip_weak_threshold}", "clip_best": clip_best, "threshold": clip_weak_threshold},
            )
        )

    # Over-filtered heuristic (if you provide these stats)
    cand = signals.get("candidates_before_filter")
    kept = signals.get("candidates_after_filter")
    try:
        cand_i = int(cand) if cand is not None else None
        kept_i = int(kept) if kept is not None else None
    except Exception:
        cand_i, kept_i = None, None
    if cand_i and kept_i is not None and cand_i >= 50 and kept_i <= 3:
        decisions.append(
            TagDecision(
                tag="OVERFILTERED",
                confidence=0.60,
                reason={"rule": "candidates_before_filter>=50 and candidates_after_filter<=3", "candidates_before_filter": cand_i, "candidates_after_filter": kept_i},
            )
        )

    # Engine error presence (if you store it)
    if session.get("error"):
        decisions.append(
            TagDecision(
                tag="ENGINE_ERROR",
                confidence=0.95,
                reason={"rule": "session.error exists", "error": str(session.get('error'))[:500]},
            )
        )

    # finalize
    for d in decisions:
        if d.tag not in tags:
            tags.append(d.tag)
            reasons.append(
                {
                    "tag": d.tag,
                    "confidence": float(d.confidence),
                    "evidence": d.reason,
                }
            )

    tag_counts = {t: 1 for t in tags}
    summary = {
        "tag_counts": tag_counts,
        "top_tags": tags[:5],
        "rolling_latency": rolling_latency or {},
    }
    return tags, reasons, summary