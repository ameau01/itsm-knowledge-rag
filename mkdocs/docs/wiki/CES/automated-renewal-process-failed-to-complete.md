---
hide:
  - navigation
root_cause_id: CES/automated-renewal-process-failed-to-complete
family: CES
ticket_count: 3
curated: true
self_serviceable: false
---

# Expired certificate served by load balancer after automated renewal failure

[← Back to categories](../../index.md)

## Description

Affected users attempting to access internal web services over HTTPS encounter certificate-expired warnings in their browsers, typically displaying a "NET::ERR_CERT_DATE_INVALID" error. The issue prevents normal access to the service portal and causes dependent systems — such as API gateways, integration pipelines, inventory sync services, and automated health checks — to fail TLS handshakes as well. The result is a complete loss of secure connectivity to the affected endpoint.

The issue typically becomes apparent shortly after the certificate's expiration date passes, with multiple users and teams reporting the problem at roughly the same time. Load balancer health checks against the backend pool also begin returning TLS errors, confirming that the problem is at the load balancer layer rather than on individual workstations or application servers. Browser certificate details show that the certificate's "Not After" date has lapsed, and the load balancer continues to present the expired certificate and its associated chain.

In reported cases, the outage has affected entire teams and offices simultaneously, since all HTTPS traffic to the service passes through the same load balancer. The issue persists until the certificate is renewed and the full certificate chain — including any intermediate certificates — is redeployed to the load balancer and its listener configuration is reloaded.

!!! note "Reported variations"

    - The renewal job may fail due to a permissions change (e.g., an RBAC policy update revoking the service account's access to update the load balancer), rather than a script execution failure.
    - The renewal script may execute but exit with an error code and no automatic retry, leaving the renewal incomplete without any visible alert.
    - Certificate-expiry monitoring may have been disabled weeks or months before the expiration date, removing the safety-net alert that would otherwise warn of an approaching deadline.
    - The intermediate certificate bundle on the load balancer may also be stale, requiring a full chain redeployment — not just the leaf certificate — to restore successful TLS validation for all clients.

## Affected environment

Distribution across 3 reported cases:

- **Device / platform:** on-prem Kubernetes (kubeadm) (33%), Linux nginx (33%), on-premise (33%)
- **Team:** Platform Engineers (33%), internal_services (33%), internal_apps (33%)
- **Region:** us-east-1-dc1 (33%), us-east-1 (33%), internal-dc-1 (33%)

## Root cause

The automated certificate renewal process failed to complete before the existing certificate's expiration date, and the load balancer continued serving the now-expired certificate. In some cases the renewal job encountered a permissions error (such as a revoked service account permission) that prevented it from updating the load balancer configuration; in others the renewal script failed silently without retrying. Certificate-expiry monitoring that would normally alert before the renewal window closed had been inadvertently disabled, so no pre-expiry warning was generated and the missed renewal went unnoticed until users began experiencing TLS errors.

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

**Example 1**

1. Issued a replacement TLS certificate from the internal Certificate Authority for internal-web.svc.cluster.local and exported the full certificate chain (new serial 5B:A1:09:EE:44:C7), performed by <PERSON> (<USER>, <EMP_ID>).
2. Uploaded and applied the renewed certificate chain to the internal load balancer instance LB-EAST-01 serving the service endpoint, replacing the expired leaf certificate serial 3A:7F:02:CB:91:DE.
3. Reloaded the load balancer configuration on LB-EAST-01 so the new certificate chain was presented to clients, verified by <USER> at 05:42 UTC.
4. Validated successful TLS handshakes from internal clients including workstation <HOSTNAME> (<IP>) and <HOSTNAME>, and browser access by <PERSON> and <PERSON>, confirming the expired certificate warning was cleared.
5. Corrected the renewal automation permissions so the service account svc-<PERSON> can update load balancer configuration on LB-EAST-01, reverting the RBAC change made by <USER>, then tested the renewal workflow with a dry run and restored certificate expiry monitoring with alerts routed to <EMAIL>.

**Example 2**

1. Obtain an emergency reissued certificate for internal.example.com from the Certificate Authority (CERTOPS-8841) after confirming the previous certificate (serial 3A:F2:9C:01) had expired on 2025-12-14. Emergency issuance approved by <PERSON> (<EMAIL>) and new certificate generated with <PERSON> of 2026-12-14.
2. Deploy the renewed server certificate and complete intermediate chain (including updated corplabs-intermediate-g3.crt) to lb-int-01 (<IP>), then reload the nginx TLS configuration via 'nginx -s reload' to apply the new certificate bundle without full service restart.
3. Validate the endpoint from the client side (tested from <IP> and <HOSTNAME>) and load balancer side to confirm the presented certificate subject matches internal.example.com, the expiration date is 2026-12-14, and TLS handshakes succeed without date warnings. <PERSON> confirmed user-facing access restored from the <LOCATION> office.
4. Restore the cert-renewal scheduler by correcting the failed renewal execution path in /opt/certops/renew.sh (API endpoint URL had been changed without updating the script), confirming the next automated renewal cycle is scheduled for 2026-11-14, and assigning renewal ownership to <USER> (<EMP_ID>) with backup to <USER>.
5. Re-enable the cert_expiry_warning monitoring alert rule and test certificate expiration monitoring and alert escalation so future renewal failures or near-expiry conditions generate actionable notifications to the cert<EMAIL> distribution list and on-call pager for the <LOCATION> infrastructure team.
6. Update the certificate deployment and renewal runbook (RUNBOOK-CERT-017) to require post-deployment chain validation on the load balancer using openssl verify, tracked renewal ownership with named assignee, and mandatory 30/14/7-day expiry alert checkpoints.

## Recommendation

This issue is resolved by IT support; reference "automated renewal process failed to complete" when reporting it.

---

[← Back to categories](../../index.md)
