---
hide:
  - navigation
root_cause_id: DCP/encryption-telemetry-broken-after-os-or-hardware-change
family: DCP
ticket_count: 4
curated: true
self_serviceable: false
---

# Intermittent Encryption Signal Loss After OS Update Causes False Noncompliance

[← Back to categories](../../index.md)

## Description

Affected users report that their corporate-managed devices are marked Noncompliant in Intune immediately following an OS update, OS upgrade, or a compliance policy change that introduces an encryption requirement. Although encryption (BitLocker on Windows, device encryption on Android) appears enabled when verified locally via Control Panel or Company Portal, the Intune compliance service does not reliably receive or retain the encryption signal. Conditional Access consequently blocks access to Microsoft 365 resources including Outlook, Teams, SharePoint Online, Exchange Online, and other Office 365 services.

Forced device syncs and compliance reevaluations initiated from the Intune admin console may briefly return the device to a Compliant state, but the status reverts to Noncompliant within minutes. In some cases the device's last check-in timestamp in Intune is significantly stale—up to nine days old—meaning the compliance state never refreshes after the OS change. The intermittent or absent encryption telemetry persists across reboots and repeated Company Portal syncs performed by the affected users.

The issue has been observed on Windows 10, Windows 11, and Android 11 corporate-managed devices across multiple office locations. In all reported cases, policy scope reviews confirm that the affected devices are correctly targeted by the relevant encryption compliance policy with no duplicate or stale assignments present.

!!! note "Reported variations"

    - Multiple Android devices simultaneously affected after an admin-pushed compliance policy change adding an encryption requirement, rather than after an OS update
    - Device check-in timestamp in Intune stale by over a week following an OS upgrade, preventing any compliance refresh until a manual sync is forced
    - Encryption signal briefly restored after a forced compliance reevaluation from the admin console, then reverted to missing within minutes
    - Windows 10 to 21H2 feature upgrade triggering the issue, as distinct from a routine overnight patch

## Affected environment

Distribution across 4 reported cases:

- **Operating system:** Windows 10 20H2 (25%), Android 11 (25%), Windows 11 22H2 (25%)
- **Device / platform:** Windows (50%), Intune MDM (25%), laptop (25%)
- **Team:** Sales (50%), All Corporate Laptops (25%), Engineering (25%)
- **Region:** us-east (50%), EMEA (25%), US-West (25%)

## Root cause

A recent OS update or a newly tightened compliance policy left the device's Intune management check-in state stale, preventing the BitLocker or device-encryption status from being reported back to the compliance service. Because the encryption-required compliance policy depended on that signal, back-end evaluations intermittently or persistently missed the encryption state, and Conditional Access consumed a false Noncompliant result until device telemetry and policy evaluation were refreshed and stabilized.

## Diagnostics

Steps used to confirm this root cause:

1. Confirm the device has recently checked in to Intune and that a compliance evaluation was triggered.  
   *Expected:* Device check-in timestamp is current and compliance evaluation has run.
2. Review the encryption compliance signal and compare the endpoint BitLocker state with the value reported in Intune.  
   *Expected:* Required compliance signals report healthy values.
3. Compare the assigned EncryptionRequired compliance policy with the user's device group membership and assignment scope.  
   *Expected:* Device is in the intended policy scope with no stale assignment.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Confirmed <HOSTNAME> (user <USER>, IP <IP>) had checked in to Intune, then forced a fresh device sync and immediate compliance re-evaluation from the admin console.
2. Validated that the failing compliance control was the EncryptionRequired encryption requirement and guided <PERSON> through re-running the corporate BitLocker enablement process on the laptop via the Company BitLocker enable script.
3. Verified local encryption state on <HOSTNAME> using manage-bde -status and confirmed the device began reporting encryption status consistently to Intune's Device Compliance Service after remediation.
4. Re-published the applicable EncryptionRequired compliance policy to the Sales-Devices-US-East group so the corrected device state for <USER> would be re-evaluated without waiting for the next normal 8-hour cycle.
5. Monitored <HOSTNAME> for 45 minutes until the compliance state remained healthy and confirmed Conditional Access no longer blocked Outlook, Teams, and Office 365 access for <EMAIL>. <PERSON> confirmed full productivity restored from the <LOCATION> office.

**Example 2**

1. Triggered a remote Intune sync and forced a fresh device compliance evaluation for the affected laptop <HOSTNAME> (registered to <USER>, <EMP_ID>) from the Intune admin console.
2. Reviewed the failing compliance signal for <USER>'s device and confirmed the missing attribute was the BitLocker encryption reporting state rather than OS version or policy assignment.
3. Re-applied the BitLocker reporting/compliance policy to the device <HOSTNAME> (IP <IP>) and initiated encryption state re-reporting via the Intune management extension.
4. Instructed the user to reboot the laptop, install pending Windows updates, and run a Company Portal sync to complete local policy refresh. Contacted <PERSON> at <PHONE> to walk through the reboot and sync steps at her <LOCATION> office workstation.
5. Monitored Intune until the device reported its encryption state correctly, changed back to Compliant, and Conditional Access allowed Outlook and SharePoint access again. Confirmed with <EMAIL> that email and SharePoint were accessible, and notified <USER> on the endpoint team that the issue was resolved.

## Recommendation

Resolved by IT after device telemetry and compliance policy evaluation were refreshed and stabilized to restore accurate encryption signal reporting.

---

[← Back to categories](../../index.md)
