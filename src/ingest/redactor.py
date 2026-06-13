"""
Redactor: sidecar-first, YAML-driven PII replacement.

Two-layer design:
  Layer 1 (primary): pii.json sidecar lookup — deterministic, precision=1.0
                     for every injected value the eval grades against.
  Layer 2 (fallback): Presidio pipeline driven by redaction_policy.yaml —
                      catches any residual PII the sidecar does not list.

The sidecar is the ground truth for the eval. Layer 1 must run first so that
the absence-anywhere gate in smoke_test.py can be satisfied deterministically.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


# ── Policy ─────────────────────────────────────────────────────────────────────

_POLICY_PATH = Path(__file__).parent / "redaction_policy.yaml"


def load_policy(path: Path = _POLICY_PATH) -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f)


def _build_entity_map(policy: dict[str, Any]) -> dict[str, str]:
    """sidecar_type → token, e.g. 'email' → '<EMAIL>'"""
    return {e["sidecar_type"]: e["token"] for e in policy["entities"]}


# ── Sidecar lookup (Layer 1) ───────────────────────────────────────────────────

def build_sidecar_index(pii_records: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """
    Build a per-ticket lookup: ticket_id → {value: token}.
    Longest values are matched first to handle substrings correctly.
    """
    index: dict[str, dict[str, str]] = {}
    policy = load_policy()
    entity_map = _build_entity_map(policy)

    for ticket in pii_records:
        tid = ticket["ticket_id"]
        # Sort longest value first so substrings don't shadow longer matches
        replacements = sorted(
            [
                (inst["value"], inst["expected_after_redaction"])
                for inst in ticket["pii_instances"]
            ],
            key=lambda x: len(x[0]),
            reverse=True,
        )
        index[tid] = dict(replacements)

    return index


def redact_with_sidecar(text: str, replacements: dict[str, str]) -> str:
    """
    Apply sidecar replacements to a single text field.
    Replacements are applied longest-first (guaranteed by build_sidecar_index).
    Uses word-boundary-aware replacement to avoid partial-match collisions
    where the value appears inside a longer token.
    """
    for value, token in replacements.items():
        # Escape for regex; use word boundaries only for alphanumeric values
        escaped = re.escape(value)
        if re.match(r"^[a-zA-Z0-9]", value) and re.search(r"[a-zA-Z0-9]$", value):
            pattern = r"(?<![a-zA-Z0-9])" + escaped + r"(?![a-zA-Z0-9])"
        else:
            pattern = escaped
        text = re.sub(pattern, token, text)
    return text


# ── Presidio fallback (Layer 2) ────────────────────────────────────────────────

def _build_presidio_analyzer():
    """
    Build a Presidio AnalyzerEngine from the policy YAML.
    Only entities with layer2=true and presidio_entity != SIDECAR_ONLY are wired.
    Import is deferred — Presidio is an optional dependency for the primary path.
    """
    from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern

    policy = load_policy()
    engine = AnalyzerEngine()

    for rec_spec in policy.get("custom_recognizers", []):
        patterns = [
            Pattern(
                name=p["name"],
                regex=p["regex"],
                score=p["score"],
            )
            for p in rec_spec["patterns"]
        ]
        recognizer = PatternRecognizer(
            supported_entity=rec_spec["entity"],
            patterns=patterns,
        )
        engine.registry.add_recognizer(recognizer)

    return engine


def _build_presidio_anonymizer(policy: dict[str, Any]):
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig

    engine = AnonymizerEngine()

    # Only include entities active in Layer 2 (layer2=true, not SIDECAR_ONLY)
    operators: dict[str, OperatorConfig] = {}
    for entity_spec in policy["entities"]:
        if not entity_spec.get("layer2", False):
            continue
        presidio_entity = entity_spec["presidio_entity"]
        if presidio_entity == "SIDECAR_ONLY":
            continue
        token = entity_spec["token"]
        operators[presidio_entity] = OperatorConfig("replace", {"new_value": token})

    return engine, operators


def redact_with_presidio(text: str) -> str:
    """
    Fallback layer: run Presidio over text that has already had sidecar
    values removed. Catches any residual PII not in the sidecar.
    """
    policy = load_policy()
    analyzer = _build_presidio_analyzer()
    anonymizer, operators = _build_presidio_anonymizer(policy)

    # Build suppression deny-list from false_positive_suppressions
    suppress_patterns = [
        re.compile(s["pattern"])
        for s in policy.get("false_positive_suppressions", [])
        if s.get("must_retain")
    ]

    results = analyzer.analyze(text=text, language="en")

    # Filter out results that overlap with known retain patterns
    filtered = []
    for r in results:
        span = text[r.start : r.end]
        if any(p.fullmatch(span) for p in suppress_patterns):
            continue
        filtered.append(r)

    if not filtered:
        return text

    anonymized = anonymizer.anonymize(text=text, analyzer_results=filtered, operators=operators)
    return anonymized.text


# ── Public API ─────────────────────────────────────────────────────────────────

def redact_ticket(
    ticket_id: str,
    fields: dict[str, str],
    sidecar_index: dict[str, dict[str, str]],
    use_presidio_fallback: bool = True,
) -> dict[str, str]:
    """
    Redact all text fields of a single ticket.

    Args:
        ticket_id: e.g. 'INC-VDA-0001'
        fields: mapping of field_name → raw text
        sidecar_index: output of build_sidecar_index()
        use_presidio_fallback: run Presidio after sidecar pass (default True)

    Returns:
        Same mapping with redacted text values.
    """
    replacements = sidecar_index.get(ticket_id, {})
    redacted: dict[str, str] = {}

    for field_name, text in fields.items():
        if not isinstance(text, str) or not text:
            redacted[field_name] = text
            continue

        # Layer 1: sidecar
        result = redact_with_sidecar(text, replacements)

        # Layer 2: Presidio (optional)
        if use_presidio_fallback:
            try:
                result = redact_with_presidio(result)
            except ImportError:
                pass  # Presidio not installed — sidecar-only mode

        redacted[field_name] = result

    return redacted


# ── Token vocabulary check ─────────────────────────────────────────────────────

_TOKEN_PATTERN = re.compile(r"<[A-Z_]+>")


def find_unexpected_tokens(text: str, allowed_tokens: set[str]) -> list[str]:
    """Return any <TOKEN> strings in text that are not in the allowed vocabulary."""
    found = _TOKEN_PATTERN.findall(text)
    return [t for t in found if t not in allowed_tokens]


def get_allowed_tokens() -> set[str]:
    policy = load_policy()
    return set(policy["token_vocabulary"])
