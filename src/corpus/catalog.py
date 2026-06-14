"""
Catalog helpers — load eval-set/catalog.json and build lookup maps.

The catalog is the authoritative source for:
  - root_cause_id per ticket (ticket_id → root_cause_id)
  - family membership and family metadata

Usage
-----
    from corpus.catalog import build_rc_map

    rc_map = build_rc_map()   # build once before the ingest loop
    root_cause_id = rc_map["INC-AIT-0001"]
    # → 'AIT/expired-api-token-auth-failures'
"""

from __future__ import annotations

import json
from pathlib import Path

# eval-set/catalog.json sits two levels above src/corpus/
_CATALOG_PATH = Path(__file__).parent.parent.parent / "eval-set" / "catalog.json"


def build_rc_map(catalog_path: Path | None = None) -> dict[str, str]:
    """
    Invert catalog.json into a ticket_id → root_cause_id mapping.

    Args:
        catalog_path: path to catalog.json. Defaults to eval-set/catalog.json.

    Returns:
        Dict mapping every ticket_id in the catalog to its root_cause_id.
        Example: {"INC-AIT-0001": "AIT/expired-api-token-auth-failures", ...}

    Raises:
        FileNotFoundError: if catalog.json does not exist at the resolved path.
    """
    path = catalog_path or _CATALOG_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"catalog.json not found at {path}\n"
            "Expected at eval-set/catalog.json in the project root."
        )

    catalog = json.loads(path.read_text(encoding="utf-8"))
    rc_map: dict[str, str] = {}
    for family in catalog.get("families", []):
        for rc in family.get("root_causes", []):
            rc_id = rc["root_cause_id"]
            for tid in rc.get("ticket_ids", []):
                rc_map[tid] = rc_id
    return rc_map
