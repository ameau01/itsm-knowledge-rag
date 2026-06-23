---
hide:
  - navigation
root_cause_id: PDQ/spool-directory-permissions
family: PDQ
ticket_count: 1
curated: true
self_serviceable: false
---

# Shared printer queue failures due to spool directory permission changes

[← Back to categories](../../index.md)

## Description

Affected users attempting to print through a shared printer queue hosted on the print server find that jobs enter the queue but never complete. The printer appears visible and accepts submissions, yet documents remain stuck without printing. Some users may see the printer show as offline in their print dialog, even though the device is reachable and the queue is not paused.

In addition to stalled jobs, some workstations display access-related printing errors or spooler timeout messages rather than the offline or driver-related errors associated with other print issues. The errors point to a processing failure on the print server side rather than a problem with workstation connectivity or driver availability.

The issue typically affects multiple users across different floors or workgroups who share the same server-hosted print queue. Individual workstations can discover and connect to the printer normally, but no jobs are processed to completion regardless of which user or workstation submits them.

!!! note "Reported variations"

    - Some workstations may report the shared printer as offline rather than displaying an explicit access or spooler timeout error.
    - The specific error presentation can vary by workstation, with some users seeing "driver unavailable" messages alongside the access errors, even though the driver package itself is intact.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** Windows Server 2019 (100%)
- **Device / platform:** Print Server (100%)
- **Team:** Office Staff (100%)
- **Region:** us-east-1 (100%)

## Root cause

A recent Group Policy update changed the permissions on the shared printer queue's spool directory on the print server, removing write access for the print spooler service account. Without the necessary permissions, the Print Spooler service could not process submitted jobs, causing them to stall in the queue and triggering access-related errors on client workstations.

## Diagnostics

Steps used to confirm this root cause:

1. Checked the shared print queue state on PS-PRINT01 to confirm whether jobs were paused, stuck, or failing.  
   *Expected:* Print queue is online and accepts new jobs.
2. Compared the installed print driver package on PS-PRINT01 with the approved HP Universal Print Driver version.  
   *Expected:* Endpoint uses the current approved printer driver.
3. Reviewed Print Spooler service status and attempted to process a test job through the affected queue.  
   *Expected:* Spooler processes a test job without retry or access errors.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

1. Review the affected printer queue security settings and spool folder (C:\Windows\System32\spool\PRINTERS) NTFS permissions on PS-PRINT01 for the svc-printspooler service account and authenticated users. <PERSON> (tchen, <EMP_ID>) confirmed the ACLs were modified by a recent GPO push.
2. Restore the standard print queue and spool directory permissions from the approved server baseline, granting svc-printspooler full control and authenticated users print access. Applied by tchen on PS-PRINT01.
3. Restart the Print Spooler service on PS-PRINT01 and submit test print jobs from impacted users <USER> (<HOSTNAME>), <USER> (<HOSTNAME>), and <USER> to verify jobs complete without access errors. All three users confirmed successful printing after the fix.

## Recommendation

This issue is resolved by IT support; reference "spool directory permissions" when reporting it.

---

[← Back to categories](../../index.md)
