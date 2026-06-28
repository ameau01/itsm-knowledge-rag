---
hide:
  - navigation
root_cause_id: LPD/resource-heavy-startup-policy
family: LPD
ticket_count: 3
curated: true
self_serviceable: false
---

# Post-Login CPU Contention From Resource-Heavy Startup Policy Deployment

[← Back to categories](../../index.md)

## Description

Affected users with managed Windows 10 corporate laptops report significant slowness immediately after signing in. CPU usage rapidly climbs to 70–90% within one to two minutes of login, and common productivity applications — including Outlook, Chrome, Teams, Edge, and Windows Explorer — take 20–60 seconds to open. Desktop interaction is noticeably delayed during the startup window, and normal post-login work is disrupted for several minutes before performance gradually improves. The issue is confined to individual endpoints rather than the broader network.

Diagnostic review of affected devices reveals multiple resource-intensive processes competing for CPU cycles during the login phase, including endpoint management extensions, scheduled policy-enforcement tasks, asset inventory agents, synchronization triggers, and telemetry collectors — all launched simultaneously as part of the updated startup configuration. In some cases, a single enforced startup application is the dominant source of the CPU spike rather than a combination of competing processes. The onset of symptoms aligns directly with the timing of a corporate startup application policy push.

Affected users span multiple office locations and groups such as Sales and Mobile Workforce. The issue has been observed following policy pushes on consecutive days, indicating that successive rounds of startup policy revisions can independently trigger the same resource-contention behavior on newly targeted devices. In at least one case, the issue initially appeared attributable to a different root cause before diagnostics confirmed the startup policy as the actual trigger.

!!! note "Reported variations"

    - In some cases, a specific enforced startup application (such as an asset inventory agent) is the dominant source of the CPU spike, rather than a combination of multiple competing processes.
    - One affected user reported that performance partially self-recovered after several minutes, though applications remained slower than normal throughout the session.
    - The problematic startup policy was delivered via Group Policy (GPO) in some instances and via Intune endpoint management in others, but the resulting symptoms were identical.
    - At least one case initially appeared to have a different root cause (e.g., low disk space) before diagnostics confirmed the startup policy as the actual trigger.

## Affected environment

Distribution across 3 reported cases:

- **Operating system:** Windows 10 21H2 (100%)
- **Device / platform:** Corporate Laptop (Managed) (33%), Laptop (33%), Corporate Laptop (33%)
- **Team:** Sales - Mobile Workforce (33%), Office Staff (33%), Sales (33%)
- **Region:** US-East (100%)

## Root cause

A recently applied corporate startup policy introduced or re-enabled multiple resource-heavy startup items and service activity at user logon. The simultaneous launch of these processes caused sustained CPU and memory contention, delaying application launches and degrading post-login responsiveness on affected endpoints.

## Diagnostics

Steps used to confirm this root cause:

1. Reviewed CPU, memory, and disk activity during user login and while launching common applications.  
   *Expected:* Resource usage returns to normal after startup completes.
2. Checked recently applied startup items, endpoint policy changes, and managed post-login activity for correlation with the slowdown.  
   *Expected:* No heavy startup task or scan backlog blocks normal use.
3. Verified the endpoint was not experiencing low disk space or abnormal temporary file growth contributing to slow launches.  
   *Expected:* Disk has sufficient free space and no runaway temporary files.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Reviewed active startup processes and svchost-hosted service activity after login on <HOSTNAME> (user <USER>, IP <IP>) to confirm policy-related CPU contention on the affected laptop, identifying IntuneManagementExtension.exe, duplicate OneDrive sync triggers, and telemetry collectors as primary offenders.
2. Disabled non-essential startup items on <PERSON>'s user profile (<USER>) to reduce immediate post-login CPU load and restore usability, removing redundant telemetry collectors and a duplicate OneDrive sync task introduced by the policy.
3. Triggered a device policy refresh from Intune on <HOSTNAME> so the endpoint would receive the latest managed configuration state and reconcile with the corrected Corporate Startup Application Policy.
4. Updated the Corporate Startup Application Policy in Intune to remove unapproved or unnecessary startup entries (including duplicate sync triggers and redundant telemetry agents) that were contributing to high CPU after sign-in across the Sales - Mobile Workforce device group.
5. Rebooted the laptop <HOSTNAME> and validated that CPU utilization dropped below 20% after login and application launch times returned to normal levels (Outlook: ~3.5s, Chrome: ~2s, Explorer: immediate).
6. Scheduled follow-up cleanup for the broader <LOCATION> Sales device group and advised <PERSON> (<EMAIL>) to report any recurrence after future policy deployments; ticket escalation contact is <PERSON> (<EMAIL>, <PHONE>).

**Example 2**

1. Reviewed startup-related processes on the affected laptop <HOSTNAME> (IP <IP>) after login by user <USER> and confirmed the primary CPU spike was tied to <PERSON> launched by the recent startup policy (Corp-Startup-Inventory-v3).
2. Disabled the unnecessary startup item (AssetInventoryAgent.exe) on the affected device under <USER>'s profile to validate that login performance and application launch times improved. CPU dropped from 70-90% to under 20% within the first minute post-login.
3. Updated the corporate startup policy (Corp-Startup-Inventory-v3) in Endpoint Management to stop forcing the heavy autostart application AssetInventoryAgent.exe for the <LOCATION> office device population. Change coordinated by <PERSON> (<USER>).
4. Triggered a policy sync from Endpoint Management so the corrected startup configuration applied to <HOSTNAME> and other affected endpoints in the <LOCATION> office group.
5. Rebooted the laptop <HOSTNAME> and verified post-login CPU utilization for <USER> dropped back to expected levels (8-12% idle) and Outlook, Teams, and Chrome opened normally within 3-5 seconds. <PERSON> confirmed the issue was resolved.

## Recommendation

Resolved by IT after identifying and adjusting the recently deployed startup application policy responsible for post-login resource contention on affected endpoints.

---

[← Back to categories](../../index.md)
