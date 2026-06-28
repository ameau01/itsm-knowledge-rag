---
hide:
  - navigation
root_cause_id: CES/renewed-chain-not-deployed-to-lb-with-monitoring-gap
family: CES
ticket_count: 46
curated: true
self_serviceable: false
---

# Renewed Certificate Chain Not Deployed to Load Balancer Before Expiry

[← Back to categories](../../index.md)

## Description

Affected users attempting to access internal web services over HTTPS encountered browser certificate warnings — most commonly NET::ERR_CERT_DATE_INVALID and ERR_CERT_DATE_INVALID — along with TLS handshake failures that rendered services unreachable. The issue was reported across multiple offices and internal networks simultaneously, affecting both interactive browser sessions and programmatic clients such as CI/CD pipelines, API consumers, health-check monitors, and service-to-service integrations. Dependent systems experienced cascading failures including 502/523/525 HTTP errors, broken automation workflows, and disrupted business-critical applications such as payroll and inventory management.

Investigation consistently revealed that the load balancer fronting the affected service continued to present an expired leaf certificate and an outdated or incomplete intermediate certificate chain, even though a renewed certificate had already been issued by the internal Certificate Authority. The renewed certificate and full chain were never successfully deployed to the load balancer's TLS termination configuration. In some cases a prior deployment attempt had been reported as complete but no corresponding configuration change existed on the load balancer. Restarting or reloading the load balancer service alone did not resolve the issue, as the listener configuration still referenced the old certificate material.

A contributing factor across these incidents was a gap in certificate expiration monitoring. Pre-expiry alerting rules had been inadvertently disabled, suppressed, or misconfigured — in some cases during a prior maintenance window — so no advance warning was generated before the certificate expired. This monitoring gap allowed the incomplete deployment to go undetected until users and automated probes began reporting TLS failures.

!!! note "Reported variations"

    - In one instance, only the renewed leaf certificate was deployed to the load balancer while the intermediate CA bundle was omitted, resulting in an incomplete trust chain rather than a fully expired certificate.
    - In one case, the renewed certificate was inconsistently deployed across a multi-node load balancer cluster, causing intermittent TLS failures depending on which node handled the request.
    - In one incident, the initial certificate bundle import to the load balancer failed due to incorrect chain ordering; the intermediate CA certificate had to be reordered before the root certificate for the reload to succeed.
    - Some incidents involved the expired certificate appearing on both the load balancer and the direct backend application port, indicating the stale certificate was present at multiple layers.
    - One environment used a Kubernetes ingress controller with a TLS secret still referencing the expired certificate bundle, rather than a traditional load balancer binding.
    - The monitoring suppression mechanism varied: in some cases a prior maintenance window disabled the alerting rule, while in others a misconfigured threshold or manually added filter suppressed the alert.
    - Downstream impacts ranged from CI/CD pipeline failures and blocked sprint deployments to disrupted payroll integrations and internal API authentication failures.
    - Certain incidents were first detected by automated Nagios health checks or synthetic monitoring probes rather than by end-user reports.

## Affected environment

Distribution across 46 reported cases:

- **Operating system:** linux (15%), RHEL 8 (4%), Ubuntu 20.04 (4%)
- **Device / platform:** on-premises (15%), Kubernetes (15%), on-prem load balancer (F5) (4%)
- **Team:** internal_services (33%), internal-developers (13%), internal_users (13%)
- **Region:** us-east-1 (67%), us-east-1-dc1 (7%), us-central-1 (private) (4%)

## Root cause

The TLS certificate for the internal web service expired, and the renewed certificate along with its full chain from the internal Certificate Authority was not deployed to the load balancer's TLS termination configuration. The load balancer continued serving the expired leaf certificate and stale intermediate chain to clients. Certificate expiration monitoring and renewal alerting were inactive, misconfigured, or suppressed, preventing advance warning and allowing the deployment gap to persist until service impact occurred.

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

1. Requested and obtained a renewed TLS certificate for internal.web.internal from the internal Certificate Authority (serial 8B:12:D4:F7, valid 2025-12-13 through 2026-12-13) before restoring service. The CSR was generated by <USER> and approved by the PKI team lead <PERSON> (<USER>, <EMP_ID>).
2. Installed the renewed leaf certificate and full intermediate certificate chain on the production load balancer that terminates TLS for the internal web service. The certificate bundle was deployed to LB-PROD-F5-01 (<IP>) by <USER> at 11:40 UTC, replacing the expired leaf (serial 4A:7C:3E:91) and outdated intermediate with the current chain from the internal CA vault.
3. Reloaded the load balancer TLS listener so the endpoint stopped presenting the expired certificate and began serving the updated chain. The reload was executed on LB-PROD-F5-01 at 11:42 UTC with zero dropped connections using the graceful reload procedure.
4. Validated the HTTPS endpoint from multiple internal client perspectives to confirm the certificate subject matched the service name and the handshake completed successfully. Verification was performed from <HOSTNAME> (<IP>, user <USER>) in the <LOCATION> office and from a test host in <LOCATION> (<IP>, user <USER>), both returning valid certificate chains with no warnings.
5. Re-enabled and tested certificate expiry monitoring and renewal alerting so future notifications trigger ahead of the renewal window. The alert rule for internal.web.internal was restored in the monitoring platform with 30-day and 7-day expiry thresholds, and test notifications were confirmed delivered to <EMAIL> and the on-call channel.

**Example 2**

1. Renewed the TLS certificate with the internal Certificate Authority (ca.corplabs.internal) and obtained the correct full certificate chain — including the updated CorpLabs Internal CA G2 intermediate — for the Internal Web Service endpoint portal.internal.corplabs.com. New certificate serial: 5B:9D:4F:02:CC, notAfter 2026-12-16T23:59:59Z.
2. Replaced the expired certificate and chain bundle at /etc/haproxy/certs/portal-chain.pem on the HAProxy load balancer lb-haproxy-east-01.corplabs.internal, ensuring the active bind listener on port 443 referenced the updated files rather than stale certificate material. Deployment performed by <PERSON> (<USER>, <EMP_ID>).
3. <PERSON> (systemctl reload haproxy) after deployment on lb-haproxy-east-01.corplabs.internal and verified the service was presenting the renewed leaf certificate (CN=portal.internal.corplabs.com, serial 5B:9D:4F:02:CC) together with the required CorpLabs Internal CA G2 intermediate chain via openssl s_client.
4. Validated successful TLS handshakes from client perspective — confirmed from <HOSTNAME> (<IP>, user <USER>) and <USER>'s workstation in <LOCATION> — and confirmed certificate warnings and expiry-related handshake failures were cleared for the affected endpoint https://portal.internal.corplabs.com.
5. Reviewed and restored certificate renewal monitoring and alerting in Nagios: re-enabled the 'TLS Cert - portal.internal.corplabs.com' check, set threshold to alert at 30 days before expiry, and confirmed notification routing to <EMAIL> and <EMAIL> so future expiration and renewal failures generate actionable alerts before the renewal window closes.

## Recommendation

Resolved by IT; expired TLS certificate and stale chain on load balancer replaced with renewed full certificate chain after deployment gap and monitoring alert failure were identified.

---

[← Back to categories](../../index.md)
