---
hide:
  - navigation
root_cause_id: SDA/unconfirmed-backend-replication-or-auth-escalated
family: SDA
ticket_count: 1
curated: true
self_serviceable: false
---

# Kerberos Token Not Reflecting AD Group Despite Confirmed Membership

[← Back to categories](../../index.md)

## Description

Affected users experience "Access is denied" errors and repeated credential prompts when attempting to open a departmental shared drive. The issue occurs both through a mapped drive letter and via direct UNC path access to the same file server share. Entering credentials multiple times does not resolve the prompts, and the folder remains inaccessible. The issue is account-specific; colleagues on the same team with equivalent share access are able to open the folder without difficulty.

Diagnostic review of the affected user's Active Directory account confirms that the correct security group membership is present. However, the Kerberos token on the affected workstation does not consistently reflect that group membership. The UNC path and drive mapping were verified as correct, ruling out a stale or misconfigured shortcut. The inconsistency between confirmed AD group membership and the token presented during authentication points to a backend replication or authentication-layer issue that could not be isolated to a single cause during initial investigation.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** Windows 10 (100%)
- **Device / platform:** On-premise File Server (SMB) (100%)
- **Team:** Marketing (100%)
- **Region:** NYC-DC (100%)

## Root cause

There is conflicting evidence between directory entitlement state and actual SMB authentication behavior. The affected user's Active Directory group membership is confirmed as correct, but the Kerberos token presented during file share authentication does not consistently reflect that membership. The root cause is attributed to a backend permission replication or file service authentication issue requiring higher-tier review.

## Diagnostics

Steps used to confirm this root cause:

1. Verify the user's Active Directory group membership against the shared drive access group required by the Marketing folder.  
   *Expected:* User belongs to the group that grants the requested drive permission.
2. Ask the user to refresh sign-in after the group change and compare shared drive access with a new session token.  
   *Expected:* Refreshed token includes the updated drive entitlement.
3. Confirm the user is opening the current mapped drive path and not a stale shortcut or obsolete share target.  
   *Expected:* Current shared drive path opens without permission errors.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

1. Document the verified current share path (\\FS-<LOCATION>-01.corplabs.internal\Departments\Marketing), AD group lookup results for <USER> showing SG-Marketing-Share membership, Kerberos token inconsistencies observed on <HOSTNAME> (<IP>), and the failed post-refresh access tests (3/5 denied) for escalation package.
2. Escalate to Tier 2 identity/file services support (assigned to <PERSON>, <EMAIL>) to review domain controller replication state on DC-EAST-03.corplabs.internal, effective group token contents and PAC generation for <USER>, and SMB authentication logs on FS-<LOCATION>-01.corplabs.internal for the denied sessions originating from <IP>.
3. Advise the user <PERSON> (<USER>, ext 4-7823) of the escalation to Tier 2 and provide ticket reference INC-SDA-V0030. Recommend using the SharePoint Online mirror at https://sharepoint.corplabs.com/sites/Marketing as an approved alternate access method for critical files until the backend SMB authentication issue is resolved.

## Recommendation

Resolved by IT through escalation for higher-tier review of a backend replication or authentication-layer inconsistency affecting SMB share access.

---

[← Back to categories](../../index.md)
