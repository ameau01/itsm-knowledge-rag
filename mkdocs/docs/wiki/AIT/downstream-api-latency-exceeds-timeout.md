---
hide:
  - navigation
root_cause_id: AIT/downstream-api-latency-exceeds-timeout
family: AIT
ticket_count: 23
curated: true
self_serviceable: false
---

# Downstream API Latency Exceeds Integration Gateway Timeout Causing 504 Errors

[← Back to categories](../../index.md)

## Description

Affected users experience intermittent or sustained failures of scheduled data synchronization jobs routed through the Integration Gateway to downstream API endpoints — including internal services, billing APIs, CRM endpoints, and third-party vendor APIs. The primary symptom is repeated HTTP 504 Gateway Timeout responses when downstream API response times spike well beyond the gateway's configured timeout threshold (typically 15–30 seconds, though in some cases as low as 2–5 seconds). Failures cluster during overnight or early-morning batch processing windows, often spanning 20 minutes to over two hours, and affect multiple gateway nodes and pods across Kubernetes clusters rather than isolated instances.

Gateway monitoring dashboards and distributed traces consistently show downstream p95/p99 response latency climbing dramatically — from baselines of approximately 200 milliseconds to 1–3 seconds up to peaks of 7–72 seconds — directly causing the gateway to terminate requests before responses are received. The resulting 504 errors cascade into retry exhaustion, message queue backlogs (in some cases exceeding 4,200 pending messages), and delayed or blocked data availability for dependent workflows such as finance reporting, analytics pipelines, and billing integrations. In some incidents, over 340 consecutive timeout errors were logged within a 90-minute span.

Authentication failures, rate-limiting responses, and credential expiry are consistently ruled out during investigation; gateway logs show no HTTP 401/403 or 429 responses, and token validation confirms valid credentials. Where token rotation was performed as an early troubleshooting step, it did not resolve the core 504 timeout pattern. Gateway-side actions such as pod restarts and cache clears similarly fail to eliminate the issue. Resolution occurs only after downstream API teams address service-side performance conditions such as resource exhaustion, misconfigured connection pools, or missing database indexes.

!!! note "Reported variations"

    - In one instance, a recent gateway deployment introduced intermittent HTTP 401 Unauthorized responses alongside the dominant 504 pattern; approximately 15% of requests returned authorization errors resolved by token rotation, but 504 timeouts persisted independently.
    - Gateway timeout configurations varied across incidents, ranging from as low as 2–5 seconds to the more common 30-second threshold, causing failures at correspondingly different downstream latency levels.
    - Some incidents involved external third-party partner APIs with no prior maintenance notice, while others involved internal downstream services; the timeout behavior was identical in both cases.
    - Incomplete telemetry was reported in at least one incident, where request correlation IDs were not propagated from the gateway to the monitoring system, requiring manual timestamp-based correlation.
    - Queue backlog severity varied significantly; one instance recorded over 4,200 pending messages while others reported sync lag exceeding 45 minutes without specific queue depth metrics.
    - One downstream root cause was traced to a misconfigured connection pool on the API ingest tier; another was traced to a full table scan caused by a missing database index after a schema migration.
    - In one case, the morning data availability report — rather than real-time alerting — was the first indicator of failure, as sync jobs had run overnight unattended.
    - Rate limiting (HTTP 429) was considered in some occurrences but ruled out during investigation; no throttling responses were observed in gateway logs.

## Affected environment

Distribution across 23 reported cases:

- **Operating system:** Linux (30%), Linux (container) (4%), Ubuntu 20.04 (4%)
- **Device / platform:** Kubernetes (52%), Kubernetes (EKS) (26%), Linux (9%)
- **Team:** Application Support (43%), internal_ops (4%), BusinessUsers (4%)
- **Region:** us-east-1 (96%), us-west-2 (4%)

## Root cause

