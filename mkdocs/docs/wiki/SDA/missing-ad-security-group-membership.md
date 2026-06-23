---
hide:
  - navigation
root_cause_id: SDA/missing-ad-security-group-membership
family: SDA
ticket_count: 23
curated: true
self_serviceable: false
---

# Shared drive access denied due to missing Active Directory security group membership

[← Back to categories](../../index.md)

## Description

Affected users attempting to open a department shared drive — typically via a mapped network drive letter or a direct UNC path in Windows Explorer — encounter a credentials prompt followed by an "Access is denied" error (commonly error code 0x80070005 or 0x5). Re-entering domain credentials does not resolve the prompt, which loops or fails repeatedly. The issue prevents access to department files on the on-premises file server, while other network shares and resources on the same workstation continue to function normally.

The problem is specific to the affected user's account rather than a general file server outage. Colleagues on the same team, in the same office, and on the same network subnet are typically able to access the same shared folder without difficulty. Clearing saved credentials from Windows Credential Manager, remapping the drive, or signing out and back in does not restore access on its own, which distinguishes this issue from a stale cached credentials problem.

This issue has been observed across multiple departments — including Finance, Marketing, HR, and Engineering — and across various file servers and share paths. Common triggers include recent onboarding or team transfers where the required security group was not provisioned, Active Directory group cleanup or synchronization events that inadvertently removed the user's group membership, and automated group management scripts that dropped entitlements as a side effect of unrelated group changes. In each case, the shared drive's access controls require membership in a specific Active Directory security group, and the affected user's account is not a current member of that group.

!!! note "Reported variations"

    - In some cases, the credentials prompt appears intermittently rather than on every access attempt, with the "Access is denied" error following inconsistently.
    - Users who recently transferred between departments may find that only the new department's shared drive is inaccessible while access to other network shares — including the previous department's share — continues to work.
    - In at least one instance, a follow-up audit of the file server revealed broken ACL inheritance on subfolders beneath the shared drive, which affected additional users beyond the one whose missing group membership was restored; this subfolder permissions issue is a separate remediation item.
    - Some users report that the issue began immediately after an organization-wide Active Directory group cleanup or synchronization window, with access having worked normally the previous day.
    - An automated group management script removing a user from one project-level group has been observed to inadvertently drop the user's membership in the file share access group as a side effect of nested group cleanup.

## Affected environment

Distribution across 23 reported cases:

- **Operating system:** Windows 10 (70%), Windows Server 2019 (9%), Windows Server 2019 (file server); Windows 10 client (4%)
- **Device / platform:** on-premises (13%), on-premise (13%), On-premises SMB File Server (9%)
- **Team:** Finance (57%), Finance Department (9%), Marketing (4%)
- **Region:** us-east-1 (30%), EMEA (17%), corp-dc-1 (9%)

## Root cause

The affected user's Active Directory account is missing membership in the security group that controls access to the department shared drive. Because the file server's share and folder permissions grant access exclusively through that group, the user's sign-in token does not carry the required entitlement, and the file server correctly denies access. The missing membership may result from an incomplete onboarding or team-transfer provisioning process, an Active Directory group cleanup or synchronization event that removed the user, or an automated script that inadvertently dropped the entitlement alongside an unrelated group change.

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

1. Verified the Marketing shared folder access model on FS-<LOCATION>-01 and confirmed that AD group Dept_Share_Access is the required entitlement for the mapped drive and NTFS permissions on \\FS-<LOCATION>-01\DeptShares\Marketing.
2. Added user <USER> (<EMP_ID>) to the Active Directory security group Dept_Share_Access to restore the missing group-based access. Change approved by manager <PERSON> via email.
3. Forced a policy refresh (gpupdate /force) on workstation <HOSTNAME> and instructed <PERSON> to sign out and sign back in so the updated security token would include the new Dept_Share_Access group membership.
4. Retested access to mapped drive Z: (\\FS-<LOCATION>-01\DeptShares\Marketing) from <HOSTNAME> and confirmed <USER> could open the Marketing department folder without further credential prompts or access denied errors.
5. Documented the provisioning gap for <USER> and updated the onboarding checklist to include verification of required department shared-drive group membership. Notified HR contact <PERSON> in the <LOCATION> office to ensure future Marketing hires are flagged for Dept_Share_Access during account setup.

**Example 2**

1. Reviewed the effective access requirements for \\CorpFiles\\Finance and confirmed that user <USER> (<PERSON>, employee ID <EMP_ID>) was not a member of the FINANCE_Share_Access Active Directory security group by querying CN=<USER>,OU=Finance,DC=corplabs,DC=internal.
2. Added <USER> to the FINANCE_Share_Access group via Active Directory Users and Computers to restore the required share and NTFS entitlement for the Finance folder. Change approved by manager <PERSON> (<EMAIL>).
3. Had <PERSON> sign out of the Windows domain session on <HOSTNAME> and sign back in so the refreshed Kerberos logon token would include the updated FINANCE_Share_Access group membership.
4. Verified NTFS permissions and inheritance on \\CorpFiles\\Finance to confirm the FINANCE_Share_Access group retained the expected Modify access level; icacls output showed the correct ACE propagating to child objects.
5. Retested access with <PERSON> from <HOSTNAME> (<IP>) and confirmed the Finance shared drive (F: mapped to \\CorpFiles\\Finance) opened successfully without additional credential prompts or access denied errors.

## Recommendation

This issue is resolved by IT support; reference 'missing AD security group membership for shared drive' when reporting it.

---

[← Back to categories](../../index.md)
