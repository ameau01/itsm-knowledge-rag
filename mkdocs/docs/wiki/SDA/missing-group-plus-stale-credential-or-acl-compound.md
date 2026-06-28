---
hide:
  - navigation
root_cause_id: SDA/missing-group-plus-stale-credential-or-acl-compound
family: SDA
ticket_count: 17
curated: true
self_serviceable: false
---

# Compound Missing AD Group Membership and Stale Cached Credentials Block Share Access

[← Back to categories](../../index.md)

## Description

Affected users on domain-joined Windows 10 workstations report being unable to open departmental shared drives (most commonly Finance, but also Sales and Engineering) via mapped network drives or direct UNC paths. The mapped drive repeatedly prompts for credentials and then returns an "Access is denied" error (frequently surfaced as 0x80070005 or NT_STATUS_ACCESS_DENIED). The issue is isolated to specific user accounts — colleagues on the same team with valid group membership can access the same share without difficulty, confirming the problem is not a broader server or network outage.

Investigation consistently reveals a compound condition: the affected user's Active Directory account is missing the required security group that governs access to the department share, and the workstation retains stale cached credentials or an outdated security token that has not been refreshed to reflect the current account state. The stale credential causes the repeated prompt cycle — the workstation presents outdated authentication material, the file server rejects it, and the user is re-prompted in a loop before ultimately receiving access denial. In some cases the user appears in a related distribution list but not in the security group actually referenced by the share ACL, creating a false impression of valid membership.

Contributing factors observed across tickets include broken NTFS permission inheritance or explicit deny entries on subfolders, legacy individual-SID ACL entries from prior migrations conflicting with the group-based model, stale Group Policy Object references affecting drive-mapping behavior, and delayed token evaluation on the file server following same-day AD group changes. The issue typically surfaces after a password reset, an AD group cleanup, or a weekend maintenance window.

!!! note "Reported variations"

    - Onset immediately following a corporate password reset, with stale Credential Manager entries retaining the old password on the mapped drive.
    - Missing group membership resulted from a newly submitted access request that had not yet propagated to the user's logon token, rather than an inadvertent removal.
    - File server retained stale group evaluation from before a same-day AD membership update, delaying recognition of newly granted entitlements.
    - Broken NTFS permission inheritance or an explicit deny entry on a subfolder compounded the missing-group condition, blocking access even after group membership was corrected.
    - A legacy explicit allow entry tied to an individual user SID from a prior migration created conflicting ACL state alongside the expected group-based permissions.
    - A stale Group Policy Object reference (e.g., an outdated shared-drive mapping policy) contributed to drive-mapping misbehavior on the affected workstation.
    - Affected user's account appeared in a departmental distribution list but not in the corresponding security group referenced by the share ACL, giving a false appearance of valid membership.
    - One affected user attempted self-remediation by deleting and remapping the drive via command-line tools without success; the issue persisted until the underlying entitlement and credential state were corrected.

## Affected environment

Distribution across 17 reported cases:

- **Operating system:** Windows 10 (71%), Windows Server 2019 (18%), Windows 10 Pro (domain-joined) (6%)
- **Device / platform:** on-premises (41%), Corporate Windows domain (6%), On-prem VMware-hosted file server (6%)
- **Team:** Finance (71%), Dept-Engineering (6%), Finance_Team (6%)
- **Region:** us-east-1 (65%), us-east-1 (corporate network) (6%), us-east-1 (corporate datacenter) (6%)

## Root cause

The affected user's Active Directory account was missing the required security group membership granting access to the departmental shared drive, often due to an AD group cleanup, organizational restructure, or a newly requested addition that had not yet propagated. The condition was compounded by stale cached SMB credentials or an unrefreshed Kerberos token on the workstation, causing repeated credential prompts and continued access denial even when correct credentials were supplied. In several cases, broken NTFS permission inheritance or legacy per-user ACL entries on the share further contributed to the access failure.

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

Resolved by IT by restoring the correct Active Directory security group membership, clearing stale cached credentials, and refreshing the user's security token and session context.

---

[← Back to categories](../../index.md)
