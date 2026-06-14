"""
Extraction oracle tests (Phase 2 safety net).

These tests assert the CORRECT post-fix behaviour of corpus.extractor.
They are written BEFORE the fixes, so they must RED against the Phase 1
(buggy) implementation and GREEN only after Phase 2 fixes are applied.

Five assertions:
  1. family        — non-empty, equals record_id.split('-')[1]
  2. root_cause_id — non-null, from catalog.json inversion
  3. root_cause_narrative — present and non-empty in extract_text_fields()
  4. observed_errors      — non-empty list for tickets with diagnostic errors
  5. diag_cardinality     — unique step-sets per root_cause_id match
                            corpus-cardinality.xlsx for all 76 root causes

Run:
    uv run pytest src/test/test_extraction.py -v
    uv run sh scripts/run_extraction_test.sh
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from corpus.extractor import (
    extract_diag_steps,
    extract_metadata,
    extract_observed_errors,
    extract_text_fields,
)
from ingest.redactor import build_sidecar_index, redact_with_sidecar

# ── Paths ──────────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).parent.parent.parent
_HF_CACHE = _REPO_ROOT / ".hf_cache"
_EVAL_REDACTION = _REPO_ROOT / "eval-set"
_SNAPSHOTS = _HF_CACHE / "datasets--ameau01--synthetic-it-support-tickets" / "snapshots"


# ── Cardinality oracle (from corpus-cardinality.xlsx, Root Causes sheet) ──────
# Unique Diagnostics (excl action, observed_result, evidence; redacted)
# Key: root_cause_id  Value: expected unique step-set count

_DIAG_CARDINALITY: dict[str, int] = {
    "AIT/expired-api-token-auth-failures": 8,
    "AIT/downstream-api-latency-exceeds-timeout": 9,
    "AIT/downstream-rate-limiting-throttling": 2,
    "AIT/stale-retry-backoff-amplifies-latency": 2,
    "AIT/unconfirmed-mixed-credential-latency-throttling": 3,
    "ALP/stale-mobile-cached-credentials": 8,
    "ALP/stale-mobile-credentials-plus-expired-reset-token": 16,
    "ALP/expired-reset-token-primary": 1,
    "ALP/stale-credentials-unidentified-source": 2,
    "CES/renewed-chain-not-deployed-to-lb-with-monitoring-gap": 13,
    "CES/valid-leaf-but-stale-or-missing-intermediate-served": 4,
    "CES/automated-renewal-process-failed-to-complete": 2,
    "CES/wrong-certificate-bound-to-endpoint": 1,
    "CES/unconfirmed-tls-presentation-issue-evidence-gap": 1,
    "DCP/stale-checkin-missing-encryption-signal": 8,
    "DCP/stale-deprecated-compliance-policy-reference": 2,
    "DCP/stale-compliance-state-mismatch-ca-cache": 3,
    "DCP/encryption-telemetry-broken-after-os-or-hardware-change": 2,
    "DCP/encryption-actually-disabled-or-attestation-failed": 2,
    "DCP/indeterminate-compliance-refresh-failure": 2,
    "DRF/stale-resolver-cache-after-record-change": 5,
    "DRF/stale-authoritative-zone-record": 4,
    "DRF/missing-or-incorrect-conditional-forwarder": 9,
    "DRF/resolver-path-inconsistency-mixed-cause": 3,
    "DRF/no-server-side-fault-client-side-or-transient": 1,
    "EDE/tpm-protector-not-initialized": 16,
    "EDE/intune-policy-not-assigned-or-stale-deprecated-policy": 5,
    "EDE/recovery-key-escrow-failure-despite-healthy-tpm-and-policy": 7,
    "EDE/mdm-sync-failure-causing-state-desync": 3,
    "EDE/inconclusive-evidence-bitlocker-not-fully-enabled": 2,
    "LPD/endpoint-scan-backlog-startup-disk-contention": 20,
    "LPD/resource-heavy-startup-policy": 3,
    "LPD/low-disk-temp-file-accumulation": 1,
    "LPD/unconfirmed-transient-post-login-slowdown": 1,
    "OES/stale-corrupted-outlook-desktop-profile-cache": 9,
    "OES/intune-mdm-device-compliance-block": 14,
    "OES/stale-mobile-sync-partnership": 7,
    "OES/exchange-online-mailbox-throttling": 3,
    "OES/unresolved-endpoint-client-sync-state": 6,
    "OES/expired-m365-auth-tokens": 1,
    "OES/suspected-server-side-mailbox-fault": 2,
    "PDQ/corrupt-driver-package-spooler-load-failure": 11,
    "PDQ/stale-queue-driver-mapping": 3,
    "PDQ/spool-directory-permissions": 1,
    "PDQ/queue-left-paused": 1,
    "PDQ/unresolved-rendering-escalation-holding": 1,
    "SDA/missing-ad-security-group-membership": 9,
    "SDA/missing-group-plus-stale-credential-or-acl-compound": 10,
    "SDA/broken-ntfs-acl-inheritance-or-deny-ace": 5,
    "SDA/stale-cached-smb-credentials": 2,
    "SDA/stale-or-wrong-mapped-share-path": 1,
    "SDA/unconfirmed-backend-replication-or-auth-escalated": 1,
    "SIB/missing-entitlement-group-membership": 3,
    "SIB/missing-entitlement-plus-stale-inventory": 4,
    "SIB/missing-entitlement-group-membership-plus-endpoint-protection-block": 4,
    "SIB/endpoint-protection-app-control-block": 5,
    "SIB/endpoint-protection-block-plus-stale-inventory": 16,
    "SIB/missing-entitlement-plus-endpoint-protection-and-stale-inventory": 4,
    "SIB/stale-inventory-policy-targeting-only": 2,
    "SIB/indeterminate-incomplete-telemetry": 2,
    "SML/stale-mfa-factor-enrollment": 7,
    "SML/conditional-access-group-policy-mismatch": 6,
    "SML/combined-stale-enrollment-and-policy-desync": 4,
    "SML/authenticator-clock-drift-totp-mismatch": 2,
    "SML/post-mfa-federation-session-fault": 1,
    "VDA/expired-device-certificate-post-mfa-validation-failure": 11,
    "VDA/stale-vpn-profile-blocking-renewed-certificate": 2,
    "VDA/globalprotect-profile-cert-mapping-misconfiguration": 1,
    "VDA/gateway-portal-post-auth-instability": 1,
    "VDA/indeterminate-intermittent-disconnect": 1,
    "WCI/expired-radius-controller-eap-tls-certificate": 15,
    "WCI/cert-rollover-incomplete-trust-propagation": 3,
    "WCI/stale-or-corrupt-client-wifi-profile": 5,
    "WCI/incorrect-nac-policy-assignment": 5,
    "WCI/wireless-rf-controller-instability": 1,
    "WCI/unclassified-insufficient-evidence": 2,
}

_EXPECTED_TOTAL_UNIQUE = 365


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _latest_snapshot() -> Path | None:
    if not _SNAPSHOTS.exists():
        return None
    snaps = sorted(_SNAPSHOTS.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    return snaps[0] if snaps else None


def _find_sidecar(filename: str) -> Path:
    local = _EVAL_REDACTION / "redaction" / filename
    if local.exists():
        return local
    snap = _latest_snapshot()
    if snap:
        candidate = snap / filename
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"{filename} not found")


@pytest.fixture(scope="module")
def _data() -> dict[str, Any]:
    snap = _latest_snapshot()
    assert snap is not None, "HF snapshot not found — run: uv run sh scripts/test_hf_download.sh"

    df = pd.read_parquet(snap / "data" / "train.parquet")
    pii_records: list[dict] = json.loads(_find_sidecar("pii.json").read_text())
    sidecar_index = build_sidecar_index(pii_records)

    # Build ticket_id → root_cause_id from catalog (the authoritative source)
    catalog = json.loads((_EVAL_REDACTION / "catalog.json").read_text())
    rc_map: dict[str, str] = {}
    for fam in catalog["families"]:
        for rc in fam["root_causes"]:
            for tid in rc["ticket_ids"]:
                rc_map[tid] = rc["root_cause_id"]

    return {"df": df, "sidecar_index": sidecar_index, "rc_map": rc_map}


def _get_row(df: pd.DataFrame, ticket_id: str) -> pd.Series:  # type: ignore[type-arg]
    rows = df[df["record_id"] == ticket_id]
    assert not rows.empty, f"{ticket_id} not found in parquet"
    return rows.iloc[0]


# ── Oracle test 1: family non-empty ───────────────────────────────────────────

def test_family_non_empty(_data: dict[str, Any]) -> None:
    """
    extract_metadata must return a non-empty family equal to the 2nd segment
    of record_id for every ticket.

    PHASE 1: RED — extract_metadata reads ticket['category'] which is absent,
    so family is always ''.
    PHASE 2: GREEN — family = record_id.split('-')[1].
    """
    df = _data["df"]
    failures: list[str] = []
    for _, row in df.iterrows():
        tid = row["record_id"]
        meta = extract_metadata(row)
        expected_family = tid.split("-")[1]
        if meta["family"] != expected_family:
            failures.append(
                f"{tid}: got family={meta['family']!r}, expected {expected_family!r}"
            )
    assert not failures, (
        f"{len(failures)} ticket(s) have wrong family:\n"
        + "\n".join(failures[:10])
        + (f"\n… and {len(failures) - 10} more" if len(failures) > 10 else "")
    )


# ── Oracle test 2: root_cause_id non-null ─────────────────────────────────────

def test_root_cause_id_non_null(_data: dict[str, Any]) -> None:
    """
    extract_metadata must return a non-null root_cause_id for every ticket.

    PHASE 1: RED — extract_metadata treats root_cause as a dict (it's a string),
    so root_cause_id is always None.
    PHASE 2: GREEN — root_cause_id comes from catalog.json inversion.
    """
    df = _data["df"]
    rc_map = _data["rc_map"]
    failures: list[str] = []
    for _, row in df.iterrows():
        tid = row["record_id"]
        meta = extract_metadata(row, rc_map)  # type: ignore[call-arg]
        if meta["root_cause_id"] is None:
            failures.append(f"{tid}: root_cause_id is None (expected {rc_map.get(tid)!r})")
    assert not failures, (
        f"{len(failures)} ticket(s) have null root_cause_id:\n"
        + "\n".join(failures[:10])
        + (f"\n… and {len(failures) - 10} more" if len(failures) > 10 else "")
    )


# ── Oracle test 3: root_cause_narrative non-null ──────────────────────────────

def test_root_cause_narrative_present(_data: dict[str, Any]) -> None:
    """
    extract_text_fields must include a non-empty 'root_cause_narrative' key
    (the root_cause free-text string) for every ticket that has root_cause content.

    PHASE 1: RED — extract_text_fields reads root_cause as a dict and checks
    isinstance(rc, dict) which is always False (rc is a string), so the field
    is never populated.  Also, the key is named 'observations', not
    'root_cause_narrative'.
    PHASE 2: GREEN — field is extracted from the string root_cause column and
    stored under the key 'root_cause_narrative'.
    """
    df = _data["df"]
    failures: list[str] = []
    for _, row in df.iterrows():
        tid = row["record_id"]
        rc = row.get("root_cause")
        if not rc or not str(rc).strip():
            continue  # no root_cause content to assert on
        fields = extract_text_fields(row)
        if "root_cause_narrative" not in fields or not fields["root_cause_narrative"].strip():
            got_key = "observations" if "observations" in fields else "(absent)"
            failures.append(f"{tid}: 'root_cause_narrative' missing; found key {got_key!r}")
    assert not failures, (
        f"{len(failures)} ticket(s) missing root_cause_narrative:\n"
        + "\n".join(failures[:10])
        + (f"\n… and {len(failures) - 10} more" if len(failures) > 10 else "")
    )


# ── Oracle test 4: observed_errors extracted ──────────────────────────────────

def test_observed_errors_extracted(_data: dict[str, Any]) -> None:
    """
    extract_observed_errors must return a non-empty list for every ticket that
    has diagnostic observed_errors entries.

    PHASE 1: RED — extract_observed_errors is a stub that always returns [].
    PHASE 2: GREEN — returns diagnostics['observed_errors'].tolist().
    """
    df = _data["df"]
    failures: list[str] = []
    for _, row in df.iterrows():
        tid = row["record_id"]
        diag = row.get("diagnostics")
        if not isinstance(diag, dict):
            continue
        raw_errors = diag.get("observed_errors")
        if raw_errors is None:
            continue
        raw_list = raw_errors.tolist() if hasattr(raw_errors, "tolist") else list(raw_errors)
        if not raw_list:
            continue  # ticket genuinely has no observed_errors
        extracted = extract_observed_errors(row)
        if not extracted:
            failures.append(
                f"{tid}: raw observed_errors={raw_list[:2]}… "
                "but extract_observed_errors returned []"
            )
    assert not failures, (
        f"{len(failures)} ticket(s) have observed_errors that were not extracted:\n"
        + "\n".join(failures[:10])
        + (f"\n… and {len(failures) - 10} more" if len(failures) > 10 else "")
    )


# ── Oracle test 5: diagnostic step cardinality matches spreadsheet ─────────────

def test_diag_cardinality(_data: dict[str, Any]) -> None:
    """
    After applying the correct field exclusion (drop action, observed_result,
    evidence; keep playbook_step_id, expected_result, result_status,
    performed_by) and PII redaction, the number of unique diagnostic step-sets
    per root_cause_id must match corpus-cardinality.xlsx for all 76 root causes.

    PHASE 1: RED — extract_diag_steps keeps the wrong fields (observed_result,
    evidence included; playbook_step_id and result_status excluded), so the
    unique-set counts will not match the spreadsheet oracle.
    PHASE 2: GREEN — extract_diag_steps returns the correct field set, and
    redaction of expected_result collapses per-ticket variance to the expected
    counts.
    """
    df = _data["df"]
    sidecar_index = _data["sidecar_index"]
    rc_map = _data["rc_map"]

    # Group step-set fingerprints by root_cause_id
    rc_stepsets: dict[str, set[tuple]] = defaultdict(set)  # type: ignore[type-arg]

    for _, row in df.iterrows():
        tid = row["record_id"]
        rc_id = rc_map.get(tid)
        if rc_id is None:
            continue  # ticket not in catalog — skip

        steps = extract_diag_steps(row)
        # Redact expected_result in each step using the sidecar
        redacted_steps = []
        replacements = sidecar_index.get(tid, {})
        for step in steps:
            redacted_step = {}
            for k, v in step.items():
                v_str = str(v)  # values are always str; cast for mypy (dict[str, object])
                if k == "expected_result" and v_str and replacements:
                    redacted_val = redact_with_sidecar(v_str, replacements)
                else:
                    redacted_val = v_str
                redacted_step[k] = redacted_val
            redacted_steps.append(redacted_step)

        # Fingerprint: sorted tuple of (key, value) pairs per step, then as tuple
        fingerprint = tuple(
            tuple(sorted(s.items())) for s in redacted_steps
        )
        rc_stepsets[rc_id].add(fingerprint)

    # Compare against oracle
    failures: list[str] = []
    for rc_id, expected in _DIAG_CARDINALITY.items():
        actual = len(rc_stepsets.get(rc_id, set()))
        if actual != expected:
            failures.append(
                f"  {rc_id}: expected {expected} unique step-sets, got {actual}"
            )

    # Also check total
    total_unique = sum(len(s) for s in rc_stepsets.values())

    assert not failures, (
        f"{len(failures)}/76 root causes have wrong diagnostic cardinality "
        f"(total unique: {total_unique}, expected {_EXPECTED_TOTAL_UNIQUE}):\n"
        + "\n".join(failures)
    )

    assert total_unique == _EXPECTED_TOTAL_UNIQUE, (
        f"Total unique diagnostic step-sets: {total_unique}, "
        f"expected {_EXPECTED_TOTAL_UNIQUE}"
    )


# ── Main (direct run) ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import subprocess
    import sys
    sys.exit(subprocess.call(
        ["python", "-m", "pytest", __file__, "-v"],
        cwd=str(_REPO_ROOT),
    ))
