---
hide:
  - navigation
root_cause_id: CES/unconfirmed-tls-presentation-issue-evidence-gap
family: CES
ticket_count: 1
curated: true
self_serviceable: false
---

# Unconfirmed TLS certificate presentation issue with insufficient diagnostic evidence

[← Back to categories](../../index.md)

## Description

Affected users accessing the internal web service reported TLS certificate warnings in their browsers, specifically "ERR_CERT_DATE_INVALID" errors when navigating to the service URL. At the same time, dependent internal API calls routed through the API gateway began failing with TLS handshake errors, compounding the service disruption for both interactive users and automated consumers.

The issue was reported by multiple users across different locations and workstations, suggesting it was not isolated to a single machine or network segment. However, the symptoms were not consistently reproducible during the diagnostic review period — the certificate-related errors observed by users did not always align with what the investigating team found when examining the load balancer configuration at the time of review.

This inconsistency left open the possibility that the fault was transient, limited to a specific network path, or had already resolved itself before validation could be completed. As a result, the full scope and root cause of the disruption could not be definitively confirmed from the available evidence.

!!! note "Reported variations"

    - In some cases, only browser-based access triggered the certificate warning while command-line or scripted checks against the same endpoint did not reproduce the error at the time of review.
    - Dependent internal API calls failed with TLS handshake errors simultaneously, even though the API gateway endpoint was not the primary subject of the user report.

## Affected environment

Distribution across 1 reported cases:

- **Device / platform:** on-prem Kubernetes (kubeadm) (100%)
- **Team:** Platform Engineers (100%)
- **Region:** us-east-1-dc1 (100%)

## Root cause

The available diagnostics did not confirm an active certificate expiration or a defective certificate chain on the load balancer serving the affected internal web endpoint. User-reported symptoms were consistent with a certificate-serving problem, but gaps in diagnostic access and incomplete monitoring history prevented confirmation of whether the fault was transient, specific to certain network paths, or had already cleared before the investigation was completed.

## Diagnostics

Steps used to confirm this root cause:

1. Inspect the presented certificate on the service endpoint for expiration date and SAN coverage.  
   *Expected:* Certificate is current and matches the service endpoint name.
2. Validate the deployed certificate chain from both client and load balancer perspectives.  
   *Expected:* Full chain validates without expired or missing intermediate certificates.
3. Review certificate monitoring alerts and renewal job history for the affected endpoint.  
   *Expected:* Renewal alerts are active and renewal job completed before expiration.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

1. Capture fresh certificate and chain checks from each affected client path at the time symptoms recur, including the exact VIP (<IP>) and hostname (internal-web.corplabs.internal) used. Ensure checks are run from both the <LOCATION> and <LOCATION> office subnets to cover the paths reported by <USER> and <USER>.
2. Obtain access to the relevant F5 configuration partition (partition-internal-web on LB-EAST-01) or engage the load balancer team to export the active certificate and chain bindings for the impacted virtual server serving VIP <IP>. Contact <PERSON> (<EMAIL>) to coordinate access restoration.
3. Increase retention and coverage for certificate renewal and LB deployment logs (minimum 90-day retention) so future incidents can confirm whether the served chain changed during the event. Ensure CertMonitor alerts for internal-web.corplabs.internal are routed to the Platform Engineers distribution list.
4. If symptoms recur, escalate immediately to the load balancer team for live path comparison before the condition clears. Assign to <USER> or the on-call platform engineer and include diagnostic captures from both <LOCATION> and <LOCATION> office client paths.

## Recommendation

This issue is resolved by IT support; reference "unconfirmed TLS certificate presentation issue" when reporting it.

---

[← Back to categories](../../index.md)
