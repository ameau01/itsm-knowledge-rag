---
hide:
  - navigation
root_cause_id: DRF/resolver-path-inconsistency-mixed-cause
family: DRF
ticket_count: 3
curated: true
self_serviceable: false
---

# Intermittent internal DNS failures due to resolver path inconsistency after maintenance

[← Back to categories](../../index.md)

## Description

Affected users experience intermittent failures when their machines attempt to resolve internal hostnames used by corporate applications and services. The failures manifest as a mix of responses: some lookups return NXDOMAIN (indicating the name does not exist), some time out entirely, some return SERVFAIL errors, and others return outdated IP addresses that no longer correspond to the correct backend server. The inconsistency means that the same hostname may resolve correctly on one attempt and fail on the next, making the problem difficult to predict.

The issue is not confined to a single machine or network segment. Reports have shown the problem affecting multiple hosts across different racks, subnets, and office locations simultaneously. For example, users on one subnet may predominantly see timeouts while users on another see stale address responses or NXDOMAIN errors for the same internal hostname. This cross-subnet, cross-location pattern distinguishes the issue from a problem on any individual workstation or a single network segment.

The practical impact is that internal services relying on name-based connections — such as database endpoints, payment backends, and other internally hosted applications — become intermittently unreachable. Deployment pipelines, application health checks, and monitoring dashboards may all flag failures during the affected period. The onset of symptoms has been observed following scheduled DNS maintenance windows, though the link to maintenance is not always immediately apparent to the reporting user.

!!! note "Reported variations"

    - Some affected subnets experienced predominantly NXDOMAIN responses while others saw timeouts or stale IP addresses for the same hostname, depending on which internal resolver served that subnet.
    - In at least one case, flushing the resolver cache did not immediately restore consistent behavior, suggesting that forwarder configuration or routing — not just cached data — contributed to the inconsistency.
    - The exact resolver failure mode could not always be conclusively isolated due to limited change history or rotated logs on the primary DNS servers.

## Affected environment

Distribution across 3 reported cases:

- **Device / platform:** on-premises (67%), On-premises DNS infrastructure (33%)
- **Team:** Internal Services (33%), Internal Applications (33%), Internal Apps (33%)
- **Region:** us-east-1-datacenter (33%), corp-net (33%), corp-datacenter-1 (33%)

## Root cause

Scheduled DNS maintenance or zone changes left the internal DNS resolver infrastructure in an inconsistent state, with some resolvers serving stale cached data, incorrect forwarder routing, or a combination of both. Because multiple internal resolvers were affected — each potentially holding different outdated information — clients on different subnets received different (and often incorrect) answers for the same internal hostname. The authoritative DNS zone records themselves were typically healthy; the fault lay in how the resolvers cached or forwarded queries for internal zones.

## Diagnostics

Steps used to confirm this root cause:

1. Query db.internal.example.com from affected client resolvers and compare results with a known-good internal resolver.  
   *Expected:* Both resolvers return the same current address.
2. Inspect the internal DNS zone record for db.internal.example.com, including TTL and any recent change history.  
   *Expected:* Zone contains the current record with expected TTL.
3. Check internal DNS forwarder configuration and clear stale resolver cache entries for the affected hostname.  
   *Expected:* Forwarder routes the zone correctly and cache returns fresh data.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Verify the authoritative internal DNS zone entry for db.internal.example.com, confirm the correct A record value (<IP>) and TTL (300s), and correct the record where it differs from the intended database endpoint address. The stale record pointing to <IP> was updated by <USER> on the primary zone server.
2. Clear cache on the affected internal DNS resolvers (dns-resolver-1.internal.example.com and dns-resolver-2.internal.example.com) so stale responses and negative cache entries for db.internal.example.com are removed and new queries return fresh zone data reflecting the corrected <IP> address.
3. Flush DNS cache on representative affected clients — including <HOSTNAME> (<IP>) and <HOSTNAME> (<IP>) — and retest name resolution from multiple subnets (<IP>/24 and <IP>/24) to confirm the hostname consistently resolves to the current address <IP> without NXDOMAIN or timeout behavior.
4. Review and correct any conditional forwarder or delegation path used for the internal.example.com zone on dns-resolver-1.internal.example.com so queries are routed to the proper authoritative source. The stale conditional forwarder entry was updated and validated by the network team.
5. Validate steady-state resolution by repeating lookups from impacted racks (Rack 14A and Rack 14B in <LOCATION>) and monitoring via Network Monitoring dashboards for consistent answers (<IP>) and elimination of intermittent lookup failures. <PERSON> and <PERSON> confirmed resolution from their respective hosts.

**Example 2**

1. Reviewed the internal zone record and recent maintenance changes for app.payments.corp to confirm the expected target value (<IP>) and TTL (300s) after the DNS work performed during change CHG-90412 by <USER> on 2026-01-07.
2. Validated resolution from affected clients (<HOSTNAME> at <IP> for <USER> in <LOCATION>, <HOSTNAME> at <IP> for <USER> in <LOCATION>) against the internal resolver and compared results with the authoritative or known-good internal DNS path to confirm inconsistent resolver behavior.
3. Cleared positive and negative caches on the impacted internal caching resolvers (DNS-CACHE-01.corplabs.internal and DNS-CACHE-03.corplabs.internal) and verified conditional forwarder or zone routing configuration for the payments.corp namespace, ensuring the forwarder pointed to DNS-AUTH-02.corplabs.internal.
4. Corrected the resolver-side DNS path so app.payments.corp returned the current internal record (<IP>) consistently, then restarted or refreshed the caching service where required on DNS-CACHE-01 and DNS-CACHE-03.
5. Had affected clients (<USER> on <HOSTNAME>, <USER> on <HOSTNAME>) flush local DNS cache and retest name resolution, confirming the hostname resolved consistently without NXDOMAIN or timeout responses.
6. Monitored resolver metrics and incident symptoms via Network Monitoring after the change window to verify the spikes in NXDOMAIN and timeouts did not recur, with <USER> confirming stable resolution across <LOCATION> and <LOCATION> regions for 4 hours post-fix.

## Recommendation

This issue is resolved by IT support; reference "internal DNS resolver path inconsistency" when reporting it.

---

[← Back to categories](../../index.md)
