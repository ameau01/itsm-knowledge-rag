"""DeepEval metric construction for the overview eval.

Overview_quality (G-Eval, the primary bar) rewards a faithful, concise overview that captures the primary root cause + main symptom.
"""

from __future__ import annotations

OVERVIEW_QUALITY_STEPS = [
    "Read the SOURCE PAGE in INPUT and identify its primary root cause and main presenting symptom.",
    "Check that ACTUAL_OUTPUT (the overview) states that primary root cause and main symptom — "
    "especially in its first sentence. Reward capturing the essential answer concisely.",
    "Check that ACTUAL_OUTPUT contains no claim, error code, count, hostname, or detail that the "
    "SOURCE PAGE does not support. Penalize anything unsupported.",
    "Do NOT penalize the overview for omitting secondary or minor details. Being concise and "
    "dropping non-essential detail is correct and expected for an overview.",
    "Check the overview's wording matches the DECLARED CONFIDENCE in INPUT: 'high' may state the "
    "cause directly; 'medium' should hedge (e.g. 'likely'); 'low' must use possibility wording and "
    "must not assert the cause as fact. Penalize over-confident wording on low-confidence pages.",
]


def build_metrics(which: str, model_obj, threshold: float):
    from deepeval.metrics import FaithfulnessMetric, GEval, SummarizationMetric
    from deepeval.test_case import LLMTestCaseParams

    want = {"overview_quality", "faithfulness", "summarization"} if which == "all" else (
        {"summarization", "faithfulness"} if which == "both" else {which})
    metrics = {}
    if "overview_quality" in want:
        metrics["overview_quality"] = GEval(
            name="Overview Quality", model=model_obj, threshold=threshold,
            evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
            evaluation_steps=OVERVIEW_QUALITY_STEPS,
        )
    if "faithfulness" in want:
        metrics["faithfulness"] = FaithfulnessMetric(
            threshold=threshold, model=model_obj, include_reason=True)
    if "summarization" in want:
        metrics["summarization"] = SummarizationMetric(
            threshold=threshold, model=model_obj, include_reason=True)
    return metrics


def geval_input(case) -> str:
    return (f"DECLARED CONFIDENCE: {case.confidence} ({case.ticket_count} source tickets)\n\n"
            f"SOURCE PAGE:\n{case.source}")


def score_case(metrics: dict, case) -> dict:
    from deepeval.test_case import LLMTestCase
    out = {}
    for name, m in metrics.items():
        if name == "overview_quality":
            tc = LLMTestCase(input=geval_input(case), actual_output=case.summary)
        elif name == "faithfulness":  # page is the retrieval context
            tc = LLMTestCase(input=case.source, actual_output=case.summary,
                             retrieval_context=[case.source])
        else:  # summarization (diagnostic)
            tc = LLMTestCase(input=case.source, actual_output=case.summary)
        m.measure(tc)
        out[name] = {"score": float(m.score or 0.0), "reason": getattr(m, "reason", None)}
    return out
