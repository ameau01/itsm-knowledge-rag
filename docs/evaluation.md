# Evaluation

How each layer is verified, and the results. The leakage axis is summarized here and specified in full in [redaction-policy.md](redaction-policy.md). For where evaluation sits in the system, see [ARCHITECTURE.md](../ARCHITECTURE.md).


## The principle

Evaluation is split by what can be checked deterministically and what needs judgment. One axis is deterministic: PII leakage, graded against an authored sidecar. The rest are judge-based or label-based and are reported as such. The project does not blur the line. Not every property can be measured the same way, and saying which is which is part of the work.

The eval is also designed to localize failures. A wrong answer is either a retrieval failure (the wrong tickets were surfaced) or a generation failure (the right tickets were surfaced but the overview was not faithful to them). Separating the axes lets a failure be traced to the layer that caused it, rather than tuning blindly.


## The frozen eval-set

The ground truth is built, frozen, and committed under `eval-set/`. The harness reads only these files. Upstream copies are documentation; these are the answer key.

Two kinds of truth are kept separate. Data truth is a property of the corpus and ships with the dataset: `pii.json` and `retention.json`, authored independently of any system under test. Design truth is the experimental choice of this project and lives in the eval-set: the canonical catalog, the query set, the abstention probes.

What is frozen:

- `catalog.json`: the canonical ontology. 14 families, 76 root causes, all 745 tickets assigned. It defines both the wiki page boundaries and every eval label. Built by one model and blind-reviewed family by family by a second model under an adversarial protocol. All 14 families converged. Convergence was contested and the full attempt history is recorded in the catalog, not hidden.
- `retrieval/simple-queries.json`: 63 questions with exactly one correct root cause. Subtypes: 21 diagnosis, 19 synthesis, 10 exact-match, 13 fix-lookup. Each one blind-verified and baseline smoke-tested at generation.
- `retrieval/complex-queries.json`: 34 questions with multiple plausible root causes. These are corpus-discovered sibling-cluster ambiguities, each anchored to a ticket-derived cause. This is the class where the system is meant to beat a general model.
- `retrieval/abstention-queries.json`: 15 questions with no answer in the corpus. The correct behavior is to abstain.
- `retrieval/abstention-certification.json`: every abstention question interrogated against all 14 families. 210 of 210 probes returned null.
- `redaction/pii.json` and `redaction/retention.json`: the two redaction answer keys, frozen alongside the rest.

Each artifact records its provenance: the dataset revision it was built against, the producing and verifying models, the generation date, and its review trail. The builders run separately from this repo, with blind label verification by an independent model and deterministic lint gates.


## Axes

| Axis | Layer | Metric | Class |
|---|---|---|---|
| PII leakage | Redaction | Leak rate vs. sidecar | Deterministic |
| Technical retention | Redaction | RETAIN strings preserved | Deterministic |
| Retrieval | L1 | recall@k, nDCG@k, context precision | Label-based |
| Curation quality | L2 | Faithfulness, citation accuracy | Judge-based |
| Abstention | Coverage | Accuracy on held-out family | Label-based |
| Efficiency | L2 | Latency, cost vs. zero-shot | Measured |


## PII leakage (deterministic)

The headline axis. For each value in a ticket's sidecar, the check asserts the value is gone from the entire redacted document and replaced by its expected token. A leak anywhere is caught, including at sites the author did not enumerate. The gate is absence-anywhere, not per-occurrence.

This number is non-circular. The sidecar was authored upstream, during data generation, with no detector involved. The redactor being tested is a separate Presidio pipeline in this project. So the redactor is graded against a key it did not write. The full classification rules and the gate are in [redaction-policy.md](redaction-policy.md). The corpus and sidecar shape are in [dataset.md](dataset.md).

Reported per type (person, username, email, phone, emp_id, location, ip, hostname).

| Type | Leak rate | Retention error |
|---|---|---|
| person | TBD | TBD |
| username | TBD | TBD |
| email | TBD | TBD |
| (all types) | TBD | TBD |


## Technical retention (deterministic)

The other side of redaction. A redactor that strips error codes and hostnames to look safe is failing, not passing. This axis asserts RETAIN-class strings (system names, service hostnames, error codes, cert serials, region codes) survive redaction. Over-redaction is scored against the system. The RETAIN list is defined in [redaction-policy.md](redaction-policy.md).


## Retrieval, L1 (label-based)

The query set is 63 single-answer and 34 ambiguous questions, scored against the frozen catalog labels. Relevance is defined by issue family: a retrieved ticket is relevant if it shares the query's family. This is a proxy, stated as an assumption, and it is reasonable for this corpus.

- recall@k: are the relevant tickets in the top k.
- nDCG@k: are they ranked high enough to be seen. The UI is a ranked list, so rank matters, not just presence.
- context precision: of what was returned, how much is the right family. Guards against a confidently wrong overview built on a wrong-family match.

The improvement experiment is the hybrid ablation: sparse alone, dense alone, fused. It shows whether the hybrid earns its place.

| Retriever | recall@10 | nDCG@10 |
|---|---|---|
| Sparse only | TBD | TBD |
| Dense only | TBD | TBD |
| Hybrid | TBD | TBD |


## Curation quality, L2 (judge-based)

Measured with DeepEval and G-Eval against the ticket descriptions and correspondence, which is the only text curation synthesizes. The golden root cause and resolution are surfaced verbatim, so they are not faithfulness-checked. There is nothing to hallucinate in a copied field. This scoping follows from the generative-versus-extractive split in [retrieval.md](retrieval.md).

- Faithfulness: are the overview's claims supported by the source descriptions. Reported as an unsupported-claim rate, with examples, not just an average.
- Citation accuracy: does each claim trace to a source ticket. Precision (cited tickets that support the claim) and coverage (claims that have a citation). This directly measures the verify-against-sources trust model.

The judge model is different from the curation model, to avoid a model grading itself.

| Metric | Result |
|---|---|
| Faithfulness | TBD |
| Unsupported-claim rate | TBD |
| Citation precision | TBD |
| Citation coverage | TBD |

The automated metrics are the scalable half of curation quality. A human spot-check of a sampled set of overviews is the complement. It catches what judge-based metrics miss: a page that scores well but reads poorly, or a redaction artifact that is technically clean but confusing. In a deployment this spot-check is the human-review step of periodic lint (see [ARCHITECTURE.md](../ARCHITECTURE.md)). For this corpus it is a one-time sample, reported alongside the automated numbers.


## Abstention (label-based)

The abstention set is 15 questions with no answer in the corpus. Correct behavior is to abstain rather than invent one. The set is certified per family in `eval-set/retrieval/abstention-certification.json`: every abstention question was interrogated against all 14 families and 210 of 210 probes returned null. This checks the system declines on knowledge it does not have. A held-out family probe extends the same idea to a family withheld from the wiki at eval time.

| Metric | Result |
|---|---|
| Abstention accuracy | TBD |


## Efficiency: cache versus zero-shot

The cached overview is compared head to head against per-query zero-shot synthesis, on the same queries.

| Approach | Latency / query | Cost / query | Quality |
|---|---|---|---|
| Zero-shot synthesis | TBD | TBD | TBD |
| Cached overview | TBD | TBD | TBD |


## What is not measured

There is no end-to-end user metric. Whether an agent's final fix was correct depends on the agent, who is outside the system. The axes here are component-level: they measure the parts the system controls. This is a deliberate boundary, stated rather than hidden.
