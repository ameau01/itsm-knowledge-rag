# Metrics specification

The scoring contract: how the eval harness measures the system against the frozen
files in this folder. Parameters (k values, thresholds, judge settings) live in
`metrics-config.json`; this document defines each metric and which file feeds it.

The split that governs everything: **deterministic** metrics (exact string checks
against authored answer keys) are gates; **label-based** metrics (counting against
frozen labels) are reported numbers; **judge-based** metrics (LLM-judged) are
reported with variance and never gate anything.

---

## Axis 1: Redaction (deterministic — gates)

Input: every ticket redacted by the pipeline. Answer keys: `redaction/pii.json`,
`redaction/retention.json`.

| Metric | Definition | Gate |
|---|---|---|
| **Leakage rate** | For each of the 8,839 pii instances: FAIL if `value` appears anywhere in the redacted ticket (absence-anywhere; `occurrences` is reporting only). Rate = leaks / 8,839. | **0 leaks** |
| **Token conformance** | Each redacted span must use the instance's `expected_after_redaction` token, from the pinned 8-token vocabulary. | 0 mismatches |
| **Retention rate** | For each of the 8,581 retain instances: PASS if `value` still present in the redacted ticket. Rate = preserved / 8,581. | report; recommend >= 0.98 |

Reported per PII type (8) and per RETAIN type (10), per family, and overall. The two
keys are disjoint by construction, so the gates cannot contradict.

## Axis 2: Retrieval (label-based — reported)

Input: the system's ranked ticket results per query. Labels: `retrieval/simple-queries.json`,
`retrieval/complex-queries.json`. Relevance is cluster membership in `catalog.json`:
**strict** = tickets of the labeled `expected_root_cause`; **lenient** = tickets of
the labeled `expected_family`. Report both levels.

Per simple-query intent:

| Intent | Primary metrics | Note |
|---|---|---|
| diagnosis | recall@k (k = 5, 10) | capped recall: hits / min(k, n_relevant) |
| synthesis | **set recall**: fraction of `expected_ticket_set` in top-k | the set is a required minimum, never a precision denominator |
| exact_match | recall@k; report sparse-vs-dense gap | the sparse-retrieval probe |
| fix_lookup | **precision@k (strict)**: fraction of top-k in the labeled root-cause cluster | asker knows the cause; wrong-cause results are errors |

Also: context precision (fraction of top-k in the correct family) for every simple
query — guards against confidently-wrong overviews.

**Hybrid ablation** (the improvement experiment): all of the above for sparse-only,
dense-only, and hybrid (fused). The sparse arm is whatever the system implements
(classic BM25 or learned sparse vectors) - the contract names the role, the
implementation is recorded in the run's provenance. The per-intent breakdown shows
*where* hybrid wins (exact_match should favor sparse; diagnosis should favor dense),
not just whether.

## Axis 3: Decision policy (label-based — reported)

The three-way policy (confident / ambiguous / abstain) scored two-sided:

| Metric | Definition | Files |
|---|---|---|
| **Candidate-set F1** (complex) | precision & recall of the system's returned candidate set vs `expected_root_cause` (the plausible set, 2–3) | complex-queries.json |
| **Anchor hit rate** (complex) | fraction where `metadata.anchor_root_cause` is in the returned set | complex-queries.json |
| **Over-hedging penalty** | returned-set size vs expected-set size; a system returning 5 when 2 was right scores worse than exact-size | complex-queries.json |
| **Ambiguity-flag accuracy** | flag fires on complex queries; does NOT fire on simple ones (false-ambiguity rate, measured free on the 63) | both |
| **Abstention accuracy** | "don't know" returned on all 15 abstention queries | abstention-queries.json |
| **False-abstention rate** | "don't know" on simple/complex queries (should be ~0) | simple + complex |
| **Knowledge-gap abstention** | the 5 knowledge-gap probes answered "don't know" when DRF is excluded from the wiki — and answered correctly when included | builders' knowledge-gap-queries.json (protocol; see README) |

Policy thresholds are configuration, not tuning targets: set them on a dev slice or
report them as-configured. Tuning them on these queries and then reporting these
queries is overfitting.

## Axis 4: Curation quality (judge-based — reported with variance)

Input: generated wiki pages vs their source tickets. Framework: DeepEval / G-Eval.
Scoped to the SYNTHESIZED text only (consolidated descriptions); golden fields
(root_cause, diagnostics, resolution) are copied verbatim and cannot hallucinate.

| Metric | Definition |
|---|---|
| Faithfulness | claims in the synthesized overview supported by source descriptions/correspondence; report unsupported-claim RATE with examples |
| Citation precision | cited tickets actually support the claim |
| Citation coverage | claims that carry a citation |

Judge protocol (non-negotiable): judge model != curation model; temperature 0;
n >= 3 runs per metric with variance reported; judge prompts versioned. The
`expected_ticket_set` on synthesis queries doubles as citation ground truth where
applicable. A seeded human spot-check complements the judge.

## Axis 5: Efficiency (measured)

Cached per-family overview vs zero-shot per-query synthesis, on identical queries:
latency per query, cost per query, and the Axis-4 judge metrics applied to both arms
(same judge, same protocol) so the quality column is defined, not vibes.

---

## Failure localization

A wrong answer decomposes: retrieval metrics catch the wrong tickets being surfaced
(Axis 2); curation metrics catch a bad overview built from the right tickets
(Axis 4); decision-policy metrics catch the right knowledge wrongly hedged or
withheld (Axis 3). Score all axes so failures are attributable, not blended.

## What is not measured

No end-to-end "did the human agent fix it" metric: the agent is outside the system.
All metrics here are component-level, by design.
