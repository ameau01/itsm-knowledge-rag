# Wiki and overview evaluation

How the L2 layer is measured.

L2 is the curated layer built on top of retrieval. L1 finds the right tickets. L2 turns them into a prepared answer. This doc covers whether the generated content is faithful to the tickets it was built from. For L1 retrieval, see [evaluation.md](evaluation.md). For how L2 is built, see [retrieval.md](retrieval.md).

L2 generates text, so this is the judge-based half. A score here is a model's judgment, not a count. It is reported that way. The judge model differs from the model that wrote the page, so nothing grades itself.


## Two artifacts, what is checked

Two things in L2 are generated. Both are checked.

- The wiki curation: a title, a plain-language symptom summary, a cause statement, and a list of variations. One model call per issue consolidates many tickets into this.
- The AI-generated overview: a short, static summary compiled from the wiki page. It keeps the description and the diagnostic steps and drops the variations.

What is not generated, and not checked:

- Diagnostic steps and resolution are golden. They are surfaced verbatim from the tickets. A copied field has nothing to hallucinate.

Each generated field is checked against the source it was built from:

- Symptoms and variations: against the user descriptions and the support correspondence.
- Cause: against the engineer notes and the diagnostics summaries.


## Wiki curation metrics

All produced by DeepEval or G-Eval.

- Faithfulness (DeepEval): do the generated claims hold against the source. Reported as an unsupported-claim rate, with examples, not just an average.
- Answer relevancy (DeepEval): does the text address the issue rather than drift.
- Summarization (DeepEval): does the consolidation keep the important content and add nothing unsupported. This is the closest fit for the consolidation task.
- Variation preservation (G-Eval): does the page keep the distinct ways a problem presented, instead of flattening them into one bland line. A page can be perfectly faithful and still fail this. This is the project-specific bar, tied to the thesis that similarity is not relevance.

| Metric | Result |
|---|---|
| Faithfulness | TBD |
| Unsupported-claim rate | TBD |
| Answer relevancy | TBD |
| Summarization | TBD |
| Variation-preservation (G-Eval) | TBD |

Scope notes:

- Single-ticket pages stay in faithfulness. The page must be supported by its one ticket. An invented detail should fail.
- Single-ticket pages are excluded from variation preservation. With one source there is no cross-ticket variation to preserve.
- The judge runs at temperature zero, three times, with the spread reported.


## AI-generated overview metric

The overview is the short answer shown at the top of agent search. It is generated from the wiki page, not the raw tickets. So its reference is the wiki page. Its diagnostic steps are rendered verbatim from the golden field. They are not generated, so they are not checked.

It is scored on overview quality. Two things are checked. Does every claim hold against the source page. Is the wording calibrated to the confidence shown. The judge is an independent OpenAI model (gpt-4o), different from the Anthropic model that wrote it. It runs three times per page, across all 76 pages.

| Metric | Result |
|---|---|
| Overview quality (mean) | 0.938 |
| Range | 0.84 to 0.997 |
| Spread (stdev) | 0.033 |

Quality holds across the confidence tiers, and is highest where the system is most sure:

| Confidence | Pages | Overview quality |
|---|---|---|
| High | 22 | 0.972 |
| Medium | 26 | 0.935 |
| Low | 28 | 0.913 |

A separate guard checks the wording of low-confidence overviews. They must be worded cautiously, not stated as fact. Across all 76 pages it recorded zero hard failures and zero soft warnings. The system does not just score well on average. It hedges when it is unsure.
