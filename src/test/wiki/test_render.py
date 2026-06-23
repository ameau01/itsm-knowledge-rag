"""wiki.render — curated page vs NULL-curation placeholder (deterministic, no mkdocs build)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/ on path

import pytest  # noqa: F401

import wiki.render as R
from operational_store.store import (
    get_connection,
    init_db,
    seed_wiki_pages,
    update_wiki_curation,
)

_ENV = {"os": "Win10", "platform": "Laptop", "region": "us-east-1", "user_group": "Sales"}


def _store(tmp_path):
    c = get_connection(tmp_path / "t.db")
    init_db(c)
    for tid in ("T1", "T2", "T3"):
        c.execute(
            "INSERT INTO tickets (ticket_id, family, root_cause_id, diagnostics_steps_raw, "
            "diagnostics_procedure, environment, resolution_steps, root_cause_narrative, "
            "upserted_at, pipeline_version) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (tid, "FAM", "FAM/cause-x",
             json.dumps([{"playbook_step_id": "a", "action": "Check A", "expected_result": "ok"}]),
             json.dumps([{"step": 1, "action": "Check A", "expected_result": "ok"}]),
             json.dumps(_ENV),
             json.dumps(["fix one", "fix two", "fix three", "fix four"]),
             "narr", "t", "test"))
    c.commit()
    seed_wiki_pages(c)
    return c


def _mkdocs(tmp_path):
    m = tmp_path / "mk"
    (m / "docs").mkdir(parents=True)
    (m / "mkdocs.yml").write_text("site_name: T\ndocs_dir: docs\n")
    return m


def test_render_curated_page(tmp_path):
    conn = _store(tmp_path)
    update_wiki_curation(
        conn, "FAM", "FAM/cause-x",
        json.dumps({"title": "Nice Title", "symptoms": "Symp text", "cause": "Cause text",
                    "variations": "", "reporting": "Contact IT"}),
        json.dumps({"model": "m"}))
    mk = _mkdocs(tmp_path)
    assert R.render_all(conn, mk) == (1, 1)
    md = (mk / "docs" / "wiki" / "FAM" / "cause-x.md").read_text()
    assert "# Nice Title" in md
    assert "## Description" in md and "Symp text" in md
    assert "## Diagnostics" in md and "Check A" in md
    assert "## Affected environment" in md


def test_render_placeholder_when_uncurated(tmp_path):
    conn = _store(tmp_path)            # seeded but NOT curated
    mk = _mkdocs(tmp_path)
    assert R.render_all(conn, mk) == (1, 0)
    md = (mk / "docs" / "wiki" / "FAM" / "cause-x.md").read_text()
    assert "Curation pending" in md
    assert "## Description" not in md   # curated-only section absent
    assert "## Diagnostics" in md       # deterministic sections still rendered
    assert "## Affected environment" in md
