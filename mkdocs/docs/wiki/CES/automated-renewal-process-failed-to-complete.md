---
hide:
  - navigation
root_cause_id: CES/automated-renewal-process-failed-to-complete
family: CES
ticket_count: 3
curated: true
self_serviceable: false
---

# Expired Certificate on Load Balancer After Automated Renewal Failure

[← Back to categories](../../index.md)

## Description

Affected users and dependent internal systems experience TLS handshake failures when attempting to connect to internal web services over HTTPS. Browsers display certificate date warnings (typically "NET::ERR_CERT_DATE_INVALID") when navigating to the service URL, and automated API calls, integration pipelines, health checks, and inventory sync processes that rely on the same endpoints begin failing TLS validation simultaneously. The affected internal web service is effectively unavailable over secure access for all clients hitting the endpoint.

Investigation reveals that the organization's load balancer is presenting an expired certificate for the internal service. The certificate's validity period has lapsed, and the full certificate chain — including the leaf certificate and any intermediate CA bundles — remains stale on the load balancer. OpenSSL client checks from diagnostic hosts confirm that the certificate common name and subject alternative name entries match the service, but the expiration date has passed. Multiple workstations and automated systems across affected offices reproduce the error.

The root cause traces back to the automated certificate renewal process failing to complete before the expiration date. In some cases the renewal job encountered an access-denied error due to permissions being revoked during a recent RBAC policy change; in others the renewal script returned a non-zero exit code on its last attempted invocation without triggering any notification. A contributing factor across all incidents is that certificate expiry monitoring or alerting had been disabled — often weeks or months prior to the expiration — as a result of a configuration change, so no pre-expiry warning was generated to prompt manual intervention.

!!! note "Reported variations"

    - The automated renewal job failed specifically because its service account lost required permissions following an RBAC policy update, resulting in an "access denied" error when pushing the renewed chain to the load balancer.
    - The renewal script executed but returned a non-zero exit code without generating an alert, and no subsequent retry was attempted before the certificate expired.
    - The certificate expiry alerting rule was found to have been explicitly disabled weeks or months before the expiration event, preventing any pre-expiry notification from being raised.
    - Load balancer health checks against backend pools reported TLS errors, compounding the outage by marking backends as unhealthy in addition to blocking direct user access.
    - Dependent automated workflows — such as inventory sync services, DevOps integration pipelines, and monitoring dashboards — failed alongside browser-based access due to strict TLS validation.

## Affected environment

Distribution across 3 reported cases:

- **Device / platform:** on-prem Kubernetes (kubeadm) (33%), Linux nginx (33%), on-premise (33%)
- **Team:** Platform Engineers (33%), internal_services (33%), internal_apps (33%)
- **Region:** us-east-1-dc1 (33%), us-east-1 (33%), internal-dc-1 (33%)

## Root cause

The TLS certificate for an internal service expired on the load balancer because the automated renewal process failed to complete. The renewal job was unable to update the load balancer configuration due to missing permissions (access denied) following an RBAC policy change, and certificate expiry monitoring had been disabled, so no pre-expiry alert was raised to prompt manual remediation.

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

Resolved by IT after reauthorizing the renewal service account, deploying the renewed certificate chain to the load balancer, and re-enabling certificate expiry alerting.

---

[← Back to categories](../../index.md)
