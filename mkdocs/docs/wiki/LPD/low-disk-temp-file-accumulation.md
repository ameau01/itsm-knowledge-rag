---
hide:
  - navigation
root_cause_id: LPD/low-disk-temp-file-accumulation
family: LPD
ticket_count: 1
curated: true
self_serviceable: true
---

# Post-Login Laptop Sluggishness Due to Temp File Disk Exhaustion

[← Back to categories](../../index.md)

## Description

Affected users experience consistent sluggishness on their managed Windows 10 laptop during the post-login period. Core applications such as Outlook, Chrome, and File Explorer take noticeably longer than normal to open in the first several minutes after sign-in, and general desktop responsiveness is degraded. No single application failure is identified; rather, the slowdown is broad and affects routine work across multiple programs.

The underlying issue is an accumulation of temporary files consuming a significant portion of the system drive's available space. In reported cases, tens of gigabytes of temp files had built up in user-profile and system temp directories, leaving the drive critically low on free space. This disk-space exhaustion produces elevated CPU and disk utilization immediately after login, which subsides only partially and continues to impair application launch times until the temp-file buildup is addressed.

!!! note "Reported variations"

    - Affected users may initially correlate the onset of sluggishness with a recent company update push, though diagnostics confirm the root cause is disk-space exhaustion from temp-file accumulation rather than an update- or policy-related issue.
    - The slowdown presents as a general performance degradation with no single failing application, making it difficult for the affected user to pinpoint the source of the problem.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** Windows 10 21H2 (100%)
- **Device / platform:** Corporate laptop (Dell Latitude) (100%)
- **Team:** Sales (100%)
- **Region:** EMEA (100%)

## Root cause

Critically low available disk space combined with excessive temporary file accumulation caused ongoing disk contention and degraded laptop performance after login.

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

Resolved by IT after identifying and clearing accumulated temporary files that had exhausted available disk space on the affected laptop.

---

[← Back to categories](../../index.md)
