---
hide:
  - navigation
root_cause_id: DCP/indeterminate-compliance-refresh-failure
family: DCP
ticket_count: 2
curated: true
self_serviceable: false
---

# Conditional Access block due to indeterminate compliance refresh failure

[← Back to categories](../../index.md)

## Description

Affected users find that their managed devices are marked as "NonCompliant" in Company Portal, and Conditional Access subsequently blocks access to Microsoft 365 applications such as Outlook and OneDrive. The block may appear suddenly on a device that was previously functioning normally, with no obvious change on the user's end. Email and cloud file access are unavailable until the compliance state is corrected.

When users attempt to resolve the issue by running a manual sync from Company Portal, the sync may appear to complete without returning an error, yet the device's compliance status does not update. The last successful check-in timestamp displayed in Company Portal remains stale — in some cases by 48 hours or more — suggesting the device is not successfully refreshing its compliance evaluation with the management service.

Company Portal may display a specific noncompliant condition, such as an encryption-related policy failure, but the information shown can be misleading. In the reported cases, first-line diagnostics were unable to confirm that the flagged condition (for example, disk encryption status or operating system version) was genuinely out of compliance. The noncompliant state persisted even after remote sync attempts initiated from the administration console, further indicating that the compliance evaluation itself was failing to complete rather than reflecting a true policy violation.

The issue has been observed on both Windows and Android devices and has affected multiple users within the same organizational group simultaneously, particularly following a compliance policy update or group membership change.

!!! note "Reported variations"

    - On Android devices, Company Portal may display an encryption-related compliance failure referencing a specific policy name, even though the actual encryption status of the device cannot be confirmed as noncompliant from available evidence.
    - Following a compliance policy update or Azure AD group membership change, multiple devices in the same user group may be affected simultaneously; some devices may self-resolve after a manual sync while most remain stuck in a noncompliant state.
    - A remote sync triggered from the Intune administration console may register a check-in attempt on the backend without actually updating the device's compliance record.

## Affected environment

Distribution across 2 reported cases:

- **Operating system:** Windows 10 21H2 (50%), Windows 10 and Android 11 mixed fleet (50%)
- **Device / platform:** Windows (50%), Intune-managed (50%)
- **Team:** Sales (100%)
- **Region:** us-east-1 (100%)

## Root cause

The device's regular check-in with the Intune mobile device management service stalled or failed to complete, preventing the compliance evaluation from refreshing. Because the compliance state was not updated, Conditional Access continued to enforce an outdated "NonCompliant" determination and blocked access to protected applications. In some cases, the available compliance, encryption, and policy-assignment signals were inconsistent, making it impossible to confirm a single root cause from standard first-line diagnostics alone; platform-side review by the Intune administration team was required to clear the stale state.

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

This issue is resolved by IT support; reference "indeterminate compliance refresh failure" when reporting it.

---

[← Back to categories](../../index.md)
