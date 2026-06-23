---
hide:
  - navigation
root_cause_id: SDA/stale-cached-smb-credentials
family: SDA
ticket_count: 2
curated: true
self_serviceable: false
---

# Shared drive access denied due to stale cached SMB credentials

[← Back to categories](../../index.md)

## Description

Affected users experience repeated credential prompts followed by "Access Denied" (Error 5) when attempting to open a mapped network drive or a direct shared folder path through File Explorer on a domain-joined Windows workstation. The issue typically arises shortly after a password change or an Active Directory group membership update, even though the underlying account permissions are correct and fully replicated.

The credential prompt appears each time the user tries to access the shared drive, and entering the current password does not resolve the denial. Both the mapped drive letter and the direct network path (e.g., \\server\share) exhibit the same behavior, effectively blocking all access to department files stored on the file server.

The issue is confined to the individual workstation that holds the outdated cached credentials; other devices or fresh sessions are not affected. Normal file access is restored once the stale credentials are cleared and the drive is remapped, with no changes required to Active Directory group membership or share permissions.

!!! note "Reported variations"

    - Historical NTFS deny entries may appear on the file server during investigation, but access is restored without modifying those entries, indicating they are not the immediate cause of the denial.
    - In some cases the issue follows an Active Directory group membership addition rather than a password change; the stale cached session still prevents the new entitlement from taking effect on the workstation.

## Affected environment

Distribution across 2 reported cases:

- **Operating system:** Windows 10 (100%)
- **Device / platform:** On-prem File Server (SMB) (50%), Windows Domain (50%)
- **Team:** Finance (50%), HR-Dept (50%)
- **Region:** us-east-1 (100%)

## Root cause

The workstation's Windows Credential Manager retains stored credentials for the mapped network drive that predate a recent password change or Active Directory group update. When the user attempts to connect, the system presents these outdated credentials to the file server, which rejects them and denies access. Clearing the cached credentials, refreshing the authentication session, and remapping the drive allows the workstation to authenticate with current credentials and restores access.

## Diagnostics

Steps used to confirm this root cause:

1. Verify the user's Finance share AD group membership against the permissions expected for FIN_SHARE.  
   *Expected:* User belongs to the group that grants the requested drive permission.
2. Refresh the user's sign-in token and compare Finance share access with a new SMB session.  
   *Expected:* Refreshed token includes the updated drive entitlement.
3. Confirm the user is opening the current FIN_SHARE path rather than an outdated mapped drive target or stale shortcut.  
   *Expected:* Current shared drive path opens without permission errors.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Confirmed <USER> (<PERSON>, <EMP_ID>) was a member of the FINANCE_SHARE AD security group and that the group change (CR-20260302-114, processed by <USER>) had replicated successfully across all domain controllers including DC-EAST-03.corp.local.
2. Validated the Finance shared drive path (\\FS-EAST-02.corp.local\FIN_SHARE mapped as F:) being used on <HOSTNAME> and ruled out access through an outdated mapped path or stale shortcut.
3. Cleared cached Windows credentials from Credential Manager on <HOSTNAME> (stale entry for FS-EAST-02.corp.local dated 2026-02-18) and disconnected the existing mapped network drive session (net use F: /delete) for the Finance share.
4. Refreshed the user's Kerberos logon <PERSON> (klist purge) and remapped FIN_SHARE (net use F: \\FS-EAST-02.corp.local\FIN_SHARE /user:CORP\<USER>) using the current corporate identity context with updated group membership.
5. Retested access to the Finance department folder (F:\Finance_Dept) on <HOSTNAME> and confirmed the share opened without credential prompts or further DENY events. Notified <PERSON> at <USER>@corpfinance.com that access was restored.

**Example 2**

1. Reviewed the user's access path, confirmed the issue affected \\fileserver\Dept, and verified the user <USER> (<PERSON>, <EMP_ID>) was already a member of the expected AD access group HR-Dept-Share-Access.
2. Checked the mapped drive and stored Windows Credentials on <HOSTNAME> (IP <IP>), identifying cached credentials that were likely stale following the user's password change earlier that day.
3. Removed the stored credential for the shared drive target \\fileserver\Dept from Windows Credential Manager on <HOSTNAME> to force fresh authentication for <USER>.
4. Deleted and recreated the mapped network drive using the current path \\fileserver\Dept so the session would establish with updated credentials for user <USER>.
5. Validated that the user <PERSON> could open the shared folder \\fileserver\Dept successfully after remapping and no longer received repeated credential prompts on <HOSTNAME>.
6. Documented the presence of historical NTFS deny ACL evidence and recommended follow-up review of folder inheritance and deny entries by the file server owners; notified <EMAIL> and agent <PERSON> of closure.

## Recommendation

This issue is resolved by IT support; reference "stale cached SMB credentials on mapped drive" when reporting it.

---

[← Back to categories](../../index.md)
