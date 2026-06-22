# Evaluation

Evaluation here separates two questions. Can a check be made deterministic, or does it need a model's judgment? And when an answer is wrong, was it retrieval that failed or generation? The first question decides how each axis is scored. The second lets a failure be traced to the layer that caused it.

This page is the map. Each axis links to the doc that covers it in full.


## The axes

| Axis | Layer | Metric | Class |
|---|---|---|---|
| PII leakage | Redaction | Leak rate vs. authored key | Deterministic |
| Technical retention | Redaction | RETAIN strings preserved | Deterministic |
| Retrieval | L1 | recall@k | Label-based |
| Curation quality | L2 | Faithfulness, citation accuracy | Judge-based |
| Abstention | L1 | Accuracy on out-of-corpus queries | Label-based |
| Efficiency | L2 | Latency, cost vs. zero-shot | Measured |

The Class column is the point. Not every property is checked the same way, and the doc says which is which. A leak rate is a count. A faithfulness score is a model's judgment. Treating them as the same kind of number would be the mistake.


## Two things hold the eval together

Non-circularity. The ground truth is authored independently of the system being graded. The redactor is scored against a key written during data generation, before any redactor existed, so it is graded against an answer it never saw. Retrieval is scored against root-cause ids assigned in the frozen catalog, not against the retriever's own similarity. A score where the system grades its own work means nothing. These do not.

Failure localization. A wrong answer is one of two failures. The wrong tickets were retrieved (L1), or the right tickets were retrieved and the overview was not faithful to them (L2). The axes are kept separate so a failure can be traced to the layer that caused it, instead of tuning the whole system blind.


## The three docs

- [redaction-evaluation.md](redaction-evaluation.md). Does the redactor remove every PII value and keep every technical term? Deterministic, scored against two authored keys. This is the one axis with measured results today: 98.9 percent of PII removed, 97.6 percent of technical content kept.
- [retrieval-evaluation.md](retrieval-evaluation.md). Does L1 surface the right prior tickets, and does the hybrid beat its parts? Label-based, scored against the frozen catalog. Covers the arm ablation, complex-query resilience, and abstention.
- [wiki-evaluation.md](wiki-evaluation.md). Is the L2 overview faithful to the tickets it draws on? Judge-based, with the cache-versus-zero-shot efficiency comparison alongside.


## The frozen eval-set

The ground truth is built, frozen, and committed under `eval-set/`. The harness reads only those files. Upstream copies are documentation. These are the answer key.

The labels were not hand-waved. The canonical catalog of 14 families and 76 root causes was built by one model and reviewed family by family by a second model under an adversarial protocol. The query set was blind-verified the same way.

What is frozen:

- `catalog.json`: the canonical ontology. 14 families, 76 root causes, all 745 tickets assigned. It defines both the wiki page boundaries and every eval label. Built by one model and blind-reviewed family by family by a second model under an adversarial protocol. All 14 families converged. Convergence was contested and the full attempt history is recorded in the catalog, not hidden.
- `retrieval/simple-queries.json`: 63 questions with exactly one correct root cause. Subtypes: 21 diagnosis, 19 synthesis, 10 exact-match, 13 fix-lookup. Each one blind-verified and baseline smoke-tested at generation.
- `retrieval/complex-queries.json`: 34 questions with multiple plausible root causes. These are corpus-discovered sibling-cluster ambiguities, each anchored to a ticket-derived cause. This is the class where the system is meant to beat a general model.
- `retrieval/abstention-queries.json`: 15 questions with no answer in the corpus. The correct behavior is to abstain.
- `retrieval/abstention-certification.json`: every abstention question interrogated against all 14 families. 210 of 210 probes returned null.
- `redaction/pii.json` and `redaction/retention.json`: the two redaction answer keys, frozen alongside the rest.
- `wiki/wiki-currated-tickets.json`: eval ground truth for wiki-curation with one record per curated page (family + root_cause_id).

Each artifact records its provenance: the dataset revision it was built against, the producing and verifying models, the generation date, and its review trail. The builders run separately from this repo, with blind label verification by an independent model and deterministic lint gates.


## What is not measured

There is no end-to-end metric for whether the agent's final fix was correct. That depends on the agent, who is outside the system. Every axis here is component-level. It measures a part the system controls. The boundary is stated, not hidden.
