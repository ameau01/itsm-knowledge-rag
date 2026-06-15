"""
Corpus extraction helpers — single source of truth for pulling fields out of
HF parquet rows for use by the ingest pipeline and test scripts.

Schema decisions are documented in src/corpus/DECISION.md.
Primitive helpers (to_list, str_or_empty) live in src/corpus/utils.py.
"""

from __future__ import annotations

import json

import pandas as pd

from corpus.utils import str_or_empty, to_list


# ── Diagnostic step extraction (shared base) ───────────────────────────────────

# Field lists for each public step-extraction variant.
# Order determines JSON key order in the output.
_FIELDS_CANONICAL  = ["playbook_step_id", "expected_result", "result_status", "performed_by"]
_FIELDS_RAW        = ["playbook_step_id", "action", "expected_result",
                      "observed_result", "evidence", "result_status", "performed_by"]
_FIELDS_PROCEDURE  = ["action", "expected_result"]


def _extract_steps(
    row: pd.Series,  # type: ignore[type-arg]
    fields: list[str],
    *,
    include_step_number: bool = False,
) -> list[dict[str, object]]:
    """
    Shared step-extraction loop used by all three public variants.

    Args:
        row:                 pandas Series from the HF parquet file.
        fields:              Step attribute names to include (in order).
        include_step_number: If True, prepend {"step": <1-based int>} to each dict.

    Returns [] if diagnostics is absent or has no steps.
    """
    diag = row.get("diagnostics")
    if not isinstance(diag, dict):
        return []

    result = []
    for i, step in enumerate(to_list(diag.get("steps"))):
        step_d = (
            step._asdict()
            if hasattr(step, "_asdict")
            else (dict(step) if isinstance(step, dict) else {})
        )
        entry: dict[str, object] = {}
        if include_step_number:
            entry["step"] = i + 1
        for field in fields:
            entry[field] = str_or_empty(step_d.get(field, ""))
        result.append(entry)
    return result


def extract_diag_steps(row: pd.Series) -> list[dict[str, object]]:  # type: ignore[type-arg]
    """
    Extract diagnostic steps keeping only the fields that define the canonical
    step-set for cardinality / dedup / embedding.

    Fields KEPT (match corpus-cardinality.xlsx exclusion rule):
        playbook_step_id  — canonical playbook step identifier (strongest dedup signal)
        expected_result   — prose describing the expected state (redacted by caller)
        result_status     — pass / fail / inconclusive
        performed_by      — team name

    Fields DROPPED:
        action            — high-variance per-ticket prose; inflates unique count
        observed_result   — per-incident narrative
        evidence          — per-incident artefacts
        step_id           — per-row serial, not meaningful for dedup
    """
    return _extract_steps(row, _FIELDS_CANONICAL)


def extract_diag_steps_raw(row: pd.Series) -> list[dict[str, object]]:  # type: ignore[type-arg]
    """
    Extract diagnostic steps retaining ALL fields — for L1 similarity context
    window and the redaction retention test.

    Fields: step (1-based), playbook_step_id, action, expected_result,
            observed_result, evidence, result_status, performed_by

    observed_result and evidence are per-ticket narratives that appear in
    retention.json — including them ensures retention test coverage.
    See DECISION.md for the full rationale.
    """
    return _extract_steps(row, _FIELDS_RAW, include_step_number=True)


def extract_diag_steps_procedure(row: pd.Series) -> list[dict[str, object]]:  # type: ignore[type-arg]
    """
    Extract diagnostic steps as lean procedure dicts for the wiki generator LLM.

    Fields: step (1-based), action, expected_result

    Rationale: the wiki LLM needs only the procedure instruction (action) and
    the success criterion (expected_result) to synthesise a canonical numbered
    procedure.  All other fields are noise that wastes context tokens.
    See DECISION.md for the full rationale.
    """
    return _extract_steps(row, _FIELDS_PROCEDURE, include_step_number=True)


# ── Observed errors extraction ─────────────────────────────────────────────────

def extract_observed_errors(row: pd.Series) -> list[str]:  # type: ignore[type-arg]
    """
    Return the observed_errors array from diagnostics as a plain Python list.

    These are structured error codes (e.g. '0xC0000234', 'VPN-ERR-201') — not
    free-text prose — so they are NOT run through PII redaction.  They are stored
    as a JSON array for BM25 / sparse-retrieval indexing.

    Returns [] if diagnostics is absent or observed_errors is empty.
    """
    diag = row.get("diagnostics")
    if not isinstance(diag, dict):
        return []
    raw = diag.get("observed_errors")
    if raw is None:
        return []
    return to_list(raw)


# ── Text field extraction ──────────────────────────────────────────────────────

