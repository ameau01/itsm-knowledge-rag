---
hide:
  - navigation
root_cause_id: DRF/stale-resolver-cache-after-record-change
family: DRF
ticket_count: 23
curated: true
self_serviceable: false
---

# Stale DNS resolver cache serving outdated records after internal zone change

[← Back to categories](../../index.md)

## Description

After a recent change to an internal DNS zone record — such as an A record update following a service migration or infrastructure change — affected users experience intermittent failures when attempting to reach internal services by hostname. Lookups may return an outdated IP address pointing to a decommissioned or previous endpoint, NXDOMAIN responses indicating the hostname does not exist, SERVFAIL errors, or DNS query timeouts. These failures typically alternate unpredictably: some queries return the correct new address while others return stale data or errors, depending on which internal resolver or cache answers the request.

The issue is confined to internal name resolution through corporate recursive resolvers and caching forwarders. Direct connectivity to the service by its current IP address continues to work normally, confirming that the service itself is available and the problem lies in the DNS resolution path. Affected users are generally concentrated on specific office subnets or datacenter segments served by the resolvers that hold stale data, though multiple sites can be involved if several resolvers or downstream forwarders retain outdated cache entries.

The authoritative internal DNS zone already contains the correct, updated record. The discrepancy is between what the authoritative servers hold and what the recursive resolvers and forwarders are serving from their local caches. This mismatch can persist for an extended period — sometimes hours or longer — because the cached entries carry elevated or long-lived TTL values that delay automatic refresh. In some cases, different resolvers in the same environment return different answers, causing the issue to appear inconsistent across users and applications even within the same office.

Impact ranges from individual workstation lookup failures to broader disruption of application-to-application connectivity, CI/CD pipelines, monitoring health checks, and internal service discovery for any system that relies on hostname-based access through the affected resolver infrastructure.

!!! note "Reported variations"

    - Some resolvers serve a stale negative cache entry (cached NXDOMAIN) rather than a stale A record, causing the hostname to appear nonexistent even though the correct record exists in the authoritative zone.
    - The issue may affect only a subset of resolvers in the environment while others have already refreshed, producing a split where users on different subnets or offices see different results for the same hostname.
    - In some cases, a resolver does not honor TTL expiry or refresh behavior correctly, requiring a service restart in addition to a cache flush before it begins returning current data.
    - Downstream caching forwarders may retain stale data independently of the primary resolver, causing mixed responses to persist even after the primary resolver cache has been cleared.
    - Occasionally the authoritative zone serial number was not incremented or the zone was not fully reloaded at the time of the record change, compounding the propagation delay across resolver layers.

## Affected environment

Distribution across 23 reported cases:

- **Operating system:** Linux (17%), CentOS 7 (DNS Resolver hosts) (4%), Debian 11 (4%)
- **Device / platform:** on-premises (35%), on-prem (17%), on-premise (9%)
- **Team:** Internal Users (26%), internal-services (17%), Engineering (13%)
- **Region:** us-east-1 (35%), corp-dc-1 (13%), corp-datacenter-1 (13%)

## Root cause

After an internal DNS zone record is updated, one or more internal recursive resolvers or caching forwarders continue serving previously cached data instead of fetching the current record from the authoritative zone. This typically occurs because the cached entry has a long TTL that has not yet expired, or because the resolver did not properly refresh from the authoritative source after the zone change. The result is that clients querying different resolvers — or even the same resolver at different times — receive inconsistent answers until the stale cache entries are cleared and the resolver picks up the updated zone data.

## Diagnostics

Steps used to confirm this root cause:

1. Queried affected corp.local hostnames against the corporate resolver and compared responses with the authoritative internal DNS servers.  
   *Expected:* Both resolvers return the same current address.
2. Inspected the internal DNS zone records, TTL values, and current authoritative data for the impacted hostnames.  
   *Expected:* Zone contains the current record with expected TTL.
3. Reviewed resolver handling for the internal zone and flushed the resolver cache to clear stale entries before retesting lookups.  
   *Expected:* Forwarder routes the zone correctly and cache returns fresh data.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Flushed the stale cache entries on the primary corporate DNS resolver (dns-resolver-01.corp.local / <IP>) using rndc flush to remove outdated A records (e.g., <IP>) being returned for affected corp.local hosts including internal-portal.corp.local, service-discovery.corp.local, and inventory-api.corp.local.
2. Verified the authoritative internal DNS zone contents on ns1-auth.corp.local and ns2-auth.corp.local for impacted records and confirmed the current addresses (<IP>, <IP>, <IP>) were correct on the authoritative servers. SOA serial and zone transfer status validated between both authoritative nodes.
3. Adjusted TTL values for the affected zone records from 86400 seconds (24 hours) to 3600 seconds (1 hour) to reduce the likelihood and duration of long-lived stale cache entries after future record changes. Change approved by <PERSON> and applied to the corp.local zone on ns1-auth.corp.local.
4. Validated name resolution from representative clients — <PERSON>'s workstation <HOSTNAME> (<IP>) and <PERSON> workstation <HOSTNAME> (<IP>) — and Network Monitoring paths to confirm the resolver now returned the same current addresses as the authoritative servers. All three affected service endpoints confirmed reachable by FQDN.
5. Documented the cache validation and flush procedure (rndc flush on dns-resolver-01.corp.local) in the DNS support playbook and continued post-change monitoring via Network Monitoring for 48 hours for recurrence. Sent closure notification to <USER>@corpnet.com and <EMAIL> confirming resolution.

**Example 2**

1. Verified the correct A record value for internal-service.corp.local on the primary internal DNS zone (dns-auth-east-01.corp.local) and confirmed the record had been updated to the intended IP address <IP> by <PERSON>, replacing the decommissioned <IP>.
2. Incremented the DNS zone serial from 2026010701 to 2026010702 and reloaded the zone on the primary authoritative server dns-auth-east-01.corp.local using rndc reload so the change could propagate correctly to downstream resolvers.
3. Confirmed the zone reload and AXFR transfer/update state to secondary authoritative DNS servers (dns-auth-east-02.corp.local) handling the corp.local internal zone. Serial 2026010702 was reflected on all secondaries.
4. Flushed stale cache entries on internal BIND9 resolver instances dns-resolver-east-01.corp.local and dns-resolver-east-02.corp.local using rndc flush so resolvers would stop serving the outdated <IP> result.
5. Validated fresh resolution with dig from multiple subnets (<LOCATION>, <LOCATION>, <LOCATION>) including from <PERSON>'s workstation <HOSTNAME> and <PERSON>'s host <HOSTNAME>, and confirmed the hostname returned the expected address <IP> consistently.
6. Confirmed Network Monitoring alerts for internal-service.corp.local cleared after cache flush and zone propagation completed at 20:41 UTC, indicating full service restoration. <PERSON> notified affected application teams including <PERSON>'s order-processing group.

## Recommendation

This issue is resolved by IT support; reference 'stale DNS resolver cache after record change' when reporting it.

---

[← Back to categories](../../index.md)
