# Wiki and overview evaluation

How the L2 layer is measured. L2 is the curated overview built on top of retrieval. Where L1 finds the right tickets, L2 turns them into a prepared answer. This doc covers whether that answer is faithful to the tickets it draws on, and whether precomputing it pays off against generating one per query. For L1 retrieval, see [retrieval-evaluation.md](retrieval-evaluation.md). For how L2 is built, see [retrieval.md](retrieval.md).

L2 is where text is generated, so this is the judge-based half of the evaluation. A faithfulness score is a model's judgment, not a count. It is reported as such, with the judge protocol stated.


## What is generated, and what is not

The split decides what gets checked.

The curated description is generated. A model takes the many ways users described one problem and writes a single coherent issue statement. This is the only synthesized text on the page, and the only text that can drift from its source.

The root cause and the resolution are not generated. They are the golden fields, surfaced verbatim from the ticket. A copied field has nothing to hallucinate, so it is not faithfulness-checked. Checking a verbatim copy against itself would be circular and meaningless.

So faithfulness is scoped to the generated description, measured against the ticket descriptions and correspondence it was built from. Nothing else.


## Faithfulness

The core L2 metric. Does the generated description claim only what its source tickets support?

Measured with DeepEval's faithfulness metric. The reference is the source description and correspondence for that root cause, the same text the curation read. The metric breaks the generated description into claims and checks each against the source. A claim the source does not support is a hallucination, reported as an unsupported-claim rate with examples, not just an average.

| Metric | Result |
|---|---|
| Faithfulness | TBD |
| Unsupported-claim rate | TBD |

The judge is a different model from the one that wrote the description. A model grading its own output is not a check. Temperature is zero, three runs, variance reported.


## Variation preservation

A faithfulness score alone misses a failure that matters for this corpus. Curation consolidates many descriptions into one statement. The risk is that consolidation flattens the real variations into a bland average, dropping the differences that a reading agent needs.

This is a project-specific quality bar, so it is checked with a custom G-Eval rubric rather than a stock metric. The rubric scores whether the consolidated description preserves the distinct ways a problem presented, instead of collapsing them into a single generic line. A page can be perfectly faithful and still fail this, by being faithful to a flattened summary that lost the useful detail.

| Metric | Result |
|---|---|
| Variation-preservation (G-Eval) | TBD |

G-Eval is used here because the criterion is specific to this project's design, where preserving variation is an explicit goal. A generic metric does not know to look for it.


## Citation accuracy (planned)

If the curated page emits per-claim citations back to source tickets, two things are checked: precision, whether a cited ticket actually supports the claim, and coverage, whether claims carry a citation at all. This measures the verify-against-sources trust model directly. The agent should be able to trace any claim to a ticket.

| Metric | Result |
|---|---|
| Citation precision | TBD |
| Citation coverage | TBD |

This is a planned check. It applies once the curated page carries claim-level citations. Until then, faithfulness is the grounding metric.


## The query-time relevance line (planned)

The cached page is built once. On top of it, the planned serving step generates a short per-query line: why this page answers the specific question asked, and which diagnostic steps apply. This is not a static lookup and not a zero-shot synthesis. It is a small generation grounded in the already-curated page, written for the query in hand.

Because it generates text per query, it needs its own grounding check, separate from the build-time faithfulness above.

| Metric | Result |
|---|---|
| Relevance-line faithfulness | TBD |
| Relevance-line answer-relevancy | TBD |

Faithfulness asks whether the line claims only what the cached page supports. Answer-relevancy asks whether the line actually addresses the query. Both run under the same judge protocol: a different model, temperature zero, repeated runs, variance reported. This check is planned alongside the serving step.


## Efficiency: cache versus zero-shot

The reason L2 is precomputed is cost and latency. The cached overview is compared head to head against per-query zero-shot synthesis, on the same queries.

| Approach | Latency / query | Cost / query | Quality |
|---|---|---|---|
| Zero-shot synthesis | TBD | TBD | TBD |
| Cached overview | TBD | TBD | TBD |

Zero-shot runs a model over the retrieved tickets every query. The cached overview pays that cost once, during ingest, and serves it thereafter. The expected result is lower latency and cost per query for the cache, at no loss of quality, because the cached page was built in one careful pass rather than a rushed per-query one. The measured numbers are reported either way.


## A human read alongside the automated scores

The judge-based metrics are the scalable half. A human spot-check of a sample of pages is the complement. It catches what a judge misses: a page that scores well but reads poorly, or a redaction artifact that is technically clean but confusing. For this corpus it is a one-time sample, reported next to the automated numbers. In a deployment it is the human-review step before a page is published.


## What is not measured

Whether the agent's final fix was correct is outside this layer. L2 is judged on faithfulness to its sources and on the efficiency of serving, which are the parts the system controls. The boundary is stated, not hidden.
