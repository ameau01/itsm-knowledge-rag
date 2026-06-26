"""CLI: evaluate the live curation in wiki_pages against the source tickets.

    uv run --group eval python3 src/evaluation/curation/run.py [--family VDA] [--runs N]
        [--model gpt-...] [--no-cache] [--db PATH]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/ on the path

from evaluation.curation import resolver  # noqa: E402
from evaluation.curation.cache import CurationCache  # noqa: E402
from evaluation.curation.report import format_report  # noqa: E402
from evaluation.curation.runner import aggregate_curation, run_curation_eval  # noqa: E402

SUBJECT = "curated"  # the single thing evaluated: the store's curation


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--family", default="VDA",
                    help="family code (e.g. VDA), or ALL for the whole 76-page corpus")
    ap.add_argument("--runs", type=int, default=int(os.getenv("JUDGE_N_RUNS", "3")))
    ap.add_argument("--model", default=os.getenv("JUDGE_MODEL", "gpt-5.4"))
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--db", type=Path)
    args = ap.parse_args()

    conn = resolver.open_store(args.db)
    recipe = resolver.load_recipe()
    records = recipe if args.family.upper() == "ALL" else resolver.family_records(recipe, args.family)
    if not records:
        sys.exit(f"no eval recipe records for family {args.family!r}")

    # Short-circuit: the curation must exist in wiki_pages before it can be evaluated.
    missing = resolver.missing_curation(conn, records)
    if missing:
        sys.exit(
            f"Curation not found in wiki_pages for {len(missing)}/{len(records)} page(s) in "
            f"{args.family!r}. Run curation + load_wiki first.\nMissing:\n  " + "\n  ".join(missing)
        )

    cands, meta = resolver.build_subject(conn, records)

    # Lazy import so --help / arg errors don't require deepeval or a key.
    from evaluation.curation.judge import CurationJudge

    cache = None if args.no_cache else CurationCache()
    judge = CurationJudge(model=args.model, cache=cache)

    results = run_curation_eval({SUBJECT: cands}, meta, judge, n_runs=args.runs)
    agg = aggregate_curation(results)
    print(format_report(
        agg, arms=[SUBJECT], page_meta=meta, judge_name=judge.name, n_runs=args.runs,
    ))


if __name__ == "__main__":
    main()
