---
hide:
  - navigation
root_cause_id: DRF/no-server-side-fault-client-side-or-transient
family: DRF
ticket_count: 1
curated: true
self_serviceable: false
---

# Hostname resolution failures caused by client-side DNS cache or transient conditions

[← Back to categories](../../index.md)

## Description

Affected users experience intermittent failures when attempting to reach internal services by hostname. Some workstations return "NXDOMAIN" (host not found) responses or resolve hostnames to outdated IP addresses belonging to decommissioned hosts, while other systems on the same network resolve the same hostnames successfully. The failures are most visible on clients that have recently changed networks, reconnected via VPN, or resumed from long-running sessions.

The inconsistency between machines is a hallmark of this issue: central DNS infrastructure returns correct, current answers when queried directly, yet individual endpoints continue to serve stale or incorrect results from their local caches. Access to internal endpoints such as service-discovery registries and application dependencies may be disrupted on the affected workstations, even though the underlying DNS records are accurate.

Reports may come from multiple users in the same office at roughly the same time, which can initially suggest a broader infrastructure problem. However, the pattern typically narrows to a small number of endpoints rather than a site-wide outage.

!!! note "Reported variations"

    - Some affected workstations resolve hostnames to an older, decommissioned IP address rather than returning a "not found" error, making the issue appear to be a stale zone record on the server side.
    - The issue may clear on its own after a user reconnects to the corporate VPN, with no other intervention required.
    - Endpoints that have recently switched networks (e.g., moving between wired and wireless, or between office and remote connections) are disproportionately affected.

## Affected environment

Distribution across 1 reported cases:

- **Device / platform:** BIND 9 on CentOS 7 (100%)
- **Team:** internal-devs (100%)
- **Region:** datacenter-1 (100%)

## Root cause

No fault is present in the central internal DNS service. The authoritative DNS servers and corporate resolvers return correct, current answers for the affected hostnames. The resolution failures originate from stale entries in the local DNS cache on individual workstations, local network configuration issues (such as endpoints pointing to an alternate resolver), or a transient condition that has already cleared by the time investigation begins.

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

This issue is resolved by IT support; reference 'client-side DNS cache resolution failure' when reporting it.

---

[← Back to categories](../../index.md)
