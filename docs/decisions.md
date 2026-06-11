# Design notes

A few choices in this design are deliberate but not obvious. Each one is local to a part of the system, not a global property. This document explains the reasoning behind them. For the system as a whole, see [ARCHITECTURE.md](../ARCHITECTURE.md).


## At the query surface: it recommends, the agent decides

The serving layer is a recommender, not an auto-resolver. This is a choice about the query surface specifically, not the whole pipeline.

When a new ticket arrives, the agent reads it, writes a query, and reviews what the system returns. The system surfaces how similar issues were resolved and ranks the evidence. It does not take the new ticket, decide it matches a past one, or apply a fix. The system never sees the new ticket at all.

This is deliberate. Deciding whether two tickets are the same problem has real consequences if it is wrong, so that judgment stays with the human. The system makes the prior knowledge fast to find and easy to verify. The agent makes the call. Keeping the human in the loop here is the right boundary for an action that touches a live system. See the query path in [ARCHITECTURE.md](../ARCHITECTURE.md).


## At L2: the overview is precomputed, not generated per query

The overview for each issue family is built once during ingest and cached. This choice is local to L2. L1 retrieval still runs per query.

The alternative is zero-shot synthesis: run an LLM over the retrieved tickets on every query. That pays the synthesis cost every time, adds latency to each search, and produces a rushed single-pass answer with no cross-ticket consolidation.

Precompute is available here because the corpus is bounded. A finite set of issue families means each overview can be built ahead of time and reused. A live web search cannot do this, because the web is unbounded. So the experience matches a Google AI overview, but the mechanism is a cache lookup, not live generation. The latency and cost gain is measured head to head against zero-shot in [evaluation.md](evaluation.md).


## At ingest: redaction runs first, and it does more than protect

Redaction is the first step of ingest, over the whole ticket. The obvious reason is safety: no personal data reaches the index or the published surface.

The less obvious reason is that redaction is also an enabling precondition for curation. Person-specific tokens, a name, a username, a device hostname, are what make one ticket look different from another describing the same problem. Removing them is what lets curation consolidate many descriptions into one common pattern.

So the ordering is deliberate. Redaction does not normalize; curation does. But curation cannot generalize cleanly over text still full of unique identifiers. Redaction clears that noise first, then curation consolidates. The policy and the leakage contract are in [redaction-policy.md](redaction-policy.md). The consolidation step is in [retrieval.md](retrieval.md).