def extract_text_fields(row: pd.Series) -> dict[str, str]:  # type: ignore[type-arg]
    """
    Extract all free-text fields that must be run through PII redaction.

    Returns a dict of field_name → raw text.  Empty strings are omitted.
    All JSON blobs are serialised strings — the redactor treats them as text
    and replaces PII values in-place before storage.

    Field inventory:
      submitted_description    — user's original ticket description
      correspondence           — all message bodies joined with newlines
      diagnostics_summary      — diagnostic summary paragraph
      diagnostics_steps        — JSON array: canonical step dicts
                                 (playbook_step_id, expected_result,
                                 result_status, performed_by)
      diagnostics_steps_raw    — JSON array: full step dicts, all 8 fields
                                 incl. action / observed_result / evidence;
                                 used by L1 context + retention test
      diagnostics_procedure    — JSON array: lean dicts {step, action,
                                 expected_result}; fed to wiki generator LLM
      resolution_steps         — JSON array of resolution step strings
      root_cause_narrative     — engineer's causal summary (root_cause column)

    See src/corpus/DECISION.md for full field-inclusion rationale.
    """
    parts: dict[str, str] = {}

    ticket = row.get("ticket")
    if isinstance(ticket, dict):
        parts["submitted_description"] = str_or_empty(
            ticket.get("submitted_description", "")
        )

    corr = to_list(row.get("correspondence"))
    if corr:
        messages = []
        for c in corr:
            msg = (
                c.get("message", "")
                if hasattr(c, "get")
                else (c._asdict().get("message", "") if hasattr(c, "_asdict") else "")
            )
            if msg:
                messages.append(str_or_empty(msg))
        parts["correspondence"] = "\n".join(messages)

    diag = row.get("diagnostics")
    if isinstance(diag, dict):
        parts["diagnostics_summary"] = str_or_empty(diag.get("summary", ""))

        # Canonical steps — for dedup / embedding / BM25 / cardinality oracle
        steps = extract_diag_steps(row)
        if steps:
            parts["diagnostics_steps"] = json.dumps(steps, ensure_ascii=False)

        # Raw steps — all fields; for L1 context window + retention test
        raw_steps = extract_diag_steps_raw(row)
        if raw_steps:
            parts["diagnostics_steps_raw"] = json.dumps(raw_steps, ensure_ascii=False)

        # Procedure steps — lean {step, action, expected_result}; for wiki LLM
        proc_steps = extract_diag_steps_procedure(row)
        if proc_steps:
            parts["diagnostics_procedure"] = json.dumps(proc_steps, ensure_ascii=False)

    # resolution_steps stored as JSON array so wiki generator can slice
    # a representative subset without parsing a flat text blob.
    res = row.get("resolution")
    if isinstance(res, dict):
        res_list = [str_or_empty(s) for s in to_list(res.get("steps")) if s]
    elif res is not None:
        res_list = [str_or_empty(s) for s in to_list(res) if s]
    else:
        res_list = []
    if res_list:
        parts["resolution_steps"] = json.dumps(res_list, ensure_ascii=False)

    # root_cause is a plain string — engineer's causal summary.
    rc = row.get("root_cause")
    rc_text = str_or_empty(rc).strip() if rc is not None else ""
    if rc_text:
        parts["root_cause_narrative"] = rc_text

    return {k: v for k, v in parts.items() if v}


# ── Metadata extraction ────────────────────────────────────────────────────────

def extract_metadata(
    row: pd.Series,  # type: ignore[type-arg]
    rc_map: dict[str, str] | None = None,
) -> dict[str, object]:
    """
    Extract structured metadata fields (not run through PII redaction).

    Args:
        row:    pandas Series from the HF parquet file.
        rc_map: ticket_id → root_cause_id mapping built from catalog.json.
                Build once before the ingest loop with corpus.catalog.build_rc_map().
                If None, root_cause_id will be None (legacy / test behaviour).

    Returns dict with keys:
        family          str   — 2nd segment of record_id (e.g. 'AIT')
        root_cause_id   str | None — e.g. 'AIT/expired-api-token-auth-failures'
        submitted_at    str | None
        priority        str | None
        sla_plan        str | None
        environment     str | None — JSON-encoded dict {os, platform, region, user_group}
        applications    str | None — JSON-encoded list of app name strings
        diagnostics_coverage  str | None — 'standard' / 'extended' / etc.
    """
    ticket_id = str_or_empty(row.get("record_id"))

    # family — second segment of record_id (always present and correct)
    family = ticket_id.split("-")[1] if ticket_id.count("-") >= 2 else ""

    # root_cause_id — from caller-supplied catalog inversion
    root_cause_id: str | None = rc_map.get(ticket_id) if rc_map else None

    # ticket metadata fields
    ticket = row.get("ticket")
    submitted_at: str | None = None
    priority: str | None = None
    sla_plan: str | None = None
    environment: str | None = None
    applications: str | None = None

    if isinstance(ticket, dict):
        submitted_at = str_or_empty(ticket.get("submitted_at")) or None
        priority = str_or_empty(ticket.get("priority")) or None
        sla_plan = str_or_empty(ticket.get("sla_plan")) or None

        env = ticket.get("environment")
        if env is not None:
            environment = json.dumps(dict(env), ensure_ascii=False)

        apps = ticket.get("applications")
        if apps is not None:
            applications = json.dumps(to_list(apps), ensure_ascii=False)

    # diagnostics coverage
    diag = row.get("diagnostics")
    diagnostics_coverage: str | None = None
    if isinstance(diag, dict):
        cov = diag.get("coverage")
        diagnostics_coverage = str_or_empty(cov) or None

    return {
        "family":               family,
        "root_cause_id":        root_cause_id,
        "submitted_at":         submitted_at,
        "priority":             priority,
        "sla_plan":             sla_plan,
        "environment":          environment,
        "applications":         applications,
        "diagnostics_coverage": diagnostics_coverage,
    }
