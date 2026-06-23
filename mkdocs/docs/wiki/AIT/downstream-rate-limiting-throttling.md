---
hide:
  - navigation
root_cause_id: AIT/downstream-rate-limiting-throttling
family: AIT
ticket_count: 2
curated: true
self_serviceable: false
---

# Downstream API rate limiting causes integration job timeouts

[← Back to categories](../../index.md)

## Description

Affected users observe that scheduled or real-time integration jobs begin failing with timeout errors during periods of high request volume, such as overnight batch processing or nightly ingestion runs. The failures typically appear as repeated 504 Gateway Timeout errors in application and gateway logs, and monitoring dashboards show a sharp increase in downstream response times alongside elevated error rates from the external API endpoint.

The issue can affect multiple integration workflows simultaneously — both scheduled batch syncs and real-time data synchronization jobs may fail or stall. Users may notice that data updates stop flowing, backlogs accumulate in the gateway worker queue, and previously successful jobs no longer complete within their expected windows. Individual test calls to the downstream API endpoint may still succeed, which can make the issue appear intermittent or suggest a partial outage rather than a throughput-related problem.

In some cases, initial error logs may also include unrelated status codes such as 401 Unauthorized alongside the 504 timeouts, which can complicate early triage. However, investigation typically confirms that authentication credentials remain valid and that the root failure is the volume of requests exceeding the downstream API's rate or quota limits.

!!! note "Reported variations"

    - Initial error logs may include 401 Unauthorized responses alongside the 504 timeouts, potentially suggesting an authentication issue, even though credentials are confirmed valid upon investigation.
    - The issue may surface only during overnight or off-hours batch windows when large record volumes (e.g., thousands of queued records) are processed in a short period, while daytime or lower-volume operations continue to function normally.
    - Individual manual test calls to the downstream API endpoint may succeed, masking the rate-limiting condition and giving the impression that the external service is fully operational.

## Affected environment

Distribution across 2 reported cases:

- **Device / platform:** Kubernetes (AKS) (50%), Kubernetes (EKS) (50%)
- **Team:** Data Integration (50%), backend-syncers (50%)
- **Region:** us-east-1 (100%)

## Root cause

The downstream external API enforces rate or quota limits on the integration client, and when request volume exceeds those limits — particularly during large batch processing windows — the API returns sustained throttling responses. These throttling responses cause the Integration Gateway to retry failed requests repeatedly, which increases the number of pending requests in the retry queue and drives up overall latency. As retries accumulate, individual requests eventually exceed the gateway's timeout threshold, resulting in timeout errors that cause integration job failures and delayed data synchronization.

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

This issue is resolved by IT support; reference 'downstream rate-limiting throttling' when reporting it.

---

[← Back to categories](../../index.md)
