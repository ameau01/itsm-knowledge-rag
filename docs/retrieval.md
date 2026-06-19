# Retrieval: L1 and L2

Similarity is not relevance. Two tickets can read alike and be different problems. Two can read differently and be the same root cause. A retriever ranks by similarity, so even the best search returns a list that still needs judgment. That gap is the reason this system has a second layer.

L1 is raw-ticket search. L2 is the curated overview built on top of it. They are weak alone and strong together. For where this sits in the system, see [ARCHITECTURE.md](../ARCHITECTURE.md). For how each is measured, see [retrieval-evaluation.md](retrieval-evaluation.md) and [wiki-evaluation.md](wiki-evaluation.md).


## The two layers

| Layer | What it returns | Built |
|---|---|---|
| L1 | Ranked source tickets, with snippets | Per query, at search time |
| L2 | A curated overview for the issue family | Once, during ingest, then cached |

L1 is the matching layer. It does the best it can with similarity. L2 is the knowledge layer. It is the answer to what similarity alone cannot do.


## L1: hybrid retrieval and reranking

L1 is a funnel. Two retrievers, fused, then reranked.

Dense retrieval embeds the tickets and the query, then matches by vector similarity. It catches semantic matches. A query about "cannot sign in after reset" finds tickets about account lockout even with different words.

Sparse retrieval scores exact terms with BM25. It catches identifiers, error codes, and product names that embeddings blur. A query naming a specific error string surfaces tickets carrying that exact string.

The two are fused into one ranked list with Reciprocal Rank Fusion. RRF merges by rank, not by raw score, so the two retrievers' incompatible score scales never have to be reconciled. Dense alone misses exact codes. Sparse alone misses paraphrase. The fusion is meant to get both. Whether it beats either component alone is measured as an ablation, not assumed. See [retrieval-evaluation.md](retrieval-evaluation.md).

A cross-encoder reranker then re-scores the fused candidates against the query. It reads query and ticket together, so it catches ordering a bi-encoder misses. Its lift may be modest on this corpus, where most families have one dominant cause and the fused list is often already in order. It is in the design because it is the right component as the corpus grows, and because its lift is measured rather than assumed.

Qdrant is the vector store. It holds both the dense and sparse vectors and fuses them in a single query, so the fusion is not hand-rolled in application code. Tickets are indexed after redaction. No personal data enters the index.

The funnel: fuse with RRF, then rerank, then return the top results. Abstention is decided before the reranker runs, on the fused score, covered below.


## Knowing when to decline

L1 always returns something. A semantic retriever ranks whatever is closest, even when nothing in the corpus fits. So the system needs a way to say the answer is not here.

That decision is made on the fused RRF score, before the reranker runs. The reranker orders whatever it is handed and will rank its best candidate highly even when none fit, so its score is a poor signal for declining. The fused score reflects how well the query actually matched the corpus, so it is the signal that drops on an out-of-corpus query. Below a calibrated floor, the system abstains rather than return a confident wrong answer. How the floor is set and tested is in [retrieval-evaluation.md](retrieval-evaluation.md).


## L2: the curated overview

L2 is the curated wiki page for an issue family, built once during ingest.

This is the answer to the relevance gap. L1 can return tickets of the wrong family, or the same family with a different observed error. Even good hybrid search has that limit, because it matches on similarity. L2 addresses it by consolidating at build time. For each issue family, curation takes the many ways users described the same problem and combines them into one coherent issue statement, then attaches the golden root cause and resolution surfaced verbatim. The conflicting descriptions are resolved into knowledge, not left as a pile of similar-looking tickets.

The work happens once, offline, and is cached. The alternative is zero-shot synthesis: run a model over the retrieved tickets on every query. That is slow, costly, and lower quality, because it synthesizes in one rushed pass with no cross-ticket consolidation. The cached overview pays that cost once and serves it cheaply thereafter. The latency and cost difference is measured head to head. See [wiki-evaluation.md](wiki-evaluation.md). The cache is the relational store; how it is read at build and query time is in [operational-store.md](operational-store.md).

The experience matches a Google AI overview: a prepared answer on top, the sources below. The difference is the mechanism. A web overview is generated live because the web is unbounded. This corpus is bounded, so the overview is precomputed.


## Generative versus extractive

L2 is part generated, part copied, and the split matters for evaluation.

The description consolidation is generated. A model writes the one coherent issue statement from the many source descriptions. The golden fields inside the page are extractive. The root cause and resolution are surfaced verbatim from the ticket, never rewritten. Only the generated part can drift from its source, so only the generated part is faithfulness-checked. A copied field has nothing to hallucinate. See [wiki-evaluation.md](wiki-evaluation.md) for how this scopes the curation metric.


## Why both, not either

L2 alone is a confident summary with no way to verify it. L1 alone is a pile of tickets the agent must read and synthesize by hand. Together they serve the real workflow. The overview gives the likely answer fast. The ranked source tickets let the agent confirm it before acting. The recommender model depends on this pairing. The system answers, the agent verifies. See [ARCHITECTURE.md](../ARCHITECTURE.md).
