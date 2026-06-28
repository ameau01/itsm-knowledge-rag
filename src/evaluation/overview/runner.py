"""Eval runner — score each case, run the guard, aggregate.

Mirrors evaluation/curation/runner.py: judge each case (optionally N runs, spread reported), apply
the deterministic guard, and summarize by metric and confidence tier.
"""

from __future__ import annotations

import statistics as st

from evaluation.overview import guard as guardmod
from evaluation.overview import metrics as metricmod
from evaluation.overview.contracts import CaseScore


def run(cases, metrics: dict, *, runs: int = 1) -> list[CaseScore]:
    metric_names = list(metrics)
    results: list[CaseScore] = []
    for i, c in enumerate(cases, 1):
        per_run: dict[str, list[float]] = {name: [] for name in metric_names}
        reasons: dict[str, str | None] = {}
        for _ in range(max(1, runs)):
            sc = metricmod.score_case(metrics, c)
            for name, d in sc.items():
                per_run[name].append(d["score"])
                reasons[name] = d["reason"]
        scores = {name: {"score": round(st.mean(v), 3), "runs": v, "reason": reasons.get(name)}
                  for name, v in per_run.items()}
        g = guardmod.check_low_hedge(c.confidence, c.lead)
        cs = CaseScore(root_cause_id=c.root_cause_id, family=c.family, confidence=c.confidence,
                       ticket_count=c.ticket_count, scores=scores,
                       guard={"ok": g.ok, "hard_fail": g.hard_fail, "soft_warn": g.soft_warn})
        results.append(cs)
        cells = "  ".join(f"{n}={scores[n]['score']:.2f}" for n in metric_names)
        flag = "" if g.ok else "  GUARD-FAIL!"
        print(f"[{i}/{len(cases)}] {c.root_cause_id}  (conf={c.confidence})  {cells}{flag}")
    return results


def aggregate(results: list[CaseScore], metric_names: list[str]) -> dict:
    agg = {}
    for name in metric_names:
        vals = [r.scores[name]["score"] for r in results if name in r.scores]
        if not vals:
            continue
        agg[name] = {
            "n": len(vals), "mean": round(st.mean(vals), 3),
            "min": round(min(vals), 3), "max": round(max(vals), 3),
            "stdev": round(st.pstdev(vals), 3) if len(vals) > 1 else 0.0,
            "by_confidence": {},
        }
        for tier in ("high", "medium", "low"):
            tv = [r.scores[name]["score"] for r in results
                  if name in r.scores and r.confidence == tier]
            if tv:
                agg[name]["by_confidence"][tier] = {"n": len(tv), "mean": round(st.mean(tv), 3)}
    hard = [r.root_cause_id for r in results if not r.guard.get("ok", True)]
    warn = [r.root_cause_id for r in results if r.guard.get("soft_warn")]
    agg["_guard"] = {"hard_fail": hard, "soft_warn_count": len(warn)}
    return agg
