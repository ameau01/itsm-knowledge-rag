---
hide:
  - navigation
root_cause_id: DCP/stale-deprecated-compliance-policy-reference
family: DCP
ticket_count: 7
curated: true
self_serviceable: false
---

# Deprecated Compliance Policy Reference Causes False Encryption Noncompliance

[← Back to categories](../../index.md)

## Description

Affected users with Intune-managed devices were blocked from accessing corporate resources — including Exchange Online, SharePoint Online, Microsoft Teams, Outlook, and OneDrive — by Conditional Access enforcement after compliance policy consolidation or baseline refresh activities. The Intune admin console and Company Portal reported encryption signals as missing (e.g., "EncryptionMissing" or "Not reported"), even though BitLocker or device-level encryption was confirmed as fully enabled on most affected endpoints. The issue impacted Windows 10, Windows 11, and Android devices across multiple offices and security groups.

Investigation revealed that affected devices were still evaluating against deprecated or retired compliance policy revisions rather than the current replacement versions. Stale device check-in timestamps meant compliance had not been re-evaluated since the policy change, causing encryption telemetry mappings to fail and Conditional Access to deny access based on outdated compliance state. The noncompliant status persisted through repeated manual sync attempts and remote sync operations, though some devices returned to compliant status after syncing while others required administrative correction of the underlying policy reference.

In at least one case, the missing encryption signal reflected a genuine device state — BitLocker had stalled after an OS update and was not fully enabled — distinguishing that instance from the more common false-reporting pattern. The issue typically affected groups of users tied to specific security or device groups whose policy assignments still pointed to the deprecated policy version.

!!! note "Reported variations"

    - Android devices in the same security group were affected alongside Windows endpoints, with identical Conditional Access blocks on corporate resource access.
    - On Android 11 devices, Company Portal showed encryption status as "Not reported" even though device-level encryption was confirmed enabled at the OS level.
    - In one case, BitLocker had stalled after an OS update and was not fully enabled, meaning the missing encryption signal reflected an actual device state rather than a telemetry reporting gap.
    - Some devices had pending Windows cumulative updates that acted as a secondary blocker to restoring compliance even after the policy reference was corrected.
    - Remote and traveling users experienced extended periods of noncompliance due to prolonged gaps between Intune check-ins, resulting in especially stale compliance evaluations.
    - Some affected users experienced intermittent partial restoration of access to individual services (e.g., Outlook) after a manual sync, while other services (e.g., OneDrive Mobile) remained blocked.
    - In one group, the stale reference pointed to a retired policy scope associated with a legacy assignment group rather than simply an outdated policy version.
    - Mobile device access (e.g., Outlook on a personal phone) remained unaffected, with Conditional Access blocks limited to managed endpoints evaluating against the deprecated policy.

## Affected environment

Distribution across 7 reported cases:

- **Operating system:** Windows 10 21H2 (43%), Windows 10 and Android 11 mixed fleet (14%), Windows 11 21H2 (14%)
- **Device / platform:** Intune-managed (14%), Endpoint (14%), laptop (14%)
- **Team:** Sales (57%), RemoteWorkers (14%), Sales Laptops (14%)
- **Region:** us-east (43%), EMEA (29%), US-West (29%)

## Root cause

Deprecated Intune compliance policies remained assigned to device groups through stale group mappings after policy consolidation. Affected devices continued evaluating against the retired policy revisions, which did not include the current encryption requirement or signal mapping. Stale device check-in status further delayed receipt of corrected policy assignments and updated compliance evaluations.

## Diagnostics

Steps used to confirm this root cause:

1. Confirmed recent Intune check-in status and whether a new compliance evaluation had executed on impacted devices.  
   *Expected:* Device check-in timestamp is current and compliance evaluation has run.
2. Reviewed the failing compliance signal to determine why devices were being marked noncompliant.  
   *Expected:* Required compliance signals report healthy values.
3. Compared assigned compliance policies against Sales group membership and active device scope in Intune.  
   *Expected:* Device is in the intended policy scope with no stale assignment.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Removed the stale Intune assignment referencing CorpCompliance_v2 from the SG-Sales-<LOCATION> group mappings and republished the intended compliance scope with CorpCompliance_v3, verified by admin <PERSON> (<EMAIL>) in the Endpoint Manager console.
2. Forced remote device check-in on all 14 impacted endpoints — including <HOSTNAME> (<USER>, IP <IP>), <HOSTNAME> (<USER>), and <USER>'s Android device — so they would download the corrected policy assignment and trigger a fresh compliance evaluation cycle.
3. Pushed the required encryption configuration (BitLocker for Windows 10 devices, device encryption for Android 11 devices) to endpoints that were specifically failing the encryption compliance signal, including <PERSON>'s Surface and <PERSON>'s Pixel device.
4. Reviewed post-sync compliance reports in Endpoint Manager and confirmed all 14 devices were evaluating only against CorpCompliance_v3 with the expected encryption signal present. <PERSON> (<EMP_ID>) and <PERSON> (<EMP_ID>) both confirmed restored access to protected resources.
5. Directed the remaining 2 outlier devices through manual Company Portal sync or re-enrollment where prior stale enrollment state prevented automatic remediation — one belonged to <PERSON> (<USER>) — then verified Conditional Access no longer blocked compliant devices by confirming successful sign-in from each affected user account.

**Example 2**

1. Confirmed the device <HOSTNAME> (user <USER>, <EMP_ID>) had a stale compliance state with last check-in on 2025-12-29T14:22:00Z, and triggered a remote Intune device check-in plus Company Portal sync to force policy and signal refresh.
2. Reviewed the compliance evaluation details in the Intune admin console and identified that <HOSTNAME> was still referencing the retired 'Require device encryption v1' policy (policyId: 8a3f-comp-enc-v1) instead of the current encryption requirement 'Require device encryption v2' deployed to Sales-West-Devices.
3. Updated the Device Compliance policy mapping for the Sales-West-Devices group so <HOSTNAME> evaluated against 'Require device encryption v2' (policyId: 9b4g-comp-enc-v2) rather than the stale policy reference, and confirmed the assignment propagated in the Intune console.
4. Allowed the device to complete a fresh compliance re-evaluation cycle and verified the encryption status for <HOSTNAME> moved from 'EncryptionMissing/pending' to 'Compliant' after sync; Conditional Access block on Exchange Online was lifted and <PERSON> confirmed email access was restored.
5. Advised <PERSON> (<USER>) to verify BitLocker remained enabled locally via manage-bde -status and to install any pending Windows updates on the Surface Laptop to avoid delayed compliance reporting on the next evaluation cycle. Also recommended periodic manual Company Portal syncs if working remotely from <LOCATION> for extended periods to prevent stale check-in issues.

## Recommendation

The issue was resolved by IT after removing deprecated compliance policy assignments and ensuring affected devices re-evaluated against the current policy revision.

---

[← Back to categories](../../index.md)
