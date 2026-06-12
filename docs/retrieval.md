# Retrieval: L1 and L2

How a query becomes an answer. L1 is raw-ticket search. L2 is the cached overview. They are weak alone and strong together. For where this sits in the system, see [ARCHITECTURE.md](../ARCHITECTURE.md). For how each is measured, see [evaluation.md](evaluation.md).


## The two layers

| Layer | What it returns | Built |
|---|---|---|
| L1 | Ranked source tickets, with snippets | Per query, at search time |
| L2 | A synthesized overview for the issue family | Once, during ingest, then cached |

L1 is retrieval. L2 is the precomputed wiki page. A query hits both: L2 gives the prepared answer, L1 gives the evidence underneath it.


## L1: hybrid retrieval

L1 fuses two retrievers.

Dense retrieval embeds tickets and the query, then matches by vector similarity. It catches semantic matches: a query about "cannot sign in after reset" finds tickets about account lockout even with different words.

Sparse retrieval (BM25) matches exact terms. It catches identifiers, error codes, and product names that embeddings blur. A query naming a specific error string should surface tickets with that exact string.

The two are fused into one ranked list. Neither alone is enough. Dense misses exact codes. Sparse misses paraphrase. The hybrid is meant to get both. Whether it actually beats either component alone is measured as an ablation, not assumed. See [evaluation.md](evaluation.md).

Storage and indexing use LlamaIndex over Qdrant. Qdrant fuses the dense and sparse vectors natively in a single query, so the fusion is not hand-rolled in application code. Tickets are indexed after redaction. No personal data enters the index.


## L2: the cached overview

L2 is the curated wiki page for an issue family, built once during ingest.

A bounded corpus clusters into a finite set of issue families. For each family, curation consolidates the many ways users described that problem into one common issue statement, then attaches the golden root cause and resolution surfaced verbatim. That page is the overview. It is computed once and cached.

At query time the matched family's overview is read from cache, not generated. This is the key efficiency choice. The alternative, zero-shot synthesis, would run an LLM over retrieved tickets on every query: slow, costly, and lower quality because it synthesizes in one rushed pass with no cross-ticket consolidation. The cached overview pays that cost once, offline, and amortizes it across every future query.

The experience matches a Google "AI overview": a synthesized answer on top, sources below. The difference is that a web overview must be generated live because the web is unbounded. This corpus is bounded, so the overview can be precomputed. The latency and cost win over zero-shot is measured head to head. See [evaluation.md](evaluation.md).


## Generative versus extractive

L2 is generative: the description consolidation is LLM-written. The golden fields inside it are extractive: root cause and resolution are surfaced verbatim from the ticket, never regenerated. This split matters for evaluation. Only the generated part can drift from its source, so only the generated part is faithfulness-checked. The verbatim fields cannot hallucinate; they are copied. See [evaluation.md](evaluation.md) for how this scopes the curation metric.


## Why both, not either

L2 alone is a confident summary with no way to verify it. L1 alone is a pile of tickets the agent must read and synthesize by hand. Together they serve the real workflow: the overview gives the likely answer fast, the ranked source tickets let the agent confirm it before acting. The recommender model depends on this pairing. The system answers, the agent verifies. See [ARCHITECTURE.md](../ARCHITECTURE.md).
