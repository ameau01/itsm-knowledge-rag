"""SLA tier normalization tests."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # src/ on path

from corpus.sla import TIER_LABELS, sla_tier


def test_known_examples():
    assert sla_tier("Gold - 4 hour response") == "Gold"
    assert sla_tier("Standard 24x7") == "Standard"
    assert sla_tier("Standard Business Hours (8x5)") == "Standard"   # standard before business
    assert sla_tier("Business Critical") == "Business"
    assert sla_tier("Enterprise - 4hr Response") == "Enterprise"
    assert sla_tier("Internal Infrastructure SLA") == "Internal"
    assert sla_tier("Tier 1 - 4 hour response") == "Tier"
    assert sla_tier("standard_24x7") == "Standard"


def test_unknown_and_empty():
    assert sla_tier("") == "Other"
    assert sla_tier(None) == "Other"
    assert sla_tier("Platinum membership") == "Other"


def test_collapses_to_small_set_over_real_corpus():
    db = Path(__file__).resolve().parents[2] / ".operational_store" / "itsm_rag.db"
    if not db.exists():
        return  # store not present; unit cases above still cover the logic
    con = sqlite3.connect(db)
    vals = [r[0] for r in con.execute("SELECT DISTINCT sla_plan FROM tickets")]
    con.close()
    tiers = {sla_tier(v) for v in vals}
    assert tiers <= set(TIER_LABELS)
    assert len(tiers) <= len(TIER_LABELS)
