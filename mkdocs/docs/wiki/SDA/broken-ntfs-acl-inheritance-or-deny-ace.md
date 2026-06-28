---
hide:
  - navigation
root_cause_id: SDA/broken-ntfs-acl-inheritance-or-deny-ace
family: SDA
ticket_count: 5
curated: true
self_serviceable: false
---

# Broken NTFS Inheritance or Explicit Deny ACE on Shared Folder

[← Back to categories](../../index.md)

## Description

Affected users attempting to open a Finance department shared drive from Windows 10 workstations encounter a credential prompt followed by an "Access is denied" error (in some cases error code 0x80070005). The issue prevents users from listing or opening files within the Finance folder path, despite their Active Directory accounts holding confirmed membership in the appropriate file-access security groups. The problem persists after standard client-side remediation steps such as signing out and back in, clearing cached SMB credentials, disconnecting and remapping the network drive, and even attempting access from a different workstation — indicating a server-side rather than client-side cause.

Investigation consistently reveals that the affected users' AD group memberships and directory replication are correct across all domain controllers. However, NTFS ACL review on the file server discloses broken permission inheritance on the Finance folder or an explicit deny access control entry (ACE) on a parent or target folder that overrides the group-based allow permissions. In at least one case, the deny ACE was traced to a bulk permission change that inadvertently applied an explicit deny entry for a Finance security group. File server access logs corroborate the denial, recording NT_STATUS_ACCESS_DENIED events for the affected users' security identifiers even after group membership updates are confirmed.

Colleagues on the same Finance team who belong to a legacy or alternate security group that is separately listed on the folder ACL are unaffected, which initially makes the issue appear account-specific. No client-side changes alone restore access; the issue is resolved only after server-side ACL corrections are applied.

!!! note "Reported variations"

    - In some cases the mapped drive reconnects successfully at the share level, but the "Access is denied" error appears only when navigating into a specific department subfolder beneath the Finance share.
    - File server logs in certain instances record intermittent rather than consistent NTFS permission errors, with access occasionally succeeding briefly after a token refresh before failing again on subsequent attempts.
    - At least one case involved a colleague's access functioning normally because the colleague's account belonged to a legacy security group that remained on the folder ACL, while the current standard group was missing from the ACL entirely.
    - In one instance, initial access restoration steps (credential cleanup and drive remap) appeared to resolve the issue in a remote test session, but file server logs continued to record deny events, revealing a deeper ACL inconsistency.

## Affected environment

Distribution across 5 reported cases:

- **Operating system:** Windows 10 (80%), Windows Server 2019 (20%)
- **Device / platform:** on-premises (40%), On-premises File Server (SMB) (20%), On-prem Windows File Server (SMB) (20%)
- **Team:** Finance (100%)
- **Region:** US-East (40%), primary-datacenter (20%), us-east-1-dc1 (20%)

## Root cause

NTFS permissions on the Finance department shared folder were misconfigured. The expected security group was either absent from the folder ACL due to broken or removed permission inheritance, or an explicit deny ACE on a parent or target folder overrode the allow permissions granted through the group. Affected users held valid AD group membership, but the file server's effective permissions denied access because of the conflicting ACL configuration. In one case, a folder/share ACL inheritance mismatch continued to deny the user's SID even after correct group membership was confirmed and applied.

## Diagnostics

Steps used to confirm this root cause:

1. Verify the user's FINANCE_USERS membership against the Finance shared folder ACL entries.  
   *Expected:* User belongs to the group that grants the requested drive permission.
2. Ask the user to refresh sign-in state and retry access with a new session token after clearing cached credentials.  
   *Expected:* Refreshed token includes the updated drive entitlement.
3. Confirm the user is connecting to the current \\Shared\\Finance path rather than a stale mapped shortcut.  
   *Expected:* Current shared drive path opens without permission errors.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Reviewed the Finance share NTFS permissions on FS-EAST-02.corplabs.internal and confirmed the FINANCE_USERS group was missing from the \\Shared\\Finance folder ACL despite valid AD membership for <USER> (employee ID <EMP_ID>).
2. Restored the intended permission inheritance or reapplied the approved Finance folder ACL so that FINANCE_USERS was included with the correct access rights (Read/Write). Change performed by file services admin <USER> in the <LOCATION> office.
3. Validated that share and NTFS permissions were aligned on FS-EAST-02.corplabs.internal and that no explicit deny entry or broken inheritance continued to block access for FINANCE_USERS members.
4. Cleared any cached Windows credentials and removed the stale mapped drive connection on the user's workstation <HOSTNAME> (IP <IP>), then remapped \\Shared\\Finance using net use commands executed by <USER>.
5. Retested access with the user <USER> after the ACL correction and confirmed the Finance shared drive opened successfully without prompting again for credentials. <PERSON> confirmed via email at <EMAIL> that all Finance files were accessible.

**Example 2**

1. Confirmed <USER>'s membership in the Finance_SharedDrive AD security group (CN=<USER>,OU=Finance Users,DC=corplabs,DC=internal) and verified replication had completed across all domain controllers so directory entitlement was current.
2. Reviewed the Finance folder ACLs on FS-FIN-01.corplabs.internal, specifically \Finance$\Department_Reports, identified an explicit deny ACE and inheritance inconsistency affecting the target path, and removed the deny condition from the folder permissions.
3. Restored the intended permission inheritance on the Department_Reports folder and reapplied the correct allow access (Read/Write) for the Finance_SharedDrive group, ensuring all subfolders inherited the corrected permissions.
4. Cleared <USER>'s cached network credentials on <HOSTNAME> using 'cmdkey /delete:FS-FIN-01.corplabs.internal' and had the F: drive remapped so the client reconnected with a fresh access token.
5. Retested access from <HOSTNAME> (IP <IP>) to the current Finance shared drive path \\FS-FIN-01.corplabs.internal\Finance$\Department_Reports and confirmed <USER> could open and list the folder without receiving Access Denied events. <PERSON> confirmed normal access was restored.

## Recommendation

Resolved by IT through server-side NTFS ACL remediation, removing the erroneous explicit deny ACE and restoring proper permission inheritance on the affected folder hierarchy.

---

[← Back to categories](../../index.md)
