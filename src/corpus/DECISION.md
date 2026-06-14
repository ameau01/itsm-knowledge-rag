# Corpus Extraction — Schema Decisions

This document records the **final decisions** for every column produced by the ETL
ingest pipeline (`src/ingest/run_ingest.py` → `src/ingest/store.py`).  It is a
reference, not a process log.

---

## Diagnostic Step Columns

Three columns are produced from `diagnostics.steps` in the parquet.  Each serves a
different downstream consumer and contains a different field subset.

### `diagnostics_steps`  *(canonical)*

**Fields kept:** `playbook_step_id`, `expected_result`, `result_status`, `performed_by`

**Fields dropped:** `action`, `observed_result`, `evidence`, `step_id`

**Why:** `expected_result` is 100 % stable across all tickets that share a
`playbook_step_id` (verified: 42/42 step IDs, 745 tickets).  `action` varies
per-ticket (17–54 variants per step ID) and is in the same variability class as
`observed_result` and `evidence`.  Dropping the high-variance fields collapses the
corpus from 745 unique step-sets to **365 unique step-sets** across 76 root causes —
matching the cardinality oracle in `corpus-cardinality.xlsx` column
*"Unique Diagnostics (excl action, observed_result, evidence; redacted)"*.

**Cardinality contract:** 365 unique step-sets across all 76 root causes.
Enforced by `src/test/test_extraction.py::test_diag_cardinality`.

**Consumers:** embedding / vector index, BM25 sparse retrieval index (extracts
`expected_result` text at index-build time), cardinality oracle test.

---

### `diagnostics_steps_raw`  *(full per-ticket detail)*

**Fields kept:** `step` (1-based integer), `playbook_step_id`, `action`,
`expected_result`, `observed_result`, `evidence`, `result_status`, `performed_by`

**Why:** Retains every field for consumers that need full incident context.
`observed_result` and `evidence` are per-ticket narratives that appear in
`retention.json` — including them here ensures the redaction retention test can
verify those values survive redaction (`_all_text` covers them).

**Consumers:** L1 similarity search context window, redaction retention test
(`test_retention_report`).

---

### `diagnostics_procedure`  *(lean wiki input)*

**Fields kept:** `step` (1-based integer), `action`, `expected_result`

**Why:** The wiki generator LLM needs only the procedure instruction (`action`) and
the success criterion (`expected_result`) to synthesise a canonical numbered
procedure.  Sending `observed_result`, `evidence`, `result_status`, `performed_by`
wastes tokens on noise irrelevant to procedure normalisation.

**Note on `action` variation:** `action` has 17–54 per-ticket variants per
`playbook_step_id` (tense drift + wording variation).  Tense normalisation was
evaluated but reduces unique variants by only 1 across 2,235 entries — not
meaningful.  The wiki generator LLM handles normalisation at curation time by
receiving all tickets' `diagnostics_procedure` for a root cause and synthesising one
canonical procedure.  The wiki generator picks the **shortest `action`** per
`playbook_step_id` as a seed before synthesis.

**Consumers:** wiki generator / AI overview curation step.

---

## Resolution Steps Column

### `resolution_steps`

**Format:** JSON array of strings (changed from newline-joined text).

**Why JSON array:** Resolution steps are 100 % unique across the entire corpus
(3,788/3,788 unique strings) — no deduplication is possible at ETL time.  Storing
as a JSON array lets the wiki generator slice a representative subset (e.g. one
ticket's 5 steps) rather than consuming all tickets' steps in one text blob.  The
redactor handles the JSON string transparently (PII replacement works on the
serialised string).

**Consumers:** wiki generator (samples 1–2 tickets' steps for the AI overview
"example resolutions" section), redaction retention test (via `_all_text`).

---

## Observed Errors Column

### `observed_errors`

**Format:** JSON array of error-code strings.

**Why not redacted:** Error codes (e.g. `AUTH_EXPIRED`, `HTTP 429`,
`VPN-ERR-201`) are structured identifiers, not free-text PII.  They are excluded
from the redaction pipeline and stored verbatim.

**Consumers:** BM25 sparse retrieval (error-code matching), wiki generator.

---

## Field Exclusion Summary

| parquet field | `diagnostics_steps` | `diagnostics_steps_raw` | `diagnostics_procedure` |
|---|:---:|:---:|:---:|
| step (index) | — | ✅ | ✅ |
| playbook_step_id | ✅ | ✅ | — |
| action | — | ✅ | ✅ |
| expected_result | ✅ | ✅ | ✅ |
| observed_result | — | ✅ | — |
| evidence | — | ✅ | — |
| result_status | ✅ | ✅ | — |
| performed_by | ✅ | ✅ | — |
| step_id (serial) | — | — | — |

---

## Cardinality Reference

Source: `corpus-cardinality.xlsx`, sheet *Root Causes*.

| xlsx column | value | maps to |
|---|---|---|
| Unique Diagnostic-Step Sets (full, raw) | 745 | `diagnostics_steps_raw` (all unique by design) |
| Unique Diagnostics (excl action, observed_result, evidence; redacted) | 365 | `diagnostics_steps` — oracle-tested |
| Unique Resolutions | per-RC | `resolution_steps` (100 % unique corpus-wide) |
