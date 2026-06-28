"""Report writers — JSON (full) + CSV (flat, with guard columns)."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


def write_json(path: Path, *, results, aggregate, metric_names, meta: dict) -> None:
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **meta,
        "n_pages": len(results),
        "aggregate": aggregate,
        "pages": [
            {"root_cause_id": r.root_cause_id, "family": r.family, "confidence": r.confidence,
             "ticket_count": r.ticket_count, "scores": r.scores, "guard": r.guard}
            for r in results
        ],
    }
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, *, results, aggregate, metric_names) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        cols = ["root_cause_id", "family", "confidence", "ticket_count"]
        for name in metric_names:
            cols += [f"{name}_mean", f"{name}_runs"]
        cols += ["guard_ok", "guard_offending"]
        w = csv.writer(fh)
        w.writerow(cols)
        for r in results:
            row = [r.root_cause_id, r.family, r.confidence, r.ticket_count]
            for name in metric_names:
                s = r.scores.get(name, {})
                row += [s.get("score", ""), ";".join(f"{x:.2f}" for x in s.get("runs", []))]
            row += [r.guard.get("ok", True), ";".join(r.guard.get("hard_fail", []))]
            w.writerow(row)
        w.writerow([])
        agg_row = ["AGGREGATE (mean)", "", "", ""]
        for name in metric_names:
            agg_row += [round(aggregate.get(name, {}).get("mean", 0.0), 3), ""]
        agg_row += ["", ""]
        w.writerow(agg_row)


def print_aggregate(aggregate: dict, metric_names: list[str]) -> None:
    print("\n=== aggregate ===")
    for name in metric_names:
        a = aggregate.get(name)
        if not a:
            continue
        bc = " · ".join(f"{t}:{d['mean']:.2f}(n{d['n']})" for t, d in a["by_confidence"].items())
        note = "  (diagnostic only — penalizes compression)" if name == "summarization" else ""
        print(f"  {name:16s} mean={a['mean']:.3f}  min={a['min']:.2f}  max={a['max']:.2f}  "
              f"sd={a['stdev']:.3f}  |  {bc}{note}")
    g = aggregate.get("_guard", {})
    print(f"  guard: hard_fail={len(g.get('hard_fail', []))} "
          f"soft_warn={g.get('soft_warn_count', 0)}"
          + (f"  -> {g['hard_fail']}" if g.get("hard_fail") else ""))
