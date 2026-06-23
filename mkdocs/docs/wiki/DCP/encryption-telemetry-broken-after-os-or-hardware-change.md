---
hide:
  - navigation
root_cause_id: DCP/encryption-telemetry-broken-after-os-or-hardware-change
family: DCP
ticket_count: 4
curated: true
self_serviceable: false
---

# Encryption compliance signal lost after OS update or policy change

[← Back to categories](../../index.md)

## Description

Affected users find that their corporate-managed devices — both Windows laptops and Android phones — are marked as Noncompliant in Intune and blocked from Microsoft 365 services such as Outlook, Teams, SharePoint Online, and Exchange Online webmail. The block is enforced by Conditional Access immediately after a recent operating system update or a newly tightened compliance policy requiring encryption. Users confirm that encryption (BitLocker on Windows or device encryption on Android) appears enabled locally or in Company Portal, yet the Intune compliance portal continues to report the encryption signal as missing or not detected.

The noncompliant state may appear intermittently: a forced device sync can briefly return the device to a compliant status before it reverts to noncompliant within minutes. In some cases the device's last Intune check-in timestamp is visibly stale — up to nine or more days old — indicating that the management connection did not refresh after the OS change. The issue has been observed across multiple offices and device platforms, and can affect several users simultaneously when a compliance policy change is rolled out to a group of devices at once.

Affected users are unable to sign in to any Conditional Access–protected resource from the impacted device, regardless of whether they use a desktop client or a web browser. Rebooting the device alone does not resolve the problem.

!!! note "Reported variations"

    - On Android devices, the issue can surface immediately after a tightened encryption compliance policy is pushed, even without an OS update, because the server-side evaluation intermittently loses the encryption signal that Company Portal reports locally.
    - Some Windows devices show a check-in timestamp that is many days old (nine or more days stale), meaning the compliance state never refreshed after the OS upgrade completed.
    - In certain cases the compliance status briefly flips to Compliant after a manual sync but reverts to Noncompliant within minutes, rather than remaining persistently noncompliant.

## Affected environment

Distribution across 4 reported cases:

- **Operating system:** Windows 10 20H2 (25%), Android 11 (25%), Windows 11 22H2 (25%)
- **Device / platform:** Windows (50%), Intune MDM (25%), laptop (25%)
- **Team:** Sales (50%), All Corporate Laptops (25%), Engineering (25%)
- **Region:** us-east (50%), EMEA (25%), US-West (25%)

## Root cause

An operating system update or a newly applied encryption compliance policy causes the device's encryption status to stop reporting reliably to the Intune compliance service. Although encryption is active on the device itself, the backend telemetry that Intune uses to evaluate compliance either goes stale (because the device has not fully checked in since the update) or fluctuates intermittently. Because Conditional Access relies on that compliance evaluation, it treats the device as noncompliant and blocks access to protected resources until the encryption signal is stabilized through device remediation and a fresh compliance evaluation.

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

1. Validated that affected Android devices for <USER> (<HOSTNAME>), <USER> (<HOSTNAME>), and <USER> (<HOSTNAME>) had encryption enabled locally in Company Portal and confirmed the issue was specific to the Intune compliance encryption signal rather than user enrollment state.
2. Forced fresh device check-ins and Intune policy synchronizations for all three impacted devices from the <LOCATION> office to clear stale compliance evaluations and trigger new backend compliance calculations. Sync commands issued by <USER> via the Intune admin console.
3. Reviewed the encryption requirement assignment against the impacted Sales device scope (<EMP_ID>, <EMP_ID>, <EMP_ID>) to confirm the devices were targeted by the intended policy pushed by <USER> and not by a stale or duplicate assignment.
4. Remediated affected endpoints by having users update the Android OS and refresh the management client state, including Company Portal re-registration where needed on <HOSTNAME> and <HOSTNAME>, to restore consistent encryption telemetry reporting. Coordinated by <PERSON> (<USER>) with on-site support in <LOCATION>.
5. Re-ran compliance evaluation after remediation and confirmed the devices for <USER>, <USER>, and <USER> returned to Compliant status in Intune, which allowed Conditional Access to permit normal user sign-in again. Final verification completed by <USER> at 16:40 UTC.

## Recommendation

This issue is resolved by IT support; reference 'encryption compliance signal lost after OS or policy change' when reporting it.

---

[← Back to categories](../../index.md)
