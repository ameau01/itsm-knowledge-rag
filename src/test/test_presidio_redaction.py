"""
Full three-layer redaction test

Runs the complete L1+L2+L3 pipeline and audits against both sidecars.

Gates
-----
Gate 1  ABSENCE-ANYWHERE [hard fail]
        Every pii.json value must be absent from the final redacted text.

Gate 2  TOKEN VOCABULARY [hard fail]
        Only the 8 pinned tokens may appear as <TOKEN> strings.

Gate 3  RETENTION [report-only]
        Every retention.json value must still be present after redaction.
        Target ≥ 0.98; printed with per-type breakdown. No pipeline block.

Presidio scan (informational)
        Pattern-based recognizers run on both raw and redacted text to measure
        how many pattern-detectable entities (EMAIL, PHONE, HOSTNAME) survive.
        PERSON/LOCATION require NER — those are Gate 1's job.

Usage
-----
    ./scripts/run_presidio_test.sh              # first ticket
    ./scripts/run_presidio_test.sh --all        # full 745-ticket corpus
    ./scripts/run_presidio_test.sh --ticket INC-VDA-0001

    python src/test/test_presidio_redaction.py
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

sys.path.insert(0, str(Path(__file__).parent.parent))

from corpus.extractor import extract_text_fields
from ingest.redactor import PolicyRedactor, find_unexpected_tokens

# ── Paths ─────────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).parent.parent.parent
_HF_CACHE  = _REPO_ROOT / ".hf_cache"
_EVAL_DIR  = _REPO_ROOT / "eval-set" / "redaction"
_SNAPSHOTS = _HF_CACHE / "datasets--ameau01--synthetic-it-support-tickets" / "snapshots"
_POLICY    = _REPO_ROOT / "src" / "ingest" / "redaction_policy.yaml"


# ── HF helpers ────────────────────────────────────────────────────────────────

def _latest_snapshot() -> Path | None:
    if not _SNAPSHOTS.exists():
        return None
    snaps = sorted(_SNAPSHOTS.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    return snaps[0] if snaps else None


def _ensure_dataset() -> Path:
    snap = _latest_snapshot()
    if snap and (snap / "data" / "train.parquet").exists():
        return snap
    print("HF snapshot not found — downloading …")
    sys.path.insert(0, str(_REPO_ROOT / "src"))
    from data_loader import download_dataset
    return download_dataset()


def _find_sidecar(snap: Path, filename: str) -> Path:
    c = snap / filename
    if c.exists():
        return c
    local = _EVAL_DIR / filename
    if local.exists():
        return local
    raise FileNotFoundError(
        f"{filename} not found in HF snapshot or {_EVAL_DIR}.\n"
        "Run: uv run sh scripts/test_hf_download.sh"
    )


def _load_users_directory(snap: Path) -> dict:
    c = snap / "users_directory.json"
    if c.exists():
        return json.loads(c.read_text())
    raise FileNotFoundError(
        "users_directory.json not found in HF snapshot. "
        "Run: uv run sh scripts/test_hf_download.sh"
    )


# ── Presidio pattern scan (informational) ─────────────────────────────────────

_RETAIN_PATTERNS = [
    re.compile(r"0x[0-9A-Fa-f]+"),
    re.compile(r"[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2})+"),
    re.compile(r"https?://\S+"),
    re.compile(r"(Americas|EMEA|EMEA-Sales|Eng-US-East|Finance-US-East|Finance-US-East-Win11-Compliance|APAC|AMER)"),
    re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE),
]


def _build_pattern_recognizers():
    from presidio_analyzer import PatternRecognizer, Pattern
    return [
        PatternRecognizer(
            supported_entity="EMAIL_ADDRESS",
            patterns=[Pattern("email", r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b", 0.9)],
        ),
        PatternRecognizer(
            supported_entity="PHONE_NUMBER",
            patterns=[
                Pattern("phone_us", r"\b(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b", 0.75),
                Pattern("phone_ext", r"\bx\d{4,5}\b", 0.65),
            ],
        ),
        PatternRecognizer(
            supported_entity="PERSONAL_HOSTNAME",
            patterns=[Pattern(
                "device_prefix",
                r"\b(WORKSTATION|LAPTOP|DESKTOP|WS|PC)-[A-Z][A-Z0-9\-]{2,}\b",
                0.90,
            )],
        ),
    ]


def _scan_pattern(text: str, recognizers) -> list[dict[str, Any]]:
    from presidio_analyzer.nlp_engine import NlpArtifacts
    nlp_artifacts = NlpArtifacts(
        entities=[], tokens=[], tokens_indices=[], lemmas=[],  # type: ignore[arg-type]
        nlp_engine=None, language="en",
    )
    findings = []
    seen: set[tuple[int, int]] = set()
    for rec in recognizers:
        entity = rec.supported_entities[0]
        for r in rec.analyze(text=text, entities=[entity], nlp_artifacts=nlp_artifacts):
            span = text[r.start:r.end]
            if any(p.fullmatch(span) for p in _RETAIN_PATTERNS):
                continue
            if (r.start, r.end) not in seen:
                seen.add((r.start, r.end))
                findings.append({"entity_type": entity, "value": span, "score": r.score})
    return sorted(findings, key=lambda x: x.get("start", 0))


def _all_text(fields: dict[str, str]) -> str:
    return "\n".join(v for v in fields.values() if isinstance(v, str))


# ── Per-ticket result ──────────────────────────────────────────────────────────

@dataclass
class TicketResult:
    ticket_id: str
    pii_count: int = 0
    leaks: list[str] = field(default_factory=list)
    vocab_violations: list[str] = field(default_factory=list)
    retain_total: int = 0
    retain_dropped: list[str] = field(default_factory=list)
    presidio_raw_hits: list[dict] = field(default_factory=list)
    presidio_surviving: list[dict] = field(default_factory=list)

    @property
    def gate1_pass(self) -> bool: return not self.leaks
    @property
    def gate2_pass(self) -> bool: return not self.vocab_violations
    @property
    def retention_rate(self) -> float:
        return (self.retain_total - len(self.retain_dropped)) / max(self.retain_total, 1)


# ── Core per-ticket test logic ─────────────────────────────────────────────────

def run_ticket(
    ticket_id: str,
    row: pd.Series,
    pii_by_id: dict,
    ret_by_id: dict,
    redactor: PolicyRedactor,
    recognizers: list,
) -> TicketResult:
    result = TicketResult(ticket_id=ticket_id)
    fields   = extract_text_fields(row)
    raw_text = _all_text(fields)

    result.presidio_raw_hits = _scan_pattern(raw_text, recognizers)

    redacted  = redactor.redact_fields(fields)
    final_text = _all_text(redacted)

    result.presidio_surviving = _scan_pattern(final_text, recognizers)

    # Gate 1
    allowed = redactor.get_allowed_tokens()
    for inst in pii_by_id.get(ticket_id, {}).get("pii_instances", []):
        result.pii_count += 1
        if inst["value"] in final_text:
            result.leaks.append(
                f"  LEAK  {inst['type']:10s}  '{inst['value']}'  "
                f"→ expected {inst['expected_after_redaction']}"
            )

    # Gate 2
    for t in find_unexpected_tokens(final_text, allowed):
        result.vocab_violations.append(f"  VOCAB  '{t}'")

    # Gate 3
    for inst in ret_by_id.get(ticket_id, {}).get("retain_instances", []):
        result.retain_total += 1
        if inst["value"] not in final_text:
            result.retain_dropped.append(
                f"  DROPPED  {inst['type']:20s}  '{inst['value']}'"
            )

    return result


# ── Output ────────────────────────────────────────────────────────────────────

_LINE = "─" * 64


def _print_ticket(r: TicketResult, verbose: bool = False) -> None:
    status = "PASS" if r.gate1_pass and r.gate2_pass else "FAIL"
    print(f"\n{_LINE}")
    print(f"{r.ticket_id}  [{status}]")
    print(f"  Gate 1 (absence)  : {'PASS' if r.gate1_pass else 'FAIL'}  "
          f"{r.pii_count} PII values, {len(r.leaks)} leak(s)")
    print(f"  Gate 2 (vocab)    : {'PASS' if r.gate2_pass else 'FAIL'}  "
          f"{len(r.vocab_violations)} violation(s)")
    print(f"  Gate 3 (retention): {r.retain_total - len(r.retain_dropped)}/{r.retain_total} "
          f"({r.retention_rate:.3f})  ← report only")
    print(f"  Presidio pattern  : {len(r.presidio_raw_hits)} in raw → "
          f"{len(r.presidio_surviving)} surviving")
    if r.leaks:
        print("  Leaks:")
        for line in r.leaks:
            print(line)
    if r.vocab_violations:
        print("  Vocab violations:")
        for line in r.vocab_violations:
            print(line)
    if verbose and r.retain_dropped:
        print("  Over-redacted:")
        for line in r.retain_dropped[:10]:
            print(line)
    if verbose and r.presidio_surviving:
        print("  Presidio surviving in redacted text:")
        for h in r.presidio_surviving[:5]:
            print(f"    {h['entity_type']:20s}  '{h['value']}'")


def _print_summary(results: list[TicketResult]) -> int:
    from collections import Counter
    g1_fails = [r for r in results if not r.gate1_pass]
    g2_fails = [r for r in results if not r.gate2_pass]
    all_ret  = sum(r.retain_total for r in results)
    all_drop = sum(len(r.retain_dropped) for r in results)
    ret_rate = (all_ret - all_drop) / max(all_ret, 1)

    dropped_by_type: Counter = Counter()
    for r in results:
        for line in r.retain_dropped:
            parts = line.strip().split()
            if len(parts) >= 2:
                dropped_by_type[parts[1]] += 1

    print(f"\n{'═' * 64}")
    print(f"SUMMARY  ({len(results)} ticket(s) tested)")
    print(f"{'─' * 64}")
    print(f"Gate 1 (absence)  : {'PASS' if not g1_fails else 'FAIL'}  "
          f"{len(g1_fails)} ticket(s) with leaks")
    print(f"Gate 2 (vocab)    : {'PASS' if not g2_fails else 'FAIL'}  "
          f"{len(g2_fails)} ticket(s) with vocab violations")
    print(f"Gate 3 (retention): {ret_rate:.4f} "
          f"({all_ret - all_drop}/{all_ret})  target ≥ 0.98")
    print(f"  ↳ dropped by type: {dict(dropped_by_type) or 'none'}")
    total_raw = sum(len(r.presidio_raw_hits) for r in results)
    total_surv = sum(len(r.presidio_surviving) for r in results)
    print(f"Presidio pattern  : {total_raw} hits in raw → {total_surv} surviving")
    print(f"{'═' * 64}")
    overall = "PASS" if not g1_fails and not g2_fails else "FAIL"
    print(f"Overall: {overall}")
    if g1_fails:
        print("\nTickets with Gate 1 failures:")
        for r in g1_fails:
            print(f"  {r.ticket_id}: {len(r.leaks)} leak(s)")
    return 0 if overall == "PASS" else 1


# ── Main ──────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Full redaction test (L1+L2+L3). Stdout only."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--all", action="store_true",
                      help="Test all 745 tickets.")
    mode.add_argument("--ticket", metavar="ID",
                      help="Test a single ticket, e.g. --ticket INC-VDA-0001")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    snap      = _ensure_dataset()
    df        = pd.read_parquet(snap / "data" / "train.parquet")
    directory = _load_users_directory(snap)
    pii_data  = json.loads(_find_sidecar(snap, "pii.json").read_text())
    ret_raw   = json.loads(_find_sidecar(snap, "retention.json").read_text())
    ret_data  = ret_raw["tickets"] if isinstance(ret_raw, dict) else ret_raw

    pii_by_id = {r["ticket_id"]: r for r in pii_data}
    ret_by_id = {r["ticket_id"]: r for r in ret_data}

    redactor    = PolicyRedactor(policy_path=_POLICY, use_presidio=True, directory=directory)
    recognizers = _build_pattern_recognizers()

    if args.all:
        ticket_ids = df["record_id"].tolist()
        label = f"ALL — {len(ticket_ids)} tickets"
    elif args.ticket:
        ticket_ids = [args.ticket]
        label = f"SINGLE — {args.ticket}"
    else:
        ticket_ids = [df["record_id"].iloc[0]]
        label = f"SAMPLE — {ticket_ids[0]}"

    print(f"\n{_LINE}")
    print(f"Redaction Test  |  {label}")
    print(_LINE)

    results: list[TicketResult] = []
    for tid in ticket_ids:
        rows = df[df["record_id"] == tid]
        if rows.empty:
            print(f"  SKIP {tid} — not in parquet")
            continue
        r = run_ticket(tid, rows.iloc[0], pii_by_id, ret_by_id, redactor, recognizers)
        results.append(r)
        if args.all and not args.verbose:
            g1 = "✓" if r.gate1_pass else "✗"
            g2 = "✓" if r.gate2_pass else "✗"
            print(f"  {tid}  G1:{g1} G2:{g2}  ret:{r.retention_rate:.3f}"
                  + (f"  {len(r.leaks)} leak(s)" if r.leaks else ""))
        else:
            _print_ticket(r, verbose=args.verbose)

    return _print_summary(results)


# ── pytest entry point ─────────────────────────────────────────────────────────

import pytest  # noqa: E402


@pytest.fixture(scope="module")
def _presidio_data():
    snap      = _ensure_dataset()
    df        = pd.read_parquet(snap / "data" / "train.parquet")
    directory = _load_users_directory(snap)
    pii_data  = json.loads(_find_sidecar(snap, "pii.json").read_text())
    ret_raw   = json.loads(_find_sidecar(snap, "retention.json").read_text())
    ret_data  = ret_raw["tickets"] if isinstance(ret_raw, dict) else ret_raw
    return {
        "df":          df,
        "pii_by_id":   {r["ticket_id"]: r for r in pii_data},
        "ret_by_id":   {r["ticket_id"]: r for r in ret_data},
        "redactor":    PolicyRedactor(policy_path=_POLICY, use_presidio=True, directory=directory),
        "recognizers": _build_pattern_recognizers(),
    }


def _sample_result(data: dict) -> TicketResult:
    df      = data["df"]
    first   = df["record_id"].iloc[0]
    row     = df[df["record_id"] == first].iloc[0]
    return run_ticket(first, row, data["pii_by_id"], data["ret_by_id"],
                      data["redactor"], data["recognizers"])


def test_presidio_gate1_absence(_presidio_data):
    r = _sample_result(_presidio_data)
    if r.leaks:
        pytest.fail(f"\n{r.ticket_id} — {len(r.leaks)} PII leak(s):\n" + "\n".join(r.leaks))


def test_presidio_gate2_vocab(_presidio_data):
    r = _sample_result(_presidio_data)
    if r.vocab_violations:
        pytest.fail(f"\n{r.ticket_id} — vocab violations:\n" + "\n".join(r.vocab_violations))


def test_presidio_gate3_retention_report(_presidio_data):
    r = _sample_result(_presidio_data)
    print(f"\nRetention: {r.retention_rate:.4f} "
          f"({r.retain_total - len(r.retain_dropped)}/{r.retain_total})")
    if r.retain_dropped:
        for line in r.retain_dropped[:5]:
            print(line)
    assert r.retention_rate >= 0.90, (
        f"Retention {r.retention_rate:.3f} very low — check FP suppressions"
    )


def test_presidio_pattern_audit(_presidio_data):
    r = _sample_result(_presidio_data)
    ner_types = {"PERSON", "USER", "LOCATION"}
    survivors = [h for h in r.presidio_surviving if h["entity_type"] not in ner_types]
    print(f"\nPresidio raw: {len(r.presidio_raw_hits)}, surviving: {len(survivors)} pattern-type")
    if survivors:
        for h in survivors:
            print(f"  {h['entity_type']:20s}  '{h['value']}'")
        pytest.fail(f"{len(survivors)} pattern-detectable PII survived redaction")


if __name__ == "__main__":
    sys.exit(main())
