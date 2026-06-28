---
hide:
  - navigation
root_cause_id: DCP/stale-checkin-missing-encryption-signal
family: DCP
ticket_count: 27
curated: true
self_serviceable: false
---

# Stale Intune Check-In Causes Missing Encryption Signal and Noncompliance

[← Back to categories](../../index.md)

## Description

Affected users on corporate-managed devices — including Windows 10/11 laptops, macOS endpoints, iOS/iPadOS devices, and Android mobile devices — are blocked from accessing Microsoft 365 resources (Exchange Online, SharePoint, Teams, Outlook) and other Conditional Access–protected services such as corporate VPN. Azure AD Conditional Access evaluates the device as noncompliant, and users receive errors such as "Your device is not compliant" or "You can't get there from here." Company Portal reflects a noncompliant status with a stale last-sync timestamp.

The underlying compliance failure is a missing or unreported encryption signal in Intune. Device records show the encryption attribute as blank, unknown, "Not Encrypted," "EncryptionNotReported," or "EncryptionRequired," even when local encryption (BitLocker, FileVault, or native device encryption) is confirmed enabled on the endpoint. The affected devices have not completed a successful Intune check-in for periods ranging from approximately 36 hours to more than 14 days, preventing the Device Compliance Service from receiving a current encryption status.

Manual or remote sync attempts do not always resolve the issue on the first try. In several cases, the device briefly shows as compliant in the portal after a forced sync, but Conditional Access continues to block access based on older noncompliant evaluations until a full compliance re-evaluation incorporating a fresh encryption signal completes. The issue has been observed on individual devices and in bulk — in one case affecting approximately 12–14 devices simultaneously after a compliance policy update — disrupting access during time-sensitive work. Temporary Conditional Access exemptions were applied in some instances to restore productivity while compliance state caught up.

!!! note "Reported variations"

    - On macOS devices, the missing signal corresponds to FileVault; in at least one case FileVault was not yet fully enabled, requiring user-side enablement before compliance could be restored.
    - On Android devices, the stale check-in window reached up to 14 days, with encryption reported as "Not reported" despite all other policy conditions passing.
    - On iOS/iPadOS devices, encryption status appeared as "unknown" or "not reported" rather than explicitly failing, and in one case a scheduled compliance policy update immediately triggered the stale state.
    - Following a hardware change such as a motherboard replacement, TPM attestation data was invalidated, causing Intune to report encryption as noncompliant despite BitLocker being enabled locally.
    - BitLocker encryption was found paused after a BIOS update, preventing the encryption signal from being reported even though the device was online and connected.
    - In some cases a forced sync briefly flipped the device to compliant in Intune, but Conditional Access continued to deny access based on an older evaluation until a full re-evaluation completed.
    - After a compliance policy update, multiple devices within the same policy group became noncompliant simultaneously, with a subset requiring individual remediation because BitLocker was not enabled or had not reported status.
    - The issue affected access to non-Microsoft gated resources such as corporate VPN, depending on the organization's Conditional Access policy scope.

## Affected environment

Distribution across 27 reported cases:

- **Operating system:** Windows 10 21H2 (37%), Windows 10 22H2 (7%), Android 11 (4%)
- **Device / platform:** Windows (19%), laptop (15%), macOS (7%)
- **Team:** Sales (44%), Marketing (7%), RemoteWorkers (7%)
- **Region:** US-East (41%), EMEA (41%), NA (7%)

## Root cause

Affected devices had not checked in to Intune within the expected sync window, leaving the required encryption compliance signal (BitLocker, FileVault, or native device encryption) absent or stale in the device inventory. Because the compliance policy required device encryption and no current signal was available, the Device Compliance Service evaluated the devices as noncompliant. Conditional Access then enforced the noncompliant result and blocked access to protected corporate resources.

## Diagnostics

Steps used to confirm this root cause:

1. Confirmed the device's recent Intune check-in status and whether compliance evaluation had run after the reported access issue.  
   *Expected:* Device check-in timestamp is current and compliance evaluation has run.
2. Reviewed the failing compliance signal for device encryption to determine why the endpoint was marked noncompliant.  
   *Expected:* Required compliance signals report healthy values.
3. Compared the assigned compliance policy with the device's intended scope and assignment to rule out stale or incorrect targeting.  
   *Expected:* Device is in the intended policy scope with no stale assignment.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Validated that <HOSTNAME>'s Intune check-in was stale (last seen 2025-12-27T05:32:00Z) and that the active compliance failure for <USER> (<EMP_ID>) was tied to the missing BitLocker encryption signal rather than a broader enrollment failure.
2. Had <PERSON> run a manual Company Portal sync on <HOSTNAME> and reboot the device to trigger a fresh management check-in and compliance evaluation cycle against the 'Sales-Win10-Standard' policy.
3. Verified BitLocker status on <HOSTNAME> via the manage-bde -status command and confirmed full disk encryption was enabled on the OS drive (C:), so the required encryption compliance signal could be reported back to Intune's Device Compliance Service.
4. Triggered a follow-up Intune sync on <HOSTNAME> after encryption status was confirmed active, allowing the device record to refresh and the compliance state to be recalculated by Device Compliance Service. Agent <PERSON> monitored the sync from the Intune admin console.
5. Confirmed <HOSTNAME> returned to compliant status in Intune at approximately 06:45 UTC and that Conditional Access no longer blocked <EMAIL> access to Exchange Online email and SharePoint Online. <PERSON> verified he could open Outlook and SharePoint successfully.
6. Used the documented temporary access exception (applied by <PERSON> for <USER>'s account) only during the remediation window and removed reliance on the workaround once compliant reporting was restored on <HOSTNAME>.

**Example 2**

1. Validated that <HOSTNAME> (enrolled under <USER>, <EMP_ID>) had not checked in to Intune for approximately 72 hours (last check-in 2025-12-24T22:48:00Z) and confirmed the missing BitLocker encryption attribute was the compliance signal causing the Noncompliant state.
2. Triggered a remote device sync from the Intune admin console targeting <HOSTNAME> and had <PERSON> retry local sync from Company Portal to force a fresh compliance evaluation.
3. Reapplied the assigned encryption/compliance policy (ENG-RemoteWorkers-Compliance-v3) so the endpoint <HOSTNAME> could submit the required BitLocker status back to Intune device inventory.
4. Used re-enrollment as the remediation path for devices that still failed to report encryption after sync. <PERSON> guided <USER> through the re-enrollment steps, then verified <HOSTNAME> resumed normal management check-in from IP <IP>.
5. Confirmed the device compliance state for <HOSTNAME> returned to Compliant and removed the temporary Conditional Access exemption for <USER> after SharePoint and Teams access was restored. <PERSON> confirmed full access at 2025-12-28T01:45:00Z.

## Recommendation

Resolved by IT by forcing a device sync, confirming encryption enablement, and allowing a full compliance re-evaluation to restore compliant status and lift Conditional Access blocks.

---

[← Back to categories](../../index.md)
