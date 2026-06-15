"""
Redactor Three-layer design:
  Layer 1: AD identity exact match
           Source: users_directory.json (HuggingFace / Kaggle export of the
           synthesised corporate AD). In production: Get-ADUser / ldapsearch dump.
           Covers: username (sAMAccountName) → <USER>
                   display_name (displayName)  → <PERSON>
                   email (mail)                → <EMAIL>
           Exact match is more precise than any regex and requires no maintenance.
           Over-redaction is accepted — identity fields carry no technical knowledge.

  Layer 2: Format-based rules (regex)
           Driven by format_rules section of redaction_policy.yaml.
           Covers: emp_id, hostname, ip, phone, location.

  Layer 3: Presidio NER (catch-all)
           Driven by presidio section of redaction_policy.yaml.
           Covers: residual person names, international phone formats.

pii.json and retention.json are NOT used at runtime — eval artefacts only.
See src/ingest/score.py to run the scored benchmark.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_POLICY_PATH = Path(__file__).parent / "redaction_policy.yaml"


# ── Policy loader ─────────────────────────────────────────────────────────────

def load_policy(path: Path = _POLICY_PATH) -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f)


# ── Layer 1: AD identity exact match ─────────────────────────────────────────

@dataclass
class AdRule:
    token: str
    pattern: re.Pattern  # type: ignore[type-arg]


def build_ad_rules(
    policy: dict[str, Any],
    directory: dict[str, Any] | None = None,
) -> list[AdRule]:
    """
    Build one compiled regex per AD attribute (username, display_name, email).

    If *directory* is provided (pre-loaded users_directory.json dict) it is used
    directly. Otherwise the path in ad_identity.source is resolved relative to
    the policy file's parent directory (fallback for local dev).

    Longest-first ordering inside each alternation prevents short values from
    shadowing longer ones (e.g. 'dcho' shadowing 'dcho@corp.com').
    """
    ad_cfg = policy.get("ad_identity", {})

    if directory is not None:
        raw = directory
    else:
        source  = ad_cfg.get("source", "dictionaries/users_directory.json")
        db_path = _POLICY_PATH.parent / source
        raw     = json.loads(db_path.read_text())

    users: list[dict[str, Any]] = raw.get("users", [])

    rules: list[AdRule] = []
    for attr_cfg in ad_cfg.get("attributes", []):
        key        = attr_cfg["yaml_key"]
        token      = attr_cfg["token"]
        case_sens  = attr_cfg.get("case_sensitive", True)
        whole_word = attr_cfg.get("whole_word", True)

        values = [
            str(rec[key])
            for rec in users
            if isinstance(rec, dict) and key in rec and rec[key]
        ]
        if not values:
            continue

        sorted_vals = sorted(set(values), key=len, reverse=True)
        escaped     = [re.escape(v) for v in sorted_vals]
        alternation = "|".join(escaped)
        pat_str     = (r"\b(?:" + alternation + r")\b") if whole_word else alternation
        flags       = 0 if case_sens else re.IGNORECASE
        rules.append(AdRule(token=token, pattern=re.compile(pat_str, flags)))

    return rules


def _apply_ad_rules(text: str, rules: list[AdRule]) -> str:
    for rule in rules:
        text = rule.pattern.sub(rule.token, text)
    return text


# ── Layer 2: Format-based rules ───────────────────────────────────────────────

@dataclass
class FormatRule:
    name: str
    token: str
    priority: int
    patterns: list[re.Pattern]  # type: ignore[type-arg]


def build_format_rules(policy: dict[str, Any]) -> list[FormatRule]:
    rules: list[FormatRule] = []
    for rd in policy.get("format_rules", []):
        compiled = [re.compile(p) for p in rd.get("patterns", [])]
        rules.append(FormatRule(
            name=rd["name"],
            token=rd["token"],
            priority=rd.get("priority", 99),
            patterns=compiled,
        ))
    rules.sort(key=lambda r: r.priority)
    return rules


def _apply_format_rules(text: str, rules: list[FormatRule]) -> str:
    for rule in rules:
        for pattern in rule.patterns:
            text = pattern.sub(rule.token, text)
    return text


# ── Layer 3: Presidio NER ─────────────────────────────────────────────────────

def _build_presidio_analyzer(policy: dict[str, Any]):
    from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern

    engine = AnalyzerEngine()
    for rec_spec in policy.get("presidio", {}).get("custom_recognizers", []):
        patterns = [
            Pattern(name=p["name"], regex=p["regex"], score=p["score"])
            for p in rec_spec["patterns"]
        ]
        engine.registry.add_recognizer(
            PatternRecognizer(supported_entity=rec_spec["entity"], patterns=patterns)
        )
    return engine


def _apply_presidio(text: str, policy: dict[str, Any], analyzer) -> str:
    entity_token: dict[str, str] = {}
    for e in policy.get("presidio", {}).get("entities", []):
        entity_token[e["presidio_entity"]] = e["token"]
    for cr in policy.get("presidio", {}).get("custom_recognizers", []):
        entity_token[cr["entity"]] = cr["token"]

    if not entity_token:
        return text

    suppress_patterns = [
        re.compile(s["pattern"])
        for s in policy.get("presidio", {}).get("false_positive_suppressions", [])
    ]
    per_entity_threshold: dict[str, float] = (
        policy.get("presidio", {}).get("per_entity_threshold", {})
    )

    results = analyzer.analyze(
        text=text, language="en",
        entities=list(entity_token.keys()),
        score_threshold=None,
    )
    if not results:
        return text

    filtered = []
    for r in results:
        floor = per_entity_threshold.get(r.entity_type)
        if floor is not None and r.score < floor:
            continue
        span = text[r.start:r.end]
        if any(p.fullmatch(span) for p in suppress_patterns):
            continue
        filtered.append(r)
    if not filtered:
        return text

    # Apply right-to-left to preserve offsets
    filtered.sort(key=lambda r: r.start, reverse=True)
    text_list = list(text)
    for r in filtered:
        token = entity_token.get(r.entity_type, f"<{r.entity_type}>")
        text_list[r.start:r.end] = list(token)
    return "".join(text_list)


# ── Public API ────────────────────────────────────────────────────────────────

class PolicyRedactor:
    """
    Three-layer redactor driven by redaction_policy.yaml.
    No pii.json dependency at runtime.

    Args:
        policy_path:  Path to redaction_policy.yaml.
        use_presidio: Enable Layer 3 Presidio NER (default True).
        directory:    Pre-loaded users_directory.json dict
                      ({"metadata": ..., "users": [...]}).  When supplied, the
                      ad_identity.source path in the policy is ignored — the
                      caller controls where the user directory comes from (HF
                      snapshot, Kaggle download, or local file).
    """

    def __init__(
        self,
        policy_path: Path = _POLICY_PATH,
        use_presidio: bool = True,
        directory: dict[str, Any] | None = None,
    ) -> None:
        self.policy       = load_policy(policy_path)
        self.ad_rules     = build_ad_rules(self.policy, directory=directory)
        self.format_rules = build_format_rules(self.policy)
        self.presidio     = None
        if use_presidio:
            try:
                self.presidio = _build_presidio_analyzer(self.policy)
            except ImportError:
                pass  # Presidio not installed — L1+L2 only

    def redact(self, text: str) -> str:
        """Redact a single string through all three layers."""
        if not text:
            return text
        text = _apply_ad_rules(text, self.ad_rules)
        text = _apply_format_rules(text, self.format_rules)
        if self.presidio:
            text = _apply_presidio(text, self.policy, self.presidio)
        return text

    def redact_fields(self, fields: dict[str, str]) -> dict[str, str]:
        """Redact all text fields in a dict, returning the same dict shape."""
        return {
            name: self.redact(text) if isinstance(text, str) and text else text
            for name, text in fields.items()
        }

    def get_allowed_tokens(self) -> set[str]:
        return set(self.policy.get("token_vocabulary", []))


# ── Token vocabulary check (used by tests) ────────────────────────────────────

_TOKEN_PATTERN = re.compile(r"<[A-Z_]+>")


def find_unexpected_tokens(text: str, allowed_tokens: set[str]) -> list[str]:
    """Return any <TOKEN> strings in text that are not in the allowed vocabulary."""
    return [t for t in _TOKEN_PATTERN.findall(text) if t not in allowed_tokens]