Elevated latency on downstream API services caused Integration Gateway outbound requests to exceed the configured timeout window, producing intermittent or sustained HTTP 504 Gateway Timeout responses. The downstream performance degradation was traced to backend conditions such as resource exhaustion, misconfigured connection pools, or missing database indexes. Token expiry and rate-limiting were investigated but not supported by available evidence as contributing factors.

## Diagnostics

Steps used to confirm this root cause:

1. Confirm the integration token or secret is valid and accepted by the downstream API.  
   *Expected:* <PERSON> validation succeeds and the API accepts authenticated calls.
2. Compare integration job timing with API gateway latency and downstream service health.  
   *Expected:* API response latency is within the integration timeout window.
3. Check API gateway logs for rate-limit or retry exhaustion events.  
   *Expected:* No rate-limit response prevents the integration job from completing.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Validated that the integration credential for service account <USER> was present in Vault configuration (secret/intg-gateway/api-token) and found no supporting evidence of token rejection or 401/403 authentication failures during the incident window in logs from pod intg-gw-worker-7b4d9.
2. Correlated the nightly job failure window (02:00–02:45 UTC) with <PERSON> monitoring data and confirmed a sharp increase in downstream API Service latency on api-svc-node-east-03, with p95 response time rising from ~200ms to ~6s — well above normal baseline — during the affected sync-nightly runs.
3. Applied a mitigation on the Integration Gateway job path (namespace intg-gateway-prod, pod intg-gw-worker-7b4d9) by increasing the request timeout from 30s to 90s and configuring exponential retry with backoff (max 3 retries, initial delay 5s) so long-running downstream API calls could complete instead of failing at the prior 30-second limit. Change applied by <PERSON>.
4. Restarted the affected Integration Gateway pod intg-gw-worker-7b4d9 from workstation <HOSTNAME> to clear transient connection state and reran a validation job (sync-validate-20251206-0015) after the timeout adjustment; validation completed successfully in 74 seconds.
5. Escalated the latency finding to the API Service owner <PERSON> <PERSON> (<EMAIL>, phone <PHONE>) for backend performance investigation on api-svc-node-east-03 during the nightly batch window and documented the dependency on their service health for permanent correction. Escalation ticket INC-AIT-0028-ESC created and assigned to the <LOCATION> platform engineering team.

**Example 2**

1. Validated that authentication was not the trigger by confirming there was no matching pattern of 401 or 403 failures for service account <USER> during the timeout window (09:12–09:24 UTC); token expiry date verified as 2026-03-15.
2. Confirmed the timeout condition was latency-driven by correlating 14 failed integration jobs with downstream API latency spikes (p95: 48s vs. 1.2s baseline) and repeated 504 Gateway Timeout responses on pod intg-gw-worker-7b4d9, as identified by <PERSON>.
3. Temporarily increased the Integration Gateway request timeout from 30 seconds to 90 seconds in the intg-gateway-prod namespace ConfigMap so in-flight downstream calls could complete during the latency event; change applied at 09:31 UTC.
4. Adjusted retry and exponential backoff settings on upstream calls (<PERSON> retries: 5, initial backoff: 2s, multiplier: 2x) to reduce immediate job failure rates and avoid excessive retry pressure while the downstream service remained slow.
5. Cleared 14 queued integration jobs and monitored processing throughput via the Monitoring System until the sync backlog returned to acceptable levels at 09:48 UTC; confirmed with <PERSON> in <LOCATION> that data lag was resolved.
6. Escalated the incident to the downstream API service team lead <PERSON> (<USER>) via ESC-7841 with supporting latency trends, <PERSON> snapshots, and request traces (trx-8a3f29c), and updated Monitoring System alert thresholds to detect future 95th-percentile latency spikes above 10 seconds earlier.

## Recommendation

Resolved by IT; downstream API latency exceeded the Integration Gateway timeout threshold, causing 504 Gateway Timeout errors and batch sync job failures during scheduled processing windows.

---

[← Back to categories](../../index.md)
