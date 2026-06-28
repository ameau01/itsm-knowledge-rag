"""Deterministic low-hedge guard — judge-free regression check.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

ASSERTIVE = [
    r"\bthe (root )?cause is\b",
    r"\bis caused by\b",
    r"\bis due to\b",
    r"\bprobabl(e|y)\b",
    r"\b(definitely|certainly|clearly)\b",
    r"\bconfirmed (to be|as|that)\b",   # affirmative only — NOT "not confirmed"/"unconfirmed"
]
HEDGE_MARKERS = [
    r"\bmay\b", r"\bmight\b", r"\bcould\b", r"\bpossibl(e|y)\b", r"\bappears\b", r"\bsuggests?\b",
]


@dataclass
class GuardResult:
    ok: bool                 # False if any hard_fail
    hard_fail: list[str]     # assertive patterns matched in a low lead
    soft_warn: bool          # low lead with no hedge marker at all (asserting by omission)


def check_low_hedge(confidence: str, lead: str) -> GuardResult:
    if confidence != "low":
        return GuardResult(ok=True, hard_fail=[], soft_warn=False)
    text = (lead or "").lower()
    hard = [p for p in ASSERTIVE if re.search(p, text)]
    has_hedge = any(re.search(p, text) for p in HEDGE_MARKERS)
    return GuardResult(ok=not hard, hard_fail=hard, soft_warn=not has_hedge)
