"""
The real DeepEval judge.

Wraps DeepEval's ContextualPrecision / ContextualRelevancy metrics. The metric objects
are built once in `__init__` and reused — `measure()` overwrites their internal state on
each call, so reuse is safe and avoids rebuilding objects thousands of times.

`deepeval` is imported lazily inside the constructor, so importing this module (and
running the offline suite through MockJudge) needs neither `deepeval` nor an API key.
The judge model is cross-family vs the Anthropic generator (OpenAI frontier), to avoid
self-preference bias. Pin the exact model string via config / `.env`.
"""

from __future__ import annotations

import os

from ..common.contracts import NO_GENERATION, JudgeInput
from .base import CONTEXTUAL_PRECISION, CONTEXTUAL_RELEVANCY, JudgeScore


def _resolve_judge_model(model: str, api_key: str | None):
    """Use DeepEval's native GPTModel when it accepts the id (well-tested path); fall back
    to our custom OpenAI model when it doesn't (e.g. gpt-5.x not in the allowlist). This
    auto-adapts to whatever DeepEval version is installed."""
    try:
        from deepeval.models import GPTModel
        return GPTModel(model=model)
    except Exception:
        from .openai_model import OpenAIJudgeModel
        return OpenAIJudgeModel(model, api_key=api_key)


class DeepEvalJudge:
    def __init__(self, model: str, *, include_reason: bool = True,
                 api_key: str | None = None) -> None:
        self.model = model
        self.name = f"deepeval:{model}"
        # Lazy import: top-level `deepeval` is the third-party package, not this
        # subpackage (absolute imports resolve to sys.path, and we live under
        # `evaluation.deepeval`). Absent in CI, which is why it is imported here.
        from deepeval.metrics import ContextualPrecisionMetric, ContextualRelevancyMetric

        model_obj = _resolve_judge_model(model, api_key or os.getenv("OPENAI_API_KEY"))
        self._metrics = {
            CONTEXTUAL_PRECISION: ContextualPrecisionMetric(model=model_obj, include_reason=include_reason),
            CONTEXTUAL_RELEVANCY: ContextualRelevancyMetric(model=model_obj, include_reason=include_reason),
        }

    def score(self, case: JudgeInput, metric: str) -> JudgeScore:
        from deepeval.test_case import LLMTestCase

        tc = LLMTestCase(
            input=case.input_text,
            actual_output=NO_GENERATION,            # L1 has no generation; never the context
            retrieval_context=case.retrieval_context,
            expected_output=case.expected_output,   # used by ContextualPrecision; ignored by Relevancy
        )
        m = self._metrics[metric]
        m.measure(tc)
        return JudgeScore(metric, float(m.score))
