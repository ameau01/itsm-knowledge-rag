---
hide:
  - navigation
root_cause_id: PDQ/queue-left-paused
family: PDQ
ticket_count: 1
curated: true
self_serviceable: true
---

# Shared printer queues left paused after maintenance window

[← Back to categories](../../index.md)

## Description

Affected users found that print jobs submitted to shared printer queues on the print server remained indefinitely in a "spooling" or pending state and never printed. The issue affected multiple department queues hosted on the same server, rather than a single workstation or a single printer, and was reported by users across more than one team.

Jobs continued to queue up normally and appeared in the print queue, but no output was produced at the physical printers. In some cases, restarting the print spooler service on a local workstation provided brief, temporary relief before the same behavior returned. Some users also encountered a "Driver unavailable" message on the shared queues, which initially suggested a driver-related problem but was ultimately unrelated to the actual cause.

The issue began shortly after a scheduled maintenance window on the print server and affected all users who printed through the server-hosted printer path, including both on-site and remote users.

!!! note "Reported variations"

    - Some users received a "Driver unavailable" message on the shared queues, which was misleading; the actual cause was the paused queue state rather than a driver problem.
    - Restarting the local print spooler service on individual workstations temporarily appeared to help but did not resolve the issue, since the pause existed at the server level.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** Windows Server 2019 (100%)
- **Device / platform:** on-premises (100%)
- **Team:** Workplace Services (100%)
- **Region:** us-east-1-dc1 (100%)

## Root cause

The shared printer queues on the print server had been left in a paused state following a maintenance window. An administrative service account paused the queues during maintenance and they were not resumed afterward, which prevented any queued jobs from being released to the printers. Once the queues were resumed, printing returned to normal with no underlying software or driver issue present.

## Diagnostics

Steps used to confirm this root cause:

1. Checked the shared PDQ-Print01 queues to verify whether jobs were paused, stuck, or continuously spooling.  
   *Expected:* Print queue is online and accepts new jobs.
2. Compared the installed printer driver package and queue mappings against the approved driver version for the affected printers.  
   *Expected:* Endpoint uses the current approved printer driver.
3. Reviewed Print Spooler service behavior and tested whether restarting the service would allow jobs to clear normally.  
   *Expected:* Spooler processes a test job without retry or access errors.

## Resolution

Representative resolutions from prior cases:

1. Resume the paused shared printer queues \\PS-PRINT01\HP-Sales-3F and \\PS-PRINT01\HP-HR-2F on PS-PRINT01 using Set-Printer -Name <QueueName> -ComputerName PS-PRINT01 -PrinterStatus Normal, and clear any stale jobs that remained from the paused period (5 orphaned jobs were purged via Remove-PrintJob).
2. Review queue settings and recent administrative activity on PS-PRINT01 to determine why the queue entered or remained in a paused state — audit logs confirmed the pause was triggered by svc-printadmin during a scheduled maintenance window at 19:45 UTC but the resume step was missed. <PERSON> updated the maintenance runbook to include a mandatory post-maintenance queue status verification checklist.
3. Submit validation print jobs from affected users to confirm the queue accepts and completes jobs normally. Confirmed successful test prints from <PERSON> <PERSON> (<USER>) on \\PS-PRINT01\HP-Sales-3F and <PERSON> (<USER>) on \\PS-PRINT01\HP-HR-2F. Both users verified output at their respective printers in the <LOCATION> office.

## Recommendation

This issue is resolved by IT support; reference "printer queue paused after maintenance" when reporting it.

---

[← Back to categories](../../index.md)
