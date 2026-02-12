from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def _parse_metrics(stdout: str) -> dict:
    def find_float(pattern: str, required: bool = True):
        m = re.search(pattern, stdout)
        if not m:
            if required:
                raise ValueError(f"Failed to parse pattern: {pattern}")
            return None
        return float(m.group(1))

    hit1 = find_float(r"hit@1\s*:\s*\d+/\d+\s*=\s*([0-9.]+)")
    hit5 = find_float(r"hit@5\s*:\s*\d+/\d+\s*=\s*([0-9.]+)")
    hit10 = find_float(r"hit@10\s*:\s*\d+/\d+\s*=\s*([0-9.]+)")
    mean_rank = find_float(r"mean_rank\(best must\)\s*:\s*([0-9.]+)", required=False)

    m = re.search(r"cases:\s*(\d+)", stdout)
    cases = int(m.group(1)) if m else None

    return {
        "cases": cases,
        "hit@1": hit1,
        "hit@5": hit5,
        "hit@10": hit10,
        "mean_rank": mean_rank,
    }


def _compare(baseline, latest, tol_hit=0.0, tol_rank=0.0):
    msgs = []
    ok = True

    for k in ("hit@1", "hit@5", "hit@10"):
        b = float(baseline.get(k, 0.0))
        l = float(latest.get(k, 0.0))
        if l + 1e-12 < b - tol_hit:
            ok = False
            msgs.append(f"[REGRESSION] {k}: baseline={b:.3f} -> latest={l:.3f}")
        else:
            msgs.append(f"[OK] {k}: baseline={b:.3f} -> latest={l:.3f}")

    b_rank = baseline.get("mean_rank")
    l_rank = latest.get("mean_rank")

    if b_rank is not None and l_rank is not None:
        b = float(b_rank)
        l = float(l_rank)
        if l > b + tol_rank:
            ok = False
            msgs.append(f"[REGRESSION] mean_rank: baseline={b:.2f} -> latest={l:.2f}")
        else:
            msgs.append(f"[OK] mean_rank: baseline={b:.2f} -> latest={l:.2f}")

    return ok, msgs


def main():
    project_root = Path(__file__).resolve().parents[2]
    eval_dir = project_root / "moviefactory" / "eval"
    reports_dir = eval_dir / "eval_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    yaml_path = str(eval_dir / "text_queries_intent.yaml")
    baseline_path = eval_dir / "baseline.json"
    latest_json_path = reports_dir / "latest.json"
    latest_txt_path = reports_dir / "latest.txt"

    update_baseline = "--update-baseline" in sys.argv

    for a in sys.argv[1:]:
        if not a.startswith("--"):
            yaml_path = a

    print("[REG] Running evaluation...\n")

    cmd = [sys.executable, "-m", "moviefactory.eval.run_text_eval", yaml_path]
    proc = subprocess.run(
        cmd,
        cwd=str(project_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    combined = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    latest_txt_path.write_text(combined, encoding="utf-8")

    if proc.returncode != 0:
        print("[REG] run_text_eval crashed.")
        sys.exit(2)

    latest_metrics = _parse_metrics(combined)

    latest_payload = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "yaml": yaml_path,
        "metrics": latest_metrics,
    }

    latest_json_path.write_text(
        json.dumps(latest_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if not baseline_path.exists() or update_baseline:
        baseline_path.write_text(
            json.dumps(latest_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print("✅ baseline updated")
        sys.exit(0)

    baseline_payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline_metrics = baseline_payload.get("metrics", {})

    ok, msgs = _compare(baseline_metrics, latest_metrics)

    print("\n=== DIFF ===")
    for m in msgs:
        print(m)

    if ok:
        print("\n✅ PASS (no regression)")
        sys.exit(0)
    else:
        print("\n❌ FAIL (regression detected)")
        sys.exit(1)


if __name__ == "__main__":
    main()
