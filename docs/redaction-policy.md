# Redaction Policy and Leakage Eval

The classification contract for what is redacted and what is kept, plus the contract for how leakage is scored. The data project authored the tickets and the `pii.json` sidecar using these rules. The redaction pipeline in this project must apply the same rules to match the sidecar. For the corpus and sidecar shape, see [dataset.md](dataset.md). For where this sits in the eval, see [evaluation.md](evaluation.md).


## The master principle

Redact what identifies a person. Retain what describes the system.

Personal identifiers are removed and replaced with a token. Technical and system detail is kept. It is the value of the knowledge base. Data minimization here means minimum personal data, not minimum data.


## Classification

| Entity | Decision | Token | Reason |
|---|---|---|---|
| Person name | Redact | `<PERSON>` | Identifies a person |
| Username | Redact | `<USER>` | Identifies a person |
| Email | Redact | `<EMAIL>` | Identifies a person |
| Phone | Redact | `<PHONE>` | Identifies a person |
| Employee ID | Redact | `<EMP_ID>` | Identifies a person |
| City, locality | Redact | `<LOCATION>` | Quasi-identifier |
| Occupant location (building, floor, office) | Redact | `<LOCATION>` | Where a person is |
| Personal or client IP | Redact | `<IP>` | Identifying, full replace |
| Personal-device hostname | Redact | `<HOSTNAME>` | Maps to a person |
| System or app name | Retain | | Describes the system |
| Shared service hostname or URL | Retain | | Identifies a system |
| Infrastructure facility | Retain | | A system facility |
| Error or event IDs | Retain | | Technical signal |
| Cert serials | Retain | | System artifact |
| OS or device class | Retain | | Non-identifying |
| Region code | Retain | | Environment field |

Only the redact rows appear in the sidecar. Retain entities are never in the sidecar.


## The hard cases

**Composite, separable.** A Distinguished Name carries a username plus directory infrastructure. Redact the username, keep the infrastructure. `CN=mdelgado,OU=Corp Users` becomes `CN=<USER>,OU=Corp Users`. The DN is not a sidecar key; only the embedded username is.

**Composite, fused.** A personal-device hostname welds the person into one token with nothing separable. `WORKSTATION-MDELGADO` becomes `<HOSTNAME>`. The whole token is redacted.

**Username inside email.** A username is often the email local part. The username inside the email is part of `<EMAIL>`, not a separate `<USER>`. Span consumption is longest-match-first: the email is matched and consumed before the bare username, so it is not double counted. A standalone username elsewhere still counts.

**IP, full replace.** IPs are fully replaced with `<IP>`, not masked. A public client IP is identifying, and one uniform rule keeps the absence check simple.

**Facilities.** An occupant location (building, floor, office) is redacted; it locates a person. An infrastructure facility (a datacenter, a server room) is retained; it locates equipment, like a hostname.


## False-positive traps (retain these)

Off-the-shelf detectors over-fire on technical text. These are not PII and must be kept. Redacting them is an over-redaction error the eval measures.

| Looks like | Actually is |
|---|---|
| `0xC0000234` flagged as PERSON | Error code |
| `DC-EAST-03.corplabs.internal` | Service hostname |
| `https://sso.corplabs.com` | Service URL |
| `4A:7C:91:DE` | Cert serial |
| `EMEA`, `us-east-1` | Region code |
| `corp-datacenter-1` | Infrastructure facility |


## The leakage eval contract

This is how the sidecar is used to score the redactor. It is the deterministic axis of [evaluation.md](evaluation.md).

**Gate: absence-anywhere.** For each sidecar value, assert the value is gone from the entire redacted document and replaced by its `expected_after_redaction` token. A leak at any site is caught, including a site the author did not list. The `occurrences` list is for reporting, not the gate.

**Pin the token vocabulary.** The redactor's anonymizer must emit exactly the sidecar tokens (`<USER>`, not `<USERNAME>`). A mismatch fails on format, not leakage. This is the first task when wiring the redactor.

**Two sided.** Leakage measures under-redaction of the redact rows. Technical retention measures over-redaction of the retain rows. A good score requires both.

**Non-circular.** The sidecar was authored upstream during data generation, with no detector. The redactor here is a separate Presidio pipeline with custom recognizers. It is graded against a key it did not write. This is why the leakage number is a real guarantee, not a tautology. See [decisions.md](decisions.md).
