---
hide:
  - navigation
root_cause_id: CES/renewed-chain-not-deployed-to-lb-with-monitoring-gap
family: CES
ticket_count: 46
curated: true
self_serviceable: false
---

# Expired certificate persisted on load balancer due to incomplete chain deployment and monitoring gap

[← Back to categories](../../index.md)

## Description

Affected users attempting to access the internal web service over HTTPS encounter browser certificate warnings — most commonly NET::ERR_CERT_DATE_INVALID or ERR_CERT_DATE_INVALID — and are unable to load the service securely. Automated health checks, CI/CD pipelines, and service-to-service API calls routed through the load balancer also fail during the TLS handshake, often returning 502, 523, or 525 errors. The service appears completely unavailable over HTTPS for all users and systems that rely on the load-balanced endpoint.

In many cases, a certificate renewal has already been performed at the internal Certificate Authority, and the renewed certificate may even be available on the backend service or in the CA store. However, the load balancer continues to present the old, expired certificate and an outdated or incomplete certificate chain to connecting clients. As a result, even after an initial remediation attempt targeting the backend or the leaf certificate alone, users and monitoring continue to report the same TLS failures. The issue can persist or reappear after a partial fix if the full certificate chain — including the current intermediate certificate — is not deployed to all load balancer nodes.

The outage is typically widespread, affecting users across multiple offices and network segments simultaneously, as well as automated systems such as monitoring probes, integration test runners, and deployment pipelines. Reports often come from several teams at once, and the scope of impact may include downstream services that depend on the internal web service endpoint for authenticated or encrypted communication. In environments with multiple load balancer nodes, the issue may present intermittently if some nodes received the updated certificate while others did not.

!!! note "Reported variations"

    - In some instances, the renewed leaf certificate was deployed to the backend service but not to the load balancer, causing the outage to persist or reappear after an initial fix was reported as complete.
    - In multi-node load balancer environments, the renewed certificate chain was deployed to some nodes but not all, resulting in intermittent TLS failures depending on which node handled a given request.
    - In certain cases, the certificate renewal job completed at the Certificate Authority but the deployment automation did not execute for the current renewal cycle, leaving the load balancer configuration unchanged.
    - Some incidents involved a monitoring suppression filter or a misconfigured alerting threshold (e.g., set to zero days) that specifically prevented the pre-expiry notification from reaching the responsible team.
    - Restarting or reloading the load balancer process alone did not resolve the issue when the renewed certificate bundle had never been staged on the load balancer filesystem or referenced in its configuration.

## Affected environment

Distribution across 46 reported cases:

- **Operating system:** linux (15%), RHEL 8 (4%), Ubuntu 20.04 (4%)
- **Device / platform:** on-premises (15%), Kubernetes (15%), on-prem load balancer (F5) (4%)
- **Team:** internal_services (33%), internal-developers (13%), internal_users (13%)
- **Region:** us-east-1 (67%), us-east-1-dc1 (7%), us-central-1 (private) (4%)

## Root cause

The TLS certificate for the internal web service expired, and the renewed certificate along with the full updated certificate chain was not deployed to the load balancer that terminates TLS for client connections. The load balancer continued presenting the old expired certificate and stale intermediate chain to all connecting clients. Certificate expiry monitoring and renewal alerting were either misconfigured, suppressed, or inactive, so no advance warning was raised before the expiration date, allowing the outage to occur without preemptive intervention.

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

This issue is resolved by IT support; reference 'expired certificate not deployed to load balancer with monitoring gap' when reporting it.

---

[← Back to categories](../../index.md)
