---
hide:
  - navigation
root_cause_id: DRF/resolver-path-inconsistency-mixed-cause
family: DRF
ticket_count: 3
curated: true
self_serviceable: false
---

# Inconsistent Internal Resolver Cache or Forwarder State After DNS Maintenance

[← Back to categories](../../index.md)

## Description

Affected users experience intermittent failures when resolving internal hostnames used by critical services such as database endpoints and backend application dependencies. Failures manifest as a mix of NXDOMAIN responses, SERVFAIL errors, and DNS lookup timeouts when querying internal resolvers. In some cases, lookups return stale A records pointing to outdated IP addresses rather than the current expected address. These resolution failures prevent name-based connectivity to internal services, causing deployment pipeline failures, application errors, and loss of access to internal tools.

The issue presents non-uniformly across clients, subnets, and office locations. Hosts on one internal subnet or resolver path may experience consistent failures while hosts on a different subnet return correct results. Even within the same environment, the failure mode varies — some clients receive NXDOMAIN, others experience timeouts, and others receive outdated records — depending on which internal resolver or cache instance handles the query. Reports have spanned multiple racks within a single datacenter as well as multiple office locations.

In reported cases, symptom onset correlated with recent DNS maintenance windows or zone migrations. Authoritative DNS servers responded correctly when queried directly, while the caching or forwarding resolvers serving affected clients returned inconsistent or incorrect answers. The exact resolver failure mode was not always conclusively isolated, as post-cache-flush behavior sometimes remained inconsistent and forwarder configuration could not be fully confirmed from available evidence.

!!! note "Reported variations"

    - Some affected hosts returned stale A records pointing to a previous IP address following a recent endpoint migration, rather than returning an error
    - Failures appeared only after a scheduled DNS maintenance window, with no symptoms reported prior to the change
    - Approximately 40% of queries from a specific host returned NXDOMAIN while the remaining queries succeeded, indicating intermittent rather than total failure
    - Change log evidence on the primary DNS server was unavailable due to log rotation, preventing full confirmation of authoritative record drift
    - One resolver intermittently returned SERVFAIL for internal zone queries while authoritative servers responded correctly, but the exact failure mode could not be conclusively isolated even after cache flush

## Affected environment

Distribution across 3 reported cases:

- **Device / platform:** on-premises (67%), On-premises DNS infrastructure (33%)
- **Team:** Internal Services (33%), Internal Applications (33%), Internal Apps (33%)
- **Region:** us-east-1-datacenter (33%), corp-net (33%), corp-datacenter-1 (33%)

## Root cause

Intermittent internal DNS resolution failures were caused by stale or inconsistent data held by caching and forwarding resolvers following DNS maintenance or zone migrations. The resolver layer served outdated or incorrect answers for internal zones even though authoritative records were healthy, with the inconsistency affecting multiple subnets and regions. Misconfiguration or instability in the corporate resolver path compounded the issue, producing mixed NXDOMAIN, SERVFAIL, and stale-record responses across different resolver instances.

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

Resolved by IT; reference as intermittent internal DNS resolution failures due to inconsistent resolver cache or forwarder state following DNS maintenance.

---

[← Back to categories](../../index.md)
