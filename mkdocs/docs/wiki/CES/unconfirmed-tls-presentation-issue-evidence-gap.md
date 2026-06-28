---
hide:
  - navigation
root_cause_id: CES/unconfirmed-tls-presentation-issue-evidence-gap
family: CES
ticket_count: 1
curated: true
self_serviceable: false
---

# Suspected Transient Certificate-Serving Fault on Load Balancer Unconfirmed

[← Back to categories](../../index.md)

## Description

Affected users at a corporate office reported TLS certificate warnings and failed connections when accessing an internal web service through an F5 load balancer. Browsers displayed a certificate date-invalid error when navigating to the service URL, and dependent internal API calls through the API gateway began failing TLS handshake validation simultaneously. The issue was initially surfaced by a platform engineer via internal chat and was subsequently confirmed by multiple users at the same site.

An affected workstation was used to reproduce the browser-side certificate warning, and a second user at the same office independently confirmed identical symptoms. The application remained unavailable to some internal consumers following the certificate-related alerts.

However, the available troubleshooting data did not consistently show an expired certificate or chain defect on the F5 partition serving the relevant virtual IP at the time of diagnostic review. The investigation was unable to conclusively determine whether the certificate-serving fault was transient in nature, isolated to a specific client path or load balancer partition, or had already cleared before validation could be completed. Despite this evidentiary gap, the reported symptoms were consistent with a certificate-serving problem, and a matching fix was applied, after which the reported service impact cleared.

## Affected environment

Distribution across 1 reported cases:

- **Device / platform:** on-prem Kubernetes (kubeadm) (100%)
- **Team:** Platform Engineers (100%)
- **Region:** us-east-1-dc1 (100%)

## Root cause

Insufficient evidence existed to confirm a certificate expiration outage. The incident may have involved a transient or path-specific load balancer certificate presentation issue, but diagnostic access gaps and incomplete monitoring history prevented confirmation of the root cause.

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

Resolved by IT after applying a certificate-related fix to the F5 load balancer, though the root cause remained unconfirmed due to insufficient evidence captured during the active incident window.

---

[← Back to categories](../../index.md)
