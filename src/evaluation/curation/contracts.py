"""Pure contracts for the curation (L2) eval: candidate shape, case shape, case builder.

The judge (M2) turns a CurationCase into a DeepEval LLMTestCase. 
Keeping this layer pure means the case builder is unit-testable with no DB.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol

# ── metric keys ──────────────────────────────────────────────────────────────────
FAITHFULNESS = "faithfulness"
ANSWER_RELEVANCY = "answer_relevancy"
SUMMARIZATION = "summarization"
VARIATION = "variation"

GENERATED_FIELDS: tuple[str, ...] = ("title", "symptoms", "cause", "variations", "diagnostic_summary")
BODY_FIELDS: tuple[str, ...] = ("symptoms", "cause", "variations")


def faithfulness_metric(field_name: str) -> str:
    return f"{FAITHFULNESS}:{field_name}"


@dataclass(frozen=True)
class JudgeScore:
    """A single metric's score (duplicated from deepeval.base to keep this layer import-light)."""
    metric: str
    value: float


@dataclass(frozen=True)
class Candidate:
    """One arm's output for one root cause, plus the context that arm actually fed its model.

    `curation` keys: title, symptoms, cause, variations, reporting.
    `context` maps a generated field -> the source texts that arm used for it (per-arm, for
    faithfulness). For the gold arm the resolver synthesizes this from the eval mapping's
    input_scope; a real strategy logs what it retrieved.
    """
    arm: str
    root_cause_id: str
    family: str
    curation: Mapping[str, str]
    context: Mapping[str, Sequence[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class PageMeta:
    """Per-page facts the runner needs that don't depend on the arm: how many member
    tickets, and the FULL evidence pool (all members, uncapped) used by coverage metrics."""
    root_cause_id: str
    n_members: int
    evidence_pool: Mapping[str, Sequence[str]]

    @property
    def multi_ticket(self) -> bool:
        return self.n_members > 1


@dataclass(frozen=True)
class CurationCase:
    """One scored unit. Maps 1:1 to a DeepEval LLMTestCase (input / actual_output /
    retrieval_context / expected_output)."""
    case_id: str
    arm: str
    root_cause_id: str
    metric: str
    input_text: str
    actual_output: str
    retrieval_context: list[str]
    expected_output: str | None = None


class CurationJudge(Protocol):
    name: str

    def score(self, case: CurationCase) -> JudgeScore: ...


# ── helpers ──────────────────────────────────────────────────────────────────────
def _clean(s: object) -> str:
    return (s or "").strip() if isinstance(s, str) else ""


def _dedupe(texts: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(t for t in texts if t))


def full_source(evidence_pool: Mapping[str, Sequence[str]]) -> list[str]:
    """Deduplicated union of every field's evidence pool — the source doc for summarization."""
    merged: list[str] = []
    for texts in evidence_pool.values():
        merged.extend(texts)
    return _dedupe(merged)


# ── case builder (pure) ──────────────────────────────────────────────────────────
def build_curation_cases(
    candidate: Candidate,
    evidence_pool: Mapping[str, Sequence[str]],
    *,
    multi_ticket: bool,
) -> list[CurationCase]:
    """Expand one candidate page into the per-metric cases, wiring each metric to the right
    reference (faithfulness -> per-arm context; coverage -> full evidence pool)."""
    rc = candidate.root_cause_id
    u = candidate.curation
    stand_in = f"Known issue: {rc}"
    cases: list[CurationCase] = []

    def add(metric: str, actual: str, ctx: Sequence[str], inp: str = stand_in) -> None:
        cases.append(
            CurationCase(
                case_id=f"{rc}::{metric}",
                arm=candidate.arm,
                root_cause_id=rc,
                metric=metric,
                input_text=inp,
                actual_output=actual,
                retrieval_context=list(ctx),
            )
        )

    # 1) Faithfulness — per field, against THIS arm's own context.
    for f in GENERATED_FIELDS:
        text = _clean(u.get(f))
        if text:
            add(faithfulness_metric(f), text, candidate.context.get(f, []))

    # 2) Answer relevancy — does the symptoms text address the issue (no context needed).
    symptoms = _clean(u.get("symptoms"))
    if symptoms:
        add(ANSWER_RELEVANCY, symptoms, [], inp=_clean(u.get("title")) or stand_in)

    # 3) Summarization — combined body vs the full evidence pool (kept-the-important-content).
    body = "\n\n".join(t for t in (_clean(u.get(f)) for f in BODY_FIELDS) if t)
    source = full_source(evidence_pool)
    if body and source:
        # SummarizationMetric reads input as the source doc, actual_output as the summary.
        add(SUMMARIZATION, body, [], inp="\n\n".join(source))

    # 4) Variation preservation — multi-ticket pages only (a singleton has no cross-ticket variation). Judged against the variations' evidence pool.
    if multi_ticket:
        variation_text = "\n".join(
            t for t in (_clean(u.get("variations")), symptoms) if t
        )
        var_pool = evidence_pool.get("variations") or source
        if variation_text:
            add(VARIATION, variation_text, var_pool)

    return cases
