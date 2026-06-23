---
hide:
  - navigation
root_cause_id: LPD/low-disk-temp-file-accumulation
family: LPD
ticket_count: 1
curated: true
self_serviceable: true
---

# Post-login laptop slowdown caused by temporary file buildup and low disk space

[← Back to categories](../../index.md)

## Description

Affected users experience persistent sluggishness on their managed Windows 10 laptop beginning immediately after sign-in. Core applications — including Outlook, Chrome, and File Explorer — take noticeably longer than normal to open during the first several minutes of use, and general desktop responsiveness is degraded throughout that period. Task Manager may show CPU usage exceeding 90% while these applications are loading.

Unlike issues that resolve once the initial post-login burst of activity subsides, the slowdown in this case continues to affect application launches and overall system performance beyond the sign-in window. The affected device's system drive may show very little free space remaining (for example, under 2 GB on a 256 GB drive), though users may not be aware of the disk-space condition and may attribute the problem to a recent software update or other change.

No specific application errors or crashes are reported; the issue presents as a broad performance degradation rather than a failure of any single program or service.

!!! note "Reported variations"

    - The affected user may initially associate the onset of slowness with a recent company laptop update, though diagnostics confirm the root cause is disk-space exhaustion rather than a policy or update-related issue.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** Windows 10 21H2 (100%)
- **Device / platform:** Corporate laptop (Dell Latitude) (100%)
- **Team:** Sales (100%)
- **Region:** EMEA (100%)

## Root cause

The system drive has reached critically low free space due to a large accumulation of temporary files in user and system temp directories. In observed cases, temporary file buildup exceeded 38 GB, leaving less than 2 GB of usable space on the drive. This shortage creates ongoing disk contention that degrades application launch times and general system responsiveness well beyond the normal post-login period.

## Diagnostics

Steps used to confirm this root cause:

1. Review CPU, memory, and disk usage during login and while launching common applications.  
   *Expected:* Resource usage returns to normal after startup completes.
2. Check recently applied startup scripts, endpoint policies, and scheduled scans affecting post-login activity.  
   *Expected:* No heavy startup task or scan backlog blocks normal use.
3. Verify available disk space and temporary file growth on the endpoint.  
   *Expected:* Disk has sufficient free space and no runaway temporary files.

## Resolution

Representative resolutions from prior cases:

1. Removed temporary files from C:\Users\<USER>\AppData\Local\Temp (24.3 GB) and C:\Windows\Temp (14.1 GB), cleared local browser caches for Chrome and Edge, and reclaimed 41.6 GB on the system drive of <HOSTNAME>.
2. Reviewed large local file consumers using WinDirStat and identified an additional 8.2 GB of obsolete Sales Tool export CSVs under C:\Users\<USER>\Documents\Exports; moved these to the user's OneDrive archive and deleted nonessential local copies to restore healthy free space (now 52.1 GB available on C:\).
3. Validated after logoff and logon by user <PERSON> that disk response improved (disk queue length dropped to 0.3 avg) and common applications — Outlook, Chrome, File Explorer, and Internal Sales Tool — opened within normal timeframes (Outlook in 7 seconds, Chrome in 4 seconds). Confirmed with <PERSON> via <EMAIL> that performance was back to normal.

## Recommendation

This issue is resolved by IT support; reference "temporary file buildup and low disk space slowdown" when reporting it.

---

[← Back to categories](../../index.md)
