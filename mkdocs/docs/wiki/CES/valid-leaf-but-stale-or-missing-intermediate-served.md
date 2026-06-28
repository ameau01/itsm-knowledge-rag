---
hide:
  - navigation
root_cause_id: CES/valid-leaf-but-stale-or-missing-intermediate-served
family: CES
ticket_count: 5
curated: true
self_serviceable: false
---

# Expired or Incomplete TLS Certificate Chain Served by Load Balancer

[← Back to categories](../../index.md)

## Description

Affected users attempting to access internal web services over HTTPS encounter TLS certificate errors that prevent normal connectivity. Browsers display certificate date-invalid warnings (such as NET::ERR_CERT_DATE_INVALID), while automated clients, API integrations, and backend monitoring services fail during the TLS handshake. The errors originate from load balancers serving certificate chains that are expired or incomplete — either the leaf certificate has passed its validity date, the intermediate certificate in the served chain is expired or missing, or both conditions are present simultaneously. Reports typically surface from multiple users and teams across affected offices, with both interactive browser sessions and automated service accounts unable to establish trusted connections.

The issue manifests as a complete or near-complete loss of HTTPS access to the affected internal service endpoint. Load balancer logs confirm chain validation errors and certificate date-invalid conditions beginning at the time of the reported outage. In some cases, certificate-management alerting that should have flagged upcoming expirations did not fire, meaning the expiration went undetected until users and dependent systems began failing. The disruption affects all internal clients connecting through the impacted load balancer virtual server, spanning workstations and automated integration hosts alike.

The condition persists — blocking normal internal application access for affected user groups — until the certificate chain served by the load balancer is corrected and the updated profile is active. In at least one case, the impact extended to approximately 40 interactive users and 12 automated service accounts across a regional deployment.

!!! note "Reported variations"

    - In one instance, the leaf certificate itself remained valid, but the load balancer continued to serve an expired intermediate certificate following a recent renewal effort, causing the service to remain intermittently inaccessible until the corrected certificate bundle was applied to the load balancer's SSL profile.
    - Some cases involved the intermediate certificate being entirely absent from the served chain rather than expired, resulting in both date-validity and chain-trust failures reported by clients.
    - In certain environments, the initial chain update attempt on the load balancer failed because the correct intermediate certificate file was not available in the deployment bundle, prolonging the outage beyond the first remediation effort.
    - Certificate-management monitoring rules were found to be misconfigured in at least one case, with incorrect alerting thresholds that prevented proactive detection of the approaching certificate expiration.

## Affected environment

Distribution across 5 reported cases:

- **Operating system:** Linux (20%)
- **Device / platform:** on-premises VMware (20%), Linux (containerized) (20%), On-prem F5 Load Balancer and internal web VM pool (20%)
- **Team:** internal-services (40%), internal_services_team (20%), Internal Employees (20%)
- **Region:** us-east-1 (60%), us-central-1 (private) (20%), us-central (20%)

## Root cause

The internal web service outage was caused by an expired CA-issued leaf TLS certificate combined with an outdated or missing intermediate certificate in the chain served by the load balancer. Certificate monitoring and renewal alerting failed to trigger before expiration, and in some cases a renewed leaf certificate was not properly installed or the deployment bundle lacked the correct intermediate certificate, leaving the load balancer presenting an incomplete or invalid chain.

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

1. Obtain a re-issued valid TLS certificate for the Internal Web Service from the internal Certificate Authority, ensuring the certificate SAN matches internal-web.corplabs.internal. Re-issuance was requested by <PERSON> (<USER>) and approved by <PERSON>.
2. Deploy the renewed certificate and private key to the Internal Web Service containers in the <LOCATION> data center and reload the service so it presents the new non-expired certificate (new notAfter: 2026-12-17T23:59:59Z).
3. Update the Load Balancer LB-EAST-02.corplabs.internal to include the correct intermediate certificate chain issued 2025-11-30, then reload the listener configuration so clients receive the full chain. Performed by <PERSON>.
4. Validate the HTTPS endpoint from both service-side and client-side perspectives to confirm the certificate is current, the chain is complete, and TLS handshakes succeed without browser warnings. <PERSON> confirmed access restored from <HOSTNAME> and <PERSON> confirmed from her workstation.
5. Restore and test certificate monitoring alerts and the automated renewal workflow so expiration and renewal failures are detected before the next renewal window. Alert rule for internal-web.corplabs.internal re-enabled and verified by <PERSON>; test alert fired successfully at 2025-12-18T20:15:00Z.

## Recommendation

Resolved by IT after updating the certificate chain and SSL profile on the affected load balancer; reference: expired or incomplete TLS chain on load balancer causing internal HTTPS service outage.

---

[← Back to categories](../../index.md)
