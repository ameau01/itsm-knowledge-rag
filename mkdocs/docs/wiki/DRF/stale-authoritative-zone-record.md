---
hide:
  - navigation
root_cause_id: DRF/stale-authoritative-zone-record
family: DRF
ticket_count: 14
curated: true
self_serviceable: false
---

# Stale A Record in Authoritative Internal DNS Zone

[← Back to categories](../../index.md)

## Description

Affected users and internal services experience intermittent failures resolving internal hostnames — such as application endpoints, database services, and portal resources — across multiple subnets, VLANs, and office locations. DNS queries return inconsistent results: some yield an outdated IP address belonging to a decommissioned or migrated host, while others return NXDOMAIN. The mixed responses disrupt application-layer connectivity, causing health-check failures, connection timeouts, broken deployment pipelines, and degraded user-facing dashboards.

The issue traces to stale or incorrect A record data persisting in the authoritative internal DNS zone after a planned infrastructure change such as a service migration or host decommissioning. In some cases the authoritative zone itself retains the outdated or duplicate record; in others the zone is correctly updated but recursive resolvers continue serving cached stale data due to high TTL values or negative cache entries. Both scenarios produce the same observable pattern of alternating stale-address and NXDOMAIN responses across the resolver tier.

The problem typically surfaces shortly after a planned DNS or infrastructure change and is reported concurrently by engineering, operations, and application teams. Internal monitoring dashboards corroborate the issue with elevated DNS error rates and NXDOMAIN spikes. Contributing factors include deprecated DNS management or change-control policy references in zone or resolver configurations, zone serial numbers not incremented after record changes, and resolver caches not flushed following authoritative updates.

!!! note "Reported variations"

    - In some cases the authoritative zone already contained the correct record, but resolvers continued serving stale cached data due to an outdated policy reference in the resolver configuration, requiring a configuration update and service restart rather than a zone record correction.
    - Deprecated DNS change-control or zone management policy references delayed remediation or contributed to resolver misconfiguration.
    - Some affected environments returned purely NXDOMAIN from one resolver while a secondary resolver returned the correct address, rather than alternating between a stale IP and NXDOMAIN.
    - Some clients experienced DNS query timeouts or SERVFAIL responses rather than explicit NXDOMAIN, particularly when multiple resolver nodes held conflicting cache states.
    - In certain cases only application server hosts were affected, surfacing the issue through health-check failures and broken database connectivity rather than user-reported browsing problems.
    - Duplicate stale A records were left behind in the authoritative zone after a migration rather than the existing record being updated, causing the resolver to serve the retired address.
    - The issue affected multiple distinct hostnames within the same internal zone simultaneously rather than a single record.
    - High TTL values on the affected zone records prolonged the period during which stale data was served, extending the window of user impact beyond typical cache refresh cycles.

## Affected environment

Distribution across 14 reported cases:

- **Operating system:** Linux (7%), mixed linux/windows (7%), Linux (various app servers) (7%)
- **Device / platform:** on-premises (29%), on-prem VMware (14%), BIND 9 on CentOS 7 (7%)
- **Team:** Internal Users (36%), engineering (14%), internal-devs (7%)
- **Region:** us-east-1 (21%), corp-dc-1 (21%), corp-datacenter-1 (14%)

## Root cause

A stale A record remained in the internal authoritative DNS zone after a service IP change or host decommissioning, and recursive resolvers continued serving outdated cached data due to high TTL values or unflushed caches. In some cases, deprecated DNS management policy references in resolver or zone configurations further delayed detection and correction of the outdated zone data.

## Diagnostics

Steps used to confirm this root cause:

1. Queried app.example.internal from affected internal resolvers and comparison resolver paths to check for inconsistent answers.  
   *Expected:* Both resolvers return the same current address.
2. Inspected the internal zone record, TTL, and zone contents for app.example.internal to confirm current authoritative data.  
   *Expected:* Zone contains the current record with expected TTL.
3. Checked resolver forwarding and cache behavior, then flushed stale cache entries on internal resolvers after the zone correction.  
   *Expected:* Forwarder routes the zone correctly and cache returns fresh data.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Updated the A record for svc-db.corp.internal in the internal DNS zone on dns-int-east-01.corp.internal from the decommissioned address <IP> to the current database service IP <IP>, and confirmed the decommissioned address was removed. Change performed by <PERSON> (<USER>).
2. Reviewed the zone entry <PERSON> (adjusted from 3600s to 300s temporarily) and recent record state to ensure the corrected record would propagate as expected across internal resolvers including dns-resolver-east-02.corp.internal.
3. Flushed cached DNS entries on the affected internal resolver infrastructure (dns-resolver-east-02.corp.internal) so stale NXDOMAIN and outdated A record responses pointing to <IP> were cleared.
4. Retested name resolution for svc-db.corp.internal from multiple affected application servers including <HOSTNAME> (<USER>) and <HOSTNAME> (<USER>) and confirmed consistent return of the current IP <IP>.
5. Validated that backend applications could reconnect to the database service using the hostname and monitored Network Monitoring alerts for recurrence after the change. <PERSON> confirmed batch jobs resumed successfully at 09:15 UTC.

**Example 2**

1. Validated the authoritative internal DNS zone entry for db01.corp.local and corrected the A record from the stale address <IP> to the current database server IP address <IP>, as confirmed by <PERSON> (<USER>) from the network infrastructure team.
2. Flushed stale resolver cache entries, including negative cache data, on dns-cache01 and dns-cache02 using 'rndc flush' so cached NXDOMAIN responses for db01.corp.local were removed from both resolver nodes.
3. Restarted the resolver service on dns-cache01 via systemctl to ensure the updated zone data and refreshed cache state were being served consistently to all downstream app hosts in corp-datacenter-1.
4. Re-ran hostname resolution tests for db01.corp.local from the affected app host path (APPHOST-LNX-04 at <IP> and APPHOST-LNX-05 at <IP>) and confirmed the expected address <IP> was returned without timeout on both hosts.
5. Verified dependent service recovery by confirming inventory-service could resolve the database hostname db01.corp.local and establish connections successfully, and that Network Monitoring checks for internal DNS lookups returned healthy. Notified <PERSON> (<EMAIL>, <PHONE>) that the issue was resolved.

## Recommendation

Resolved by IT after correcting the stale authoritative zone A record, flushing resolver caches, and updating deprecated DNS policy references.

---

[← Back to categories](../../index.md)
