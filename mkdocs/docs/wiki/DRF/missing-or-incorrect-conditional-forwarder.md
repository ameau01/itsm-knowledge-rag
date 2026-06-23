---
hide:
  - navigation
root_cause_id: DRF/missing-or-incorrect-conditional-forwarder
family: DRF
ticket_count: 13
curated: true
self_serviceable: false
---

# Missing or incorrect conditional forwarder causing intermittent internal DNS failures

[← Back to categories](../../index.md)

## Description

Affected users experience intermittent failures when attempting to reach internal services by hostname. DNS lookups against corporate resolvers return a mix of NXDOMAIN responses, timeouts, SERVFAIL errors, or outdated IP addresses, while the same hostnames resolve correctly when queried directly against the authoritative internal DNS server or from other network segments. The failures typically affect users on specific subnets or office locations rather than the entire organization, and colleagues in other parts of the network often confirm that the same hostnames resolve without issue from their side.

The inconsistency can manifest in several ways. Some users see only NXDOMAIN errors, while others receive stale addresses pointing to decommissioned or retired service IPs. In some cases, repeated lookups from the same workstation alternate between successful and failed responses. Applications and automated workflows that depend on internal hostname resolution — such as CI/CD pipelines, API gateways, batch processing, and service-discovery systems — may experience connection failures, authentication timeouts, or degraded functionality even though the underlying service remains reachable by direct IP address.

The issue often surfaces after infrastructure changes such as DNS record updates, resolver maintenance windows, or the decommissioning of upstream DNS servers, though it may also appear without a clearly visible triggering event from the affected user's perspective. Impact can span multiple office locations and subnets if more than one resolver is affected, and the intermittent nature of the failures can make the problem difficult to confirm without comparing results across different resolver paths.

!!! note "Reported variations"

    - Some resolvers return a previously valid but now retired IP address instead of NXDOMAIN, causing connections to silently fail or reach a decommissioned host rather than producing an obvious lookup error.
    - The issue may affect both primary and secondary resolvers simultaneously if the conditional forwarder was removed or never added on both, resulting in broader impact across subnets and sites.
    - A cache flush alone may not fully resolve the problem; if the underlying forwarder entry remains missing or incorrect, the resolver re-caches negative responses and failures resume shortly after the flush.
    - Domain controller resolvers serving the corporate Active Directory forwarding path may be independently affected, producing SERVFAIL spikes alongside NXDOMAIN from standard resolvers.
    - Public or external DNS resolvers may return valid addresses for the same hostname while internal resolvers fail, leading users to suspect an internal network or application outage rather than a DNS configuration issue.

## Affected environment

Distribution across 13 reported cases:

- **Operating system:** Linux (bind9 resolvers) (8%)
- **Device / platform:** on-premises (31%), on-prem (31%), on-premise (15%)
- **Team:** internal_services (31%), internal-devs (15%), Internal Apps (8%)
- **Region:** us-east-1 (38%), corp-datacenter-1 (15%), us-east-1-datacenter-1 (8%)

## Root cause

One or more internal DNS resolvers are missing the required conditional forwarder for the affected internal zone, or the forwarder is pointing to an outdated or decommissioned upstream server. Without a correct forwarding path, queries routed through those resolvers never reach the authoritative DNS server that holds the current record. The resolver then caches the resulting negative or incorrect response, causing it to continue serving stale NXDOMAIN or outdated address answers to clients even after the underlying issue is identified, until both the forwarding configuration and the cached entries are corrected.

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

This issue is resolved by IT support; reference 'missing or incorrect conditional forwarder – internal DNS resolution failure' when reporting it.

---

[← Back to categories](../../index.md)
