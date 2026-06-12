# Dataset

The corpus and its ground-truth sidecar. Published at [`ameau01/synthetic-it-support-tickets`](https://huggingface.co/datasets/ameau01/synthetic-it-support-tickets). For how the data is used, see [ARCHITECTURE.md](../ARCHITECTURE.md). For the redaction rules that define the sidecar, see [redaction-policy.md](redaction-policy.md).


## What it is

745 synthetic ITSM incident records across 14 diagnostic families, roughly 13 to 60 records each. Each ticket is a closed incident: a submitted problem, agent correspondence, diagnostic steps, a root cause, and a resolution. PII is injected into the free-text fields. Two authored sidecars ship with the dataset. `pii.json` records every injected value and how it should be redacted. `retention.json` records the RETAIN-class strings that must survive redaction.

The corpus is synthetic by design. This is a strength, not a limitation. Real ticket data has no ground-truth label for what is PII and what is technical content. Synthetic data does, because the PII was authored, not detected. That authored label is what makes the deterministic leakage benchmark possible. The project demonstrates a method: redact against an authored ground truth, then measure leakage deterministically. A synthetic corpus is the controlled starting condition that gives the method a stable answer key. No real personal data is involved.


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

`retention.json` is the mirror key. It records the RETAIN-class strings that must survive redaction: system names, service hostnames, error codes, cert serials, region codes. It backs the over-retention axis the same way `pii.json` backs leakage. The two together make redaction scoring two-sided.

`retention.json` is per-ticket: one entry per ticket, each holding a `retain_instances` list. Every instance carries the value, its type, the fields it appears in, and a rationale for keeping it.

```json
{
  "ticket_id": "INC-AIT-0001",
  "retain_instances": [
    {
      "id": "INC-AIT-0001:retain:002",
      "value": "AUTH_EXPIRED",
      "type": "error_code",
      "occurrences": [
        "correspondence[0].message",
        "diagnostics.steps[0].evidence",
        "diagnostics.summary"
      ],
      "rationale": "Named authentication error code returned by the downstream API."
    }
  ]
}
```

The two sidecars are deliberately shaped differently. `pii.json` is value-keyed because a leak is checked by absence-anywhere: one value, every site it must be gone from. `retention.json` is ticket-keyed because retention is reviewed per ticket: each kept span is owner-ruled with a logged rationale.


## Known limitations

Synthetic identifiers can recur across tickets for different people. An employee ID seen in one ticket may appear in another for a different person. This does not affect the per-ticket leakage eval, which checks each ticket against its own sidecar. It is noted here for anyone using the corpus for other purposes.
