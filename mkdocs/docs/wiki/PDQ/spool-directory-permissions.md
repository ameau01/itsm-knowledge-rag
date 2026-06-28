---
hide:
  - navigation
root_cause_id: PDQ/spool-directory-permissions
family: PDQ
ticket_count: 1
curated: true
self_serviceable: false
---

# Print Spooler Fails Due to Incorrect Queue or Spool Directory Permissions

[← Back to categories](../../index.md)

## Description

Office users at a branch location reported that printing to a shared HP LaserJet hosted on the print server was failing. The printer remained visible in the shared queue and accepted job submissions, but jobs entered the queue without completing. Some users received access-related printing errors, while others observed the printer showing offline or encountered driver-unavailable and spooler-timeout messages. The issue was confirmed across multiple users on different floors of the building.

Diagnostics ruled out a paused queue and an outdated or corrupt driver package. A test job submitted through the server-hosted queue failed during spooler processing and presented as an access error (EventID 7011), pointing to a permissions issue affecting the print queue or spool path rather than a driver fault. The failure was limited to processing on the print server side; affected workstations could see the printer and submit jobs, indicating workstation-level connectivity was intact.

The issue was resolved by restoring baseline ACLs for the print spooler service account, after which normal printing resumed for all affected users.

!!! note "Reported variations"

    - Some users reported the shared printer showing offline rather than receiving explicit access-related errors
    - Driver-unavailable or spooler-timeout messages appeared on certain workstations alongside the primary queue-stuck behavior
    - Users on multiple floors of the same building were affected, confirming the issue was not isolated to a single network segment

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** Windows Server 2019 (100%)
- **Device / platform:** Print Server (100%)
- **Team:** Office Staff (100%)
- **Region:** us-east-1 (100%)

## Root cause

Incorrect permissions on the affected shared printer queue or the associated spool directory on the print server prevented the Print Spooler service from processing submitted jobs. The spooler service account lacked the necessary ACLs to complete job rendering and output.

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

The issue was resolved by IT after restoring correct permissions on the print queue and spool directory for the spooler service account.

---

[← Back to categories](../../index.md)
