"""Clear L2 columns in the operational store so curation / overview can be regenerated in place.

Tickets and the deterministic wiki_pages columns are left untouched — only the LLM-authored
L2 columns are NULLed:
  --curation   curated_description + curation_details
  --overview   ai_overview + ai_overview_details
  --all        both

Mirrors the regenerate flow: clear, then re-run the producer against the SAME store.

    uv run sh scripts/reset_l2.sh --curation       # before re-running run_curation.sh
    uv run sh scripts/reset_l2.sh --overview       # before re-running run_overview.sh
    uv run sh scripts/reset_l2.sh --all
    uv run sh scripts/reset_l2.sh --curation --db path/to/other.db
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # src/ on the path

from operational_store.store import (  # noqa: E402
    get_connection,
    reset_wiki_curation,
    reset_wiki_overview,
)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Clear L2 curation/overview columns in the operational store.")
    ap.add_argument("--db", type=Path, help="explicit DB path (default: settings.operational_store)")
    ap.add_argument("--curation", action="store_true",
                    help="NULL curated_description + curation_details")
    ap.add_argument("--overview", action="store_true",
                    help="NULL ai_overview + ai_overview_details")
    ap.add_argument("--all", action="store_true", help="clear both curation and overview columns")
    args = ap.parse_args()

    do_curation = args.curation or args.all
    do_overview = args.overview or args.all
    if not (do_curation or do_overview):
        ap.error("nothing to do: pass --curation, --overview, or --all")

    conn = get_connection(args.db)
    if do_curation:
        n = reset_wiki_curation(conn)
        print(f"cleared curation columns (curated_description, curation_details) on {n} page(s)")
    if do_overview:
        n = reset_wiki_overview(conn)
        print(f"cleared overview columns (ai_overview, ai_overview_details) on {n} page(s)")


if __name__ == "__main__":
    main()
