"""Curation (L2) evaluation harness.

Evaluates the live curation in the operational store's wiki_pages table against the source tickets.
From L1 harness scores retrieval: case x metric x runs -> (mean, stdev).

Three roles, kept strictly separate:
  - RECIPE  eval-set/wiki/wiki-currated-tickets.json — Receipe for evaluation.
  - SUBJECT wiki_pages.curated_description — the generated curation under test, read live.
  - SOURCE  the tickets table free-text columns — the ground truth the subject is judged on.

Reading the store is the only supported path: there is no gold answer and no candidate arms.
If any in-scope page has no curation, the run hard-exits — you cannot score what isn't there.

Reference wiring (the "split" decision):
  - Faithfulness  -> Did the curation invent anything not in the tickets it was meant to summarize?
  - Summarization / Variation -> the FULL evidence pool, so dropped content shows up as low coverage.
"""
