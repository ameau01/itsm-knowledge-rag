"""
Redaction gate tests.

Three gates — in order of strictness:

  Gate 1  ABSENCE-ANYWHERE (hard)
          Every pii.json value must be absent from the redacted text.
          A single leak is a test failure. This is the deterministic eval axis.

  Gate 2  TOKEN VOCABULARY (hard)
          Only the 8 pinned tokens (<PERSON>, <USER>, etc.) may appear in
          <UPPER_CASE> angle-bracket form. An unknown token is a vocab mismatch.

  Gate 3  RETENTION (report-only, soft)
          Every retention.json value must still be present after redaction.
          Target ≥ 0.98 per metrics-config.json; pipeline does not block on this.

Non-circularity: pii.json and retention.json were authored during data generation,
independently of this redactor. The redactor is graded against a key it did not write.

Run:
    uv run pytest src/test/test_redaction.py -v
    uv run pytest src/test/test_redaction.py -v -k "test_absence"    # gate 1 only
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd
import pytest

# Allow imports from src/
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest.redactor import (
    build_sidecar_index,
    get_allowed_tokens,
    redact_ticket,
    redact_with_sidecar,
)

# ── Paths ─────────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).parent.parent.parent  # itsm-knowledge-rag-project/
_HF_CACHE = _REPO_ROOT / ".hf_cache"
_EVAL_REDACTION = _REPO_ROOT / "eval-set" / "redaction"

# Sidecar files: prefer HF snapshot (latest revision), fall back to eval-set copy
def _find_sidecar(filename: str) -> Path:
    # Latest HF snapshot: newest mtime under snapshots/
    snapshots = sorted(
        (_HF_CACHE / "datasets--ameau01--synthetic-it-support-tickets" / "snapshots").iterdir(),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for snap in snapshots:
        candidate = snap / filename
        if candidate.exists():
            return candidate
    # Fall back to eval-set/ copy
    fallback = _EVAL_REDACTION / filename
    if fallback.exists():
        return fallback
    raise FileNotFoundError(
        f"{filename} not found in HF cache or {_EVAL_REDACTION}. "
        "Run test_hf_download.py first."
    )


def _find_parquet() -> Path:
    snapshots = sorted(
        (_HF_CACHE / "datasets--ameau01--synthetic-it-support-tickets" / "snapshots").iterdir(),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for snap in snapshots:
        candidate = snap / "data" / "train.parquet"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("train.parquet not found in HF cache. Run test_hf_download.py first.")


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def pii_records() -> list[dict]:
    path = _find_sidecar("pii.json")
    return json.loads(path.read_text())


@pytest.fixture(scope="session")
def retention_records() -> list[dict]:
    path = _find_sidecar("retention.json")
    data = json.loads(path.read_text())
    # retention.json has a provenance header and a 'tickets' list
    if isinstance(data, dict) and "tickets" in data:
        return data["tickets"]
    return data


@pytest.fixture(scope="session")
def df() -> pd.DataFrame:
    return pd.read_parquet(_find_parquet())


@pytest.fixture(scope="session")
def sidecar_index(pii_records) -> dict:
    return build_sidecar_index(pii_records)


# ── Text extraction ────────────────────────────────────────────────────────────

def _to_list(val) -> list:
    """Coerce numpy arrays and None to plain Python list."""
    if val is None:
        return []
    if hasattr(val, "tolist"):
        return val.tolist()
    if isinstance(val, (list, tuple)):
        return list(val)
    return []


def _str_or_empty(val) -> str:
    if val is None:
        return ""
    if isinstance(val, float):  # NaN
        return ""
    return str(val)


def _extract_text_fields(row: pd.Series) -> dict[str, str]:
    """
    Flatten all free-text fields of a parquet row into named string fields
    for passing to redact_ticket().

    Returns a flat dict:
      'submitted_description' → str
      'correspondence'        → str  (all messages concatenated)
      'diagnostics_summary'   → str
      'diagnostics_steps'     → str  (all step fields concatenated)
      'resolution_steps'      → str
      'observations'          → str

    Note: parquet nested fields come back as numpy structured arrays; use
    _to_list() before iterating to avoid numpy truth-value errors.
    """
    parts: dict[str, str] = {}

    # ticket.submitted_description
    ticket = row.get("ticket")
    if isinstance(ticket, dict):
        parts["submitted_description"] = _str_or_empty(
            ticket.get("submitted_description", "")
        )

    # correspondence[*].message
    corr = _to_list(row.get("correspondence"))
    if corr:
        messages = []
        for c in corr:
            if hasattr(c, "get"):
                msg = c.get("message", "")
            elif hasattr(c, "_asdict"):
                msg = c._asdict().get("message", "")
            else:
                msg = ""
            if msg:
                messages.append(_str_or_empty(msg))
        parts["correspondence"] = "\n".join(messages)

    # diagnostics
    diag = row.get("diagnostics")
    if isinstance(diag, dict):
        parts["diagnostics_summary"] = _str_or_empty(diag.get("summary", ""))
        steps = _to_list(diag.get("steps"))
        step_texts = []
        for step in steps:
            step_d = step._asdict() if hasattr(step, "_asdict") else (
                dict(step) if isinstance(step, dict) else {}
            )
            for key in ("description", "expected_result", "observed_result", "evidence"):
                val = step_d.get(key)
                if val:
                    step_texts.append(_str_or_empty(val))
        parts["diagnostics_steps"] = "\n".join(step_texts)

    # resolution
    res = row.get("resolution")
    if isinstance(res, dict):
        steps = _to_list(res.get("steps"))
        parts["resolution_steps"] = "\n".join(_str_or_empty(s) for s in steps if s)
    elif res is not None:
        steps = _to_list(res)
        parts["resolution_steps"] = "\n".join(_str_or_empty(s) for s in steps if s)

    # root_cause observations (if present)
    rc = row.get("root_cause")
    if isinstance(rc, dict):
        parts["observations"] = _str_or_empty(rc.get("observations", ""))

    return {k: v for k, v in parts.items() if v}


def _all_text(redacted_fields: dict[str, str]) -> str:
    """Concatenate all redacted field values for absence checking."""
    return "\n".join(redacted_fields.values())


# ── Gate 1: Absence-anywhere ──────────────────────────────────────────────────

# Tickets used for the core test. A representative spread across families.
# Keep small so the test is fast; the pipeline run validates all 745.
_SPOT_CHECK_TICKETS = [
    "INC-AIT-0001",  # has 13 PII instances — good breadth
    "INC-VDA-0001",  # VDA family (demo family)
    "INC-VDA-0002",
    "INC-VDA-0010",
    "INC-VDA-0053",  # last in dominant root cause
    "INC-LPD-0001",
    "INC-CES-0001",
    "INC-PDQ-0001",
]


class AbsenceFailure:
    def __init__(self, ticket_id: str, value: str, token: str, field: str):
        self.ticket_id = ticket_id
        self.value = value
        self.token = token
        self.field = field

    def __repr__(self):
        return f"{self.ticket_id}: '{self.value}' → '{self.token}' leaked in {self.field}"


def test_absence_anywhere_spot_check(pii_records, df, sidecar_index):
    """
    Gate 1 (hard): PII values must be absent from redacted text.

    Tests a representative subset of tickets. A single leak is a failure.
    The pii.json absence-anywhere gate: the value must not appear at ANY
    site, not just the listed occurrences.
    """
    pii_by_id = {r["ticket_id"]: r for r in pii_records}
    failures: list[AbsenceFailure] = []

    tickets_to_test = [t for t in _SPOT_CHECK_TICKETS if t in pii_by_id]

    for ticket_id in tickets_to_test:
        row = df[df["record_id"] == ticket_id]
        if row.empty:
            pytest.skip(f"{ticket_id} not found in parquet")
        row = row.iloc[0]

        fields = _extract_text_fields(row)
        redacted = redact_ticket(
            ticket_id=ticket_id,
            fields=fields,
            sidecar_index=sidecar_index,
            use_presidio_fallback=False,  # test sidecar layer in isolation
        )
        full_text = _all_text(redacted)

        for inst in pii_by_id[ticket_id]["pii_instances"]:
            value = inst["value"]
            token = inst["expected_after_redaction"]
            if value in full_text:
                # Find which field leaked
                leaking_fields = [
                    fname for fname, ftext in redacted.items() if value in ftext
                ]
                failures.append(
                    AbsenceFailure(ticket_id, value, token, ", ".join(leaking_fields))
                )

    if failures:
        msg = f"\n{len(failures)} PII leak(s) detected:\n"
        msg += "\n".join(f"  {f}" for f in failures)
        pytest.fail(msg)


def test_absence_anywhere_full_corpus(pii_records, df, sidecar_index):
    """
    Gate 1 (hard), full corpus: run absence check on all 745 tickets.

    Slower than the spot check — run with -m slow or in CI, not on every dev save.
    Mark: pytest.mark.slow
    """
    pytest.importorskip("tqdm")
    from tqdm import tqdm

    pii_by_id = {r["ticket_id"]: r for r in pii_records}
    failures: list[AbsenceFailure] = []
    tested = 0

    for _, row in tqdm(df.iterrows(), total=len(df), desc="absence gate"):
        ticket_id = row["record_id"]
        if ticket_id not in pii_by_id:
            continue

        fields = _extract_text_fields(row)
        redacted = redact_ticket(
            ticket_id=ticket_id,
            fields=fields,
            sidecar_index=sidecar_index,
            use_presidio_fallback=False,
        )
        full_text = _all_text(redacted)

        for inst in pii_by_id[ticket_id]["pii_instances"]:
            value = inst["value"]
            if value in full_text:
                leaking_fields = [
                    fname for fname, ftext in redacted.items() if value in ftext
                ]
                failures.append(
                    AbsenceFailure(ticket_id, value, inst["expected_after_redaction"],
                                   ", ".join(leaking_fields))
                )
        tested += 1

    leak_rate = len(failures) / max(tested, 1)
    print(f"\nAbsence gate: {tested} tickets tested, {len(failures)} leaks, rate={leak_rate:.4f}")

    if failures:
        sample = failures[:20]
        msg = f"\n{len(failures)} PII leak(s) (showing first 20):\n"
        msg += "\n".join(f"  {f}" for f in sample)
        pytest.fail(msg)


# ── Gate 2: Token vocabulary ───────────────────────────────────────────────────

_TOKEN_RE = re.compile(r"<[A-Z_]+>")


def test_token_vocabulary(pii_records, df, sidecar_index):
    """
    Gate 2 (hard): only the 8 pinned tokens may appear as <TOKEN> strings.

    An unknown token (e.g., <USERNAME> instead of <USER>) is a vocab mismatch —
    the redactor emitted a token not in the policy YAML.
    """
    allowed = get_allowed_tokens()
    vocab_failures: list[str] = []

    for ticket_id in _SPOT_CHECK_TICKETS:
        row = df[df["record_id"] == ticket_id]
        if row.empty:
            continue
        row = row.iloc[0]

        fields = _extract_text_fields(row)
        redacted = redact_ticket(
            ticket_id=ticket_id,
            fields=fields,
            sidecar_index=sidecar_index,
            use_presidio_fallback=False,
        )

        for fname, ftext in redacted.items():
            for token in _TOKEN_RE.findall(ftext):
                if token not in allowed:
                    vocab_failures.append(
                        f"{ticket_id}/{fname}: unexpected token '{token}'"
                    )

    if vocab_failures:
        pytest.fail(
            f"\n{len(vocab_failures)} vocab mismatch(es):\n"
            + "\n".join(f"  {v}" for v in vocab_failures)
        )


# ── Gate 3: Retention (report-only) ───────────────────────────────────────────

def test_retention_report(retention_records, df, sidecar_index):
    """
    Gate 3 (soft, report-only): retained values must survive redaction.

    Target ≥ 0.98 per metrics-config.json; this test WARNS but does not FAIL.
    Over-redaction (false positives) is what this measures.
    """
    ret_by_id = {r["ticket_id"]: r for r in retention_records}

    total = 0
    dropped = 0
    dropped_examples: list[str] = []

    for ticket_id in _SPOT_CHECK_TICKETS:
        if ticket_id not in ret_by_id:
            continue
        row = df[df["record_id"] == ticket_id]
        if row.empty:
            continue
        row = row.iloc[0]

        fields = _extract_text_fields(row)
        redacted = redact_ticket(
            ticket_id=ticket_id,
            fields=fields,
            sidecar_index=sidecar_index,
            use_presidio_fallback=False,
        )
        full_text = _all_text(redacted)

        for inst in ret_by_id[ticket_id]["retain_instances"]:
            value = inst["value"]
            total += 1
            if value not in full_text:
                dropped += 1
                if len(dropped_examples) < 5:
                    dropped_examples.append(
                        f"{ticket_id}: '{value}' ({inst['type']}) was over-redacted"
                    )

    if total == 0:
        pytest.skip("No retention instances found for spot-check tickets")

    rate = (total - dropped) / total
    print(f"\nRetention rate: {rate:.4f} ({total - dropped}/{total} retained)")
    print("Target: ≥ 0.98 (report-only, pipeline does not block on this)")

    if dropped_examples:
        print("Over-redaction examples:")
        for ex in dropped_examples:
            print(f"  {ex}")

    # Soft warning threshold — adjust if the spot-check sample is unrepresentative
    WARN_THRESHOLD = 0.95
    if rate < WARN_THRESHOLD:
        pytest.warns(
            UserWarning,
            match=f"Retention rate {rate:.3f} < {WARN_THRESHOLD}",
        )
        import warnings
        warnings.warn(
            f"Retention rate {rate:.3f} < {WARN_THRESHOLD} on spot-check tickets. "
            f"Run full corpus check. Target ≥ 0.98.",
            UserWarning,
            stacklevel=2,
        )


# ── Unit tests: redact_with_sidecar() ─────────────────────────────────────────

class TestRedactWithSidecar:
    """Unit tests for the core string-replacement function."""

    def test_simple_person_name(self):
        replacements = {"Priya Nair": "<PERSON>"}
        result = redact_with_sidecar("Hi Priya Nair, your ticket is ready.", replacements)
        assert "Priya Nair" not in result
        assert "<PERSON>" in result

    def test_email_whole_string(self):
        """Email consumed whole — domain must NOT survive as a fragment."""
        replacements = {"pnair@corplabs.com": "<EMAIL>"}
        result = redact_with_sidecar("Contact pnair@corplabs.com for details.", replacements)
        assert "pnair@corplabs.com" not in result
        assert "<EMAIL>" in result
        # The domain part should also be gone (consumed with local-part)
        assert "pnair" not in result

    def test_username_after_email_consumed(self):
        """If email is already redacted, standalone username is still caught."""
        replacements = {
            "pnair@corplabs.com": "<EMAIL>",
            "pnair": "<USER>",
        }
        # Email consumed first (longest-first), bare username also replaced
        text = "Sent from pnair@corplabs.com — user pnair confirmed."
        result = redact_with_sidecar(text, replacements)
        assert "pnair" not in result
        assert "<EMAIL>" in result
        assert "<USER>" in result

    def test_personal_hostname_fused(self):
        """Personal hostname replaced as a whole token."""
        replacements = {"WORKSTATION-PNAIR-L14": "<HOSTNAME>"}
        result = redact_with_sidecar(
            "Device WORKSTATION-PNAIR-L14 is not enrolled.", replacements
        )
        assert "WORKSTATION-PNAIR-L14" not in result
        assert "<HOSTNAME>" in result

    def test_dn_infrastructure_preserved(self):
        """
        Distinguished Name: username portion redacted, OU/DC retained.
        The sidecar lists the bare username ('mdelgado'), not the DN path.
        The DN infrastructure (OU=Corp Users, DC=corplabs) must survive.
        """
        # Sidecar lists the embedded username value
        replacements = {"mdelgado": "<USER>"}
        text = "Account CN=mdelgado,OU=Corp Users,DC=corplabs,DC=internal is locked."
        result = redact_with_sidecar(text, replacements)
        assert "mdelgado" not in result
        assert "<USER>" in result
        assert "OU=Corp Users" in result
        assert "DC=corplabs" in result

    def test_error_code_retained(self):
        """Error codes must survive — they are in the retain class."""
        replacements = {"Priya Nair": "<PERSON>"}
        text = "Error 0xC0000234 was logged for Priya Nair's account."
        result = redact_with_sidecar(text, replacements)
        assert "0xC0000234" in result
        assert "Priya Nair" not in result

    def test_service_hostname_retained(self):
        """Service hostnames must not be redacted."""
        replacements = {"mdelgado": "<USER>"}
        text = "mdelgado logged into DC-EAST-03.corplabs.internal."
        result = redact_with_sidecar(text, replacements)
        assert "mdelgado" not in result
        assert "DC-EAST-03.corplabs.internal" in result

    def test_longest_match_first(self):
        """Longer value matches before shorter substring."""
        replacements = {
            "Melissa Williams": "<PERSON>",
            "Williams": "<PERSON>",
        }
        text = "Melissa Williams submitted the ticket."
        result = redact_with_sidecar(text, replacements)
        # Should be a single <PERSON>, not "<PERSON> <PERSON>"
        assert result.count("<PERSON>") == 1
        assert "Melissa" not in result
        assert "Williams" not in result

    def test_emp_id(self):
        replacements = {"E-40821": "<EMP_ID>"}
        result = redact_with_sidecar("Employee E-40821 submitted the request.", replacements)
        assert "E-40821" not in result
        assert "<EMP_ID>" in result

    def test_empty_text_passthrough(self):
        result = redact_with_sidecar("", {"Alice Smith": "<PERSON>"})
        assert result == ""

    def test_no_match_passthrough(self):
        result = redact_with_sidecar(
            "The server returned HTTP 200.", {"Alice Smith": "<PERSON>"}
        )
        assert result == "The server returned HTTP 200."


# ── Smoke: policy YAML loads cleanly ─────────────────────────────────────────

def test_policy_yaml_loads():
    """Policy YAML must load without error and contain the 8 required tokens."""
    from ingest.redactor import load_policy

    policy = load_policy()
    vocab = set(policy["token_vocabulary"])
    required = {"<PERSON>", "<USER>", "<EMAIL>", "<PHONE>",
                "<EMP_ID>", "<LOCATION>", "<IP>", "<HOSTNAME>"}
    missing = required - vocab
    assert not missing, f"Missing tokens in policy YAML: {missing}"

    # Every entity entry must have a token in the vocabulary
    for entity in policy["entities"]:
        assert entity["token"] in vocab, (
            f"Entity '{entity['sidecar_type']}' token '{entity['token']}' "
            "not in token_vocabulary"
        )
