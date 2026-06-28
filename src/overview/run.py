"""CLI: generate AI overviews into wiki_pages.ai_overview (reads curated_description).

A build-time / regeneration tool — it's how the committed ai_overview seeds are produced. It does
NOT run at serve time (the demo loads the overview from the committed seeds).

    uv run sh scripts/run_overview.sh --mock --limit 3   # no API, validates plumbing
    uv run sh scripts/run_overview.sh --heaviest          # one real call
    uv run sh scripts/run_overview.sh --family VDA        # one family
    uv run sh scripts/run_overview.sh --all               # every curated page
    uv run sh scripts/run_overview.sh --verify            # read back + check (no writes)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # src/ on the path

from operational_store.store import get_connection  # noqa: E402
from overview import node  # noqa: E402
from overview import store  # noqa: E402
from overview.agent import OverviewAgent  # noqa: E402


def main() -> None:
    try:
        from dotenv import find_dotenv, load_dotenv
        load_dotenv(find_dotenv(usecwd=True))
    except ImportError:
        pass

    ap = argparse.ArgumentParser(description="Generate AI overviews into wiki_pages.ai_overview")
    ap.add_argument("--root-cause-id")
    ap.add_argument("--family")
    ap.add_argument("--heaviest", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--db", type=Path, help="explicit DB path (default: settings.operational_store)")
    ap.add_argument("--provider", default=os.getenv("OVERVIEW_PROVIDER") or "anthropic")
    ap.add_argument("--model", default=os.getenv("OVERVIEW_MODEL"))
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--mock", action="store_true", help="no API; deterministic placeholder")
    ap.add_argument("--dry-run", action="store_true", help="no API; print one prompt preview")
    ap.add_argument("--verify", action="store_true", help="read back ai_overview and check; no writes")
    args = ap.parse_args()

    conn = get_connection(args.db)

    if args.verify:
        sys.exit(1 if node.verify(conn) else 0)

    pages = store.iter_curated_pages(conn, family=args.family, root_cause_id=args.root_cause_id,
                                     heaviest=args.heaviest, limit=args.limit)

    provider = (args.provider or "anthropic").lower()
    model = args.model or ("gpt-4o" if provider == "openai" else "claude-opus-4-8")
    mode = "MOCK" if args.mock else ("DRY-RUN" if args.dry_run else f"{provider}:{model}")
    print(f"overview: {len(pages)} page(s)  mode={mode}\n")

    agent = None
    if not args.mock and not args.dry_run:
        agent = OverviewAgent(provider, model, args.temperature)

    stats = node.run_batch(conn, pages, agent=agent, mock=args.mock, dry_run=args.dry_run)
    if not args.dry_run:
        print(f"\noverview: {stats['ok']} ok, {stats['fail']} failed.  "
              f"Verify: uv run sh scripts/run_overview.sh --verify")


if __name__ == "__main__":
    main()
