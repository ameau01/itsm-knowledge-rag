# Redaction Policy and Leakage Evaluation

The classification contract for what is redacted and what is kept, the redactor that applies it, and how the result is scored. The data project authored the tickets, the `pii.json` sidecar, and the `retention.json` sidecar using the classification below. The redactor applies the same classification at ingest. It never reads either sidecar at runtime. The sidecars are held-out scoring keys only. For the corpus and sidecar shape, see [dataset.md](dataset.md). For where this sits in the eval, see [evaluation.md](evaluation.md).


## The master principle

Redact what identifies a person. Retain what describes the system.

Personal identifiers are removed and replaced with a token. Technical and system detail is kept. It is the value of the knowledge base. Data minimization here means minimum personal data, not minimum data.


## The redactor

Three layers run in sequence on every ticket field. No sidecar is read at runtime.

**Layer 1, AD identity match.** The redactor loads `users_directory.json`, the synthesized corporate directory shipped with the dataset (769 users from the HuggingFace snapshot). It replaces each directory username, display name, and email with its token. Exact match against a directory is more precise than any name regex and needs no maintenance. The email rule runs first, so a full address is consumed before the bare username inside it could match. Over-redaction of identity fields is accepted, since they carry no technical knowledge. In production this directory is a live `Get-ADUser` or `ldapsearch` export, pulled on a schedule. The redactor matches against the latest snapshot at startup.

**Layer 2, format rules.** Regex patterns for structured PII that a directory does not supply: employee IDs, IP addresses, personal-device hostnames, phone numbers, office locations. Each rule has a structural signature, so it generalizes to tickets the directory has never seen.

**Layer 3, Presidio NER.** A spaCy-backed catch-all for residual identifiers the first two layers miss: informal name mentions, international phone formats, and personal emails from contractors or external contacts who are not in the directory. Layer 3 can be disabled for a faster run.

The directory is the primary control on identity recall. A complete, fresh directory catches more; the format and NER layers recover what it misses. Some identities are absent from the directory by the nature of any real export, such as contractors and recent leavers. That residual is caught by Layers 2 and 3 or accepted as a known gap.


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
| Third-party vendor/partner organization | Retain | | System landscape; name, domain, URL, portal travel together as one entity |
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

**Domain inside email.** The corporate domain inside an email address (`@corplabs.com`) is consumed by `<EMAIL>` along with the local part. The entire string `xx@corplabs.com` is one redacted value. The domain class itself is RETAIN wherever it occurs without the `@` context: service URLs (`sso.corplabs.com`), hostnames (`*.corplabs.internal`), and directory components (`DC=corplabs`). Partial email redaction (`<USER>@corplabs.com`) was considered and rejected: the surviving domain carries no knowledge value (every employee email shares it) and whole-string replacement is the simpler, stronger guarantee.

**IP, full replace.** IPs are fully replaced with `<IP>`, not masked. A public client IP is identifying, and one uniform rule keeps the absence check simple.

**Facilities.** An occupant location (building, floor, office) is redacted; it locates a person. An infrastructure facility (a datacenter, a server room) is retained; it locates equipment, like a hostname.

**Vendor identity is atomic.** A third-party vendor/partner's name, domain, service URL, and portal reference are one entity and share one classification: Retain. Retaining `api.meridiandata.io` while redacting "Meridian Data Services" (or vice versa) would be incoherent. The domain reveals the name. Which vendor's token expires is exactly the organization-specific knowledge this system exists to preserve.


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


## The scoring contract

The two sidecars score the redactor. They are held-out keys, read only by the scorer, never by the redactor. This is the deterministic axis of [evaluation.md](evaluation.md).

**Gate: absence-anywhere.** For each `pii.json` value, assert it is gone from the entire redacted ticket. A leak at any site is caught, including a site the author did not list. The `occurrences` list is for reporting, not the gate.

**Token vocabulary.** The redactor emits exactly the eight tokens (`<PERSON>`, `<USER>`, `<EMAIL>`, `<PHONE>`, `<EMP_ID>`, `<LOCATION>`, `<IP>`, `<HOSTNAME>`). A test asserts no other `<TOKEN>` string appears.

**Two sided.** Recall measures under-redaction of the redact rows against `pii.json`. Retention measures over-redaction of the retain rows against `retention.json`. A good score requires both.

**Non-circular.** The sidecars were authored upstream during data generation, with no detector. The redactor is a separate three-layer pipeline that never reads them. It is graded against keys it did not write, so the numbers are a real guarantee, not a tautology. See [decisions.md](decisions.md).


## Results

Scored over all 745 tickets with the three-layer redactor (L1 + L2 + L3), against the held-out sidecars.

PII recall, 98.9% overall (8,739 of 8,837):

| Class | Recall |
|---|---|
| person | 100.0% |
| ip | 100.0% |
| location | 99.8% |
| email | 99.7% |
| emp_id | 99.6% |
| username | 98.3% |
| hostname | 97.6% |
| phone | 87.7% |

Retention, 97.6% overall (8,372 of 8,581). All ten retain classes clear the 80% floor, ranging from service_url at 88.6% to vendor_name at 100.0%.

The main recall miss is phone at 87.7%. International formats such as `+65-9173-4028` match no Layer 2 pattern, and Presidio catches only some. The lowest retention class is service_url at 88.6%, where infrastructure hostnames that share the personal-device naming shape are over-redacted. Both are structural format tradeoffs, documented as accepted gaps. Username at 98.3% reflects the directory gap by design: identities not in the directory, mostly contractors and recent leavers, are the residual misses.
