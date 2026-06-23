"""CLI: run the curation (L2) eval over a family and print the arm-comparison table.

The gold arm is always present (synthesized from the eval mapping). Extra strategy arms are
loaded from frozen candidate files under --candidates-dir/<arm>/<root_cause>.json — so adding
a strategy never touches this harness. Needs OPENAI_API_KEY for the live judge.

    uv run --group eval python3 src/evaluation/curation/run.py [--family VDA] [--runs N]
        [--model gpt-...] [--candidates-dir DIR] [--no-cache] [--db PATH]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/ on the path

from evaluation.curation import resolver  # noqa: E402
from evaluation.curation.cache import CurationCache  # noqa: E402
from evaluation.curation.contracts import Candidate  # noqa: E402
from evaluation.curation.report import format_report  # noqa: E402
from evaluation.curation.runner import aggregate_curation, run_curation_eval  # noqa: E402


def _load_candidate_arms(candidates_dir: Path, keep_rcs: set[str]) -> dict[str, list[Candidate]]:
    """Each subdir is an arm; each *.json a candidate page. Only keep in-scope root causes."""
    arms: dict[str, list[Candidate]] = {}
    for arm_dir in sorted(p for p in candidates_dir.iterdir() if p.is_dir()):
        cands = []
        for jf in sorted(arm_dir.glob("*.json")):
            rec = json.loads(jf.read_text(encoding="utf-8"))
            if rec["root_cause_id"] not in keep_rcs:
                continue
            cands.append(
                Candidate(
                    arm=arm_dir.name,
                    root_cause_id=rec["root_cause_id"],
                    family=rec["family"],
                    curation=rec["curation"],
                    context=rec.get("context", {}),
                )
            )
        if cands:
            arms[arm_dir.name] = cands
    return arms


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--family", default="VDA",
                    help="family code (e.g. VDA), or ALL for the whole 76-page corpus")
    ap.add_argument("--runs", type=int, default=int(os.getenv("JUDGE_N_RUNS", "3")))
    ap.add_argument("--model", default=os.getenv("JUDGE_MODEL", "gpt-5.4"))
    ap.add_argument("--candidates-dir", type=Path)
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--db", type=Path)
    args = ap.parse_args()

    conn = resolver.open_store(args.db)
    gold = resolver.load_gold()
    records = gold if args.family.upper() == "ALL" else resolver.family_records(gold, args.family)
    if not records:
        sys.exit(f"no eval records for family {args.family!r}")

    gold_cands, meta = resolver.build_gold_arm(conn, records)
    arms_by_name: dict[str, list] = {"gold": gold_cands}
    if args.candidates_dir:
        arms_by_name.update(_load_candidate_arms(args.candidates_dir, set(meta)))

    # Lazy import so --help / arg errors don't require deepeval or a key.
    from evaluation.curation.judge import CurationJudge

    cache = None if args.no_cache else CurationCache()
    judge = CurationJudge(model=args.model, cache=cache)

    results = run_curation_eval(arms_by_name, meta, judge, n_runs=args.runs)
    agg = aggregate_curation(results)
    print(format_report(
        agg, arms=list(arms_by_name), page_meta=meta, judge_name=judge.name, n_runs=args.runs,
    ))


if __name__ == "__main__":
    main()
