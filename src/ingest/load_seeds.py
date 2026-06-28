"""Load the operational store from committed SQL seeds — NO HF download, NO redaction, NO LLM.

This is the demo/mock counterpart to run_ingest.py (which is the HF + redaction path). It is kept
SEPARATE so the live ingest path is never touched. Two modes:

  --full      (default) rebuild the store from seeds (tickets.sql, curated_content.sql, ai_overview.sql)
  --l2-only   apply ONLY curated_content.sql + ai_overview.sql

The L2 seeds (curation + overview) are applied in BOTH modes — that is the common part. The only
thing --full adds is sourcing tickets from tickets.sql instead of HF.

    uv run sh scripts/load_seeds.sh                 # --full  (mock store from seeds)
    uv run sh scripts/load_seeds.sh --l2-only       # L2 only (after run_ingest, live)
    uv run sh scripts/load_seeds.sh --seeds-dir path/to/db_seeds
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # src/ on the path

from operational_store.store import (  # noqa: E402
    apply_sql_seed,
    get_connection,
    reset_tickets_table,
    reset_wiki_pages,
    seed_wiki_pages,
)

_SEEDS_DIR = Path(__file__).parent.parent.parent / "db_seeds"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--full", action="store_true",
                      help="rebuild store from seeds: tickets + wiki_pages + L2 (default, mock)")
    mode.add_argument("--l2-only", action="store_true",
                      help="apply only curation+overview seeds (the L2 tail after run_ingest, live)")
    ap.add_argument("--seeds-dir", type=Path, default=_SEEDS_DIR,
                    help=f"directory holding the .sql seeds (default: {_SEEDS_DIR})")
    args = ap.parse_args(argv)

    full = not args.l2_only  # default to --full unless --l2-only given

    sd = args.seeds_dir
    tickets_sql = sd / "tickets.sql"
    curation_sql = sd / "curated_content.sql"
    overview_sql = sd / "ai_overview.sql"
    for required in ([tickets_sql, curation_sql, overview_sql] if full else [curation_sql, overview_sql]):
        if not required.exists():
            sys.exit(f"seed not found: {required}")

    conn = get_connection()
    try:
        if full:
            reset_tickets_table(conn)
            apply_sql_seed(conn, tickets_sql)
            n_tk = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
            print(f"[load_seeds] tickets loaded from tickets.sql: {n_tk}")
            reset_wiki_pages(conn)
            n_pg = seed_wiki_pages(conn)
            print(f"[load_seeds] seeded {n_pg} wiki_pages rows (deterministic columns)")

        # L2 — applied in both modes (the common part)
        apply_sql_seed(conn, curation_sql)
        apply_sql_seed(conn, overview_sql)
        conn.commit()

        n_cur = conn.execute(
            "SELECT COUNT(*) FROM wiki_pages WHERE curated_description IS NOT NULL").fetchone()[0]
        n_ov = conn.execute(
            "SELECT COUNT(*) FROM wiki_pages WHERE ai_overview IS NOT NULL").fetchone()[0]
        print(f"[load_seeds] curated_description: {n_cur} | ai_overview: {n_ov}")
        print(f"[load_seeds] done ({'full' if full else 'l2-only'}) -> "
              f"{settings_store_path()}")
    finally:
        conn.close()
    return 0


def settings_store_path() -> str:
    from config import settings
    return str(settings.operational_store / "itsm_rag.db")


if __name__ == "__main__":
    raise SystemExit(main())
