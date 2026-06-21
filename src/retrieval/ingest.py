"""
Build the Qdrant retrieval index from the operational store.

Each non-empty ticket section becomes a point keyed `(ticket_id, section_name)`. The
description point's EMBEDDING text is augmented with the ticket's observed error codes so
BM25/dense can match them; the clean section text (excerpt + what the judge reads) is
unchanged. Point ids are a deterministic UUID5 of the key, so re-running overwrites in
place rather than duplicating.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # src/ on path

from qdrant_client import models

from config import settings
from corpus.sections import SECTION_COLUMNS, SECTION_NAMES, render_section
from corpus.sla import sla_tier
from retrieval.qdrant_ops import DENSE, SPARSE, QdrantOps

_NS = uuid.UUID("a3f1c2d4-0000-4000-8000-000000000001")  # fixed namespace for stable ids

_FILTER_COLS = "priority, environment, applications, submitted_at, observed_errors, sla_plan"


def build_index(*, dense=None, sparse=None, ops=None, db_path=None, batch: int = 256) -> int:
    if dense is None:
        from retrieval.embeddings import DenseEmbedder
        dense = DenseEmbedder()
    if sparse is None:
        from retrieval.embeddings import SparseEmbedder
        sparse = SparseEmbedder()
    ops = ops or QdrantOps()
    ops.ensure_collection(dense.dim)

    db = db_path or (settings.operational_store / "itsm_rag.db")
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    cols = ", ".join(SECTION_COLUMNS[s] for s in SECTION_NAMES)
    rows = conn.execute(
        f"SELECT ticket_id, family, root_cause_id, {_FILTER_COLS}, {cols} FROM tickets").fetchall()

    index_texts: list[str] = []
    metas: list[dict] = []
    for r in rows:
        env = json.loads(r["environment"] or "{}") or {}
        errors = json.loads(r["observed_errors"] or "[]")
        base = {
            "ticket_id": r["ticket_id"], "family": r["family"],
            "root_cause_id": r["root_cause_id"], "priority": r["priority"],
            "applications": json.loads(r["applications"] or "[]"),
            "env_region": env.get("region"),
            "sla_plan": r["sla_plan"], "sla_tier": sla_tier(r["sla_plan"]),
            "submitted_at": r["submitted_at"], "observed_errors": errors,
        }
        for sec in SECTION_NAMES:
            display = render_section(r[SECTION_COLUMNS[sec]])
            if not display.strip():
                continue
            augment = "\n" + " ".join(errors) if sec == "description" and errors else ""
            index_texts.append(display + augment)
            metas.append({**base, "section_name": sec, "excerpt": display[:300]})

    conn.close()
    print(f"read {len(rows)} tickets -> {len(index_texts)} non-empty section chunks", flush=True)
    print("embedding (dense)…", flush=True)
    dvecs = dense.embed_documents(index_texts)
    print("embedding (sparse)…", flush=True)
    svecs = sparse.embed_documents(index_texts)
    print(f"upserting {len(index_texts)} points…", flush=True)
    points = [
        models.PointStruct(
            id=str(uuid.uuid5(_NS, f'{m["ticket_id"]}:{m["section_name"]}')),
            vector={DENSE: dv, SPARSE: sv}, payload=m)
        for m, dv, sv in zip(metas, dvecs, svecs)
    ]
    ops.upsert(points, batch=batch)
    print(f"indexed {len(points)} section-points across {len(rows)} tickets "
          f"(collection '{ops.collection}', total {ops.count()})")
    return len(points)


if __name__ == "__main__":
    build_index()
