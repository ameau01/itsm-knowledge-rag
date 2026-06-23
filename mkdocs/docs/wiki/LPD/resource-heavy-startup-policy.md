---
hide:
  - navigation
root_cause_id: LPD/resource-heavy-startup-policy
family: LPD
ticket_count: 3
curated: true
self_serviceable: false
---

# Post-login slowdown caused by resource-heavy corporate startup policy

[← Back to categories](../../index.md)

## Description

Affected users experience significant slowness on their managed Windows 10 laptops immediately after signing in. Within one to two minutes of login, CPU usage climbs to 70–90%, and common applications — including Outlook, Chrome, Teams, Edge, and Windows Explorer — take 20 to 60 seconds to open. Normal post-login work is noticeably delayed during this window.

The slowness is most pronounced in the first several minutes after login and may gradually improve as the startup workload subsides, though the delay is sustained enough to disrupt routine tasks. The issue is limited to the affected endpoint and does not indicate a broader network or hardware problem.

Symptoms began appearing after a corporate startup policy was deployed to devices via endpoint management tooling, with the earliest reports coinciding with policy pushes on or around 2026-02-05. Affected users have been located across multiple office locations and belong to groups such as Sales - Mobile Workforce. Task Manager on affected devices shows elevated CPU consumption driven by startup-related processes and services running under the new policy.

!!! note "Reported variations"

    - In some cases, a single startup application (such as an asset inventory agent) is the dominant source of CPU consumption rather than multiple competing processes.
    - Some affected devices show duplicate sync triggers or redundant telemetry collectors layered on top of the primary startup workload, amplifying the resource contention.
    - The specific startup policy name and deployment date may vary across affected groups (e.g., a sales-specific hardening policy versus a broader corporate startup application policy).

## Affected environment

Distribution across 3 reported cases:

- **Operating system:** Windows 10 21H2 (100%)
- **Device / platform:** Corporate Laptop (Managed) (33%), Laptop (33%), Corporate Laptop (33%)
- **Team:** Sales - Mobile Workforce (33%), Office Staff (33%), Sales (33%)
- **Region:** US-East (100%)

## Root cause

A recently applied corporate startup policy introduced or re-enabled multiple resource-heavy applications and services that run automatically at user login. These startup items — including inventory agents, policy-enforcement tasks, telemetry collectors, and duplicate sync triggers — compete for CPU and memory immediately after sign-in, causing sustained high utilization and delaying normal application launches. The issue is configuration-driven rather than related to hardware limitations or low disk space.

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

This issue is resolved by IT support; reference 'post-login slowdown from startup policy' when reporting it.

---

[← Back to categories](../../index.md)
