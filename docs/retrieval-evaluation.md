# Retrieval evaluation

How L1 retrieval is measured. L1 returns a ranked list of source tickets for a query. This doc covers whether the right tickets are found, whether the parts of the hybrid earn their place, and whether the system declines when the answer is not in the corpus. For the overview layer built on top of retrieval, see [wiki-evaluation.md](wiki-evaluation.md). For where retrieval sits in the system, see [retrieval.md](retrieval.md).

The ground truth is the frozen eval-set under `eval-set/`. The harness reads only those files. See [evaluation.md](evaluation.md) for how the eval-set was built and verified.


## What relevance means here

A retrieved ticket is scored against two labels, both exact ids that exist on the query and on the corpus ticket.

- Strict: the ticket's `root_cause_id` matches the query's `expected_root_cause`. This is the real target. The system claims to pinpoint the specific cause, so this is the number that measures the claim.
- Lenient: the ticket's `family` matches the query's `expected_family`. This is the easier bar, reported as a secondary level.

Matching is id to id. No LLM, no string comparison of free text, no lookup. A retrieved ticket is either the right cause or it is not.

Strict leads the reporting. Family-level alone would flatter the system. With 14 families and one dominant cause in most of them, almost any retriever finds the right family. The strict number is lower and more honest, and it separates the arms where family-level would not.


## The four arms

The hybrid is not assumed to help. It is measured against its parts.

| Arm | What it is |
|---|---|
| Dense only | Embedding similarity alone |
| BM25 only | Sparse keyword scoring alone |
| Hybrid | Dense and BM25 fused with Reciprocal Rank Fusion |
| Hybrid + reranker | The fused list re-scored by a cross-encoder reranker |

Dense catches the same problem described in different words. BM25 catches the exact error codes and identifiers that embeddings blur. Fusing them should beat either alone. The reranker re-scores the fused candidates by reading query and ticket together. Whether each step adds something is what the table shows.


## Table 1: retrieval performance

Scored on the 63 simple queries. Strict relevance (`root_cause_id`) leads; lenient (`family`) is the secondary level.

| Arm | Recall@10 (strict) | nDCG@10 (strict) | Recall@10 (family) |
|---|---|---|---|
| Dense only | TBD | TBD | TBD |
| BM25 only | TBD | TBD | TBD |
| Hybrid | TBD | TBD | TBD |
| Hybrid + reranker | TBD | TBD | TBD |

Hit Rate@10 is not reported. On a corpus with a dominant cause per family it sits near the top for every arm and does not separate them. MRR is reported as a single aggregate figure where useful.

Numbers are computed once over the full query set. Uncertainty is a 95 percent bootstrap confidence interval, 1,000 query resamples with replacement, the 2.5 and 97.5 percentiles. The retriever has no parameters fit on the query set, so there is nothing to cross-validate. At this sample size the interval will not be tight. That is the honest read, not a number to hide.


## Table 2: semantic quality

A judge-based cross-check, run with DeepEval across the same four arms. These are not rank metrics. They read the retrieved context and score it directly. They corroborate Table 1 from a different angle rather than repeat it.

| Arm | Contextual Precision | Contextual Relevancy |
|---|---|---|
| Dense only | TBD | TBD |
| BM25 only | TBD | TBD |
| Hybrid | TBD | TBD |
| Hybrid + reranker | TBD | TBD |

Contextual Precision asks whether relevant context is ranked above irrelevant context. It is the judged view of what the reranker is meant to do. Contextual Relevancy asks whether the retrieved context fits the query, and needs no ground truth. The judge is a different model from any used in the pipeline. Temperature is zero. LLM judges vary run to run, so each score is measured at three runs and the variance is reported.

These two metrics pull apart in a way that restates the central point. No single section of a ticket scores highest on both. The section most on topic for the query is often not the section that names the cause. Similarity and relevance are not the same measurement, which is the reason retrieval spans several section points and a second layer sits on top.


## Table 3: reranker depth

Produced only if Table 1 shows a meaningful reranker lift. If the lift is flat, this is one sentence, not a table.

The reranker re-orders the fused candidates. To show where that ordering helps, nDCG is reported at several depths for the hybrid list with and without the reranker.

| k | nDCG@k (hybrid) | nDCG@k (hybrid + reranker) |
|---|---|---|
| 5 | TBD | TBD |
| 10 | TBD | TBD |
| 15 | TBD | TBD |
| 20 | TBD | TBD |

A note on expectations. The reranker may add little on this corpus. The corpus is small and most families have one dominant cause, so the fused list is often already in good order. There is little room left to improve. A cross-encoder reranker earns more on larger corpora with many close candidates to separate. It is in the design because it is the right component as the corpus grows, and because measuring its lift is more useful than assuming it. The measured number is reported either way.


## Complex queries

Scored on the 34 complex queries, held out from any tuning. These carry more than one valid root cause on purpose. They are the corpus-discovered sibling ambiguities where several causes are genuinely plausible.

Scoring is against the candidate set, not a single id. The metric is candidate-set recall over `expected_root_cause`, with a penalty for over-hedging. Returning five causes when two were right is not a win.

| Metric | Result |
|---|---|
| Candidate-set recall@10 | TBD |
| nDCG@10 | TBD |

This is the class where the system should hold up under ambiguity. The result is reported as measured, on queries the tuning never saw.


## Abstention

Scored on the 15 abstention queries, also pure held-out test. These have no answer in the corpus. The correct behavior is to decline, not to return the closest thing.

Abstention here is calibration, not classification. Semantic retrieval always returns something with some score, so there is no built-in signal for no match. The decision is made on the fused RRF score, before the reranker runs. A reranker orders whatever it is given and will rank its best candidate highly even when nothing fits, so its score is a poor signal for declining. The fused score reflects how well the query matched the corpus, so it is the signal that drops on an out-of-corpus query.

The threshold is set from the in-corpus score distribution, the floor below which a legitimate match does not fall. The abstention set only tests that threshold. It is never used to tune it.

| Metric | Result |
|---|---|
| Abstention accuracy | TBD |
| False-abstention rate (on simple and complex) | TBD |

Two distributions are recorded alongside the numbers: the fused scores of in-corpus matches, and the fused scores of the out-of-corpus queries. Whether they separate cleanly or overlap is the real finding. A clean gap is a strong result. An overlap is an honest limit, and is reported as one.


## What is not measured

There is no end-to-end metric for whether the agent's final fix was correct. That depends on the agent, who is outside the system. These metrics measure retrieval, which is the part the system controls. The boundary is stated, not hidden.
