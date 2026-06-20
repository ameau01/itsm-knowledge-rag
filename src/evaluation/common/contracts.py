"""
Shared contracts for the L1 evaluation: the data shapes that bridge a retriever's
output, the deterministic harness, and the DeepEval judge.

All pure (no IO, no deepeval import). The retriever returns `RetrievedPoint`s (one per
ticket section). The deterministic path dedupes those to parent tickets; the judge path
keeps them granular and pairs each with its redacted text. `build_l1_eval_case` is the
pure adapter that assembles both views — the IO (reading section text / narratives from
the store) happens in `adapter/corpus.py` and is passed in already-resolved.
"""

from __future__ import annotations

from dataclasses import dataclass

from .queries import Query

# DeepEval's generation metrics read actual_output as "the generated answer." L1 has no
# generation, so we use an explicit placeholder — never the retrieved context, which
# would let a generation metric score retrieval as if it were an answer.
NO_GENERATION = "[no generation: L1 retrieval only]"


@dataclass(frozen=True)
class RetrievedPoint:
    """One retrieved section of a ticket. Identified by (ticket_id, section_name);
    the redacted text is resolved from the operational store by that composite key."""
    ticket_id: str
    section_name: str
    score: float


@dataclass(frozen=True)
class JudgeInput:
    """The minimal shape a judge needs. ContextualPrecision uses expected_output;
    ContextualRelevancy ignores it (set None)."""
    query_id: str
    input_text: str
    retrieval_context: list[str]
    expected_output: str | None


@dataclass(frozen=True)
class L1EvalCase:
    query_id: str
    query: str
    expected_root_cause: list[str]    # ids; deterministic strict label
    expected_family: list[str]        # ids; deterministic lenient label
    retrieved_ticket_ids: list[str]   # deduped to parent tickets, ranked (deterministic)
    retrieved_texts: list[str]        # redacted point texts, ranked (judge)
    root_cause_reference: str         # expected_output for ContextualPrecision

    def to_judge_input(self) -> JudgeInput:
        return JudgeInput(
            query_id=self.query_id,
            input_text=self.query,
            retrieval_context=self.retrieved_texts,
            expected_output=self.root_cause_reference,
        )


def dedupe_to_tickets(point_ticket_ids: list[str]) -> list[str]:
    """Collapse a ranked list of point→ticket ids to distinct tickets, order preserved.
    Stops one ticket (whose several sections all rank) from filling many top-k slots."""
    seen: set[str] = set()
    out: list[str] = []
    for tid in point_ticket_ids:
        if tid not in seen:
            seen.add(tid)
            out.append(tid)
    return out


def build_l1_eval_case(
    query: Query,
    retrieved: list[RetrievedPoint],
    retrieved_texts: list[str],
    root_cause_reference: str,
) -> L1EvalCase:
    """Pure adapter: assemble the dual-granularity case. `retrieved_texts` is aligned to
    `retrieved` (resolved by the caller from the store); the deterministic side dedupes
    the points to parent tickets."""
    return L1EvalCase(
        query_id=query.query_id,
        query=query.text,
        expected_root_cause=query.expected_root_cause,
        expected_family=query.expected_family,
        retrieved_ticket_ids=dedupe_to_tickets([p.ticket_id for p in retrieved]),
        retrieved_texts=list(retrieved_texts),
        root_cause_reference=root_cause_reference,
    )
