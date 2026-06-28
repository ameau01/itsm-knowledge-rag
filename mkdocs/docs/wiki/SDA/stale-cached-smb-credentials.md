---
hide:
  - navigation
root_cause_id: SDA/stale-cached-smb-credentials
family: SDA
ticket_count: 2
curated: true
self_serviceable: false
---

# Stale Cached SMB Credentials Cause Mapped Drive Access Denial

[← Back to categories](../../index.md)

## Description

Affected users on domain-joined Windows 10 workstations experience repeated credential prompts followed by "Access is denied" messages when attempting to open department shared folders via mapped network drives in File Explorer. In one instance, the denial was accompanied by Error 5. The issue prevents normal access to SMB file shares and blocks routine file work.

The underlying cause is stale cached SMB credentials stored on the workstation. In the reported cases, the credential cache became outdated due to a recent change — either an AD group membership update that granted new share access, or a same-day password change. Although the user's Active Directory membership and share permissions are confirmed correct and fully replicated across domain controllers, the workstation continues to present outdated cached credentials from Windows Credential Manager when connecting to the file server. This causes the SMB session to authenticate with obsolete information, resulting in denied access even when the user re-enters current, valid credentials at the prompt.

!!! note "Reported variations"

    - Error 5 explicitly returned alongside the "Access Denied" message (observed in one case involving a post-AD-group-change scenario)
    - Credential prompt and access denial reproduced when navigating directly to the UNC share path, in addition to the mapped drive (observed in one case involving a same-day password change)
    - Stale credentials triggered by an AD group membership change processed days prior, with full domain controller replication confirmed; resolution in that instance included refreshing the Kerberos ticket
    - Stale credentials triggered by a same-day password change on the affected user's account
    - Historical NTFS deny entries noted on the file server for separate follow-up by the file server owner

## Affected environment

Distribution across 2 reported cases:

- **Operating system:** Windows 10 (100%)
- **Device / platform:** On-prem File Server (SMB) (50%), Windows Domain (50%)
- **Team:** Finance (50%), HR-Dept (50%)
- **Region:** us-east-1 (100%)

## Root cause

The affected user's workstation retained stale cached SMB credentials in Windows Credential Manager that did not reflect a recent change — either a password update or a newly granted AD group membership for the target share. Despite correct AD group membership and fully replicated permissions across domain controllers, the workstation continued to present outdated credentials during SMB authentication, causing repeated access denials. Historical NTFS deny entries were noted on the file server but were not the immediate cause, as access was restored without any ACL modification.

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

Resolved by IT by clearing stale cached credentials and remapping the affected network drive with fresh authentication.

---

[← Back to categories](../../index.md)
