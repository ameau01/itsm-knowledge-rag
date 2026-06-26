"""Resolver — recipe is content-free; curation read from wiki_pages; source from tickets.

Asserts: recipe_context honors dedup/cap, evidence_pool is uncapped, the curation under test
comes from wiki_pages (not the recipe), and missing/empty curation is detected for the
short-circuit."""

from __future__ import annotations

import json

from evaluation.curation.resolver import (
    curation_candidate,
    evidence_pool,
    has_curation,
    missing_curation,
    page_meta,
    recipe_context,
    store_curation,
)
from operational_store.store import get_connection, init_db

# Content-free recipe: ids + sections + scope only (no curated_description).
_RECORD = {
    "root_cause_id": "VDA/x",
    "family": "VDA",
    "curated_tickets": ["T1", "T2", "T3"],
    "source_sections": {
        "title": ["root_cause_narrative"],          # the page IS one root cause
        "symptoms": ["submitted_description", "correspondence"],
        "variations": ["submitted_description", "correspondence"],
        "cause": ["root_cause_narrative", "diagnostics_summary"],
        "diagnostic_summary": ["diagnostics_summary"],
        "reporting": [],
    },
    "input_scope": {
        "submitted_description": {"ticket_ids": ["T1", "T2", "T3"]},
        "correspondence": {"ticket_ids": ["T1", "T2", "T3"]},
        "root_cause_narrative": {"ticket_ids": ["T1", "T2", "T3"], "deduplicated": True},
        "diagnostics_summary": {"ticket_ids": ["T1", "T2", "T3"], "capped_at": 2},
    },
}
_TICKETS = {
    "T1": ("sd1", "co1", "NARR", "ds1"),
    "T2": ("sd2", "co2", "NARR", "ds2"),   # narrative duplicates T1
    "T3": ("sd3", "co3", "NARR3", "ds3"),
}
_CURATION = {"title": "Ti", "symptoms": "Sy", "cause": "Ca", "variations": "Va",
             "diagnostic_summary": "Dg", "reporting": "Re"}


def _store(tmp_path, *, curate=True, name="t"):
    c = get_connection(tmp_path / f"{name}.db")
    init_db(c)
    for tid, (sd, co, narr, ds) in _TICKETS.items():
        c.execute(
            "INSERT INTO tickets (ticket_id, family, root_cause_id, submitted_description, "
            "correspondence, root_cause_narrative, diagnostics_summary, upserted_at, "
            "pipeline_version) VALUES (?,?,?,?,?,?,?,?,?)",
            (tid, "VDA", "VDA/x", sd, co, narr, ds, "t", "test"),
        )
    cd = json.dumps(_CURATION) if curate else None   # None = uncurated page
    c.execute(
        "INSERT INTO wiki_pages (family, root_cause_id, curated_description, curated_tickets, "
        "upserted_at) VALUES (?,?,?,?,?)",
        ("VDA", "VDA/x", cd, "T1,T2,T3", "t"),
    )
    c.commit()
    return c


# ── source (tickets) ────────────────────────────────────────────────────────────
def test_recipe_context_honors_dedup_and_cap(tmp_path):
    ctx = recipe_context(_store(tmp_path), _RECORD)
    assert ctx["title"] == ["NARR", "NARR3"]                          # narrative only, deduped
    assert ctx["cause"] == ["NARR", "NARR3", "ds1", "ds2"]            # deduped narr + capped@2
    assert ctx["symptoms"] == ["sd1", "sd2", "sd3", "co1", "co2", "co3"]
    assert ctx["diagnostic_summary"] == ["ds1", "ds2"]               # diagnostics_summary, capped@2


def test_evidence_pool_is_uncapped_undeduped(tmp_path):
    pool = evidence_pool(_store(tmp_path), _RECORD)
    assert pool["cause"] == ["NARR", "NARR", "NARR3", "ds1", "ds2", "ds3"]


# ── subject (wiki_pages) ──────────────────────────────────────────────────────────
def test_store_curation_reads_wiki_pages(tmp_path):
    cur = store_curation(_store(tmp_path), "VDA", "VDA/x")
    assert cur["title"] == "Ti" and cur["symptoms"] == "Sy"


def test_store_curation_empty_when_uncurated(tmp_path):
    assert store_curation(_store(tmp_path, curate=False, name="a"), "VDA", "VDA/x") == {}
    assert store_curation(_store(tmp_path, name="b"), "VDA", "VDA/missing") == {}   # no such row


def test_curation_candidate_subject_from_store(tmp_path):
    cand = curation_candidate(_store(tmp_path), _RECORD)
    assert cand.arm == "curated"
    assert cand.curation["title"] == "Ti"                 # subject from wiki_pages, not recipe
    assert cand.context["cause"] == ["NARR", "NARR3", "ds1", "ds2"]   # faithfulness ref


# ── short-circuit detector ────────────────────────────────────────────────────────
def test_missing_curation_flags_empty(tmp_path):
    assert has_curation(_CURATION) is True
    assert has_curation({}) is False
    assert missing_curation(_store(tmp_path, name="a"), [_RECORD]) == []             # curated -> ok
    assert missing_curation(_store(tmp_path, curate=False, name="b"), [_RECORD]) == ["VDA/x"]


def test_page_meta(tmp_path):
    meta = page_meta(_store(tmp_path), _RECORD)
    assert meta.n_members == 3 and meta.multi_ticket is True
