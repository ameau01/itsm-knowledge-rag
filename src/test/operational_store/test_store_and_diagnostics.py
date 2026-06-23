"""operational_store — schema reconciliation, wiki_pages seeding, canonical diagnostics."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/ on path

import pytest

from operational_store.diagnostics import canonical_diagnostic_steps
from operational_store.store import (
    get_connection,
    init_db,
    seed_wiki_pages,
    update_wiki_curation,
)

UNIFORM = "FAM/uniform-playbook"
BROKEN = "FAM/broken-redaction"

_DEFAULT_ENV = {"os": "Win10", "platform": "Laptop", "region": "us-east-1", "user_group": "Sales"}


def _ins(con, tid, rc, raw, proc):
    con.execute(
        "INSERT INTO tickets (ticket_id, family, root_cause_id, diagnostics_steps_raw, "
        "diagnostics_procedure, environment, resolution_steps, root_cause_narrative, "
        "upserted_at, pipeline_version) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (tid, "FAM", rc, json.dumps(raw), json.dumps(proc), json.dumps(_DEFAULT_ENV),
         json.dumps(["a", "b", "c", "d"]), "engineer note", "t", "test"),
    )


@pytest.fixture
def conn(tmp_path):
    c = get_connection(tmp_path / "t.db")
    init_db(c)
    # Uniform playbook: identical playbook_step_id sequence, varied action wording.
    _ins(c, "T1", UNIFORM,
         [{"playbook_step_id": "a-check", "action": "Check A precisely", "expected_result": "A ok"},
          {"playbook_step_id": "b-check", "action": "Check B", "expected_result": "B ok"}],
         [{"step": 1, "action": "Check A precisely", "expected_result": "A ok"},
          {"step": 2, "action": "Check B", "expected_result": "B ok"}])
    _ins(c, "T2", UNIFORM,
         [{"playbook_step_id": "a-check", "action": "Check A precisely", "expected_result": "A ok"},
          {"playbook_step_id": "b-check", "action": "Verify B thoroughly", "expected_result": "B ok"}],
         [{"step": 1, "action": "Check A precisely", "expected_result": "A ok"}])
    _ins(c, "T3", UNIFORM,
         [{"playbook_step_id": "a-check", "action": "Inspect A", "expected_result": "A ok"},
          {"playbook_step_id": "b-check", "action": "Check B", "expected_result": "B ok"}],
         [{"step": 1, "action": "Inspect A", "expected_result": "A ok"}])
    # Over-redacted playbook ids -> free-text fallback path.
    for tid in ("T4", "T5"):
        _ins(c, tid, BROKEN,
             [{"playbook_step_id": "<HOSTNAME>", "action": "x", "expected_result": "y"}],
             [{"step": 1, "action": "Restart X", "expected_result": "X up"}])
    c.commit()
    return c


def test_schema_has_reconciled_columns(conn):
    tcols = {r[1] for r in conn.execute("PRAGMA table_info(tickets)")}
    assert "upserted_at" in tcols and "redacted_at" not in tcols
    wcols = {r[1] for r in conn.execute("PRAGMA table_info(wiki_pages)")}
    assert {"family", "root_cause_id", "curated_description", "diagnostic_steps",
            "curated_tickets", "curation_details", "upserted_at"} <= wcols


def test_seed_wiki_pages_writes_deterministic_columns(conn):
    assert seed_wiki_pages(conn) == 2
    row = conn.execute(
        "SELECT curated_tickets, diagnostic_steps, curated_description, upserted_at "
        "FROM wiki_pages WHERE root_cause_id=?", (UNIFORM,)).fetchone()
    assert row["curated_tickets"] == "T1,T2,T3"        # sorted membership snapshot
    assert row["curated_description"] is None           # generated column left for curation
    assert row["upserted_at"]                           # seeded timestamp
    steps = json.loads(row["diagnostic_steps"])
    assert [s["action"] for s in steps] == ["Check A precisely", "Check B"]  # canonical + modal wording


def test_canonical_diagnostics_uniform(conn):
    steps = canonical_diagnostic_steps(conn, UNIFORM)
    assert [s["step"] for s in steps] == [1, 2]
    assert [s["action"] for s in steps] == ["Check A precisely", "Check B"]


def test_canonical_diagnostics_falls_back_on_redaction(conn):
    steps = canonical_diagnostic_steps(conn, BROKEN)
    assert [s["action"] for s in steps] == ["Restart X"]   # free-text modal of diagnostics_procedure


def test_update_curation_touches_only_generated_columns(conn):
    seed_wiki_pages(conn)
    before = conn.execute(
        "SELECT diagnostic_steps, curated_tickets FROM wiki_pages WHERE root_cause_id=?",
        (UNIFORM,)).fetchone()
    assert update_wiki_curation(conn, "FAM", UNIFORM, '{"title":"T"}', '{"model":"m"}') == 1
    after = conn.execute(
        "SELECT curated_description, curation_details, diagnostic_steps, curated_tickets "
        "FROM wiki_pages WHERE root_cause_id=?", (UNIFORM,)).fetchone()
    assert json.loads(after["curated_description"])["title"] == "T"
    assert json.loads(after["curation_details"])["model"] == "m"
    assert after["diagnostic_steps"] == before["diagnostic_steps"]   # ingest-owned, untouched
    assert after["curated_tickets"] == before["curated_tickets"]
