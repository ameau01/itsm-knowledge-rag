---
hide:
  - navigation
root_cause_id: DCP/indeterminate-compliance-refresh-failure
family: DCP
ticket_count: 2
curated: true
self_serviceable: false
---

# Stale Compliance Refresh Leaves Devices Noncompliant Despite Sync Attempts

[← Back to categories](../../index.md)

## Description

Affected users report that their managed devices are marked as noncompliant in Company Portal, triggering Conditional Access blocks that prevent access to corporate resources such as Outlook email and OneDrive. The noncompliant status persists even after manual sync attempts through Company Portal, which complete without error but do not update the compliance state.

On Windows devices, the last device check-in remained stale at approximately 48 hours. A backend sync triggered by support staff registered a check-in attempt but did not cause the compliance record to refresh, indicating the device was not successfully processing compliance signals. No specific policy condition was surfaced in this scenario.

On Android devices, the noncompliance appeared following a compliance policy update and presented as an encryption-related condition tied to a specific device compliance policy. Diagnostics produced mixed findings, including inconsistent encryption reporting from the Android attestation layer and a stale policy assignment following a group membership change. These observations complicated the resolution path and required additional platform-side review by the Intune administration team before a definitive fix could be applied.

Across both platforms, the core behavior was consistent: compliance evaluation failed to complete or refresh properly, leaving devices in an indeterminate noncompliant state that blocked access to business applications through Conditional Access.

!!! note "Reported variations"

    - On Android devices, some units in the affected group cleared their noncompliant status after a manual Company Portal sync, while the majority remained noncompliant and did not update promptly — indicating inconsistent compliance refresh behavior across the same device population.
    - The Android noncompliance specifically referenced an encryption-related policy condition, whereas the Windows case did not surface an encryption indicator and instead presented primarily as a stale check-in with no policy condition called out.
    - The issue affected multiple users within a single group, suggesting group-level policy targeting or group membership changes as a contributing scope factor.

## Affected environment

Distribution across 2 reported cases:

- **Operating system:** Windows 10 21H2 (50%), Windows 10 and Android 11 mixed fleet (50%)
- **Device / platform:** Windows (50%), Intune-managed (50%)
- **Team:** Sales (100%)
- **Region:** us-east-1 (100%)

## Root cause

A stale Intune MDM check-in prevented the affected devices from refreshing their compliance evaluation, leaving Conditional Access to enforce an outdated noncompliant state. Available evidence pointed to failed or incomplete compliance state refresh rather than a confirmed BitLocker or OS-version policy violation. A single root cause could not be confirmed from first-line diagnostics because the available compliance, encryption, and assignment signals were inconsistent.

## Diagnostics

Steps used to confirm this root cause:

1. Confirmed whether the device had a recent Intune check-in and whether a manual and remote sync updated compliance evaluation.  
   *Expected:* Device check-in timestamp is current and compliance evaluation has run.
2. Reviewed likely failing compliance signals by asking for BitLocker status and pending Windows feature or quality updates.  
   *Expected:* Required compliance signals report healthy values.
3. Compared the incident pattern against policy assignment behavior to determine whether the device appeared to be in an incorrect or stale compliance policy scope.  
   *Expected:* Device is in the intended policy scope with no stale assignment.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Have <PERSON> connect <HOSTNAME> to a stable network at the <LOCATION> office (or VPN), sign in to Windows with her <USER> credentials, open Company Portal, and run a manual Sync followed by a full device reboot to restart MDM services and the Intune Management Extension.
2. From the Intune admin center, trigger a remote device sync for <HOSTNAME> and confirm the device's last check-in timestamp updates from the previously stale 48-hour value (≈2025-12-28T20:00Z) to a current timestamp.
3. After check-in resumes, review the reported compliance signals for encryption and OS update posture on <HOSTNAME>, then remediate any outstanding requirement by enabling BitLocker if not active (via manage-bde -on C:) and installing pending Windows 10 21H2 quality updates through Settings > Windows Update.
4. Force a new compliance evaluation by waiting for the refreshed check-in to complete on <HOSTNAME>, then verify the device status changes from NonCompliant to Compliant in both the Intune device blade and Company Portal for user <USER>.
5. Confirm Conditional Access access is restored by having <PERSON> reopen Outlook on <HOSTNAME> and validate that email sign-in to <EMAIL> is no longer blocked. Notify <PERSON> at phone <PHONE> once the ticket is fully resolved.

**Example 2**

1. Collected updated Intune compliance logs, policy assignment details, and Company Portal screenshots from <PERSON> (<EMAIL>, <HOSTNAME>) and <PERSON> (<EMAIL>) to compare device-side encryption status and service-side compliance evaluation state in Endpoint Manager.
2. Requested a manual Company Portal sync on both <HOSTNAME> and <PERSON>'s device, then monitored the Intune compliance evaluation pipeline for a completed re-evaluation cycle to determine whether the encryption signal discrepancy and noncompliant state would self-correct after a fresh attestation report.
3. Escalated to the Intune administration team (assigned to agent <PERSON>, <USER>) for deeper review of compliance evaluation history, encryption signal propagation from Android attestation, and assignment processing for the Sales-Mobile-Users group before making any policy changes to 'Sales-Mobile-Encryption-v3'.

## Recommendation

Resolved by IT after escalation for platform-side review; reference as stale compliance refresh causing persistent noncompliant state and Conditional Access blocks.

---

[← Back to categories](../../index.md)
