"""Curation (L2) evaluation harness.

Scores a curation *strategy* (single-shot, ReAct, IR pipeline, ...) the same way the L1
harness scores a retrieval arm: arm x case x metric x runs -> (mean, stdev). An "arm" here
is a curation strategy; the unit under test is the generated `curation` per root cause.

Strategy code never lives here. A strategy emits frozen candidate files
(eval-set/wiki/candidates/<arm>/<root_cause>.json); this package only *scores* candidates,
so runs are reproducible and the measuring stick is fixed before any strategy is written.
The human-curated gold is just the first arm (synthesized from the eval mapping), doubling
as the harness self-test.

Reference wiring (the "split" decision):
  - Faithfulness  -> each arm's OWN logged context (per-field). A strategy that under-
    retrieves and then invents detail correctly fails.
  - Summarization / Variation -> the FULL evidence pool (all member tickets, uncapped), so
    under-retrieval shows up as dropped content.
"""
