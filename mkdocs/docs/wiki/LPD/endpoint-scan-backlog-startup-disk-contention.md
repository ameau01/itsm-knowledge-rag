---
hide:
  - navigation
root_cause_id: LPD/endpoint-scan-backlog-startup-disk-contention
family: LPD
ticket_count: 53
curated: true
self_serviceable: false
---

# Endpoint Protection Scan Backlog Causing Post-Login CPU Saturation

[← Back to categories](../../index.md)

## Description

Affected users on managed Windows 10 laptops experience severe slowness immediately after sign-in, with CPU utilization sustained at 80–100% and disk I/O frequently reaching near-maximum levels for several minutes. The Antimalware Service Executable (MsMpEng.exe) or a comparable endpoint protection process consistently appears as the dominant CPU consumer in Task Manager. Core productivity applications — including Outlook, Teams, Chrome, Edge, Excel, Word, File Explorer, and line-of-business tools — take anywhere from 10 seconds to over five minutes to open or become responsive. Users report loud continuous fan activity, and in some cases brief periods of complete system unresponsiveness. The slowdown recurs across reboots and is not resolved by restarting the device.

Investigation reveals a backlog of queued endpoint protection scans — ranging from a handful of deferred jobs to hundreds or thousands of pending items — that trigger simultaneously at user login. The backlogs typically accumulate after a group policy or endpoint management policy refresh that altered scan scheduling, or after missed scan windows while devices were offline. Multiple resource-heavy startup items (such as cloud-sync clients, Teams auto-launch, updater services, and endpoint management agents) launch concurrently, compounding the CPU and disk contention during the same post-login window.

Low free disk space on the system drive is a consistent aggravating factor, with affected devices showing as little as 2–19 GB free on 256 GB drives. The constrained storage increases I/O contention and swap activity during the already resource-intensive startup period. Once the scan backlog is cleared and contributing factors are addressed, CPU usage drops to normal levels within minutes and application responsiveness returns.

!!! note "Reported variations"

    - Scan backlog size varied widely across devices, from a handful of deferred full scans to approximately 200 pending items or over 14,000 queued scan entries.
    - In some cases the endpoint protection product was CrowdStrike Falcon rather than Microsoft Defender, with the same pattern of queued scans triggering at login.
    - Free disk space ranged from critically low (approximately 2–3 GB) to moderately constrained (around 19 GB) on 256 GB drives, with lower availability correlating to more severe slowdowns.
    - Some devices had up to 14 active startup items — including policy-pushed agents, duplicate helper processes, and legacy updater services — loading concurrently at sign-in.
    - At least one affected device experienced brief full unresponsiveness rather than just slowness, with disk queue lengths averaging above four during peak contention.
    - In several cases the issue recurred after a prior partial remediation, with the scan backlog re-accumulating because underlying scan scheduling or startup policies had not been permanently corrected.
    - Application impact extended beyond standard productivity tools to include engineering build tools and CRM or line-of-business applications on some devices.
    - Inconsistent policy deployment was observed in at least one instance, where a colleague with an identical laptop model was unaffected because the corrected startup policy had been applied to that device.

## Affected environment

Distribution across 53 reported cases:

- **Operating system:** Windows 10 21H2 (57%), Windows 10 Pro (19%), Windows 10 (9%)
- **Device / platform:** Laptop (43%), Corporate Laptop (9%), Corporate Laptop (Dell Latitude) (6%)
- **Team:** Sales (72%), Engineering (8%), Finance (6%)
- **Region:** us-east-1 (47%), EMEA (25%), us-west-2 (13%)

## Root cause

A backlog of endpoint protection scans — typically accumulated after a policy refresh or missed scan windows — triggered at user login alongside multiple resource-heavy startup applications, causing sustained CPU and disk I/O contention. Low free disk space on the system drive further amplified the performance degradation by increasing storage pressure during the post-login window.

## Diagnostics

Steps used to confirm this root cause:

1. Review CPU, memory, and disk usage during login and application launch.  
   *Expected:* Resource usage returns to normal after startup completes.
2. Check recently applied startup scripts, endpoint policies, and scheduled scans.  
   *Expected:* No heavy startup task or scan backlog blocks normal use.
3. Verify available disk space and temporary file growth on the endpoint.  
   *Expected:* Disk has sufficient free space and no runaway temporary files.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Reviewed startup-impacting processes on the affected laptop <HOSTNAME> (user <USER>) and disabled 4 non-essential startup items (including redundant telemetry agents and a legacy inventory scanner) contributing to the post-login CPU spike.
2. Forced a device policy refresh through Endpoint Management (gpupdate /force) on <HOSTNAME> to correct the 2026-01-27 startup-related GPO policy application and prevent the heavy startup behavior from reapplying; confirmed the revised policy version was received.
3. Cleared the Endpoint Protection scan backlog of 14 queued definition updates by rescheduling full scans to off-hours (02:00 local <LOCATION> time) and allowing an immediate lighter quick-scan cycle to complete during support handling on <USER>'s device.
4. Removed 11.1 GB of temporary files from C:\Windows\Temp and C:\Users\<USER>\AppData\Local\Temp and reclaimed disk space (free space restored to 19.3 GB) to reduce paging and startup disk contention during user sign-in on <HOSTNAME>.
5. Validated performance after logoff and logon on <USER>'s session, then monitored CPU and disk I/O until they returned to normal startup levels (CPU below 25% within 90 seconds, disk queue length < 2) and <PERSON> confirmed Outlook, Chrome, and the Sales CRM opened normally within 3-5 seconds. Advised agent <PERSON> to apply the same remediation to <PERSON>'s device under the parent investigation.

**Example 2**

1. Reviewed Task Manager resource usage on <HOSTNAME> after login by user <USER> and confirmed CPU spikes (88-92%) were tied to EndpointProtectionService.exe activity and concurrent startup processes.
2. Cleared the queued endpoint protection scan backlog (four deferred full-disk scans) on <HOSTNAME> to stop repeated scan execution immediately after sign-in.
3. Disabled three nonessential startup applications (Adobe Updater, OneDrive auto-sync, Teams background launch) on <HOSTNAME> to reduce concurrent CPU load during the login sequence.
4. Refreshed device policy from endpoint management for <HOSTNAME> so scan behavior and startup-related policy state were updated on the laptop; confirmed successful policy sync at 2026-01-30T02:10Z.
5. Removed temporary files from C:\Users\<USER>\AppData\Local\Temp and C:\Windows\Temp, reclaiming approximately 8 GB of disk space on the 256 GB SSD to reduce endpoint performance pressure and help prevent future scan queuing.

## Recommendation

Resolved by IT; endpoint protection scan backlog cleared and startup/scan policies adjusted to eliminate post-login CPU saturation.

---

[← Back to categories](../../index.md)
