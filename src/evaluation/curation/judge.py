"""The real DeepEval / G-Eval judge for curation (L2).

Mirrors evaluation.deepeval.deepeval_judge: 

Metric -> DeepEval mapping (per the build spec):
  faithfulness:<field>  FaithfulnessMetric   actual=field, retrieval_context=per-arm context
  answer_relevancy      AnswerRelevancyMetric actual=symptoms, input=title
  summarization         SummarizationMetric   input=full source pool, actual=combined body
  variation             GEval (custom)        actual=variations+symptoms, context=full pool

The case-shaping (which LLMTestCase slot each metric fills) is a pure function so it is
unit-tested offline without deepeval or an API key.
"""

from __future__ import annotations

import os

from .cache import CurationCache
from .contracts import (
    ANSWER_RELEVANCY,
    FAITHFULNESS,
    SUMMARIZATION,
    VARIATION,
    CurationCase,
    JudgeScore,
)

# ── G-Eval variation-preservation criterion (verbatim from the build spec) ──────────
_VARIATION_CRITERIA = (
    "Assess whether the consolidated text preserves the distinct ways this problem presented "
    "across the source tickets, instead of collapsing them into one generic description. "
    "Reward keeping real, meaningfully different presentations and edge cases. Penalize "
    "flattening several distinct presentations into a single bland line."
)
_VARIATION_STEPS = [
    "Read the source tickets and list the distinct ways the problem presented.",
    "Read the consolidated text and list the presentations it mentions.",
    "Compare. Note any distinct presentation in the source that is missing.",
    "Score higher when distinct presentations are preserved, lower when they are flattened "
    "or dropped.",
]

# ── pure case-shaping: which LLMTestCase slots each base metric needs ────────────────
# input + actual_output are always present (LLMTestCase requires them); retrieval_context is
# added only where a metric consumes it.
_SHAPES: dict[str, tuple[str, ...]] = {
    FAITHFULNESS: ("input", "actual_output", "retrieval_context"),
    ANSWER_RELEVANCY: ("input", "actual_output"),
    SUMMARIZATION: ("input", "actual_output"),
    VARIATION: ("input", "actual_output", "retrieval_context"),
}


def base_metric(metric_key: str) -> str:
    """'faithfulness:symptoms' -> 'faithfulness'; everything else maps to itself."""
    return metric_key.split(":", 1)[0]


def build_test_case(case: CurationCase, factory):
    """Pure: assemble the test-case kwargs for `case` and hand them to `factory`. The real
    factory is deepeval's LLMTestCase; tests pass a dict factory to assert the wiring."""
    slots = _SHAPES[base_metric(case.metric)]
    kwargs: dict[str, object] = {}
    if "input" in slots:
        kwargs["input"] = case.input_text
    if "actual_output" in slots:
        kwargs["actual_output"] = case.actual_output
    if "retrieval_context" in slots:
        kwargs["retrieval_context"] = list(case.retrieval_context)
    return factory(**kwargs)


class CurationJudge:
    def __init__(
        self,
        model: str,
        *,
        include_reason: bool = True,
        api_key: str | None = None,
        cache: CurationCache | None = None,
    ) -> None:
        self.model = model
        self.name = f"deepeval-curation:{model}"
        self._cache = cache

        # Lazy: deepeval is the third-party package (absent in CI / sandbox).
        from deepeval.metrics import (
            AnswerRelevancyMetric,
            FaithfulnessMetric,
            GEval,
            SummarizationMetric,
        )
        from deepeval.test_case import LLMTestCaseParams

        # Reuse L1's STATELESS model adapter (the only shared code) — it just wraps a model
        # string, so importing/using it cannot change L1 behavior.
        from ..deepeval.deepeval_judge import _resolve_judge_model

        model_obj = _resolve_judge_model(model, api_key or os.getenv("OPENAI_API_KEY"))
        self._metrics = {
            FAITHFULNESS: FaithfulnessMetric(model=model_obj, include_reason=include_reason),
            ANSWER_RELEVANCY: AnswerRelevancyMetric(model=model_obj, include_reason=include_reason),
            SUMMARIZATION: SummarizationMetric(model=model_obj),
            VARIATION: GEval(
                name="Variation preservation",
                criteria=_VARIATION_CRITERIA,
                evaluation_steps=_VARIATION_STEPS,
                evaluation_params=[
                    LLMTestCaseParams.ACTUAL_OUTPUT,
                    LLMTestCaseParams.RETRIEVAL_CONTEXT,
                ],
                model=model_obj,
            ),
        }

    def score(self, case: CurationCase) -> JudgeScore:
        cache = self._cache  # local binding so mypy narrows the Optional
        ckey = cache.key(self.name, case) if cache is not None else None
        if cache is not None and ckey is not None:
            hit = cache.get(ckey)
            if hit is not None:
                return JudgeScore(case.metric, hit)

        from deepeval.test_case import LLMTestCase

        tc = build_test_case(case, LLMTestCase)
        metric = self._metrics[base_metric(case.metric)]
        metric.measure(tc)
        value = float(metric.score or 0.0)

        if cache is not None and ckey is not None:
            cache.put(ckey, value)
        return JudgeScore(case.metric, value)
