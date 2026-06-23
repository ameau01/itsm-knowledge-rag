---
hide:
  - navigation
root_cause_id: LPD/endpoint-scan-backlog-startup-disk-contention
family: LPD
ticket_count: 53
curated: true
self_serviceable: false
---

# Post-login laptop slowdown caused by endpoint protection scan backlog and disk contention

[← Back to categories](../../index.md)

## Description

Affected users experience severe slowness on their managed Windows 10 laptops immediately after signing in. Within the first one to two minutes of login, CPU usage rises to 80–100% and disk activity becomes heavily elevated, causing the device to feel largely unresponsive. Common business applications — including Outlook, Teams, Chrome, Edge, Word, Excel, File Explorer, and line-of-business tools — take anywhere from 10 seconds to several minutes to open, and the desktop may lag or appear to hang during this window. Fan noise often increases noticeably during the slowdown period.

The performance degradation typically persists for five to fifteen minutes before the system gradually settles, though in some cases the laptop remains noticeably slower than normal even after that initial window. Task Manager consistently shows the endpoint protection process (commonly listed as "Antimalware Service Executable" or "MsMpEng.exe") consuming a large share of CPU — often 60–95% on its own — alongside several startup applications that load at the same time. Disk utilization on the system drive frequently reaches 90–100% during the affected period.

The issue has been observed across multiple offices and teams, and it often follows a recent endpoint policy refresh, definition update, or overnight patch window. Restarting the laptop does not resolve the problem; the slowdown returns after each subsequent login. In many cases, the system drive also has limited free space — sometimes well below 10% — which compounds the resource pressure during startup. Some users have reported the issue recurring after an earlier partial fix, indicating that the underlying scan backlog or startup configuration was not fully addressed on the first attempt.

!!! note "Reported variations"

    - In some cases the issue recurred after a prior remediation because the scan backlog re-accumulated following a subsequent definition update or policy refresh, requiring a second round of cleanup.
    - On certain devices, a recently applied startup policy introduced duplicate or unnecessary startup entries that were not present before, amplifying the resource contention beyond what the scan backlog alone would cause.
    - At least one device had an unnecessary third-party startup utility (a "PC optimization" tool) that was itself consuming additional CPU during the post-login window, compounding the slowdown.
    - Some affected laptops had adequate free disk space but still experienced the slowdown due to the scan backlog and startup load alone, without the low-disk-space component.
    - The issue was observed both on-site over wired connections and remotely over VPN, confirming it is not related to network conditions.

## Affected environment

Distribution across 53 reported cases:

- **Operating system:** Windows 10 21H2 (57%), Windows 10 Pro (19%), Windows 10 (9%)
- **Device / platform:** Laptop (43%), Corporate Laptop (9%), Corporate Laptop (Dell Latitude) (6%)
- **Team:** Sales (72%), Engineering (8%), Finance (6%)
- **Region:** us-east-1 (47%), EMEA (25%), us-west-2 (13%)

## Root cause

A backlog of endpoint protection scans — often accumulated over days or weeks of missed or deferred scheduled scan windows — is triggered at user login, causing the security scanning process to consume sustained CPU and disk resources immediately after sign-in. This scan activity coincides with multiple resource-heavy startup applications (such as cloud sync clients, auto-updaters, and collaboration tools) that also launch during the same post-login window, creating significant CPU and disk contention. Low free space on the system drive further worsens the impact by increasing disk input/output pressure and reducing the system's ability to handle concurrent activity efficiently.

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

1. Reviewed startup performance data on <HOSTNAME> (IP <IP>) and confirmed three Endpoint Protection Client full-scan jobs were stacking at login for user <USER>, driving CPU spikes to 97% during the first 5-8 minutes after sign-in.
2. Cleared the queued endpoint protection scan backlog (three stacked full-scan jobs) on <HOSTNAME> and refreshed device policy via the Endpoint Management console so startup scanning behavior returned to a single scheduled quick-scan at a normal cadence.
3. Disabled nonessential startup items (OneDrive auto-sync, Teams auto-launch, CRM background agent) on <HOSTNAME> that were adding additional resource load during user logon for <USER> and competing with foreground application launches like Outlook and Edge.
4. Removed 14.6 GB of temporary files from C:\Users\<USER>\AppData\Local\Temp, browser cache, and stale Windows Update packages using Disk Cleanup, reclaiming local storage space on the 256 GB SSD and reducing the performance impact from low free disk availability (restored to ~27% free).
5. Validated post-remediation behavior by having <PERSON> log in again on <HOSTNAME> and confirming CPU activity normalized to under 30% within 90 seconds of login, and common applications (Outlook, Office, Edge) opened within 15 seconds — well within acceptable time. Notified <USER> at <EMAIL> that the ticket is resolved.

## Recommendation

This issue is resolved by IT support; reference "endpoint scan backlog startup slowdown" when reporting it.

---

[← Back to categories](../../index.md)
