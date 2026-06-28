---
hide:
  - navigation
root_cause_id: DRF/missing-or-incorrect-conditional-forwarder
family: DRF
ticket_count: 13
curated: true
self_serviceable: false
---

# Missing or Incorrect Conditional Forwarder on Internal DNS Resolver

[← Back to categories](../../index.md)

## Description

Affected users experience intermittent DNS resolution failures when looking up internal hostnames through specific corporate resolvers. Queries return NXDOMAIN, SERVFAIL, or time out, while the same records resolve successfully against the authoritative internal DNS servers or from other subnets and office locations. Direct access to services by IP address succeeds in all cases, confirming that underlying applications and network paths are healthy. The failures disrupt internal dashboards, authentication endpoints, API gateways, CI/CD pipelines, automated deployments, and service-discovery workflows, often initially appearing to be application outages rather than DNS issues.

The inconsistency is resolver-specific and often subnet-specific: one internal recursive resolver returns correct results while another serving a different subnet or site returns negative or stale responses for the same hostname. In some cases, a public resolver returns a valid address while corporate resolvers fail. Affected users in multiple offices may observe different failure modes simultaneously — some receiving NXDOMAIN, others experiencing timeouts or stale A records pointing to outdated IP addresses — contributing to confusion about the scope of the outage.

The root cause is a missing, outdated, or partially incorrect conditional forwarder configuration on the affected resolver. The forwarder may be absent entirely, may reference a decommissioned upstream server, or may inconsistently forward the internal zone. Stale negative-cache entries compound the problem, causing the resolver to continue serving incorrect responses even after authoritative zone data is correct. Once forwarder targets are corrected and resolver caches flushed, name resolution returns to normal across affected hosts and subnets.

!!! note "Reported variations"

    - In some cases the resolver round-robins between a valid and a decommissioned forwarder target, causing approximately 20–30% of queries to fail while the remainder succeed, producing partial rather than total resolution failure.
    - Certain incidents present with stale cached IP addresses (resolving to an older, incorrect IP) rather than NXDOMAIN, causing connections to fail silently against the old endpoint.
    - A cache flush alone may not resolve the issue if the stale or missing forwarder entry remains in place, as the resolver re-caches negative responses on subsequent queries to the dead target.
    - The failure may affect multiple internal zones or hostnames simultaneously when the conditional forwarder covers a parent domain, broadening the blast radius beyond a single service record.
    - Cross-site impact has been observed when multiple office locations share the same misconfigured resolver instance, causing geographically dispersed users to report identical symptoms independently.
    - SERVFAIL spikes were observed in network monitoring during the resolution failure window, correlating with the resolver misconfiguration.
    - Automated deployments and CI/CD pipelines were blocked in one incident due to intermittent NXDOMAIN responses for an internal service hostname.
    - The issue may emerge following scheduled DNS record updates or maintenance windows, with certain resolvers continuing to serve outdated or negative responses after authoritative zone data has been corrected.

## Affected environment

Distribution across 13 reported cases:

- **Operating system:** Linux (bind9 resolvers) (8%)
- **Device / platform:** on-premises (31%), on-prem (31%), on-premise (15%)
- **Team:** internal_services (31%), internal-devs (15%), Internal Apps (8%)
- **Region:** us-east-1 (38%), corp-datacenter-1 (15%), us-east-1-datacenter-1 (8%)

## Root cause

One or more internal DNS resolvers had a missing, outdated, or incorrectly configured conditional forwarder for the affected internal zone. This caused queries to be routed incorrectly — returning NXDOMAIN, SERVFAIL, timeouts, or stale cached records — while other resolvers with correct forwarder configurations continued to return the authoritative answer. Stale negative-cache entries on affected resolvers perpetuated the failures until both the forwarder configuration and cache state were corrected.

## Diagnostics

Steps used to confirm this root cause:

1. Query app-db.internal from the resolver used by <IP>/24 and compare it with a known-good internal resolver path.  
   *Expected:* Both resolvers return the same current address.
2. Inspect the internal DNS zone record presence, TTL, and recent change history for app-db.internal.  
   *Expected:* Zone contains the current record with expected TTL.
3. Check the affected resolver's conditional forwarder behavior and clear stale cached responses for the internal zone.  
   *Expected:* Forwarder routes the zone correctly and cache returns fresh data.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Confirmed the authoritative DNS zone on ns1.corp.local and ns2.corp.local for service1.corp.local contained the intended current A record (<IP>) and verified the low TTL (300s) and recent record change by <USER> on 2026-01-11T21:47Z were correct.
2. Compared responses from authoritative servers (ns1.corp.local, ns2.corp.local), known-good recursive resolver dns-resolver-03.corp.local, and the affected resolver cluster (dns-resolver-01.corp.local, dns-resolver-02.corp.local) to isolate inconsistent behavior to internal recursive resolution in the <LOCATION> datacenter rather than the zone itself.
3. Added the missing conditional forwarder configuration for the corp.local zone on dns-resolver-02.corp.local (<IP>) so requests for the internal zone were routed to the correct authoritative path (ns1.corp.local, ns2.corp.local). Change performed by <PERSON> (<USER>) and verified by <PERSON>.
4. Flushed caches on dns-resolver-01.corp.local (<IP>) and dns-resolver-02.corp.local (<IP>) using rndc flush to remove stale positive and negative cached entries that were continuing to return NXDOMAIN and timeouts after the record change. Verified cache clear via rndc dumpdb on both nodes.
5. Validated successful resolution of service1.corp.local from all monitored subnets — confirmed from <USER>'s workstation at <IP>, <USER>'s host at <IP>, and additional test clients on <IP>/16 that all clients now received the same current address (<IP>) consistently.
6. Continued monitoring via Network Monitoring dashboards after the change and performed staggered follow-up cache clearing on secondary caching layers where residual historical cache entries still produced intermittent lookup failures. <PERSON> confirmed full resolution stability at 2026-01-12T14:30Z and notified <USER> and <USER> via email.

**Example 2**

1. Validated that the authoritative DNS server dns-auth-01.internal.corp (<IP>) for the internal zone returned the expected A record for service.internal.corp (<IP>, TTL 300) and confirmed the issue was isolated to recursive resolver <IP> behavior rather than a missing zone record. Verification performed by <PERSON> from the <LOCATION> network monitoring host.
2. Reviewed and corrected the conditional forwarder path for the internal zone on resolver <IP> — removed stale secondary forwarder target <IP> (decommissioned) so queries for service.internal.corp consistently routed only to the valid authoritative DNS server dns-auth-01.internal.corp (<IP>).
3. Cleared stale cached entries and negative cache data (rndc flush) on the affected internal resolver <IP> after the forwarder configuration was corrected, ensuring no residual NXDOMAIN responses persisted from the decommissioned target.
4. Retested repeated lookups for service.internal.corp from the affected resolver and from multiple client locations — including <PERSON>'s workstation <HOSTNAME> (<IP>, <LOCATION>) and <PERSON>'s machine <HOSTNAME> (<LOCATION>) — to confirm the resolver now returned <IP> consistently without NXDOMAIN or timeout responses. 100/100 queries succeeded.
5. Monitored resolver and DNS query behavior via Network Monitoring dashboards for 2 hours after the change to verify timeout spikes stopped and internal applications (internal-service-api, developer-portal) could consistently resolve the service endpoint. Confirmed with <PERSON> (<EMAIL>) that CI/CD pipeline and portal access were fully restored.

## Recommendation

Resolved by IT after correcting the conditional forwarder configuration on the affected internal DNS resolvers and flushing stale cached entries.

---

[← Back to categories](../../index.md)
