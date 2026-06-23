---
hide:
  - navigation
root_cause_id: DCP/stale-deprecated-compliance-policy-reference
family: DCP
ticket_count: 7
curated: true
self_serviceable: false
---

# Noncompliance caused by stale deprecated Intune compliance policy reference

[← Back to categories](../../index.md)

## Description

Affected users find that their Intune-managed devices are marked as noncompliant, with Conditional Access blocking access to corporate resources such as Exchange Online, SharePoint, Teams, and OneDrive. The compliance failure typically appears in Company Portal as a missing or unreported encryption signal — for example, "Encryption not enabled," "EncryptionMissing," or "Not reported" — even though device-level encryption (such as BitLocker on Windows or native encryption on Android) is confirmed to be active and healthy on the endpoint.

The issue commonly surfaces after a compliance policy change, consolidation, or baseline refresh carried out by an administrator. Devices continue to evaluate against a retired or deprecated compliance policy revision rather than the current one, so the encryption requirement is assessed using outdated criteria that do not correctly detect the device's actual encryption state. As a result, Conditional Access treats the devices as noncompliant and denies sign-in to protected services.

In many cases, affected devices also have stale Intune check-in timestamps — sometimes days old — which compounds the problem by preventing the updated policy assignment from reaching the device and delaying compliance re-evaluation. Manual sync attempts from Company Portal may succeed at the device level but do not resolve the noncompliant status because the underlying policy reference remains pointed at the deprecated revision.

The issue has been observed across both Windows 10/11 and Android 11 devices and has affected individual users as well as larger groups of devices (up to approximately 18 endpoints in a single incident). It tends to cluster within specific device groups or security groups — such as regional sales teams or remote worker groups — that were scoped to the retired policy assignment.

!!! note "Reported variations"

    - Some devices that were reassigned to the correct policy still required endpoint-level remediation — such as completing a stalled BitLocker enablement or installing pending Windows cumulative updates — before compliance could be restored.
    - Android devices exhibited the same stale policy reference behavior, with encryption reported as "Not reported" in Company Portal rather than "Encryption not enabled," despite device-level encryption being active.
    - In some cases, devices checked in successfully and remote sync completed without error, but compliance status remained noncompliant because the sync did not correct the underlying deprecated policy assignment.

## Affected environment

Distribution across 7 reported cases:

- **Operating system:** Windows 10 21H2 (43%), Windows 10 and Android 11 mixed fleet (14%), Windows 11 21H2 (14%)
- **Device / platform:** Intune-managed (14%), Endpoint (14%), laptop (14%)
- **Team:** Sales (57%), RemoteWorkers (14%), Sales Laptops (14%)
- **Region:** us-east (43%), EMEA (29%), US-West (29%)

## Root cause

After a compliance policy update or consolidation in Intune, the affected devices remained assigned to a deprecated or retired compliance policy revision through stale group assignment mappings. Because the outdated policy did not include the current encryption signal mapping, Intune evaluated the devices against criteria that could not correctly detect their encryption status, producing a false noncompliant result. This was often compounded by devices having stale check-in timestamps, which prevented them from receiving the corrected policy assignment and completing a fresh compliance evaluation.

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

This issue is resolved by IT support; reference 'stale deprecated compliance policy reference' when reporting it.

---

[← Back to categories](../../index.md)
