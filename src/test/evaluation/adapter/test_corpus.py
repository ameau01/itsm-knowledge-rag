"""Corpus reader — against the real operational store (skips if absent)."""

from __future__ import annotations

from pathlib import Path

import pytest

from evaluation.adapter.corpus import SECTION_COLUMNS, CorpusReader

# src/test/evaluation/adapter/test_corpus.py -> parents[4] = repo root
_DB = Path(__file__).resolve().parents[4] / ".operational_store" / "itsm_rag.db"
pytestmark = pytest.mark.skipif(not _DB.exists(), reason="operational store not present")

# render_section flattening is unit-tested in src/test/test_sections.py (no DB needed).


def test_section_text_and_narrative_resolve():
    with CorpusReader(_DB) as c:
        txt = c.section_text("INC-AIT-0001", "description")
        assert isinstance(txt, str) and txt
        narr = c.narratives(["INC-AIT-0001"])
        assert "INC-AIT-0001" in narr


def test_every_section_name_maps_to_a_real_column():
    with CorpusReader(_DB) as c:
        cols = {r[1] for r in c._conn.execute("PRAGMA table_info(tickets)")}
    assert set(SECTION_COLUMNS.values()) <= cols


def test_unknown_section_raises():
    with CorpusReader(_DB) as c, pytest.raises(KeyError):
        c.section_text("INC-AIT-0001", "bogus-section")
