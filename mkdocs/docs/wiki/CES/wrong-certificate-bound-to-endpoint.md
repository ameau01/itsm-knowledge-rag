---
hide:
  - navigation
root_cause_id: CES/wrong-certificate-bound-to-endpoint
family: CES
ticket_count: 1
curated: true
self_serviceable: false
---

# Wrong Certificate Bound to Load Balancer Causing Hostname Validation Failures

[← Back to categories](../../index.md)

## Description

Internal users and automated dependent services experienced TLS failures when connecting to internal web and API endpoints through an F5 load balancer. Browser-based users encountered certificate warnings and SSL protocol errors, while automated integrations such as a payroll sync service failed with hostname mismatch and trust validation errors. The failures affected all traffic routed through the load balancer virtual IP in the affected region, even though the certificate bound to the endpoint was valid and not expired.

The root cause was that a valid certificate belonging to a different internal service had been bound to the load balancer instead of the certificate matching the expected hostnames. Because the certificate's common name did not match the requested endpoints, TLS handshake validation failed for all clients enforcing hostname verification. Some clients reported a generic expired-certificate error code rather than a hostname mismatch, depending on the TLS library and validation behavior of the connecting application.

The organization's certificate monitoring platform did not flag the condition because its checks were limited to certificate expiry rather than hostname or binding correctness. Monitoring continued to report the previous certificate chain fingerprint on the affected endpoint without raising an alert, effectively masking the misconfiguration.

!!! note "Reported variations"

    - Monitoring continued to report the old certificate chain fingerprint on the affected endpoint without raising an alert, masking the misconfiguration.
    - No change record was logged for the load balancer certificate binding during the most recent renewal window, leaving the incorrect binding undetected by change-management processes.
    - Some clients reported a generic expired-certificate error code rather than a hostname mismatch, depending on the TLS library and validation behavior of the connecting application.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** RHEL 8 (100%)
- **Device / platform:** VMs behind F5 Load Balancer (100%)
- **Team:** internal-services (100%)
- **Region:** us-east-1 (100%)

## Root cause

The F5 load balancer was updated with a current certificate that did not match the internal web service endpoint name. Although the renewal process completed successfully, the wrong certificate asset was bound to the virtual server, causing hostname validation failures for connecting clients.

## Diagnostics

Steps used to confirm this root cause:

1. Inspect the certificate presented by the Internal Web Service endpoint for expiration date and hostname alignment.  
   *Expected:* Certificate is current and matches the service endpoint name.
2. Validate the deployed certificate chain from both external client path and F5 load balancer configuration views.  
   *Expected:* Full chain validates without expired or missing intermediate certificates.
3. Review certificate monitoring alerts and renewal job history to determine whether renewal completed and whether alerting covered the LB-served chain.  
   *Expected:* Renewal alerts are active and renewal job completed before expiration.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

1. Retrieve the correct certificate (serial 9B:22:4D:EE) from the internal Certificate Authority (ca01.corplabs.internal) whose SANs include svc-portal.corplabs.internal and api-internal.corplabs.internal — the Internal Web Service and Service API endpoint names used by clients.
2. Update the F5 virtual server lb-east-vip01 SSL profile (/Common/svc-portal-ssl-profile) to use the correct certificate (CN=svc-portal.corplabs.internal, serial 9B:22:4D:EE) and retain the existing valid intermediate chain. Change applied by <USER> and verified in the F5 admin console.
3. Validate from client (<HOSTNAME>, <IP>, user <USER>) and load balancer perspectives that the presented certificate is current, matches the service hostname svc-portal.corplabs.internal, and completes TLS handshakes successfully. Confirmed no further CERT_HAS_EXPIRED or ERR_SSL_PROTOCOL_ERROR reports from the <LOCATION> office or dependent <PERSON>.
4. Extend certificate monitoring on certmon.corplabs.internal to validate hostname alignment (SAN vs. expected service FQDN) in addition to expiration and chain health. New alert rule cert-san-match-east created by <USER> and tested against lb-east-vip01.

## Recommendation

Resolved by IT; incorrect certificate binding on F5 load balancer caused TLS hostname validation failures for internal web and API endpoints.

---

[← Back to categories](../../index.md)
