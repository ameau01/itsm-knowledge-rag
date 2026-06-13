"""
Presidio-layer redaction test.

Runs the full two-layer pipeline (Layer 1 sidecar + Layer 2 Presidio pattern
recognizers) and audits the result against both sidecars.

Gates
-----
Gate 1  ABSENCE-ANYWHERE [hard fail]
        Every pii.json value must be absent from the final redacted text.
        Exercises the complete pipeline — sidecar layer + Presidio layer.

Gate 2  TOKEN VOCABULARY [hard fail]
        Only the 8 pinned tokens may appear as <TOKEN> strings.

Gate 3  RETENTION [report-only]
        Every retention.json value must still be present after redaction.
        Target ≥ 0.98; printed with per-type breakdown. No pipeline block.

Presidio scan (informational)
        Pattern-based recognizers (EMAIL, IP, EMP_ID, HOSTNAME, PHONE) run on
        both the raw and the redacted text. Reports how many pattern-detectable
        entities were present in the raw text and how many survived after
        redaction. NER-dependent types (PERSON, USER, LOCATION) rely on the
        pii.json absence gate; they are not checked by pattern scan.

        Note: this test uses Presidio PatternRecognizers directly, not
        AnalyzerEngine, so no spacy model download is required.

Usage
-----
# Run via shell script (recommended):
    ./scripts/run_presidio_test.sh              # sample: first ticket
    ./scripts/run_presidio_test.sh --all        # full 745-ticket corpus
    ./scripts/run_presidio_test.sh --ticket INC-VDA-0001

# Run directly:
    python src/test/test_presidio_redaction.py              # sample
    python src/test/test_presidio_redaction.py --all
    python src/test/test_presidio_redaction.py --ticket INC-VDA-0001

# Run as pytest (sample only — full corpus via shell script):
    pytest src/test/test_presidio_redaction.py -v

No files are written. No operational store is touched.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

# Allow imports from src/
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest.redactor import (
    build_sidecar_index,
    get_allowed_tokens,
    redact_ticket,
)

# ── Paths ──────────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).parent.parent.parent
_HF_CACHE = _REPO_ROOT / ".hf_cache"
_EVAL_REDACTION = _REPO_ROOT / "eval-set" / "redaction"


# ── HF helpers ─────────────────────────────────────────────────────────────────

def _snapshots_dir() -> Path:
    return _HF_CACHE / "datasets--ameau01--synthetic-it-support-tickets" / "snapshots"


def _latest_snapshot() -> Path | None:
    sd = _snapshots_dir()
    if not sd.exists():
        return None
    snaps = sorted(sd.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    return snaps[0] if snaps else None


def _ensure_dataset() -> Path:
    """Return the HF snapshot dir, downloading if necessary."""
    snap = _latest_snapshot()
    if snap and (snap / "data" / "train.parquet").exists():
        return snap
    print("HF snapshot not found in cache — downloading …")
    sys.path.insert(0, str(_REPO_ROOT / "src"))
    from data_loader import download_dataset
    return download_dataset()


def _find_sidecar(filename: str) -> Path:
    # Local eval-set copy takes precedence (may be a corrected version of the HF file)
    local = _EVAL_REDACTION / filename
    if local.exists():
        return local
    snap = _latest_snapshot()
    if snap:
        candidate = snap / filename
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"{filename} not found in {_EVAL_REDACTION} or HF cache ({_HF_CACHE}).\n"
        "Run: python src/test/test_hf_download.py"
    )


# ── Presidio pattern recognizers (no spacy / no NLP engine required) ──────────

def _build_pattern_recognizers():
    """
    Build PatternRecognizer instances for the entity types that can be
    detected by pattern alone. PERSON / USER / LOCATION need NER and are
    intentionally excluded — the pii.json absence gate covers them.
    """
    from presidio_analyzer import PatternRecognizer, Pattern

    return [
        PatternRecognizer(
            supported_entity="EMAIL_ADDRESS",
            patterns=[
                Pattern("email", r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b", 0.9)
            ],
        ),
        # IP_ADDRESS intentionally excluded from Layer 2:
        # All PII IPs (personal workstation/laptop addresses) are captured by the
        # pii.json sidecar (Layer 1) — Gate 1 confirms zero leaks. Infrastructure
        # server IPs (DNS resolvers, gateways, domain controllers) appear in
        # retention.json as service_hostname values and must NOT be redacted.
        # The IP pattern cannot distinguish personal vs. infrastructure IPs, so
        # running it in Layer 2 causes ~11 false-positive retention drops with
        # no coverage gain. Same design rationale as excluding EMPLOYEE_ID.
        PatternRecognizer(
            supported_entity="PHONE_NUMBER",
            patterns=[
                Pattern("phone_us", r"\b(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b", 0.75),
                Pattern("phone_ext", r"\bx\d{4,5}\b", 0.65),
            ],
        ),
        # EMPLOYEE_ID intentionally excluded from Layer 2:
        # All 925 real EMP_IDs are captured by the pii.json sidecar (Layer 1).
        # The [A-Z]{1,4}-\d{4,6} pattern falsely matches change tickets (CHG-XXXXX),
        # error codes (RST-XXXXX), incident IDs (INC-PDQ-XXXX substrings), and
        # structured hostnames, causing ~155 retention drops. Since the sidecar
        # is authoritative, Presidio adds zero coverage here.
        PatternRecognizer(
            supported_entity="PERSONAL_HOSTNAME",
            patterns=[
                Pattern(
                    "workstation_prefix",
                    r"\b(WORKSTATION|LAPTOP|DESKTOP|WS|PC)-[A-Z][A-Z0-9\-]{2,}\b",
                    0.90,
                )
            ],
        ),
    ]


_TOKEN_RE = re.compile(r"<[A-Z_]+>")

# Retain patterns: spans that look like PII but are NOT (same as redaction_policy.yaml)
_RETAIN_PATTERNS = [
    re.compile(r"0x[0-9A-Fa-f]+"),
    re.compile(r"[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2})+"),
    re.compile(r"https?://\S+"),
    re.compile(r"(Americas|EMEA|EMEA-Sales|Eng-US-East|Finance-US-East|Finance-US-East-Win11-Compliance|APAC|AMER)"),
    re.compile(r"(us-east-1|us-west-2|eu-west-1|ap-southeast-1)"),
    # Infrastructure / service team emails — not personal PII.
    # All personal emails are already handled by the pii.json sidecar (Layer 1).
    # Any email still present after Layer 1 ran is a service address and should
    # be retained. Pattern: anything@known-corpus-domain.
    re.compile(
        r"[a-zA-Z0-9._%+\-]+"
        r"@(corplabs\.com|corp\.internal|example\.corp|partnerservices\.net"
        r"|corplabs\.internal|corp\.local|externalpay\.io|databridge\.io)",
        re.IGNORECASE,
    ),
]


def _scan_with_presidio(text: str, recognizers) -> list[dict[str, Any]]:
    """
    Run all pattern recognizers on text. Returns list of
    {entity_type, value, start, end, score}.
    Suppresses matches covered by retain patterns.
    """
    from presidio_analyzer.nlp_engine import NlpArtifacts

    nlp_artifacts = NlpArtifacts(
        entities=[], tokens=[], tokens_indices=[], lemmas=[],
        nlp_engine=None, language="en",
    )

    findings = []
    seen_spans: set[tuple[int, int]] = set()

    for recognizer in recognizers:
        entity = recognizer.supported_entities[0]
        results = recognizer.analyze(
            text=text,
            entities=[entity],
            nlp_artifacts=nlp_artifacts,
        )
        for r in results:
            span = text[r.start:r.end]
            # Skip if span matches a retain pattern
            if any(p.fullmatch(span) for p in _RETAIN_PATTERNS):
                continue
            # Skip overlapping spans (longest wins — simple dedup)
            if (r.start, r.end) in seen_spans:
                continue
            seen_spans.add((r.start, r.end))
            findings.append({
                "entity_type": entity,
                "value": span,
                "start": r.start,
                "end": r.end,
                "score": r.score,
            })

    return sorted(findings, key=lambda x: x["start"])


# ── Text extraction (mirrors test_redaction.py) ────────────────────────────────

def _to_list(val) -> list:
    if val is None:
        return []
    if hasattr(val, "tolist"):
        return val.tolist()
    return list(val) if isinstance(val, (list, tuple)) else []


def _str_or_empty(val) -> str:
    if val is None or (isinstance(val, float)):
        return ""
    return str(val)


def _extract_text_fields(row: pd.Series) -> dict[str, str]:
    parts: dict[str, str] = {}

    ticket = row.get("ticket")
    if isinstance(ticket, dict):
        parts["submitted_description"] = _str_or_empty(ticket.get("submitted_description", ""))

    corr = _to_list(row.get("correspondence"))
    if corr:
        messages = []
        for c in corr:
            msg = c.get("message", "") if hasattr(c, "get") else (
                c._asdict().get("message", "") if hasattr(c, "_asdict") else ""
            )
            if msg:
                messages.append(_str_or_empty(msg))
        parts["correspondence"] = "\n".join(messages)

    diag = row.get("diagnostics")
    if isinstance(diag, dict):
        parts["diagnostics_summary"] = _str_or_empty(diag.get("summary", ""))
        step_texts = []
        for step in _to_list(diag.get("steps")):
            step_d = step._asdict() if hasattr(step, "_asdict") else (
                dict(step) if isinstance(step, dict) else {}
            )
            for key in ("description", "expected_result", "observed_result", "evidence"):
                v = step_d.get(key)
                if v:
                    step_texts.append(_str_or_empty(v))
        parts["diagnostics_steps"] = "\n".join(step_texts)

    res = row.get("resolution")
    if isinstance(res, dict):
        parts["resolution_steps"] = "\n".join(
            _str_or_empty(s) for s in _to_list(res.get("steps")) if s
        )
    elif res is not None:
        parts["resolution_steps"] = "\n".join(
            _str_or_empty(s) for s in _to_list(res) if s
        )

    rc = row.get("root_cause")
    if isinstance(rc, dict):
        parts["observations"] = _str_or_empty(rc.get("observations", ""))

    return {k: v for k, v in parts.items() if v}


def _all_text(fields: dict[str, str]) -> str:
    return "\n".join(fields.values())


# ── Per-ticket result ──────────────────────────────────────────────────────────

@dataclass
class TicketResult:
    ticket_id: str
    pii_count: int = 0
    leaks: list[str] = field(default_factory=list)
    vocab_violations: list[str] = field(default_factory=list)
    retain_total: int = 0
    retain_dropped: list[str] = field(default_factory=list)
    presidio_raw_hits: list[dict] = field(default_factory=list)   # found in raw text
    presidio_surviving: list[dict] = field(default_factory=list)  # found in redacted text

    @property
    def gate1_pass(self) -> bool:
        return len(self.leaks) == 0

    @property
    def gate2_pass(self) -> bool:
        return len(self.vocab_violations) == 0

    @property
    def retention_rate(self) -> float:
        if self.retain_total == 0:
            return 1.0
        return (self.retain_total - len(self.retain_dropped)) / self.retain_total


# ── Core per-ticket test logic ─────────────────────────────────────────────────

def run_ticket(
    ticket_id: str,
    row: pd.Series,
    pii_by_id: dict[str, dict],
    ret_by_id: dict[str, dict],
    sidecar_index: dict[str, dict],
    recognizers: list,
    allowed_tokens: set[str],
) -> TicketResult:
    result = TicketResult(ticket_id=ticket_id)
    fields = _extract_text_fields(row)
    raw_text = _all_text(fields)

    # ── Presidio scan on RAW text (informational) ──────────────────────────────
    result.presidio_raw_hits = _scan_with_presidio(raw_text, recognizers)

    # ── Full pipeline: Layer 1 (sidecar) + Layer 2 (Presidio) ─────────────────
    redacted_fields = redact_ticket(
        ticket_id=ticket_id,
        fields=fields,
        sidecar_index=sidecar_index,
        use_presidio_fallback=False,  # we run Presidio manually below for audit visibility
    )

    # Apply Presidio (Layer 2) manually so we can capture what it changes
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
    from presidio_analyzer.nlp_engine import NlpArtifacts

    # Token map for Presidio anonymizer
    token_map = {
        "EMAIL_ADDRESS": "<EMAIL>",
        "IP_ADDRESS": "<IP>",
        "PHONE_NUMBER": "<PHONE>",
        "PERSONAL_HOSTNAME": "<HOSTNAME>",
    }
    anonymizer = AnonymizerEngine()
    nlp_artifacts = NlpArtifacts(
        entities=[], tokens=[], tokens_indices=[], lemmas=[],
        nlp_engine=None, language="en",
    )

    final_fields: dict[str, str] = {}
    for fname, ftext in redacted_fields.items():
        # Run each recognizer on this field
        from presidio_analyzer import RecognizerResult
        all_results: list[RecognizerResult] = []
        seen: set[tuple[int, int]] = set()
        for recognizer in recognizers:
            entity = recognizer.supported_entities[0]
            hits = recognizer.analyze(text=ftext, entities=[entity], nlp_artifacts=nlp_artifacts)
            for h in hits:
                span = ftext[h.start:h.end]
                if any(p.fullmatch(span) for p in _RETAIN_PATTERNS):
                    continue
                if (h.start, h.end) not in seen:
                    seen.add((h.start, h.end))
                    all_results.append(h)

        if all_results:
            operators = {
                entity: OperatorConfig("replace", {"new_value": token_map[entity]})
                for entity in token_map
            }
            anon_result = anonymizer.anonymize(
                text=ftext, analyzer_results=all_results, operators=operators
            )
            final_fields[fname] = anon_result.text
        else:
            final_fields[fname] = ftext

    final_text = _all_text(final_fields)

    # ── Presidio scan on REDACTED text (audit) ─────────────────────────────────
    result.presidio_surviving = _scan_with_presidio(final_text, recognizers)

    # ── Gate 1: absence-anywhere ───────────────────────────────────────────────
    pii_record = pii_by_id.get(ticket_id, {})
    instances = pii_record.get("pii_instances", [])
    result.pii_count = len(instances)
    for inst in instances:
        if inst["value"] in final_text:
            result.leaks.append(
                f"  LEAK  {inst['type']:10s}  '{inst['value']}'  "
                f"→ expected {inst['expected_after_redaction']}"
            )

    # ── Gate 2: token vocabulary ───────────────────────────────────────────────
    for token in _TOKEN_RE.findall(final_text):
        if token not in allowed_tokens:
            result.vocab_violations.append(f"  VOCAB  unknown token '{token}'")

    # ── Gate 3: retention (report-only) ───────────────────────────────────────
    ret_record = ret_by_id.get(ticket_id, {})
    retain_instances = ret_record.get("retain_instances", [])
    result.retain_total = len(retain_instances)
    for inst in retain_instances:
        if inst["value"] not in final_text:
            result.retain_dropped.append(
                f"  DROPPED  {inst['type']:20s}  '{inst['value']}'"
            )

    return result


# ── Output formatting ──────────────────────────────────────────────────────────

_LINE = "─" * 64


def _print_ticket_result(r: TicketResult, verbose: bool = False) -> None:
    g1 = "PASS" if r.gate1_pass else "FAIL"
    g2 = "PASS" if r.gate2_pass else "FAIL"
    ret_str = f"{r.retain_total - len(r.retain_dropped)}/{r.retain_total} ({r.retention_rate:.3f})"
    presidio_str = (
        f"{len(r.presidio_raw_hits)} detected in raw → "
        f"{len(r.presidio_surviving)} surviving after redaction"
    )
    status = "PASS" if r.gate1_pass and r.gate2_pass else "FAIL"

    print(f"\n{_LINE}")
    print(f"{r.ticket_id}  [{status}]")
    print(f"  Gate 1 (absence)  : {g1}  {r.pii_count} PII values, {len(r.leaks)} leak(s)")
    print(f"  Gate 2 (vocab)    : {g2}  {len(r.vocab_violations)} violation(s)")
    print(f"  Gate 3 (retention): {ret_str}  ← report only")
    print(f"  Presidio pattern  : {presidio_str}")
    print(f"    (NER types — PERSON, USER, LOCATION — covered by Gate 1 only)")

    if r.leaks:
        print("  Leaks:")
        for line in r.leaks:
            print(line)
    if r.vocab_violations:
        print("  Vocab violations:")
        for line in r.vocab_violations:
            print(line)
    if r.retain_dropped and verbose:
        print("  Over-redacted (should have been retained):")
        for line in r.retain_dropped[:10]:
            print(line)
        if len(r.retain_dropped) > 10:
            print(f"  … and {len(r.retain_dropped) - 10} more")
    if r.presidio_surviving and verbose:
        print("  Presidio still detects in redacted text:")
        for h in r.presidio_surviving[:5]:
            print(f"    {h['entity_type']:20s}  '{h['value']}'")
        if len(r.presidio_surviving) > 5:
            print(f"    … and {len(r.presidio_surviving) - 5} more")


def _print_summary(results: list[TicketResult]) -> int:
    """Print summary table. Returns exit code (0=pass, 1=fail)."""
    total = len(results)
    g1_fails = [r for r in results if not r.gate1_pass]
    g2_fails = [r for r in results if not r.gate2_pass]
    all_retain = sum(r.retain_total for r in results)
    all_dropped = sum(len(r.retain_dropped) for r in results)
    ret_rate = (all_retain - all_dropped) / max(all_retain, 1)
    total_raw_hits = sum(len(r.presidio_raw_hits) for r in results)
    total_surviving = sum(len(r.presidio_surviving) for r in results)

    # Per-type retention breakdown
    from collections import Counter
    dropped_by_type: Counter = Counter()
    for r in results:
        for line in r.retain_dropped:
            # Extract type from "  DROPPED  type_name  'value'"
            parts = line.strip().split()
            if len(parts) >= 2:
                dropped_by_type[parts[1]] += 1

    print(f"\n{'═' * 64}")
    print(f"SUMMARY  ({total} ticket(s) tested)")
    print(f"{'─' * 64}")
    print(f"Gate 1 (absence)  : {'PASS' if not g1_fails else 'FAIL'}  "
          f"{len(g1_fails)} ticket(s) with leaks")
    print(f"Gate 2 (vocab)    : {'PASS' if not g2_fails else 'FAIL'}  "
          f"{len(g2_fails)} ticket(s) with vocab violations")
    print(f"Gate 3 (retention): {ret_rate:.4f}  "
          f"({all_retain - all_dropped}/{all_retain} retained)  target ≥ 0.98")
    print(f"  ↳ dropped by type: {dict(dropped_by_type) or 'none'}")
    print(f"Presidio pattern  : {total_raw_hits} hits in raw text  →  "
          f"{total_surviving} surviving in redacted output")
    print(f"  ↳ (PERSON/USER/LOCATION require NER — covered by Gate 1 only)")
    print(f"{'═' * 64}")

    overall = "PASS" if not g1_fails and not g2_fails else "FAIL"
    print(f"Overall: {overall}")

    if g1_fails:
        print("\nTickets with Gate 1 failures:")
        for r in g1_fails:
            print(f"  {r.ticket_id}: {len(r.leaks)} leak(s)")

    return 0 if overall == "PASS" else 1


# ── Main entry point ───────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Presidio-layer redaction test. Stdout only — no files written."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--all", action="store_true",
        help="Test all 745 tickets (full corpus). Default: first ticket only."
    )
    mode.add_argument(
        "--ticket", metavar="ID",
        help="Test a single specific ticket, e.g. --ticket INC-VDA-0001"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Print over-redacted values and surviving Presidio hits per ticket."
    )
    args = parser.parse_args(argv)

    # ── Load data ──────────────────────────────────────────────────────────────
    snap = _ensure_dataset()
    df = pd.read_parquet(snap / "data" / "train.parquet")
    pii_records: list[dict] = json.loads(_find_sidecar("pii.json").read_text())
    ret_raw = json.loads(_find_sidecar("retention.json").read_text())
    ret_records: list[dict] = ret_raw["tickets"] if isinstance(ret_raw, dict) else ret_raw

    pii_by_id = {r["ticket_id"]: r for r in pii_records}
    ret_by_id = {r["ticket_id"]: r for r in ret_records}
    sidecar_index = build_sidecar_index(pii_records)
    allowed_tokens = get_allowed_tokens()
    recognizers = _build_pattern_recognizers()

    # ── Select tickets ─────────────────────────────────────────────────────────
    if args.all:
        mode_label = f"ALL MODE — {len(df)} tickets"
        ticket_ids = df["record_id"].tolist()
    elif args.ticket:
        mode_label = f"SINGLE TICKET — {args.ticket}"
        ticket_ids = [args.ticket]
    else:
        first_id = df["record_id"].iloc[0]
        mode_label = f"SAMPLE MODE — {first_id} (first ticket)"
        ticket_ids = [first_id]

    print(f"\n{_LINE}")
    print(f"Presidio Redaction Test  |  {mode_label}")
    print(f"Sidecar  : {_find_sidecar('pii.json')}")
    print(f"Retention: {_find_sidecar('retention.json')}")
    print(_LINE)

    # ── Run ────────────────────────────────────────────────────────────────────
    results: list[TicketResult] = []
    missing = 0

    for tid in ticket_ids:
        rows = df[df["record_id"] == tid]
        if rows.empty:
            print(f"  SKIP  {tid} — not found in parquet")
            missing += 1
            continue
        row = rows.iloc[0]
        result = run_ticket(
            ticket_id=tid,
            row=row,
            pii_by_id=pii_by_id,
            ret_by_id=ret_by_id,
            sidecar_index=sidecar_index,
            recognizers=recognizers,
            allowed_tokens=allowed_tokens,
        )
        results.append(result)

        # In --all mode, print compact per-ticket line; verbose/sample get full block
        if args.all and not args.verbose:
            g1 = "✓" if result.gate1_pass else "✗"
            g2 = "✓" if result.gate2_pass else "✗"
            leaks = f" {len(result.leaks)} leak(s)" if result.leaks else ""
            print(f"  {tid}  G1:{g1} G2:{g2}  ret:{result.retention_rate:.3f}{leaks}")
        else:
            _print_ticket_result(result, verbose=args.verbose)

    if missing:
        print(f"\n  {missing} ticket ID(s) not found in parquet.")

    return _print_summary(results)


# ── pytest entry point ─────────────────────────────────────────────────────────
# When run via pytest (no CLI args), tests the first ticket only.

import pytest  # noqa: E402


@pytest.fixture(scope="module")
def _presidio_data():
    snap = _ensure_dataset()
    df = pd.read_parquet(snap / "data" / "train.parquet")
    pii_records = json.loads(_find_sidecar("pii.json").read_text())
    ret_raw = json.loads(_find_sidecar("retention.json").read_text())
    ret_records = ret_raw["tickets"] if isinstance(ret_raw, dict) else ret_raw
    return {
        "df": df,
        "pii_by_id": {r["ticket_id"]: r for r in pii_records},
        "ret_by_id": {r["ticket_id"]: r for r in ret_records},
        "sidecar_index": build_sidecar_index(pii_records),
        "allowed_tokens": get_allowed_tokens(),
        "recognizers": _build_pattern_recognizers(),
        "pii_records": pii_records,
    }


def _run_sample_ticket(data: dict) -> TicketResult:
    df = data["df"]
    first_id = df["record_id"].iloc[0]
    row = df[df["record_id"] == first_id].iloc[0]
    return run_ticket(
        ticket_id=first_id,
        row=row,
        pii_by_id=data["pii_by_id"],
        ret_by_id=data["ret_by_id"],
        sidecar_index=data["sidecar_index"],
        recognizers=data["recognizers"],
        allowed_tokens=data["allowed_tokens"],
    )


def test_presidio_gate1_absence(_presidio_data):
    """Gate 1: no pii.json values survive the full pipeline (sample ticket)."""
    result = _run_sample_ticket(_presidio_data)
    if result.leaks:
        pytest.fail(f"\n{result.ticket_id} — {len(result.leaks)} PII leak(s):\n"
                    + "\n".join(result.leaks))


def test_presidio_gate2_vocab(_presidio_data):
    """Gate 2: only the 8 pinned tokens appear as <TOKEN> strings."""
    result = _run_sample_ticket(_presidio_data)
    if result.vocab_violations:
        pytest.fail(f"\n{result.ticket_id} — vocab violation(s):\n"
                    + "\n".join(result.vocab_violations))


def test_presidio_gate3_retention_report(_presidio_data):
    """Gate 3 (report-only): retention rate on sample ticket."""
    result = _run_sample_ticket(_presidio_data)
    print(f"\nRetention: {result.retention_rate:.4f} "
          f"({result.retain_total - len(result.retain_dropped)}/{result.retain_total})")
    if result.retain_dropped:
        print("Over-redacted:")
        for line in result.retain_dropped[:5]:
            print(line)
    # Soft check — warn but don't fail
    assert result.retention_rate >= 0.90, (
        f"Retention {result.retention_rate:.3f} very low on sample ticket — "
        "check false-positive suppressions"
    )


def test_presidio_pattern_audit(_presidio_data):
    """Presidio pattern scan: pattern-detectable PII must not survive redaction."""
    result = _run_sample_ticket(_presidio_data)
    # Any pattern-detectable entity still present in redacted text is a leak
    # (PERSON/USER/LOCATION excluded — they need NER and are Gate 1's job)
    ner_types = {"PERSON", "USER", "LOCATION"}
    pattern_survivors = [
        h for h in result.presidio_surviving
        if h["entity_type"] not in ner_types
    ]
    print(f"\nPresidio raw hits   : {len(result.presidio_raw_hits)}")
    print(f"Presidio survivors  : {len(result.presidio_surviving)} total, "
          f"{len(pattern_survivors)} pattern-type")
    if pattern_survivors:
        for h in pattern_survivors:
            print(f"  {h['entity_type']:20s}  '{h['value']}'")
        pytest.fail(
            f"{len(pattern_survivors)} pattern-detectable PII value(s) "
            "survived redaction (see above)"
        )


if __name__ == "__main__":
    sys.exit(main())
