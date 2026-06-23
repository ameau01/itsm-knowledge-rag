"""Canonical diagnostic-playbook derivation (deterministic, no LLM).

`diagnostic_steps` for a wiki page is the canonical playbook for its root cause, not a
modal of free-text wording. The member tickets run the same playbook (one
`playbook_step_id` sequence for 68/76 root causes); only the free-text `action` wording
varies per ticket. So: group the members' `diagnostics_steps_raw` by `playbook_step_id`,
take the modal canonical sequence, and render each step with its most-common
`action` + `expected_result`.

Source field: `diagnostics_steps_raw` is the only column carrying BOTH `playbook_step_id`
and `action` (`diagnostics_steps` has the id but no action; `diagnostics_procedure` has the
action but no id).

Fallback: when `playbook_step_id` is the over-redacted token `<HOSTNAME>` (the LPD redaction
bug), canonical grouping is impossible — fall back to the free-text modal of
`diagnostics_procedure` for that root cause.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter

_BROKEN_PLAYBOOK_ID = "<HOSTNAME>"


def _loads(value) -> list:
    try:
        out = json.loads(value) if value else []
    except (json.JSONDecodeError, TypeError):
        return []
    return out if isinstance(out, list) else []


def _renumber(steps: list) -> list:
    """Emit a clean [{step, action, expected_result}] list with 1-based step numbers."""
    return [
        {"step": i, "action": s.get("action", ""),
         "expected_result": s.get("expected_result", "")}
        for i, s in enumerate(steps, 1) if isinstance(s, dict)
    ]


def _free_text_modal(conn: sqlite3.Connection, root_cause_id: str) -> list:
    procs: Counter = Counter()
    rep: dict = {}
    for (dp,) in conn.execute(
        "SELECT diagnostics_procedure FROM tickets WHERE root_cause_id = ? ORDER BY ticket_id",
        (root_cause_id,),
    ):
        proc = _loads(dp)
        key = tuple(s.get("action", "") for s in proc if isinstance(s, dict))
        procs[key] += 1
        rep.setdefault(key, proc)
    if not procs:
        return []
    key, _freq = procs.most_common(1)[0]
    return _renumber(rep[key])


def canonical_diagnostic_steps(conn: sqlite3.Connection, root_cause_id: str) -> list:
    """The canonical diagnostic playbook for a root cause, as [{step, action, expected_result}]."""
    raws = [
        _loads(r[0]) for r in conn.execute(
            "SELECT diagnostics_steps_raw FROM tickets WHERE root_cause_id = ? ORDER BY ticket_id",
            (root_cause_id,),
        )
    ]
    raws = [r for r in raws if r]
    if not raws:
        return []

    # LPD over-redaction: playbook ids are unusable -> free-text fallback.
    if any(s.get("playbook_step_id") == _BROKEN_PLAYBOOK_ID for r in raws for s in r):
        return _free_text_modal(conn, root_cause_id)

    # Modal canonical sequence of playbook_step_ids (uniform for most root causes).
    seqs = Counter(tuple(s.get("playbook_step_id") for s in r) for r in raws)
    canon_seq, _freq = seqs.most_common(1)[0]

    # Most-common (action, expected_result) wording per playbook_step_id, across all members.
    wording: dict = {}
    for r in raws:
        for s in r:
            pid = s.get("playbook_step_id")
            wording.setdefault(pid, Counter())[
                (s.get("action", ""), s.get("expected_result", ""))
            ] += 1

    out = []
    for i, pid in enumerate(canon_seq, 1):
        if not wording.get(pid):
            continue
        (action, expected), _ = wording[pid].most_common(1)[0]
        out.append({"step": i, "action": action, "expected_result": expected})
    return out
