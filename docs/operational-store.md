# Operational store

The system keeps two stores. One is the source of truth. The other is a search index
built from it. This document explains the split, the shape of the data, and how the
store is read when wiki pages are built and when an AI-generated overview is served.

For the system as a whole, see [../ARCHITECTURE.md](../ARCHITECTURE.md). For
retrieval, see [retrieval.md](retrieval.md).


## Two stores, one truth

A relational store holds every record: the redacted tickets, the human-written golden
fields, and the curated wiki pages. It is the authority. Nothing is true unless it is
here.

A vector database holds the search index. It is built from the relational store, and
only after redaction. It can be deleted and rebuilt from the store at any time. It
carries nothing that does not already live in the store.

The two are not equals. One is the truth. The other is a rebuildable index over it.
The index answers one question well: which tickets are most similar to this query.
The store answers everything else: which tickets share a root cause, which fields to
show, and what the finished page says.


## What the store holds

The store has two kinds of record.

A **ticket** record holds one closed ticket after redaction. It carries the problem
description and the back-and-forth correspondence, which are the messy, varied text.
It also carries the golden fields: the diagnostic steps, the resolution, and the
engineer's observations. These were written by a human engineer. They are kept
exactly as recorded. Each ticket also knows which issue family and which root cause it
belongs to, so tickets can be grouped.

A **wiki page** record holds one curated page, one per root cause. It carries the
synthesized narration in three separable parts: the common pattern, the less frequent
variations, and the contradictions that are deliberately preserved. It also records
the page layout, a confidence level, and a status that marks whether the page is still
a draft, approved, or needs a human to look at it.

Two properties of this shape matter. The narration is stored in its three parts rather
than as one block of text, so each part can be read on its own when a page is assembled
or an overview is served. The exact error codes from a ticket are stored and indexed
for search, but they are not shown on the page. They make an error-code search land on
the right family. The page itself stays short and readable.


## Use in wiki page generation

Page generation reads from the store and writes back to it. It runs ahead of time, one
root cause at a time, never at query time.

First it gathers the inputs. For one root cause, it reads only the descriptions and
correspondence across all tickets that share that cause. These varied descriptions are
what the curation step consolidates into the three-part narration.

Then it assembles the answer. For the same root cause, it reads the golden fields, the
diagnostics and resolution and observations. These are combined as written. They are
never rewritten or regenerated. The finished page is the synthesized narration joined
to these verbatim fields.

Finally it writes the page back to the store as a wiki page record, with its layout,
confidence, and status. The store now holds a finished page ready to serve.


## Use in AI-generated overview synthesis

The AI-generated overview is what an agent sees after a search. The expensive work already
happened when the page was built. At query time the store simply hands back the
prepared page.

The search index returns the tickets most similar to the query, and each one points to
a root cause. For the matching root cause, the system reads the prepared page directly
from the store by its key. This is a fast lookup, not a fresh synthesis. It also reads
the golden diagnostics and resolution for that cause.

No text is generated at query time. The page body is read from the store, not rebuilt,
on every query. The corpus is bounded, so the page never goes stale between queries and
there is nothing to regenerate. This is what makes the overview fast and cheap to serve.


## What lives where

| Need | Source |
|---|---|
| Ticket content and golden fields | Relational store |
| Curated page body, layout, confidence | Relational store |
| Most similar tickets for a query | Vector index |
| Exact error-code match | Vector index |
| Prepared page for an AI-generated overview | Relational store |
