---
hide:
  - navigation
root_cause_id: DRF/stale-authoritative-zone-record
family: DRF
ticket_count: 14
curated: true
self_serviceable: false
---

# Stale A record in authoritative internal DNS zone causing intermittent resolution failures

[← Back to categories](../../index.md)

## Description

Affected users experience intermittent failures when attempting to reach internal services by hostname. DNS lookups return either NXDOMAIN responses or resolve to an outdated IP address belonging to a decommissioned or migrated host, preventing applications and users from reliably connecting to internal endpoints. The issue typically manifests across multiple office locations and subnets simultaneously, with different resolver paths sometimes returning different incorrect answers — one site may receive NXDOMAIN while another receives the stale address.

The failures are visible on user workstations, application servers, and automated monitoring systems alike. Internal services that depend on hostname-based connectivity — such as database connections, API endpoints, deployment pipelines, and health-check systems — may lose connectivity or behave erratically. Users commonly notice the problem when internal dashboards, portals, or application workflows become unreachable by name, even though the underlying service is running normally at its current address.

Monitoring dashboards and alerting systems typically show elevated DNS error rates and NXDOMAIN spikes correlating with the onset of the issue. The inconsistency between resolver responses can make the problem appear intermittent from any single vantage point, as some queries succeed while others fail depending on which resolver handles the request and whether its cache contains the stale or negative entry. The issue persists until the authoritative DNS zone record is corrected and resolver caches are cleared.

!!! note "Reported variations"

    - In some cases the authoritative zone record itself is correct but the resolver continues serving stale cached data due to an outdated resolver configuration or policy reference that prevents proper cache invalidation.
    - A duplicate stale A record may coexist alongside the correct record in the zone, causing resolvers to intermittently return either the current or retired address.
    - Multiple hostnames in the same authoritative zone may be affected simultaneously when several records are missed during an infrastructure migration.
    - Deprecated DNS change-control or zone management policy references in runbooks or resolver configurations may delay validation and correction of the stale record.
    - Negative cache entries on resolvers may produce NXDOMAIN responses even after the authoritative zone record has been corrected, until resolver caches are explicitly flushed.

## Affected environment

Distribution across 14 reported cases:

- **Operating system:** Linux (7%), mixed linux/windows (7%), Linux (various app servers) (7%)
- **Device / platform:** on-premises (29%), on-prem VMware (14%), BIND 9 on CentOS 7 (7%)
- **Team:** Internal Users (36%), engineering (14%), internal-devs (7%)
- **Region:** us-east-1 (21%), corp-dc-1 (21%), corp-datacenter-1 (14%)

## Root cause

An outdated or duplicate A record remains in the internal authoritative DNS zone after a service migration, host decommissioning, or IP address change, continuing to point to a retired address. Internal recursive resolvers then serve the stale record or cache negative (NXDOMAIN) responses from brief zone-reload gaps, producing inconsistent and incorrect answers across the network. In some cases, a long time-to-live value on the record extends the duration of the problem, and outdated DNS management policy references in zone configurations or operational runbooks delay detection and correction of the stale data.

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

This issue is resolved by IT support; reference 'stale authoritative DNS zone record' when reporting it.

---

[← Back to categories](../../index.md)
