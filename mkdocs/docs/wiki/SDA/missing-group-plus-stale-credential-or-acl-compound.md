---
hide:
  - navigation
root_cause_id: SDA/missing-group-plus-stale-credential-or-acl-compound
family: SDA
ticket_count: 17
curated: true
self_serviceable: false
---

# Shared drive access denied due to missing AD group and stale credentials combined

[← Back to categories](../../index.md)

## Description

Affected users attempting to open a department shared drive from a mapped network drive or direct UNC path on a domain-joined Windows workstation receive repeated credential prompts followed by an "Access is denied" error (often error code 0x80070005). The mapped drive letter may still appear in File Explorer, but opening the target department folder fails after the user enters valid domain credentials. Other network shares on the same file server or other servers typically continue to work normally, and colleagues on the same team or subnet can access the same shared folder without issue, confirming the problem is account-specific rather than a general server or network outage.

The issue commonly appears after an Active Directory group cleanup, a recent password change, a weekend maintenance window, or an AD group membership update that has not yet taken effect on the user's workstation session. In some cases, the user's access had been working as recently as the previous day or the previous week. The credential prompt may cycle repeatedly — the user enters correct domain credentials, only to be denied again — because the workstation is presenting outdated cached credentials or session tokens that do not reflect the user's current entitlements.

The problem affects various department shares (Finance, Engineering, HR, Sales, and others) across different file servers and mapped drive letters. Affected users are typically found to be missing from the Active Directory security group that controls access to the share, while simultaneously having stale cached SMB or Windows credentials stored on the workstation from a prior session. In some instances, broken NTFS permission inheritance on a subfolder or a legacy per-user access control entry on the shared folder further complicates the effective permissions, contributing to inconsistent or contradictory access behavior even after group membership is partially addressed.

!!! note "Reported variations"

    - In some cases, a legacy explicit per-user access control entry on the shared folder from a prior migration conflicts with the expected group-based permissions, requiring the ACL to be standardized before access is fully restored.
    - Broken NTFS permission inheritance on a subfolder (rather than the top-level share) may cause access to fail for specific subfolders even after the user's group membership is corrected at the share level.
    - The issue may surface immediately after a corporate password reset, with the old cached credential in Windows Credential Manager preventing the new password from being used for the mapped drive session.
    - A stale group policy–based drive mapping reference may contribute to outdated mapping behavior on the workstation alongside the permission and credential issues.
    - File server–side group membership evaluation may lag behind the Active Directory change, causing continued access denial even when the user's AD group membership appears correct, until the server's security context is also refreshed.

## Affected environment

Distribution across 17 reported cases:

- **Operating system:** Windows 10 (71%), Windows Server 2019 (18%), Windows 10 Pro (domain-joined) (6%)
- **Device / platform:** on-premises (41%), Corporate Windows domain (6%), On-prem VMware-hosted file server (6%)
- **Team:** Finance (71%), Dept-Engineering (6%), Finance_Team (6%)
- **Region:** us-east-1 (65%), us-east-1 (corporate network) (6%), us-east-1 (corporate datacenter) (6%)

## Root cause

The affected user's Active Directory account is missing membership in the security group required for access to the department shared drive — often due to an AD group cleanup, organizational restructure, or a membership change that has not yet propagated. At the same time, the user's workstation retains stale cached SMB credentials or an outdated Kerberos session token from a previous logon, which causes the file server to repeatedly reject authentication attempts and trigger credential prompts. In some cases, broken NTFS permission inheritance on a subfolder or a leftover per-user access control entry on the shared folder introduces additional permission conflicts that compound the access failure.

## Diagnostics

Steps used to confirm this root cause:

1. Verify the user's group membership against the shared drive access control list.  
   *Expected:* User belongs to the group that grants the requested drive permission.
2. Ask the user to refresh sign-in and compare access with a new session token.  
   *Expected:* Refreshed token includes the updated drive entitlement.
3. Confirm the user is opening the current drive path rather than a stale shortcut.  
   *Expected:* Current shared drive path opens without permission errors.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Verified the intended access model for the Finance share on FS-EAST-02.corplabs.internal and confirmed that <USER> (<PERSON>, <EMP_ID>) should receive access through the FINANCE_USERS security group rather than through a manual per-user ACL entry.
2. Added and confirmed <USER> in FINANCE_USERS via Active Directory (change originally initiated by <USER>) and validated that the membership change had replicated across domain controllers in us-east-1 before retesting access.
3. Forced FS-EAST-02.corplabs.internal to refresh its view of AD-backed security context using klist purge on the server and refreshed SMB/Netlogon dependency services where operationally safe to clear stale group evaluation for <USER>'s <PERSON>.
4. Removed the unexpected explicit allow ACE for <USER>'s individual SID from the Finance folder on FS-EAST-02 after review with the Finance team lead, and re-applied inherited permissions according to the standard Finance share ACL policy granting access via FINANCE_USERS.
5. Cleared <PERSON>'s cached credentials in Windows Credential Manager on <HOSTNAME> (<IP>), disconnected and remapped the F: drive to \\FS-EAST-02.corplabs.internal\Finance$, and had the user establish a fresh Kerberos session token before validation.
6. Retested the current Finance shared-drive path (F:\Finance) from <HOSTNAME> and confirmed the folder opened successfully without Access Denied. <PERSON> confirmed she could read and write files as expected. Ticket closed and notification sent to <USER> at <EMAIL>.

**Example 2**

1. Verified that access to \\filesvr01\Finance is controlled by the 'Dept-Editors' Active Directory security group and confirmed the user account <USER> (<EMP_ID>) was not a current member. Cross-checked against colleague <USER> who holds the group and has working access.
2. Added <USER> to the approved 'Dept-Editors' security group (via AD Users and Computers on DC-EAST-03.corplabs.internal) to restore the required file share entitlement. Change approved by Finance manager <PERSON>.
3. Refreshed the user's Kerberos/AD access token on <HOSTNAME> using 'klist purge' and instructed <USER> to log off and sign back in so the new 'Dept-Editors' group membership would apply to the session.
4. Cleared stale mapped-drive credentials associated with the password reset from Windows Credential Manager on <HOSTNAME> (targeting the filesvr01 entry) to prevent the old authentication context from being reused.
5. Retested access to the direct UNC path \\filesvr01\Finance from <HOSTNAME> (<IP>) and confirmed <USER> could open the Finance folder successfully. User confirmed via email at <EMAIL> that all department files are accessible.

## Recommendation

This issue is resolved by IT support; reference 'shared drive access denied – missing AD group and stale credentials' when reporting it.

---

[← Back to categories](../../index.md)
