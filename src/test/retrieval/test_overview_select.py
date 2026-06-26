"""retrieval.overview_select — vote + guardrail + ambiguous flag (pure), and the graceful-NULL
contract against the real store.get_ai_overview. No Qdrant, no network."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/ on path

from operational_store.store import build_card_lookup, get_ai_overview   # noqa: E402
from retrieval import overview_select as S                                # noqa: E402

A, B = "VDA/expired-cert", "OES/throttle"


# ── pure vote / fusion ──────────────────────────────────────────────────────────
def test_clean_win():
    ranked = [A, A, A, B]
    w, m = S.pick_winner(S.tally(ranked), ranked)
    assert w == A and m > 0.3


def test_thin_margin():
    ranked = [A, B, A, B]
    _, m = S.pick_winner(S.tally(ranked), ranked)
    assert m < 0.1


def test_guardrail_override_margin_zero():
    # B out-totals A on volume, but A owns ranks 0 & 1 -> override -> winner A, margin 0.
    ranked = [A, A, B, B, B, B, B, B]
    scores = S.tally(ranked)
    assert scores[B] > scores[A]
    w, m = S.pick_winner(scores, ranked)
    assert w == A and m == 0.0


def test_null_skip_and_empty():
    ranked = [None, A, A, None]
    assert None not in S.tally(ranked)
    assert S.pick_winner(S.tally([]), []) == (None, 0.0)


def test_reconstruct():
    assert S.reconstruct_rc("VDA", "expired-cert") == "VDA/expired-cert"
    assert S.reconstruct_rc("", "x") is None and S.reconstruct_rc("VDA", None) is None


# ── select_overview behavioural paths ────────────────────────────────────────────
def _fake_get(conn, rc):
    return {"family": rc.split("/")[0], "root_cause_id": rc,
            "ai_overview": {"confidence": "high", "lead": "x"},
            "curated_description": {"cause": "c"}, "diagnostic_steps": [], "curated_tickets": "a,b"}


def test_clean_selection():
    lookup = {("t1", "description"): {"family": "VDA", "root_cause": "expired-cert"},
              ("t2", "description"): {"family": "VDA", "root_cause": "expired-cert"}}
    keys = [("t1", "description"), ("t2", "description")]
    sel = S.select_overview(keys, lookup, None, get_ai_overview=_fake_get)
    assert sel.root_cause_id == "VDA/expired-cert"
    assert sel.confidence == "high" and sel.ambiguous is False


def test_ambiguous_surfaces_runner_up():
    keys = [("a1", "description"), ("a2", "description")] + \
           [(f"b{i}", "description") for i in range(6)]
    lookup = {k: {"family": "VDA", "root_cause": "alpha"} for k in keys[:2]}
    lookup.update({k: {"family": "OES", "root_cause": "beta"} for k in keys[2:]})
    sel = S.select_overview(keys, lookup, None, get_ai_overview=_fake_get)
    assert sel.root_cause_id == "VDA/alpha" and sel.ambiguous is True
    assert sel.selection_margin == 0.0 and sel.runner_up == "OES/beta"
    assert sel.confidence == "high"   # static, unchanged by ambiguity


def test_empty_keys_returns_none():
    assert S.select_overview([], {}, None, get_ai_overview=_fake_get) is None


# ── the graceful-NULL contract against the REAL store.get_ai_overview ─────────────
def _wiki(conn, *, with_col, ai_overview=None):
    cols = "family TEXT, root_cause_id TEXT, curated_description TEXT, diagnostic_steps TEXT, curated_tickets TEXT"
    if with_col:
        cols += ", ai_overview TEXT, ai_overview_details TEXT"
    conn.execute(f"CREATE TABLE wiki_pages ({cols})")
    if with_col:
        conn.execute("INSERT INTO wiki_pages (family, root_cause_id, ai_overview) VALUES (?,?,?)",
                     ("VDA", "VDA/x", ai_overview))
    else:
        conn.execute("INSERT INTO wiki_pages (family, root_cause_id) VALUES (?,?)", ("VDA", "VDA/x"))
    conn.commit()


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE tickets (ticket_id TEXT, family TEXT, root_cause_id TEXT)")
    return c


def test_get_ai_overview_missing_column_returns_none():
    c = _conn()
    _wiki(c, with_col=False)
    assert get_ai_overview(c, "VDA/x") is None      # no error, just None


def test_get_ai_overview_null_cell_returns_none():
    c = _conn()
    _wiki(c, with_col=True, ai_overview=None)
    assert get_ai_overview(c, "VDA/x") is None


def test_get_ai_overview_no_row_returns_none():
    c = _conn()
    _wiki(c, with_col=True, ai_overview=None)
    assert get_ai_overview(c, "NOPE/missing") is None


def test_select_overview_quiet_on_null():
    # End-to-end graceful path: real get_ai_overview on a NULL cell -> select_overview returns None.
    c = _conn()
    c.execute("INSERT INTO tickets VALUES ('t1','VDA','VDA/x')")
    c.commit()
    _wiki(c, with_col=True, ai_overview=None)
    lookup = build_card_lookup(c)
    sel = S.select_overview([("t1", "description")], lookup, c)   # real get_ai_overview
    assert sel is None
