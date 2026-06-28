---
hide:
  - navigation
root_cause_id: DRF/stale-resolver-cache-after-record-change
family: DRF
ticket_count: 23
curated: true
self_serviceable: false
---

# Stale Resolver Cache Serving Outdated Records After Internal Zone Update

[← Back to categories](../../index.md)

## Description

After an internal DNS zone record change — such as an A record update during a service or infrastructure migration — affected users and dependent services experience intermittent name-resolution failures for internal hostnames. Lookups against corporate recursive resolvers return a mix of outdated A records (pointing to previous or decommissioned IP addresses), NXDOMAIN errors, SERVFAIL responses, and timeouts, even though the authoritative DNS servers already reflect the correct, updated entry. Direct IP connectivity to the target service remains functional, confirming the issue is confined to DNS name resolution.

The behavior is resolver-specific: one resolver in the environment may return the expected record while another continues to serve stale cached data, causing inconsistent results depending on which resolver handles a given query. Some clients observe correct and incorrect answers alternating on repeated lookups. The inconsistency typically spans multiple subnets, office locations, or datacenter segments served by overlapping resolver infrastructure, creating partial-outage conditions.

The impact extends beyond individual users to CI/CD pipelines, automated service-to-service communication, health-check and monitoring systems, internal service registries, and any system relying on hostname-based lookups. Investigation consistently reveals a mismatch between cached entries on one or more recursive resolvers and the current authoritative zone data, with resolver cache metadata showing entries last refreshed before the zone update. In some cases, resolver latency spikes and timeouts of 30–60 seconds accompany the stale responses.

!!! note "Reported variations"

    - Some resolvers return NXDOMAIN or SERVFAIL rather than a stale A record, particularly when the resolver holds a cached negative response from a brief zone transfer hiccup.
    - Caching forwarders downstream of the primary resolver continue serving stale data even after the primary resolver cache has been cleared, requiring independent cache flushes on each downstream node.
    - A resolver fails to honor TTL refresh behavior correctly, requiring a full service restart rather than a simple cache flush to begin returning current records.
    - Records with very high TTL values (e.g., 86400 seconds) tied to decommissioned hosts persist in resolver caches long after the zone has been updated.
    - Some clients observe a mix of correct and incorrect responses on repeated queries, with stale answers appearing intermittently rather than consistently.
    - The stale resolution issue spans multiple office locations and datacenter segments when those sites share overlapping resolver infrastructure.
    - An aggressive caching policy or long-running resolver process (without restart) prevents cache entries from being refreshed on schedule.
    - Automated health checks, monitoring platforms, and dependent service registries co-report the resolution failures alongside end-user reports.

## Affected environment

Distribution across 23 reported cases:

- **Operating system:** Linux (17%), CentOS 7 (DNS Resolver hosts) (4%), Debian 11 (4%)
- **Device / platform:** on-premises (35%), on-prem (17%), on-premise (9%)
- **Team:** Internal Users (26%), internal-services (17%), Engineering (13%)
- **Region:** us-east-1 (35%), corp-dc-1 (13%), corp-datacenter-1 (13%)

## Root cause

Internal DNS recursive resolvers retained stale cached A records after the authoritative internal zone was updated, continuing to serve outdated or negative-cached responses instead of fetching the current record. High TTL values on the original cached entries prevented resolvers from re-fetching the updated record within a reasonable window after the change, prolonging the staleness period.

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

Resolved by IT flushing stale cache entries on affected internal resolver infrastructure and, where necessary, reloading the authoritative zone or restarting the resolver service, after which lookups returned the correct authoritative address and application connectivity was restored.

---

[← Back to categories](../../index.md)
