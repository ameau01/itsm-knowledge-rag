"""
SLA tier — normalize the free-text `sla_plan` into a small, filterable set of tiers.

The operational store's `sla_plan` is free text (hundreds of distinct strings like
"Gold - 4hr", "standard_24x7", "Business Critical"). For a usable UI filter we bucket it
into a handful of service tiers by keyword, first match wins. Best-effort — the source
text is inconsistent.
"""

from __future__ import annotations

# (keyword, tier label), checked in order. `standard` is checked before `business` so
# "Standard Business Hours" buckets as Standard, not Business.
_TIERS = [
    ("gold", "Gold"),
    ("enterprise", "Enterprise"),
    ("tier", "Tier"),
    ("internal", "Internal"),
    ("standard", "Standard"),
    ("business", "Business"),
]

TIER_LABELS = tuple(label for _, label in _TIERS) + ("Other",)


def sla_tier(sla_plan: str | None) -> str:
    s = (sla_plan or "").lower()
    for keyword, label in _TIERS:
        if keyword in s:
            return label
    return "Other"
