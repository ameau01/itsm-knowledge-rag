"""CLI: evaluate ai_overview vs curated_description with a DeepEval/G-Eval judge.

Reads the overview already in the store (from the committed seeds or a fresh generation) and scores
overview_quality / faithfulness / summarization + the deterministic low-hedge guard. Reuses the
project's judge resolver (evaluation/deepeval). Needs OPENAI_API_KEY.

    uv run sh scripts/run_overview_eval.sh --dry-run --limit 3   # no API; show source/summary pairs
    uv run sh scripts/run_overview_eval.sh --all --runs 3        # G-Eval overview_quality + guard
    uv run sh scripts/run_overview_eval.sh --all --metric all    # all three metrics
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/ on the path

from config import settings  # noqa: E402
from evaluation.overview import contracts, report, runner  # noqa: E402
from evaluation.overview import metrics as metricmod  # noqa: E402
from evaluation.overview import resolver  # noqa: E402
from operational_store.store import get_connection  # noqa: E402

_RESULTS = Path(__file__).resolve().parents[2].parent / "eval" / "results"


def main() -> None:
    try:
        from dotenv import find_dotenv, load_dotenv
        load_dotenv(find_dotenv(usecwd=True))
    except ImportError:
        pass

    ap = argparse.ArgumentParser(description="Evaluate ai_overview vs curated_description.")
    ap.add_argument("--db", type=Path, help="explicit DB path (default: settings.operational_store)")
    ap.add_argument("--root-cause-id")
    ap.add_argument("--family")
    ap.add_argument("--heaviest", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--metric",
                    choices=["overview_quality", "faithfulness", "summarization", "both", "all"],
                    default="overview_quality")
    ap.add_argument("--judge-model",
                    default=os.getenv("OVERVIEW_JUDGE_MODEL") or settings.judge_model)
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--label", default="v1",
                    help="suffix for output filenames so runs don't overwrite each other")
    ap.add_argument("--dry-run", action="store_true", help="no API; print the source/summary pairs")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--csv", type=Path, default=None)
    args = ap.parse_args()

    _RESULTS.mkdir(parents=True, exist_ok=True)
    if args.out is None:
        args.out = _RESULTS / f"overview-eval-report-{args.label}.json"
    if args.csv is None:
        args.csv = _RESULTS / f"overview-eval-scores-{args.label}.csv"

    conn = get_connection(args.db)
    rows = resolver.load_eval_cases(conn, family=args.family, root_cause_id=args.root_cause_id,
                                    heaviest=args.heaviest, limit=args.limit)
    if not rows:
        sys.exit("No pages with ai_overview found. Run scripts/run_overview.sh first "
                 "(or load the seeds).")
    cases = [contracts.case_from_row(r) for r in rows]
    print(f"overview eval: {len(cases)} page(s)  metric={args.metric}  judge={args.judge_model}  "
          f"runs={args.runs}\n")

    if args.dry_run:
        for c in cases:
            print(f"=== {c.root_cause_id}  (conf={c.confidence}, n={c.ticket_count}) ===")
            print(f"  source chars: {len(c.source)} | summary chars: {len(c.summary)}")
            print("  SUMMARY:\n    " + c.summary.replace("\n", "\n    ")[:600] + "\n")
        print("dry-run: no judge calls made.")
        return

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("OPENAI_API_KEY not set (judge is OpenAI). Add it to .env.")

    # Reuse the project's judge resolver (same one the curation eval uses).
    from evaluation.deepeval.deepeval_judge import _resolve_judge_model
    model_obj = _resolve_judge_model(args.judge_model, api_key)
    metric_objs = metricmod.build_metrics(args.metric, model_obj, args.threshold)

    metric_names = list(metric_objs)
    results = runner.run(cases, metric_objs, runs=args.runs)
    agg = runner.aggregate(results, metric_names)

    meta = {"db": str(args.db) if args.db else "operational_store",
            "judge_model": args.judge_model, "runs": args.runs}
    report.write_json(args.out, results=results, aggregate=agg,
                      metric_names=metric_names, meta=meta)
    report.write_csv(args.csv, results=results, aggregate=agg, metric_names=metric_names)
    report.print_aggregate(agg, metric_names)
    print(f"\nreport -> {args.out}   scores -> {args.csv}")

    sys.exit(1 if agg.get("_guard", {}).get("hard_fail") else 0)


if __name__ == "__main__":
    main()
