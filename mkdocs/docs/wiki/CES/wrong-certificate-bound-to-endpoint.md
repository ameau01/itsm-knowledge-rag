---
hide:
  - navigation
root_cause_id: CES/wrong-certificate-bound-to-endpoint
family: CES
ticket_count: 1
curated: true
self_serviceable: false
---

# Mismatched certificate bound to load balancer causing hostname validation failures

[← Back to categories](../../index.md)

## Description

Affected users attempting to access internal web services through the load balancer encountered TLS certificate warnings and connection errors. The issue presented differently depending on the client: some users saw browser-level certificate warnings, while others experienced outright connection failures with hostname mismatch or trust validation errors such as ERR_SSL_PROTOCOL_ERROR. The affected endpoints included both the internal web portal and the service API, and the issue also disrupted automated integrations such as the payroll sync service.

The outage occurred despite a recent certificate deployment that the service team believed had completed successfully. Monitoring systems did not flag the problem because they were configured to check for certificate expiration only, not for hostname mismatches. As a result, the incorrect binding went undetected until end users and dependent services began reporting failures.

Initial reports were escalated from an office user through the infrastructure on-call channel. Investigation confirmed that the load balancer was serving a valid certificate, but one that belonged to a different internal service, causing hostname validation to fail for all clients connecting to the affected endpoints.

!!! note "Reported variations"

    - Some clients displayed browser certificate warnings while others failed outright with protocol-level errors such as ERR_SSL_PROTOCOL_ERROR, depending on the client's TLS validation behavior.
    - Automated service integrations (e.g., payroll sync) failed silently or with trust validation errors rather than producing user-visible warnings.
    - Multiple hostnames served through the same load balancer virtual server were affected simultaneously because they all relied on the same certificate binding.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** RHEL 8 (100%)
- **Device / platform:** VMs behind F5 Load Balancer (100%)
- **Team:** internal-services (100%)
- **Region:** us-east-1 (100%)

## Root cause

The load balancer was updated with a valid, current certificate, but the certificate that was bound to the virtual server belonged to a different internal service. Because the certificate's common name did not match the hostnames of the endpoints being served, clients rejected the connection with hostname mismatch errors. The organization's certificate monitoring system did not detect the problem because it was configured to alert only on certificate expiration, not on hostname mismatches.

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

This issue is resolved by IT support; reference 'wrong certificate bound to load balancer endpoint' when reporting it.

---

[← Back to categories](../../index.md)
