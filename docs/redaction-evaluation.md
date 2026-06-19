# Redaction evaluation

How the redactor is measured. Redaction runs first in the pipeline, over the whole ticket, before anything is indexed or published. It has two jobs, and both are scored. Remove every piece of personal data. Keep every technical string that gives the knowledge its value. For the classification rules and the redactor itself, see [redaction-policy.md](redaction-policy.md). For the corpus and the answer keys, see [dataset.md](dataset.md).

This is the deterministic axis of the evaluation. The result is a count, not a judgment. A value is either gone or it is not.


## Why the number can be trusted

The redactor is graded against a key it did not write.

The two answer keys, `pii.json` and `retention.json`, were authored during data generation, before any redactor existed, with no detector involved. The redactor in this project is a separate three-layer pipeline: a directory exact match, format rules, then Presidio. It never reads either key at runtime. So the grade is not the system checking its own work. It is a system scored against ground truth produced independently of it.

This matters because a redaction score from a detector graded against its own detections is circular and means nothing. This one is not.


## What is scored

Two sides, each with its own key.

- Leakage, scored against `pii.json`. Every PII value in a ticket must be gone from the entire redacted document and replaced by its expected token. The check is absence-anywhere. A value that survives in any field is a leak, including in a field the author did not enumerate.
- Over-redaction, scored against `retention.json`. Technical strings that carry the knowledge, system names, hostnames, error codes, cert serials, region codes, must survive. A redactor that strips these to look safe is failing, not passing.

A correct redactor satisfies both. Removing everything is not safety. It destroys the knowledge base.


## PII leakage

Scored over all 745 tickets. Overall PII recall is 98.9 percent.

| Class | Recall | Caught / total |
|---|---|---|
| person | 100.0% | 2178 / 2178 |
| ip | 100.0% | 985 / 985 |
| location | 99.8% | 832 / 834 |
| email | 99.7% | 912 / 915 |
| emp_id | 99.6% | 921 / 925 |
| username | 98.3% | 1643 / 1671 |
| hostname | 97.6% | 1011 / 1036 |
| phone | 87.7% | 257 / 293 |
| overall | 98.9% | 8739 / 8837 |

Phone is the one class below 95 percent. International formats such as a leading-plus country code match no format rule, and Presidio recovers only some of them. This is a known gap, not a rounding artifact, and it is stated rather than averaged away.


## Technical retention

Scored over all 745 tickets. Overall retention is 97.6 percent.

| Class | Retention | Survived / total |
|---|---|---|
| vendor_name | 100.0% | 4 / 4 |
| region | 99.4% | 178 / 179 |
| app_name | 99.3% | 4197 / 4227 |
| cert_serial | 99.1% | 209 / 211 |
| error_code | 99.1% | 981 / 990 |
| event_id | 97.4% | 494 / 507 |
| facility | 96.2% | 50 / 52 |
| service_hostname | 94.8% | 1233 / 1300 |
| os_device | 94.0% | 723 / 769 |
| service_url | 88.6% | 303 / 342 |
| overall | 97.6% | 8372 / 8581 |

All ten classes clear the 80 percent floor. service_url is lowest at 88.6 percent. Some infrastructure URLs share the naming shape of a personal device hostname, so the redactor removes them. It is a format tradeoff, accepted and recorded.


## How to read these two numbers together

The two scores pull against each other. A redactor can raise leakage recall by removing more, which lowers retention. It can raise retention by removing less, which raises leakage. Reporting both is the point. One number alone hides the tradeoff the other reveals.

The headline is that both are high at once. 98.9 percent of personal data removed, 97.6 percent of technical content kept, against keys the redactor never saw.
