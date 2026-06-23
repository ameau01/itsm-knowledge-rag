---
hide:
  - navigation
root_cause_id: SDA/broken-ntfs-acl-inheritance-or-deny-ace
family: SDA
ticket_count: 5
curated: true
self_serviceable: false
---

# Finance shared drive access denied due to broken NTFS permission inheritance or conflicting deny entries

[← Back to categories](../../index.md)

## Description

Affected users attempting to open a Finance shared drive from a mapped network drive or direct path on their Windows workstation are prompted for credentials and then receive an "Access is denied" error. The issue prevents users from listing or opening files in the Finance department folder needed for normal work. The credential prompt and denial persist even after signing out and back in, disconnecting and remapping the drive, or clearing saved credentials. Attempting access from a different workstation with the same account produces the same result.

The issue typically affects individual users rather than the entire Finance team. Colleagues on the same floor or in the same department may be able to access the share without difficulty, which can make the problem appear account-specific. In some cases, affected users have recently had a group membership change or access update applied, yet the denial continues despite the update being confirmed as complete.

IT verification consistently shows that the affected user already holds the correct Active Directory security group membership for the Finance share, and that group membership has fully replicated across domain controllers. Standard client-side remediation steps — such as refreshing the user session, clearing cached credentials, and remapping the drive — do not resolve the issue on their own. File server logs continue to record access-denied events for the user's account even after these steps, pointing to a server-side permissions problem rather than a user identity or credential issue.

!!! note "Reported variations"

    - In some cases the mapped drive initially reconnects successfully, but the access-denied error appears only when the user navigates into a specific department subfolder rather than at the top level of the share.
    - Some affected users experience intermittent access-denied behavior rather than a consistent block, with the Finance folder accessible in some sessions but not others, due to inconsistent effective permissions caused by the broken inheritance.
    - In at least one instance, a colleague's account was unaffected because it belonged to a legacy security group that was still present on the folder's access control list, while the current group had been dropped due to the inheritance break.

## Affected environment

Distribution across 5 reported cases:

- **Operating system:** Windows 10 (80%), Windows Server 2019 (20%)
- **Device / platform:** on-premises (40%), On-premises File Server (SMB) (20%), On-prem Windows File Server (SMB) (20%)
- **Team:** Finance (100%)
- **Region:** US-East (40%), primary-datacenter (20%), us-east-1-dc1 (20%)

## Root cause

The file server's folder-level permissions (NTFS access control lists) on the Finance shared drive are misconfigured. Specifically, permission inheritance on the Finance folder has been broken or removed, and in some cases an explicit deny entry has been applied to the folder or a parent folder that overrides the allow permissions granted through the user's Active Directory security group. Because deny entries take precedence over allow entries in Windows file permissions, the user is blocked from access even though their group membership is correct. The misconfiguration has been traced in some instances to a bulk permission change that inadvertently introduced conflicting deny entries.

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

This issue is resolved by IT support; reference "Finance share access denied – NTFS ACL inheritance" when reporting it.

---

[← Back to categories](../../index.md)
