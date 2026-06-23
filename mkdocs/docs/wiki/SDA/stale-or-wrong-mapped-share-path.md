---
hide:
  - navigation
root_cause_id: SDA/stale-or-wrong-mapped-share-path
family: SDA
ticket_count: 1
curated: true
self_serviceable: true
---

# Mapped drive targeting retired file server path causes access denial

[← Back to categories](../../index.md)

## Description

Affected users experience "Access Denied" errors (error code 0x5) when attempting to open files on a mapped network drive — in reported cases, the Finance shared drive mapped as the F: drive. The denial may be accompanied by intermittent credential prompts that persist even after the user enters valid credentials. Attempts to access subfolders within the share (such as Reconciliation or Reports directories) fail in the same way.

Because the user's group membership and permissions are actually valid, the issue can initially appear identical to a permissions or credential problem. Colleagues in the same department may have no trouble accessing the same share, which can make the problem seem isolated to a single workstation or user session. Standard troubleshooting steps such as signing out, refreshing authentication tokens, or re-entering credentials do not resolve the error.

On closer examination, the mapped drive letter is found to be pointing to an outdated or retired server path (for example, a UNC path belonging to a file server that was decommissioned during a prior migration or consolidation) rather than the current, active share path. The stale mapping causes all access attempts through that drive letter to be directed to the wrong location, producing access-denied behavior even though the user has the correct permissions on the current share.

!!! note "Reported variations"

    - Some affected users may also see credential prompts when attempting to access the share directly via the correct UNC path, due to stale cached credentials associated with the old server name lingering on the workstation.
    - The issue may surface only after a file server migration or consolidation, affecting users whose drive mappings were not updated as part of the transition.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** Windows Server 2019 (100%)
- **Device / platform:** on-premises (100%)
- **Team:** FINANCE (100%)
- **Region:** corp-dc-1 (100%)

## Root cause

The user's mapped network drive was configured with a UNC path pointing to a retired file server that was decommissioned during a previous server consolidation. Because the old path is no longer valid, any access attempt through the mapped drive is directed to the wrong location, resulting in access-denied errors despite the user holding correct group membership and permissions on the current share.

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

This issue is resolved by IT support; reference "stale or incorrect mapped share path" when reporting it.

---

[← Back to categories](../../index.md)
