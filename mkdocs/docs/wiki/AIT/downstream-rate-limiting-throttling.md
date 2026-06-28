---
hide:
  - navigation
root_cause_id: AIT/downstream-rate-limiting-throttling
family: AIT
ticket_count: 2
curated: true
self_serviceable: false
---

# Downstream API Rate-Limit Throttling Causes Gateway Timeout Integration Failures

[← Back to categories](../../index.md)

## Description

Affected users experience failures of scheduled and real-time integration jobs that route through the Integration Gateway when downstream external API endpoints enforce rate limits. The issue typically manifests as repeated HTTP 504 Gateway Timeout errors observed in application and gateway logs. Monitoring dashboards show sharply rising downstream latency, with p99 response times exceeding normal thresholds, and elevated error rates from external API endpoints. Integration jobs that previously completed successfully begin failing within minutes of onset, blocking normal data synchronization workflows.

The underlying mechanism involves the external API returning HTTP 429 (Too Many Requests) responses due to quota enforcement, particularly during periods of high request volume such as nightly batch ingestion or overnight sync windows. The Integration Gateway's retry logic causes pending requests to queue rapidly — climbing from a handful to over a hundred within minutes — until each request exceeds the gateway's timeout threshold. This retry-stacking behavior converts the downstream throttling condition into widespread gateway timeouts visible to end users and dependent applications.

The issue affects integration paths used by reporting applications and customer data synchronization services alike, creating backlogs in gateway worker queues and delaying or entirely preventing data record updates. Affected teams observe that the downstream endpoint remains reachable and responds normally to individual test calls, confirming the external service is not fully unavailable — rather, the volume of concurrent or retried requests triggers rate-limit enforcement that cascades into job failures across the integration platform.

!!! note "Reported variations"

    - Initial error logs may include HTTP 401 Unauthorized responses alongside the 504 timeouts, leading to an initial suspicion of authentication or credential rotation issues before downstream throttling is confirmed as the root cause.
    - Both real-time data sync jobs and scheduled batch ingestion jobs may be affected simultaneously when they share the same integration gateway path and downstream API quota.
    - The gateway worker queue backlog may persist and continue growing even after the initial throttling event, as retries from earlier failed jobs compound with new incoming requests.

## Affected environment

Distribution across 2 reported cases:

- **Device / platform:** Kubernetes (AKS) (50%), Kubernetes (EKS) (50%)
- **Team:** Data Integration (50%), backend-syncers (50%)
- **Region:** us-east-1 (100%)

## Root cause

The downstream API enforced rate limits against the integration client, producing sustained HTTP 429 Too Many Requests responses. Gateway retries accumulated under elevated latency, exhausted the effective timeout window, and resulted in HTTP 504 Gateway Timeout errors that caused integration job failures and delayed data syncs.

## Diagnostics

Steps used to confirm this root cause:

1. Confirm the integration token or secret remained valid for authenticated downstream API calls during the failure window.  
   *Expected:* <PERSON> validation succeeds and the API accepts authenticated calls.
2. Compare failed integration job timing with gateway latency metrics and downstream service responsiveness during the incident window.  
   *Expected:* API response latency is within the integration timeout window.
3. Inspect gateway logs and traces for downstream rate-limit responses, retry exhaustion, and queueing behavior.  
   *Expected:* No rate-limit response prevents the integration job from completing.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Reviewed Integration Gateway traces on INTGW-AKS-PROD-01 and Monitoring System dashboards to confirm the timeout pattern was driven by repeated downstream 429 responses (1,247 occurrences) and increasing response latency (p99 >28s) rather than an internal gateway failure. Analysis performed by <PERSON> (<USER>) with input from <PERSON>.
2. Applied temporary exponential backoff (initial delay 2s, <PERSON> 60s, jitter enabled) and adjusted the Integration Gateway retry policy on INTGW-AKS-PROD-01 to cap retries at 3 attempts, reducing immediate retry storms while preserving successful completion for delayed downstream responses.
3. Coordinated with the downstream analytics API owner (contact: <PERSON>, <USER>@partnerapi.net) to increase the request quota for integration client ID intg-rpt-prod-east from 200 req/min to 500 req/min after confirming sustained rate-limit enforcement against the <LOCATION> integration path.
4. Replayed the failed ingestion job RPT-INGEST-0412 and real-time synchronization jobs after the quota increase was confirmed at 11:02 UTC, and verified that all requests completed successfully without recurring gateway 504 errors. <PERSON> (<USER>) confirmed data sync restored on her workstation <HOSTNAME>.
5. Updated the Integration Gateway retry and backoff policy for the reporting integration path on INTGW-AKS-PROD-01 and added Monitoring System alerting thresholds for 429 spike detection (>20 per 5-min window) and downstream latency growth (p95 >5s) to detect recurrence earlier. Alert recipients set to <EMAIL> and <EMAIL>.

**Example 2**

1. Confirmed the throttling pattern in gateway and downstream logs (batch-20260514-0115) and reduced request concurrency for the affected overnight batch jobs from 50 to 10 concurrent workers on the Integration Gateway EKS deployment in us-east-1.
2. Implemented stronger pacing, exponential backoff (initial delay 2s, <PERSON> 60s, jitter enabled), and batch spreading on the Integration Gateway to stay within the downstream API rate limits of 100 requests/minute. Configuration was updated by <PERSON> (<USER>) and reviewed by <PERSON>.
3. Requested a quota review or temporary limit increase from the downstream API owner (contacted via <EMAIL>) where supported, referencing the CustomerDataSyncApp integration and projected batch volumes.
4. Monitored the next batch cycle (2026-05-15T01:15:00Z) via the Monitoring System and verified sync jobs completed without retry exhaustion or timeout symptoms. <PERSON> (<EMAIL>) confirmed all customer records were synced successfully and the backlog was fully cleared.

## Recommendation

Resolved by IT after identifying that downstream API rate-limit enforcement triggered retry exhaustion and gateway timeouts across integration jobs.

---

[← Back to categories](../../index.md)
