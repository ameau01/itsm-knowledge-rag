---
hide:
  - navigation
root_cause_id: SDA/stale-or-wrong-mapped-share-path
family: SDA
ticket_count: 1
curated: true
self_serviceable: true
---

# Mapped Drive Targeting Retired UNC Path After File Server Migration

[← Back to categories](../../index.md)

## Description

Affected users experience "Access Denied" errors (0x5) when attempting to open a shared network drive via a mapped drive letter. The same error may also occur when navigating directly to the correct current UNC path in Windows Explorer. All subfolders within the share are equally inaccessible, and the issue persists regardless of the access method used.

Intermittent credential prompts appear during access attempts, but entering valid domain credentials does not resolve the error. Active Directory group membership for the affected user is verified as correct, and entitlement checks confirm the user should have access to the share.

The issue is isolated to the individual workstation; colleagues in the same department and security group retain normal access to the share, indicating the problem is specific to the affected user's session or drive configuration rather than a broader permissions or server-side outage.

!!! note "Reported variations"

    - The mapped drive letter points to a retired UNC path from a previous file server migration, while the user believes it references the current server; the direct UNC path to the correct server also fails due to stale cached credentials associated with the outdated path.
    - Credential prompts appear intermittently rather than consistently, and supplying correct credentials each time still results in Access Denied.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** Windows Server 2019 (100%)
- **Device / platform:** on-premises (100%)
- **Team:** FINANCE (100%)
- **Region:** corp-dc-1 (100%)

## Root cause

The affected user's mapped drive was pointing to a stale or retired Finance share path from a previous file server migration. The outdated UNC location produced Access Denied behavior despite valid group membership. Cached credentials associated with the retired path also prevented successful authentication when the user attempted to reach the correct server directly.

## Diagnostics

Steps used to confirm this root cause:

1. Verified the user's Active Directory group membership against the Finance share access control requirements.  
   *Expected:* User belongs to the group that grants the requested drive permission.
2. Requested a sign-out or token refresh and compared access behavior after a new session token was issued.  
   *Expected:* Refreshed token includes the updated drive entitlement.
3. Confirmed the user was opening the current UNC path and remapped the drive to rule out a stale shortcut or cached mapping.  
   *Expected:* Current shared drive path opens without permission errors.

## Resolution

Representative resolutions from prior cases:

1. Confirmed the approved current UNC path for the Finance shared drive (\\fs01\Finance) with the file services configuration and validated that \\fs01-old\Finance was officially retired during the Q1 2026 server consolidation managed by <PERSON>.
2. Removed the stale mapped drive (F: → \\fs01-old\Finance) on <HOSTNAME> using 'net use F: /delete', cleared cached credentials via Credential Manager for user <USER>, and remapped the drive to the current Finance share path with 'net use F: \\fs01\Finance /persistent:yes'.
3. Retested direct UNC access (\\fs01\Finance) and mapped-drive access (F:) with <PERSON> on <HOSTNAME> (<IP>) and verified the Finance folder — including subfolders Reconciliation and Reports — opened without further Access Denied prompts or credential challenges.

## Recommendation

The issue was resolved by IT after identifying and correcting a mapped drive that referenced a retired UNC path from a prior file server migration.

---

[← Back to categories](../../index.md)
