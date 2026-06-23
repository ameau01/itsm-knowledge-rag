"""Resolver — honors deduplicated / capped_at for the gold context; pool is uncapped."""

from __future__ import annotations

from evaluation.curation.resolver import (
    evidence_pool,
    gold_context,
    page_meta,
    synthesize_gold_candidate,
)
from operational_store.store import get_connection, init_db

_RECORD = {
    "root_cause_id": "VDA/x",
    "family": "VDA",
    "curated_tickets": ["T1", "T2", "T3"],
    "curated_description": {
        "title": "Ti", "symptoms": "Sy", "cause": "Ca", "variations": "Va", "reporting": "Re",
    },
    "source_sections": {
        "title": ["submitted_description", "correspondence", "root_cause_narrative",
                  "diagnostics_summary"],
        "symptoms": ["submitted_description", "correspondence"],
        "variations": ["submitted_description", "correspondence"],
        "cause": ["root_cause_narrative", "diagnostics_summary"],
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


def _store(tmp_path):
    c = get_connection(tmp_path / "t.db")
    init_db(c)
    for tid, (sd, co, narr, ds) in _TICKETS.items():
        c.execute(
            "INSERT INTO tickets (ticket_id, family, root_cause_id, submitted_description, "
            "correspondence, root_cause_narrative, diagnostics_summary, upserted_at, "
            "pipeline_version) VALUES (?,?,?,?,?,?,?,?,?)",
            (tid, "VDA", "VDA/x", sd, co, narr, ds, "t", "test"),
        )
    c.commit()
    return c


def test_gold_context_honors_dedup_and_cap(tmp_path):
    ctx = gold_context(_store(tmp_path), _RECORD)
    # cause = root_cause_narrative (deduped: NARR once) + diagnostics_summary (capped@2: T1,T2)
    assert ctx["cause"] == ["NARR", "NARR3", "ds1", "ds2"]
    # symptoms = submitted_description(all) + correspondence(all)
    assert ctx["symptoms"] == ["sd1", "sd2", "sd3", "co1", "co2", "co3"]


def test_evidence_pool_is_uncapped_undeduped(tmp_path):
    pool = evidence_pool(_store(tmp_path), _RECORD)
    # full pool keeps the duplicate narrative and the uncapped 3rd diagnostics summary
    assert pool["cause"] == ["NARR", "NARR", "NARR3", "ds1", "ds2", "ds3"]


def test_synthesize_gold_candidate(tmp_path):
    cand = synthesize_gold_candidate(_store(tmp_path), _RECORD)
    assert cand.arm == "gold"
    assert cand.curation["title"] == "Ti"
    assert cand.context["cause"] == ["NARR", "NARR3", "ds1", "ds2"]


def test_page_meta(tmp_path):
    meta = page_meta(_store(tmp_path), _RECORD)
    assert meta.n_members == 3 and meta.multi_ticket is True
