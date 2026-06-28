---
hide:
  - navigation
root_cause_id: DRF/no-server-side-fault-client-side-or-transient
family: DRF
ticket_count: 1
curated: true
self_serviceable: false
---

# Client-Side DNS Cache or Local Network Condition Causing Resolution Failures

[← Back to categories](../../index.md)

## Description

Affected users in a corporate office environment reported intermittent DNS resolution failures when attempting to reach internal services by hostname. The issue manifested as NXDOMAIN responses or resolution to outdated IP addresses belonging to decommissioned hosts, even though other systems on the same network were resolving the same hostnames successfully. The problem primarily impacted access to internal endpoints such as service-discovery and application dependency registries.

Investigation confirmed that both authoritative DNS servers and corporate resolvers were returning correct, current records for the affected hostnames. The inconsistency between working and non-working systems pointed to endpoint-local conditions rather than a centralized DNS infrastructure fault. One affected workstation was found returning a stale cached IP address that had already been corrected in the authoritative zone during a prior change window, while another received NXDOMAIN responses despite correct zone data being present on the servers.

The issue was most visible on clients that had recently changed networks or resumed from long-running sessions. In the reported cases, resolution returned to normal after affected users flushed their local DNS caches or reconnected to the office VPN, consistent with a transient or client-side caching condition rather than a server-side fault.

!!! note "Reported variations"

    - One affected endpoint resolved an internal hostname to an outdated IP address associated with a previously decommissioned host, suggesting a stale local cache entry persisting beyond the authoritative zone correction.
    - The issue cleared on one system only after the user reconnected to the corporate VPN, indicating that a network transition may have left the client with an unusable or outdated resolver configuration.

## Affected environment

Distribution across 1 reported cases:

- **Device / platform:** BIND 9 on CentOS 7 (100%)
- **Team:** internal-devs (100%)
- **Region:** datacenter-1 (100%)

## Root cause

No fault was found in the central internal DNS service. Client-side DNS caching, local network settings, or an already-cleared transient condition caused the earlier hostname resolution failures. The issue was isolated to individual endpoints rather than the shared resolver or authoritative infrastructure.

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

1. Have affected users flush local DNS cache and renew network configuration on impacted endpoints or application hosts. <PERSON> (<HOSTNAME>, <IP>) ran ipconfig /flushdns and ipconfig /renew; <PERSON> (<HOSTNAME>, <IP>) reconnected to the <LOCATION> office VPN, which refreshed his DNS settings.
2. Verify the affected systems are using the expected corporate DNS servers (<IP> and <IP>) and not stale or alternate resolver settings. Both <PERSON>'s and <PERSON>'s endpoints were confirmed pointing to the correct resolvers after remediation. Agent <USER> validated via ipconfig /all output collected from each user.
3. Retest hostname resolution and application access from affected endpoints; if the issue persists, collect client-side DNS diagnostics for endpoint-focused follow-up. Post-fix nslookup app.example.internal from both <HOSTNAME> and <HOSTNAME> returned <IP> successfully. Internal-app-service and monitoring-dashboard confirmed accessible by hostname from both endpoints. No further failures reported; ticket closed.

## Recommendation

Resolved by IT; intermittent internal DNS resolution failures traced to client-side caching or local network conditions with no centralized DNS fault identified.

---

[← Back to categories](../../index.md)
