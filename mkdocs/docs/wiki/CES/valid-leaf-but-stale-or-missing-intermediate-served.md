---
hide:
  - navigation
root_cause_id: CES/valid-leaf-but-stale-or-missing-intermediate-served
family: CES
ticket_count: 5
curated: true
self_serviceable: false
---

# Expired or missing intermediate certificate in load balancer chain breaks TLS

[← Back to categories](../../index.md)

## Description

Affected users attempting to access internal web services over HTTPS encounter browser certificate warnings — most commonly "NET::ERR_CERT_DATE_INVALID" — and are unable to reach the service. Automated clients and API integrations connecting through the same endpoints fail during the TLS handshake, producing certificate validation errors in application logs. The issue typically affects all users and service accounts connecting to the impacted endpoint across multiple offices and regions simultaneously.

The warnings and failures stem from the load balancer that terminates TLS for the internal web service. In most cases, the endpoint (leaf) certificate has expired and has not been replaced on the load balancer, even though a renewed certificate may already exist. At the same time, the certificate chain served by the load balancer is incomplete or outdated — the required intermediate certificate is either missing from the bundle entirely or is itself expired. This combination means that even clients willing to overlook one problem cannot establish a trusted connection.

Reports have involved multiple load balancer appliances and internal service hostnames, but the user-facing experience is consistent: browsers display date-validity errors, backend services log TLS handshake failures, and normal internal application access is blocked until the certificate and chain are corrected. In several instances, the certificate monitoring or renewal alerting that should have flagged the approaching expiration did not trigger before the outage began, meaning the issue was first discovered through direct user reports rather than automated alerts.

!!! note "Reported variations"

    - In at least one instance the leaf certificate itself was still valid, but the load balancer served a broken chain containing an expired intermediate certificate, causing the same browser warnings and TLS failures despite a successful recent renewal.
    - Some reports involved the renewed certificate existing on the infrastructure but not being activated in the load balancer's SSL profile, leaving the old expired certificate in place.
    - Automated deployment pipelines and service accounts were affected alongside interactive browser users, with TLS errors appearing in CI/CD and monitoring tooling logs.

## Affected environment

Distribution across 5 reported cases:

- **Operating system:** Linux (20%)
- **Device / platform:** on-premises VMware (20%), Linux (containerized) (20%), On-prem F5 Load Balancer and internal web VM pool (20%)
- **Team:** internal-services (40%), internal_services_team (20%), Internal Employees (20%)
- **Region:** us-east-1 (60%), us-central-1 (private) (20%), us-central (20%)

## Root cause

The load balancer serving TLS for the internal web service was configured with an expired or incomplete certificate chain. In most cases, the endpoint certificate had expired and the renewed replacement had not been fully deployed, while the intermediate certificate in the served bundle was either outdated or missing altogether. Contributing to the outage, certificate expiration monitoring and renewal alerting failed to fire before the certificates lapsed, so the condition was not caught proactively.

## Diagnostics

Steps used to confirm this root cause:

1. Inspect the service endpoint certificate expiration date and subject alternative names.  
   *Expected:* Certificate is current and matches the service endpoint name.
2. Validate the deployed certificate chain from client and load balancer perspectives.  
   *Expected:* Full chain validates without expired or missing intermediate certificates.
3. Review certificate monitoring alerts and renewal job history.  
   *Expected:* Renewal alerts are active and renewal job completed before expiration.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Requested and issued a renewed CA-signed leaf certificate (CN=portal.internal.corplabs.com, SAN: portal.internal.corplabs.com) from the CorpLabs Internal CA for the affected internal web service endpoint, with approval expedited by <PERSON> (<USER>).
2. Replaced the expired leaf certificate (serial 4A:7C:9E:01) and updated the full certificate chain on load balancer LB-CENTRAL-04 to use the current CorpLabs Intermediate CA G3 certificate, removing the stale G2 intermediate.
3. Deployed the renewed certificate bundle to the internal web service endpoints on svc-deploy-07.internal.corplabs.com and rotated or reloaded affected instances so the new certificate was actively served. Deployment coordinated by <PERSON> (<USER>, <EMP_ID>).
4. Performed a staged load balancer configuration reload on LB-CENTRAL-04 and LB-CENTRAL-05 to ensure the updated chain was presented consistently across the us-central-1 region and all backend nodes.
5. Restored and corrected certificate expiration monitoring rule cert-renew-portal-001 (owner reassigned to <USER> and <USER>) so alerts trigger 30 days before expiry, then validated successful TLS handshakes from internal clients including <HOSTNAME> (<IP>) and the <LOCATION> office without certificate warnings.

**Example 2**

1. Confirmed the certificate presented by the Load Balancer LB-EAST-01.corp.internal for internal-web-service (CN=appportal.corp.internal, serial 4A:3F:9C:01:BB:72) was past its <PERSON> date of 2025-12-23T00:00:00Z and no longer valid for production TLS connections.
2. Requested and obtained a renewed end-entity TLS certificate from the internal Certificate Authority for the affected service endpoint appportal.corp.internal, new serial 7B:12:AE:44:CF:90, valid until 2026-12-23. CSR generated and submitted by <USER>, approved by <USER>.
3. Updated the Load Balancer LB-EAST-01.corp.internal TLS configuration to deploy the renewed certificate (serial 7B:12:AE:44:CF:90) and attach the required intermediate certificate chain (CorpLabs Internal CA G2) to the appportal.corp.internal listener.
4. Reloaded the Load Balancer LB-EAST-01.corp.internal configuration via the management console so new inbound TLS sessions presented the corrected certificate bundle; verified no active session drops during the reload window.
5. Validated from the client side — including from <HOSTNAME> (<IP>, <USER>) and <HOSTNAME> (<USER>, <LOCATION> office) — that the service now completed TLS handshakes successfully without certificate date warnings or missing-chain validation failures.
6. Restored and verified certificate expiration monitoring and renewal alerting for appportal.corp.internal in the cert-ops dashboard, configured to trigger at 30-day and 7-day thresholds, with notifications routed to <USER>@corp.internal and the cert-ops distribution list, to detect future certificate age and renewal job issues before service impact.

## Recommendation

This issue is resolved by IT support; reference "expired or missing intermediate certificate on load balancer" when reporting it.

---

[← Back to categories](../../index.md)
