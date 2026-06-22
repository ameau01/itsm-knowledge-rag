# Eval-set

The frozen ground truth and experimental design for evaluating this system. Everything
here is committed, versioned, and reproducible; the eval harness reads ONLY these files
(single-authority rule — upstream copies are documentation, these are the answer key).

## Where ground truth comes from

Two kinds of truth, deliberately separated:

- **Data truth** (properties of the corpus itself) ships with the dataset
  [`ameau01/synthetic-it-support-tickets`](https://huggingface.co/datasets/ameau01/synthetic-it-support-tickets):
  `pii.json` (what was injected and must be redacted) and, when upstreamed,
  `retention.json` (what must survive redaction). Authored independently of any
  system under test — this is what makes the deterministic axes non-circular.
- **Design truth** (experimental choices of THIS project) lives here: the canonical
  root-cause catalog, the query set with expected answers, the abstention and
  knowledge-gap probes.

## Artifacts and status

| File | What it is | Status |
|---|---|---|
| `catalog.json` | Canonical family/root-cause ontology: 14 families, 76 causes, 745/745 tickets assigned. Defines wiki page boundaries AND every eval label. | **FROZEN** (2026-06-11) |
| `retrieval/simple-queries.json` | 63 questions with exactly ONE correct root cause (subtypes: diagnosis 21, synthesis 19, exact_match 10, fix_lookup 13). Every question blind-verified and baseline-smoke-tested at generation. | **FROZEN** (2026-06-11) |
| `retrieval/complex-queries.json` | 34 questions with MULTIPLE plausible root causes — corpus-discovered sibling-cluster ambiguity, each anchored to a ticket-derived cause. The differentiator class: where this system outperforms a general LLM. | **FROZEN** (2026-06-11) |
| `retrieval/abstention-queries.json` | 15 questions with NO answer in the corpus (`expected_root_cause: null`); correct behavior is to abstain. | **FROZEN** (2026-06-11) |
| `retrieval/abstention-certification.json` | Per-family evidence matrix: every abstention question individually interrogated against all 14 families — 210/210 returned null. | **FROZEN** (2026-06-11) |
| `retrieval/queries.schema.json` | JSON Schema shared by producer and eval harness | **FROZEN** (2026-06-11) |
| `knowledge-gap-queries.json` | Knowledge-gap probes: strong questions whose family (DRF) is deliberately excluded from the wiki at eval time. Kept with the builders until the consumer wiki exists. | protocol artifact (not exported, by design) |
| `wiki/wiki-currated-tickets.json` | Wiki-curation eval ground truth: one record per curated page (`family` + `root_cause_id`) with the curated content, source tickets, and per-field source sections. | added 2026-06-22 (pending merge with the curation table) |
| `wiki/family_names.json` | Family code → readable label, for rendering the wiki UI. | added 2026-06-21 |
| `redaction/retention.json` | Per-ticket RETAIN-class strings: 745/745 tickets, 8,581 entries, 0 flags, 0 unresolved suspects. Every disputed span owner-ruled with logged rationale. | **FROZEN** (2026-06-11) |
| `redaction/pii.json` | Copy of the dataset sidecar (leakage ground truth), byte-identical in revisions `6e9ec80b` (build) and `db074a5` (current) | **FROZEN** (2026-06-11) |
| `metrics.md` | The scoring contract: every metric defined per axis (deterministic gates, label-based, judge-based), failure localization, judge protocol | **FROZEN** (2026-06-11) |
| `metrics-config.json` | Machine-readable parameters: k values, gates, thresholds, ablation arms, judge settings | **FROZEN** (2026-06-11) |

## catalog.json provenance

- Dataset revision: `db074a5` (current, includes retention.json; corpus and pii.json are byte-identical to build revision `6e9ec80b`, against which all artifacts here were constructed).
- Built by `claude-opus-4-8`; every family independently reviewed in-loop by
  `claude-sonnet-4-6` under an adversarial protocol; **14/14 families converged**
  (zero `review_not_converged`).
- Convergence was stochastic with a heavy tail: families needed 3–18 build-review
  attempts (budget 20). The initial run with a budget of 4 converged only 2/14 —
  the catalog records every merge in `provenance.merges`. We report this rather
  than hide it: ground-truth construction was genuinely contested, and the
  attempt history is the evidence.
- Clusters whose every member is low-confidence are marked
  `label_class: ambiguous_zone`: kept for the wiki's variation handling, excluded
  from clean-label query sampling, and used as corpus-self-identified overlap zones
  for the `ambiguous` query type.

## Known upstream issues (queued for a future dataset revision)

- `pii.json` (unchanged through revision `db074a5`) contains one degenerate value
  (`INC-WCI-0016:pii:001`, value `'I'`) for which an absence-anywhere leakage gate is
  meaningless. Builders already guard against it (len>=3 filters).
- Native PII absent from the sidecar, discovered by the retention builder's detector
  sweep: bare person names (e.g. Tomás variants, Aisha), occupant locations
  (Building A/C), personal-device hostnames (mreeves-pc.corplabs.internal,
  LAPTOP-MELLINGHAM.corplabs.internal), phone extensions (x4417). Itemized in the
  retention builder's reports/ledger.
- Composite collision: city names baked into infrastructure hostnames
  (wlc-charlotte-02 contains sidecar location value 'Charlotte') put the leakage and
  retention gates in conflict; resolved here by dismissal-with-reason, future data
  generation should avoid city-named hosts.

## Policy rulings made during construction (reflected in docs/redaction-policy.md)

Third-party vendor/partner identity (name + domain + URL) is RETAIN, atomically.
Email addresses redact whole (`<EMAIL>` consumes local part AND domain); the domain
class is RETAIN wherever it appears without the `@` context. Device classes (iPhone
etc.) are always RETAIN os_device.

## Provenance discipline

Every artifact records: dataset revision, producing models, generation date, and its
builder's review/verification trail. Artifacts are produced by standalone builders
(separate from this repo) with in-loop verification: blind label verification by an
independent model, per-query baseline smoke tests (difficulty + abstention
separation), deterministic lint gates (PII word-boundary checks, schema validation,
coverage), and append-only ledgers. The builders' design docs and change records
live with the data project, not here.
