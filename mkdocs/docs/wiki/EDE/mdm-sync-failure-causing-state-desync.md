---
hide:
  - navigation
root_cause_id: EDE/mdm-sync-failure-causing-state-desync
family: EDE
ticket_count: 3
curated: true
self_serviceable: false
---

# BitLocker compliance mismatch due to MDM sync failure with Intune

[← Back to categories](../../index.md)

## Description

Affected users find that their managed Windows laptops are reported as noncompliant for disk encryption in Microsoft Intune and the Company Portal, even though BitLocker is confirmed as enabled locally on the device's OS drive. The device may show encryption as fully complete when checked directly (for example, via local status tools), yet Intune continues to display a status such as "EncryptionNotEnabled" or "NotEncrypted." The BitLocker recovery key is not visible in Azure AD or Intune, leaving IT support unable to confirm or retrieve the key through normal management channels.

In some cases, the local BitLocker configuration itself is incomplete — for instance, only a numerical password protector may be present on the drive with no hardware-bound TPM protector, despite the TPM being reported as ready. In other cases, the TPM protector and local encryption are fully healthy, but a device synchronization error prevents the recovery key from being transmitted to the management service. Either way, the result is the same: the device appears noncompliant in Intune, the recovery key is missing from the management portal, and the affected user may be flagged during compliance reviews.

The issue has been observed on devices in the Sales group covered by corporate BitLocker policies, across multiple office locations and device models including Surface Laptop 4 hardware. Affected users typically notice the problem when checking their compliance status in the Company Portal, during routine compliance reviews, or when attempting to verify recovery key availability before travel or client engagements. Manual Intune sync attempts initiated by the user from the device do not resolve the discrepancy.

!!! note "Reported variations"

    - The device may show a specific MDM sync error (such as error code 0x80180014) across multiple scheduled check-ins, completely blocking recovery key escrow despite healthy local encryption and TPM status.
    - In some cases, the TPM protector is not bound to the encrypted drive — only a numerical password protector exists — even though the TPM hardware is ready, resulting in an incomplete protector configuration that compounds the compliance reporting gap.
    - Azure AD may log a recovery key escrow event for the device while Intune simultaneously continues to report the device as not encrypted and does not display the key, creating a visibility mismatch between the two management surfaces.

## Affected environment

Distribution across 3 reported cases:

- **Operating system:** Windows 10 21H2 (33%), Windows 11 (33%), Windows 10 20H2 (33%)
- **Device / platform:** laptop (67%), Surface Laptop 4 (33%)
- **Team:** Sales (100%)
- **Region:** us-west-2 (67%), us-east-1 (33%)

## Root cause

BitLocker encryption starts successfully on the device, but intermittent synchronization failures between the device and the Intune mobile device management (MDM) service prevent the recovery key from being properly transmitted to Azure AD and Intune. This leaves encryption active locally while the management systems have no record of the recovery key and continue to report the device as not encrypted. In some instances, the device's BitLocker protector configuration is also left incomplete — missing the hardware-bound TPM protector — because the management sync did not fully reconcile before or after encryption was initiated.

## Diagnostics

Steps used to confirm this root cause:

1. Confirm TPM readiness on the laptop and verify whether a BitLocker protector is present and usable.  
   *Expected:* TPM is ready and a valid encryption protector exists.
2. Verify the assigned Intune BitLocker policy and review the latest MDM sync and compliance evaluation state for the endpoint.  
   *Expected:* Device receives the active encryption policy without assignment errors.
3. Check whether the current BitLocker recovery key escrowed successfully to the management service and is visible to support tooling.  
   *Expected:* Current recovery key is escrowed and visible to support.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Verified TPM 2.0 readiness on <HOSTNAME> (Infineon SLB 9670) and initialized a valid TPM-based BitLocker protector via manage-bde so encryption could start under the assigned Corp-BitLocker-Policy for user <USER> (<EMP_ID>).
2. Started BitLocker encryption locally on the laptop <HOSTNAME> (C: volume) and confirmed that protection began successfully on the endpoint; encryption completed to 100% within approximately 25 minutes.
3. Forced an immediate MDM/Intune sync from Company Portal on <HOSTNAME> (IP <IP>) and reassigned the Corp-BitLocker-Policy to refresh encryption and compliance evaluation for the device under user <USER> in the Sales device group.
4. Rotated the BitLocker recovery key on <HOSTNAME> and re-ran escrow so the current recovery key was uploaded again to Azure AD after the sync issue; confirmed new key ID was generated and escrow event logged at 2026-01-20T04:48:00Z.
5. Confirmed a recovery key escrow event existed in Azure AD for <HOSTNAME> (<EMAIL>) and documented the prior Intune portal inconsistency as a stale compliance/reporting condition rather than a continued encryption failure.
6. Escalated the remaining reporting mismatch to the Device Compliance Service backend team (contact: <PERSON>, <EMAIL>) for backend correction while treating the endpoint remediation as complete because encryption and key escrow were successfully established on <HOSTNAME> for user <USER>.

**Example 2**

1. Verified on the affected laptop <HOSTNAME> (user <USER>, IP <IP>) that BitLocker was enabled on C: with XTS-AES 256-bit encryption and that a valid TPM 2.0 protector existed before attempting remediation.
2. Triggered a manual device sync from the Intune admin center for <HOSTNAME> (Intune Device ID 6b3e91a4-c8f2-4d07-b5a1-3920ef18dc44) to re-establish policy and compliance communication with the endpoint, clearing the prior 0x80180014 sync error.
3. Rotated the BitLocker recovery key on <HOSTNAME> using 'Rotate BitLocker keys' action in Intune to force generation of a new escrow event to Azure AD.
4. Confirmed the new BitLocker recovery key (Key ID ending ...9F3A) successfully appeared in Azure AD / Intune under <USER>' device objects after the sync completed at approximately 2026-01-26T05:22:00Z.
5. Rechecked device compliance status in Intune for <HOSTNAME> and verified the endpoint returned to compliant for encryption policy 'Corp-Encryption-Win10-v3'. Notified <PERSON> and <PERSON> that the issue was resolved.

## Recommendation

This issue is resolved by IT support; reference 'MDM sync failure causing BitLocker compliance mismatch' when reporting it.

---

[← Back to categories](../../index.md)
