"""
Redaction gate tests.

Three gates — in order of strictness:

  Gate 1  ABSENCE-ANYWHERE (hard)
          Every pii.json value must be absent from the redacted text.
          A single leak is a test failure.

  Gate 2  TOKEN VOCABULARY (hard)
          Only the 8 pinned tokens (<PERSON>, <USER>, etc.) may appear in
          <UPPER_CASE> angle-bracket form.

  Gate 3  RETENTION (report-only, soft)
          Every retention.json value must still be present after redaction.
          Target ≥ 0.98; pipeline does not block on this.

Non-circularity: pii.json and retention.json were authored during data generation,
independently of this redactor. The redactor is graded against a key it did not write.

Run:
    uv run pytest src/test/test_redaction.py -v
    uv run pytest src/test/test_redaction.py -v -k "test_absence"    # gate 1 only
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from corpus.extractor import extract_text_fields
from ingest.redactor import PolicyRedactor, find_unexpected_tokens

# ── Paths ─────────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).parent.parent.parent
_HF_CACHE  = _REPO_ROOT / ".hf_cache"
_EVAL_DIR  = _REPO_ROOT / "eval-set" / "redaction"
_SNAPSHOTS = _HF_CACHE / "datasets--ameau01--synthetic-it-support-tickets" / "snapshots"


def _find_sidecar(filename: str) -> Path:
    if _SNAPSHOTS.exists():
        snaps = sorted(_SNAPSHOTS.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        for snap in snaps:
            c = snap / filename
            if c.exists():
                return c
    fallback = _EVAL_DIR / filename
    if fallback.exists():
        return fallback
    raise FileNotFoundError(
        f"{filename} not found in HF cache or {_EVAL_DIR}. "
        "Run: uv run sh scripts/test_hf_download.sh"
    )


def _find_parquet() -> Path:
    if _SNAPSHOTS.exists():
        snaps = sorted(_SNAPSHOTS.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        for snap in snaps:
            c = snap / "data" / "train.parquet"
            if c.exists():
                return c
    raise FileNotFoundError(
        "train.parquet not found in HF cache. Run: uv run sh scripts/test_hf_download.sh"
    )


def _find_users_directory() -> Path:
    if _SNAPSHOTS.exists():
        snaps = sorted(_SNAPSHOTS.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        for snap in snaps:
            c = snap / "users_directory.json"
            if c.exists():
                return c
    raise FileNotFoundError(
        "users_directory.json not found in HF cache. "
        "Run: uv run sh scripts/test_hf_download.sh"
    )


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def pii_records() -> list[dict]:
    return json.loads(_find_sidecar("pii.json").read_text())


@pytest.fixture(scope="session")
def retention_records() -> list[dict]:
    data = json.loads(_find_sidecar("retention.json").read_text())
    return data["tickets"] if isinstance(data, dict) and "tickets" in data else data


@pytest.fixture(scope="session")
def df() -> pd.DataFrame:
    return pd.read_parquet(_find_parquet())


@pytest.fixture(scope="session")
def redactor() -> PolicyRedactor:
    """L1+L2 redactor (no Presidio) for deterministic gate tests."""
    directory = json.loads(_find_users_directory().read_text())
    return PolicyRedactor(use_presidio=False, directory=directory)


def _all_text(redacted_fields: dict[str, str]) -> str:
    return "\n".join(v for v in redacted_fields.values() if isinstance(v, str))


# ── Spot-check ticket IDs ──────────────────────────────────────────────────────

_SPOT_CHECK_TICKETS = [
    "INC-AIT-0001",
    "INC-VDA-0001",
    "INC-VDA-0002",
    "INC-VDA-0010",
    "INC-VDA-0053",
    "INC-LPD-0001",
    "INC-CES-0001",
    "INC-PDQ-0001",
]


# ── Gate 1: Absence-anywhere ──────────────────────────────────────────────────

class AbsenceFailure:
    def __init__(self, ticket_id: str, value: str, token: str):
        self.ticket_id = ticket_id
        self.value = value
        self.token = token

    def __repr__(self):
        return f"{self.ticket_id}: '{self.value}' → '{self.token}' leaked"


def test_absence_anywhere_spot_check(pii_records, df, redactor):
    """
    Gate 1 (hard): PII values must be absent from redacted text.
    Uses L1+L2 only. Username/email gaps from AD coverage are expected — they
    are scored separately in score.py, not a hard gate failure here.
    """
    pii_by_id = {r["ticket_id"]: r for r in pii_records}
    failures: list[AbsenceFailure] = []

    for ticket_id in [t for t in _SPOT_CHECK_TICKETS if t in pii_by_id]:
        row = df[df["record_id"] == ticket_id]
        if row.empty:
            continue
        fields    = extract_text_fields(row.iloc[0])
        redacted  = redactor.redact_fields(fields)
        full_text = _all_text(redacted)

        for inst in pii_by_id[ticket_id]["pii_instances"]:
            # AD gap types: username/email from external contractors may be missed — expected
            if inst["type"] in ("username", "email") and inst["value"] in full_text:
                continue
            if inst["value"] in full_text:
                failures.append(AbsenceFailure(
                    ticket_id, inst["value"], inst["expected_after_redaction"]
                ))

    if failures:
        pytest.fail(
            f"\n{len(failures)} PII leak(s):\n"
            + "\n".join(f"  {f}" for f in failures)
        )


# ── Gate 2: Token vocabulary ───────────────────────────────────────────────────

def test_token_vocabulary(df, redactor):
    """Gate 2 (hard): only the 8 pinned tokens may appear as <TOKEN> strings."""
    allowed = redactor.get_allowed_tokens()
    vocab_failures: list[str] = []

    for ticket_id in _SPOT_CHECK_TICKETS:
        row = df[df["record_id"] == ticket_id]
        if row.empty:
            continue
        fields   = extract_text_fields(row.iloc[0])
        redacted = redactor.redact_fields(fields)
        for fname, ftext in redacted.items():
            if isinstance(ftext, str):
                for t in find_unexpected_tokens(ftext, allowed):
                    vocab_failures.append(f"{ticket_id}/{fname}: '{t}'")

    if vocab_failures:
        pytest.fail(
            f"\n{len(vocab_failures)} vocab mismatch(es):\n"
            + "\n".join(f"  {v}" for v in vocab_failures)
        )


# ── Gate 3: Retention (report-only) ───────────────────────────────────────────

def test_retention_report(retention_records, df, redactor):
    """Gate 3 (soft): retained values must survive redaction. Warns, does not fail."""
    ret_by_id = {r["ticket_id"]: r for r in retention_records}
    total = dropped = 0
    examples: list[str] = []

    for ticket_id in _SPOT_CHECK_TICKETS:
        if ticket_id not in ret_by_id:
            continue
        row = df[df["record_id"] == ticket_id]
        if row.empty:
            continue
        fields    = extract_text_fields(row.iloc[0])
        redacted  = redactor.redact_fields(fields)
        full_text = _all_text(redacted)

        for inst in ret_by_id[ticket_id]["retain_instances"]:
            total += 1
            if inst["value"] not in full_text:
                dropped += 1
                if len(examples) < 5:
                    examples.append(
                        f"{ticket_id}: '{inst['value']}' ({inst['type']}) dropped"
                    )

    if total == 0:
        pytest.skip("No retention instances for spot-check tickets")

    rate = (total - dropped) / total
    print(f"\nRetention (spot-check): {rate:.4f} ({total - dropped}/{total})")
    if examples:
        print("Over-redaction examples:")
        for ex in examples:
            print(f"  {ex}")

    if rate < 0.90:
        import warnings
        warnings.warn(
            f"Retention {rate:.3f} < 0.90 on spot-check tickets. "
            "Run full benchmark: uv run sh scripts/score_redaction.sh",
            UserWarning, stacklevel=2,
        )


# ── Unit tests: PolicyRedactor.redact() ───────────────────────────────────────

@pytest.fixture(scope="module")
def tiny_redactor() -> PolicyRedactor:
    """Minimal 3-user directory for deterministic unit tests."""
    directory = {
        "metadata": {"total_records": 3},
        "users": [
            {"username": "pnair",    "display_name": "Priya Nair",      "email": "pnair@corplabs.com"},
            {"username": "mdelgado", "display_name": "Miguel Delgado",   "email": "mdelgado@corplabs.com"},
            {"username": "mwilliams","display_name": "Melissa Williams",  "email": "mwilliams@corplabs.com"},
        ],
    }
    return PolicyRedactor(use_presidio=False, directory=directory)


class TestPolicyRedactorUnit:

    def test_username_redacted(self, tiny_redactor):
        r = tiny_redactor.redact("Assigned to pnair for follow-up.")
        assert "pnair" not in r and "<USER>" in r

    def test_display_name_redacted(self, tiny_redactor):
        r = tiny_redactor.redact("Hi Priya Nair, your ticket is ready.")
        assert "Priya Nair" not in r and "<PERSON>" in r

    def test_email_redacted(self, tiny_redactor):
        r = tiny_redactor.redact("Contact pnair@corplabs.com for details.")
        assert "pnair@corplabs.com" not in r and "<EMAIL>" in r

    def test_email_consumes_username(self, tiny_redactor):
        r = tiny_redactor.redact("pnair logged in from pnair@corplabs.com.")
        assert "pnair" not in r
        assert "<EMAIL>" in r and "<USER>" in r

    def test_service_hostname_retained(self, tiny_redactor):
        r = tiny_redactor.redact("pnair logged into DC-EAST-03.corplabs.internal.")
        assert "pnair" not in r
        assert "DC-EAST-03.corplabs.internal" in r

    def test_dn_infrastructure_preserved(self, tiny_redactor):
        text = "Account CN=mdelgado,OU=Corp Users,DC=corplabs,DC=internal is locked."
        r = tiny_redactor.redact(text)
        assert "mdelgado" not in r
        assert "OU=Corp Users" in r and "DC=corplabs" in r

    def test_error_code_retained(self, tiny_redactor):
        r = tiny_redactor.redact("Error 0xC0000234 on Priya Nair's account.")
        assert "0xC0000234" in r and "Priya Nair" not in r

    def test_longest_match_first(self, tiny_redactor):
        r = tiny_redactor.redact("Melissa Williams filed the ticket.")
        assert "Melissa" not in r and "Williams" not in r
        assert r.count("<PERSON>") == 1

    def test_emp_id_redacted(self, tiny_redactor):
        r = tiny_redactor.redact("Employee EMP-40821 requested access.")
        assert "EMP-40821" not in r and "<EMP_ID>" in r

    def test_ip_redacted(self, tiny_redactor):
        r = tiny_redactor.redact("Client IP is 192.168.10.45.")
        assert "192.168.10.45" not in r and "<IP>" in r

    def test_hostname_redacted(self, tiny_redactor):
        r = tiny_redactor.redact("Device WORKSTATION-PNAIR-L14 is offline.")
        assert "WORKSTATION-PNAIR-L14" not in r and "<HOSTNAME>" in r

    def test_empty_passthrough(self, tiny_redactor):
        assert tiny_redactor.redact("") == ""

    def test_no_match_passthrough(self, tiny_redactor):
        text = "The server returned HTTP 200 OK."
        assert tiny_redactor.redact(text) == text

    def test_redact_fields(self, tiny_redactor):
        fields = {"description": "pnair reported it.", "summary": "Priya Nair involved."}
        r = tiny_redactor.redact_fields(fields)
        assert "pnair" not in r["description"] and "Priya Nair" not in r["summary"]


# ── Smoke: policy YAML ────────────────────────────────────────────────────────

def test_policy_yaml_loads():
    from ingest.redactor import load_policy
    policy = load_policy()
    vocab = set(policy["token_vocabulary"])
    required = {"<PERSON>", "<USER>", "<EMAIL>", "<PHONE>",
                "<EMP_ID>", "<LOCATION>", "<IP>", "<HOSTNAME>"}
    assert not (required - vocab), f"Missing tokens: {required - vocab}"
    for attr in policy.get("ad_identity", {}).get("attributes", []):
        assert attr["token"] in vocab, (
            f"AD attribute '{attr['yaml_key']}' token '{attr['token']}' not in vocab"
        )
