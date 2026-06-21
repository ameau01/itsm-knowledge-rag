"""Ingest — temp SQLite + fake embedders + in-memory Qdrant (no models, no live DB)."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/ on path

import pytest

pytest.importorskip("qdrant_client")  # needs `uv sync --group retrieval`

from qdrant_client import QdrantClient, models

from retrieval.ingest import build_index
from retrieval.qdrant_ops import QdrantOps


class FakeDense:
    dim = 4

    def __init__(self):
        self.seen: list[str] = []

    def embed_documents(self, texts):
        self.seen = list(texts)
        return [[1.0, 0.0, 0.0, 0.0] for _ in texts]


class FakeSparse:
    def embed_documents(self, texts):
        return [models.SparseVector(indices=[1], values=[1.0]) for _ in texts]


def _make_db(path):
    con = sqlite3.connect(path)
    con.execute(
        "CREATE TABLE tickets (ticket_id TEXT, family TEXT, root_cause_id TEXT, priority TEXT, "
        "environment TEXT, applications TEXT, submitted_at TEXT, observed_errors TEXT, "
        "sla_plan TEXT, submitted_description TEXT, correspondence TEXT, "
        "diagnostics_procedure TEXT, resolution_steps TEXT)")
    con.execute(
        "INSERT INTO tickets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ("INC-AIT-0001", "AIT", "AIT/expired-api-token", "medium",
         json.dumps({"region": "us-west-2", "platform": "Gateway", "user_group": "App Support"}),
         json.dumps(["CustomerSync"]), "2025-12-01T20:48:00Z",
         json.dumps(["504 Gateway Timeout", "ERR_TIMEOUT"]), "Standard 24x7",
         "nightly sync failing", "correspondence body",
         json.dumps([{"step": 1, "action": "check token"}]), json.dumps(["rotated token"])))
    con.commit()
    con.close()


def test_ingest_points_payload_and_augmentation(tmp_path):
    db = tmp_path / "t.db"
    _make_db(db)
    dense = FakeDense()
    ops = QdrantOps(collection="t", client=QdrantClient(":memory:"))
    n = build_index(dense=dense, sparse=FakeSparse(), ops=ops, db_path=db)
    assert n == 4 and ops.count() == 4                       # 4 non-empty sections

    # D6: error codes folded into the DESCRIPTION embedding text, not other sections
    desc_text = next(t for t in dense.seen if "nightly sync failing" in t)
    assert "ERR_TIMEOUT" in desc_text and "504 Gateway Timeout" in desc_text
    corr_text = next(t for t in dense.seen if "correspondence body" in t)
    assert "ERR_TIMEOUT" not in corr_text

    pts = ops.client.scroll("t", limit=10, with_payload=True)[0]
    desc = next(p for p in pts if p.payload["section_name"] == "description").payload
    assert desc["sla_tier"] == "Standard"
    assert desc["observed_errors"] == ["504 Gateway Timeout", "ERR_TIMEOUT"]
    assert desc["env_region"] == "us-west-2"
    assert "ERR_TIMEOUT" not in desc["excerpt"]              # excerpt stays clean
    assert "env_platform" not in desc and "env_user_group" not in desc  # D7 dropped


def test_ingest_idempotent(tmp_path):
    db = tmp_path / "t.db"
    _make_db(db)
    ops = QdrantOps(collection="t2", client=QdrantClient(":memory:"))
    build_index(dense=FakeDense(), sparse=FakeSparse(), ops=ops, db_path=db)
    build_index(dense=FakeDense(), sparse=FakeSparse(), ops=ops, db_path=db)
    assert ops.count() == 4                                  # same UUIDs overwritten, not doubled
