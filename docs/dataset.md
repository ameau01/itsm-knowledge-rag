# Dataset

The corpus and its ground-truth sidecar. Published at [`ameau01/synthetic-it-support-tickets`](https://huggingface.co/datasets/ameau01/synthetic-it-support-tickets). For how the data is used, see [ARCHITECTURE.md](../ARCHITECTURE.md). For the redaction rules that define the sidecar, see [redaction-policy.md](redaction-policy.md).


## What it is

745 synthetic ITSM incident records across 15 diagnostic families, roughly 13 to 60 records each. Each ticket is a closed incident: a submitted problem, agent correspondence, diagnostic steps, a root cause, and a resolution. PII is injected into the free-text fields. An authored sidecar, `pii.json`, records every injected value and how it should be redacted.

The corpus is synthetic by design. This is a strength, not a limitation. Real ticket data has no ground-truth label for what is PII and what is technical content. Synthetic data does, because the PII was authored, not detected. That authored label is what makes the deterministic leakage benchmark possible. No real personal data is involved.


## Why synthetic transfers

The project showcases a method, not a product. The method is: redact against an authored ground truth, then measure leakage deterministically. That method does not depend on the data being real. A synthetic corpus that mirrors the structure of real tickets (free-text descriptions, embedded identifiers, technical noise) exercises the same redaction and curation logic a real corpus would. The synthetic corpus is the controlled starting condition, chosen so the eval has a stable answer key.


## Ticket schema

Per record:

| Field | Contents |
|---|---|
| `record_id`, `record_type` | Identity and type |
| `ticket.submitted_*` | Title, description, priority, SLA |
| `ticket.environment` | os, platform, region, user_group |
| `ticket.applications` | Affected systems |
| `correspondence[]` | Agent and user turns, with timestamps |
| `diagnostics.summary` | Narrative summary |
| `diagnostics.observed_errors` | Error strings |
| `diagnostics.steps[]` | Action, expected, observed, status, evidence |
| `root_cause` | The determined cause (golden, frozen) |
| `resolution.steps[]` | The fix that worked (golden, frozen) |

Injected PII lives in the free-text fields: `submitted_description`, `correspondence[].message`, `diagnostics.summary`, `diagnostics.steps[].observed_result`, `diagnostics.steps[].evidence`, and `resolution.steps[]`. The structured spine (`root_cause`, `observed_errors`, `applications`, `result_status`) was frozen during enrichment and carries no injected PII.


## The sidecar contract

`pii.json` is value-keyed: one entry per unique PII value per ticket, with a list of every field where it appears.

```json
{
  "id": "INC-ALP-0014:pii:001",
  "value": "rnguyen",
  "type": "username",
  "tier": "personal",
  "origin": "injected",
  "policy": "token_replace",
  "expected_after_redaction": "<USER>",
  "occurrences": ["ticket.submitted_description", "correspondence[0].message"]
}
```

The sidecar contains only the eight redacted types: person, username, email, phone, emp_id, location, ip, hostname. Technical content is never in the sidecar. The full classification rules, the eight types, the composite cases, and the leakage gate are in [redaction-policy.md](redaction-policy.md). How the sidecar is used to score leakage is in [evaluation.md](evaluation.md).


## Known limitations

Synthetic identifiers can recur across tickets for different people. An employee ID seen in one ticket may appear in another for a different person. This does not affect the per-ticket leakage eval, which checks each ticket against its own sidecar. It is noted here for anyone using the corpus for other purposes.
