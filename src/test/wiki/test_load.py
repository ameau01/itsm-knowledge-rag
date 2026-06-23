"""wiki.load — curation files fill curated_description; integrity check."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/ on path

import pytest  # noqa: F401

import wiki.load as L
from operational_store.store import get_connection, init_db, seed_wiki_pages


def _store(tmp_path):
    c = get_connection(tmp_path / "t.db")
    init_db(c)
    for tid in ("T1", "T2"):
        c.execute(
            "INSERT INTO tickets (ticket_id, family, root_cause_id, diagnostics_steps_raw, "
            "diagnostics_procedure, environment, resolution_steps, root_cause_narrative, "
            "upserted_at, pipeline_version) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (tid, "FAM", "FAM/c",
             json.dumps([{"playbook_step_id": "a", "action": "x", "expected_result": "y"}]),
             json.dumps([{"step": 1, "action": "x", "expected_result": "y"}]),
             "{}", "[]", "n", "t", "test"))
    c.commit()
    seed_wiki_pages(c)
    return c


def _write_curation(curation_dir, fam, slug, rc):
    p = curation_dir / fam
    p.mkdir(parents=True, exist_ok=True)
    (p / f"{slug}.curation.json").write_text(json.dumps({
        "root_cause_id": rc, "family": fam, "source_ticket_ids": ["T1", "T2"],
        "curation_model": "m", "pipeline_version": "v", "curated_at": "now",
        "curation": {"title": "Ti", "symptoms": "Sy", "cause": "Ca",
                          "variations": "", "reporting": "Re"},
    }))


def test_load_fills_curated_description(tmp_path):
    conn = _store(tmp_path)
    cdir = tmp_path / "cur"
    _write_curation(cdir, "FAM", "c", "FAM/c")
    applied, missing = L.load(conn, cdir)
    assert (applied, missing) == (1, 0)
    cd = conn.execute(
        "SELECT curated_description FROM wiki_pages WHERE root_cause_id='FAM/c'").fetchone()[0]
    assert json.loads(cd)["title"] == "Ti"


def test_integrity_clean(tmp_path):
    conn = _store(tmp_path)
    assert L.integrity(conn) == (2, 0, 0)   # 2 member links, 0 missing, 0 mismatch


def test_integrity_flags_unknown_member(tmp_path):
    conn = _store(tmp_path)
    conn.execute("UPDATE wiki_pages SET curated_tickets='T1,GHOST' WHERE root_cause_id='FAM/c'")
    conn.commit()
    _links, missing, _mismatch = L.integrity(conn)
    assert missing == 1
