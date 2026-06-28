---
hide:
  - navigation
root_cause_id: SDA/missing-ad-security-group-membership
family: SDA
ticket_count: 23
curated: true
self_serviceable: false
---

# Missing AD Security Group Membership Denies Department Share Access

[← Back to categories](../../index.md)

## Description

Affected users report being unable to open departmental shared drives (most commonly Finance, but also HR, Engineering, and other department folders) from mapped drive letters or direct UNC paths on domain-joined Windows workstations. Access attempts prompt for credentials and then return an "Access is denied" error (0x80070005 / NT_STATUS_ACCESS_DENIED). In some cases the credential prompt loops repeatedly before ultimately failing. Other network shares not gated by the same security group remain accessible, and colleagues in the same department and office can open the identical share without difficulty, confirming the issue is account-specific rather than a file server or network outage.

Standard self-remediation steps — signing out and back in, clearing cached credentials via Credential Manager, and remapping the drive — do not resolve the issue. This persistence distinguishes the problem from stale-credential scenarios and points to a server-side entitlement gap. In at least one case the mapped drive shows a "Disconnected" status, and in another the file server audit log contains explicit NTFS access-denied entries for the affected user's SID.

Investigation in every instance reveals that the affected user's Active Directory account is missing membership in the department-level security group referenced by the share and NTFS ACLs. The absence stems from varied circumstances: incomplete onboarding or inter-department transfer provisioning, automated AD group synchronization or cleanup scripts that inadvertently removed the membership, or an access request that had not yet been fulfilled. Without the group SID in the user's Kerberos token, the file server denies authorization regardless of valid credentials.

!!! note "Reported variations"

    - Missing group membership caused by an onboarding or inter-department transfer process that did not include the required shared-drive entitlement
    - Missing group membership triggered by a scheduled AD group audit or cleanup that inadvertently removed the user from a still-required group
    - Missing group membership caused by an automated nested-group cleanup script or AD synchronization event that dropped the share entitlement
    - Access request submitted through a self-service portal had not yet been provisioned into Active Directory
    - Affected user could browse to the top-level share path but was denied access only at a specific subfolder rather than at the share root
    - Credential prompt looped repeatedly before ultimately returning access denied, rather than presenting a single prompt followed by immediate denial
    - Affected user tested access from a colleague's workstation and observed the same denial, confirming the issue followed the account
    - A separate broken-ACL-inheritance issue on subfolders was identified during investigation but was unrelated to the individual user's missing group membership

## Affected environment

Distribution across 23 reported cases:

- **Operating system:** Windows 10 (70%), Windows Server 2019 (9%), Windows Server 2019 (file server); Windows 10 client (4%)
- **Device / platform:** on-premises (13%), on-premise (13%), On-premises SMB File Server (9%)
- **Team:** Finance (57%), Finance Department (9%), Marketing (4%)
- **Region:** us-east-1 (30%), EMEA (17%), corp-dc-1 (9%)

## Root cause

The affected user's Active Directory account was not a member of the security group required by the department shared drive's share-level and NTFS access control lists. Because the group SID was absent from the user's logon token, the file server denied authorization even though authentication succeeded. The missing membership resulted from provisioning gaps during onboarding or role transfers, automated AD group cleanup scripts, or unfulfilled access requests.

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

1. Verified the share and folder ACL on \\fs01\Finance granted access through the Finance_Read security group by reviewing the NTFS permissions and share-level permissions on the file server.
2. Added user <USER> (<EMP_ID>, CN=<USER>,OU=Finance,OU=Corp Users,DC=corplabs,DC=internal) to the Finance_Read Active Directory security group required for read access to the Finance shared drive. Updated the onboarding checklist and notified manager <PERSON> (<EMAIL>) of the correction.
3. Cleared cached credentials on the user's workstation <HOSTNAME> via Windows Credential Manager to remove the repeated credential prompt against the mapped drive (F:) to \\fs01\Finance.
4. Had the user sign out and sign back in on <HOSTNAME> so the updated Finance_Read group membership was included in a new Kerberos access token. Verified with 'klist' that the refreshed token contained the correct group SID.
5. <PERSON> the network drive (F:) to the current \\fs01\Finance path on <HOSTNAME> and confirmed that user <USER> could open the Finance folder successfully. <PERSON> (<USER>) from the same team verified shared access was unaffected.

## Recommendation

Resolved by IT by adding the affected user's account to the required Active Directory security group and refreshing the logon session to obtain an updated Kerberos token containing the correct group entitlement.

---

[← Back to categories](../../index.md)
