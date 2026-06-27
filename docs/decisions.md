# Design notes

A few choices in this design are deliberate but not obvious. Each one is local to a part of the system, not a global property. This document explains the reasoning behind them. For the system as a whole, see [ARCHITECTURE.md](../ARCHITECTURE.md).


## Why there is a second layer at all: similarity is not relevance

A retriever ranks by similarity. Similarity is not relevance. Two tickets can read alike and be different problems. Two can read differently and be the same root cause. So even good hybrid search returns a list that can include the wrong family, or the right family with a different observed error. That is the ceiling of a pure matching layer.

L2 exists to address that ceiling. Rather than hand the agent a ranked pile and ask them to reconcile it, curation consolidates the conflicting descriptions of one root cause into a single coherent page at build time. The matching layer does its best with similarity. The knowledge layer is the answer to what similarity alone cannot resolve. This is the reason the system is two layers, not one. See [retrieval.md](retrieval.md).


## At the query surface: it recommends, the agent decides

The serving layer is a recommender, not an auto-resolver. This is a choice about the query surface specifically, not the whole pipeline.

When a new ticket arrives, the agent reads it, writes a query, and reviews what the system returns. The system surfaces how similar issues were resolved and ranks the evidence. It does not take the new ticket, decide it matches a past one, or apply a fix. The system never sees the new ticket at all.

This is deliberate. Deciding whether two tickets are the same problem has real consequences if it is wrong, so that judgment stays with the human. The system makes the prior knowledge fast to find and easy to verify. The agent makes the call. Keeping the human in the loop here is the right boundary for an action that touches a live system. See the query path in [ARCHITECTURE.md](../ARCHITECTURE.md).


## At L2: the expensive work is precomputed

The body of each overview is built once during ingest and cached. The expensive part, consolidating many ticket descriptions into one coherent issue statement, happens at build time, not on every search. This choice is local to L2. L1 retrieval still runs per query.

The alternative is zero-shot synthesis: run an LLM over the retrieved tickets on every query. That pays the consolidation cost every time, adds latency to each search, and produces a rushed single-pass answer with no cross-ticket consolidation.

Precompute is available here because the corpus is bounded. A finite set of issue families means each overview body can be built ahead of time and reused. A live web search cannot do this, because the web is unbounded. So the experience matches a Google AI Overview, with the heavy consolidation paid once. Faithfulness, relevancy, and variation preservation are measured in [wiki-evaluation.md](wiki-evaluation.md).

## The AI overview is decoupled from curation

The AI overview is the short answer at the top of agent search. It could have been the last node in the curation loop. It is deliberately not.

Instead it is a separate stage that runs after curation. It reads the finished page and writes one more field. The reason is cost and tuning. Curation is slow and occasionally fails mid-run. The overview is fast, and its prompt is the most-tuned part of the design, since it carries the confidence tiers and the hedging. Decoupled, the overview can be re-run over the existing pages without re-curating anything. Coupled, every prompt tweak would re-enter the expensive curation path.

The seam is clean because each curation arm ends the same way, with a finished page in the store. One overview stage serves all of them, single-shot or multi-agent, unchanged. The overview is a pure update of one field, safe to re-run. A failure on one page leaves that page without an overview, and does not block the rest. How the overview is scored is in [wiki-evaluation.md](wiki-evaluation.md).

## At ingest: redaction runs first, and it does more than protect

Redaction is the first step of ingest, over the whole ticket. The obvious reason is safety: no personal data reaches the index or the published surface.

The less obvious reason is that redaction is also an enabling precondition for curation. Person-specific tokens, a name, a username, a device hostname, are what make one ticket look different from another describing the same problem. Removing them is what lets curation consolidate many descriptions into one common pattern.

So the ordering is deliberate. Redaction does not normalize; curation does. But curation cannot generalize cleanly over text still full of unique identifiers. Redaction clears that noise first, then curation consolidates. The policy and the leakage contract are in [redaction-policy.md](redaction-policy.md). How the consolidation is designed is in [wiki-curation.md](wiki-curation.md).
