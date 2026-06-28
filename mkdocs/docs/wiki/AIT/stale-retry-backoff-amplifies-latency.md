---
hide:
  - navigation
root_cause_id: AIT/stale-retry-backoff-amplifies-latency
family: AIT
ticket_count: 2
curated: true
self_serviceable: false
---

# Stale Retry Policy Amplifies Downstream Latency Into Gateway Timeout Storms

[← Back to categories](../../index.md)

## Description

Affected users experience failures during scheduled batch data synchronization jobs that route through the Integration Gateway to downstream API services. The issue manifests as repeated HTTP 504 Gateway Timeout responses when downstream service latency becomes elevated — in reported incidents, p99 latency spiked from approximately 1.2 seconds to 38 seconds, far exceeding the gateway's configured timeout window. Sync jobs fail or are significantly delayed, with failure windows lasting approximately 30 minutes or longer and delaying data availability for downstream consumers in affected fulfillment groups and queues.

The core behavior observed is that the Integration Gateway's deprecated retry and backoff policy amplifies the impact of downstream latency rather than mitigating it. When downstream services slow down, the gateway's insufficiently bounded retries compound the load, producing retry storms visible in distributed tracing. This feedback loop causes the timeout condition to persist or worsen across the batch processing window, preventing sync jobs from completing successfully.

Gateway pod restarts alone do not resolve the issue. Temporarily increasing the gateway timeout threshold (for example, from 30 seconds to 60 seconds) reduces immediate failure counts for some traffic but does not address the underlying retry amplification. The issue is not related to authentication failures, token expiry, or rate-limiting errors; logs confirm that only timeout-class errors are present during the affected windows.

!!! note "Reported variations"

    - Nightly batch sync jobs fail entirely within the affected window, delaying data availability for downstream inventory consumers.
    - Intermittent 504 responses affect order fulfillment sync pipelines, causing delayed but not always fully failed jobs.
    - Retry storms are visible in distributed tracing, indicating compounding load on the downstream service during the timeout window.
    - A gateway pod restart does not resolve the issue, and no recent deployment change to timeout settings is identified.
    - Temporarily extending the gateway timeout threshold reduces immediate failure counts but does not eliminate the retry amplification behavior.

## Affected environment

Distribution across 2 reported cases:

- **Device / platform:** Kubernetes (EKS) (100%)
- **Team:** Application Support (50%), backend-integration-team (50%)
- **Region:** us-east-1 (100%)

## Root cause

Elevated downstream service latency caused upstream request timeouts through the Integration Gateway. The impact was amplified because the gateway was still configured with a stale, deprecated retry and backoff policy that extended retry behavior beyond the effective integration window, producing retry storms that compounded load on the already-slow downstream service. Available evidence points to downstream response slowness with possible transient throttling pressure rather than an authentication failure.

## Diagnostics

Steps used to confirm this root cause:

1. Confirm the integration token or secret configured for the gateway is still valid and accepted by the API.  
   *Expected:* <PERSON> validation succeeds and the API accepts authenticated calls.
2. Compare integration job timing with API gateway latency and downstream service health during the nightly sync window.  
   *Expected:* API response latency is within the integration timeout window.
3. Review gateway logs for rate-limit responses, retry exhaustion patterns, or policy-driven retry amplification.  
   *Expected:* No rate-limit response prevents the integration job from completing.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Replaced the deprecated Integration Gateway retry policy v1.2 (rtpol-0012-deprecated) with the supported v1.3 production configuration on gw-east-prod-01.corplabs.internal in the appsync-prod namespace, applied by <PERSON>.
2. Updated gateway retry behavior to exponential backoff with jitter (base 2s, max 16s, jitter factor 0.5) and reduced the cumulative retry window from 180s to 60s to avoid amplifying downstream latency spikes against InventoryAPI.
3. <PERSON> the temporary timeout increase (30s → 45s) only during recovery validation of sync-20251203-batch4-retry, then aligned runtime settings with the corrected retry policy v1.3 defaults.
4. Coordinated with the downstream InventoryAPI team lead <PERSON> (<EMP_ID>) to review and mitigate the latency condition observed during the 03:20–03:50 UTC failure window; downstream team confirmed a database connection pool exhaustion event on their side.
5. Validated successful end-to-end batch sync completion across the next two scheduled runs (sync-20251204-batch4 and sync-20251205-batch4) and monitored gateway 504 and latency metrics on the Monitoring System for 24 hours — zero 504s observed post-fix.
6. Documented the policy correction in runbook RB-APPSYNC-017 and added guidance to verify retry-policy version references (current: v1.3) during future timeout incidents. Notification sent to <EMAIL> and <PERSON> for awareness.

**Example 2**

1. Validated that no recent gateway deployment introduced the failures by reviewing the CI/CD pipeline history for igw-prod-east.corplabs.internal (last deploy: 2025-12-08T14:12Z, unrelated config change). Reviewed failing request patterns showing 504s and upstream timeouts clustered around slow downstream Order Fulfillment API responses rather than immediate authentication rejection.
2. Confirmed the integration token path (client_id: svc-orderfulfillment-prod) required verification but did not show evidence of a broad auth failure pattern in the gateway logs, so token rotation was not performed to avoid introducing an unnecessary credential change during the incident. <PERSON> (<EMP_ID>) was asked to schedule a post-incident token rotation as a precaution.
3. Applied a gateway mitigation on igw-prod-east.corplabs.internal by increasing the downstream request timeout from 30s to 60s for affected order-sync-batch traffic and updating retry behavior to use bounded exponential backoff (base 2s, max 3 retries, jitter enabled) to stop retry storms from compounding downstream slowness.
4. Captured failing request traces (trace-8a4f21, trace-8a4f34, trace-8a4f47) from the Monitoring System and correlated them with downstream response timing to isolate the bottleneck to the downstream Order Fulfillment API latency window (p99 at 45–55s) rather than the gateway pod itself.
5. Escalated the latency evidence and trace samples to the downstream service owner <PERSON> (<EMAIL>) on the <LOCATION> platform team for remediation while keeping the gateway mitigation in place to stabilize sync job completion for the <LOCATION> fulfillment queue.
6. Monitored post-change behavior via the Monitoring System dashboard and verified timeout volume dropped from ~120/min to <5/min and order-sync-batch processing stabilized after the timeout and retry configuration adjustments. Confirmed with <PERSON> that sync jobs completed successfully by 20:15 UTC.

## Recommendation

Resolved by IT; reference Integration Gateway deprecated retry policy causing 504 timeout storms during batch sync processing.

---

[← Back to categories](../../index.md)
