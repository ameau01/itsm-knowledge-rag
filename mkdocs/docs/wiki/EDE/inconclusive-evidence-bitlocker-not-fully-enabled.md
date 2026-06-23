---
hide:
  - navigation
root_cause_id: EDE/inconclusive-evidence-bitlocker-not-fully-enabled
family: EDE
ticket_count: 3
curated: true
self_serviceable: false
---

# Disk encryption noncompliance due to incomplete BitLocker initialization on endpoint

[← Back to categories](../../index.md)

## Description

Affected users' corporate Windows 10 laptops appear as noncompliant for disk encryption in Intune. The device's encryption status is reported as "Not encrypted," and no BitLocker recovery key is visible in Azure AD or Intune escrow for the device. This compliance failure prevents the laptop from meeting endpoint security requirements for normal corporate use.

In some cases, the user may recall having accepted a BitLocker enablement prompt days or weeks earlier, yet encryption never completed — the drive icon never displayed a lock symbol, and no completion notification was received. Forcing a sync through Company Portal or rebooting the laptop does not resolve the noncompliant status, and the device continues to report as unencrypted after these attempts.

Because device-specific details such as TPM readiness, protector state, and recent sync timestamps are often unavailable at the time of the initial report, IT support may not be able to immediately confirm whether the root cause lies with the device hardware, policy delivery, or the encryption process itself. The compliance alert, however, is genuine and reflects a truly unencrypted endpoint rather than a false reading.

!!! note "Reported variations"

    - The user accepted the BitLocker enablement prompt but encryption silently failed to start or stalled before completion, with no error message or follow-up notification displayed on the device.
    - A manual Company Portal sync and device reboot did not change the encryption status or trigger BitLocker to resume initialization.
    - Initial ticket submissions lacked device hostname, TPM state, or last sync details, delaying diagnosis until the user could provide endpoint-level information.

## Affected environment

Distribution across 3 reported cases:

- **Operating system:** Windows 10 21H2 (67%), Windows 10 (33%)
- **Device / platform:** Corporate laptop (33%), Corporate managed laptop (33%), x86_64 (33%)
- **Team:** Sales (67%), Finance (33%)
- **Region:** us-west-2 (33%), NA (33%), us-east-1 (33%)

## Root cause

BitLocker encryption was never fully initialized on the affected device, leaving the disk unencrypted and preventing a recovery key from being generated or escrowed to Azure AD or Intune. The exact blocking factor — whether TPM or protector readiness, incomplete policy application, or a stalled encryption process — could not be conclusively isolated from the available evidence, but the combined indicators point to an endpoint-side failure to complete the BitLocker startup sequence.

## Diagnostics

Steps used to confirm this root cause:

1. Confirm TPM readiness and whether a protector is initialized on the affected laptop.  
   *Expected:* TPM is ready and a valid encryption protector exists.
2. Verify the disk encryption policy assignment and latest endpoint sync result in Intune.  
   *Expected:* Device receives the active encryption policy without assignment errors.
3. Check whether the recovery key has escrowed to the management service.  
   *Expected:* Current recovery key is escrowed and visible to support.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Identify the affected device in Intune (<HOSTNAME>, user <USER>, <EMP_ID>) and confirm the assigned BitLocker or Endpoint Security disk encryption policy is targeted to the device without assignment conflicts. Verify the device object in Intune matches the expected hostname and user principal name <EMAIL>.
2. Validate TPM readiness on the Windows endpoint <HOSTNAME> and initialize the TPM or BitLocker protector if it is present but not ready for use by encryption policy. Run tpm.msc or Get-Tpm via PowerShell to confirm TPM 2.0 is enabled and owned, and coordinate with <PERSON> (phone: <PHONE>) if on-device action is needed.
3. Force an Intune device sync on <HOSTNAME> so the active encryption policy is reapplied and the endpoint can begin BitLocker enablement. This can be triggered from the Intune portal under the device record for <USER> or via the Company Portal app on the device.
4. Enable BitLocker on the system drive (C:) using the managed policy path and verify the device <HOSTNAME> reports encryption in progress or protection on. Confirm via manage-bde -status that the volume is fully encrypted with a TPM protector.
5. Escrow or rotate the BitLocker recovery key to Azure AD after protection is enabled on <HOSTNAME>, then confirm the recovery key is visible in the device record under Azure AD > Devices > <USER>'s device > BitLocker keys.
6. Recheck Intune compliance after policy refresh and key escrow to confirm the device <HOSTNAME> no longer reports 'Encryption not enabled' and returns to compliant status. Notify <PERSON> at <EMAIL> and close the ticket once compliance is verified.

**Example 2**

1. Identify the affected device <HOSTNAME> in Intune using the device name or primary user association (<USER> / <EMP_ID>) and review the latest compliance, encryption, and device sync status.
2. On the endpoint <HOSTNAME>, verify TPM is present and ready for use; if TPM is not initialized, complete TPM provisioning and confirm a valid BitLocker protector can be created.
3. Confirm the active Intune disk encryption policy is assigned to <HOSTNAME> without assignment or applicability errors, then force a device sync from Company Portal or Intune and verify sync completes from IP <IP>.
4. Enable BitLocker on the operating system drive of <HOSTNAME> if encryption is not active, allowing the recovery password protector to be generated as required by policy.
5. Trigger recovery key backup or rotation to the management service for <HOSTNAME> and validate that the recovery key becomes visible in tenant escrow after the sync completes. Notify <PERSON> at <EMAIL> upon successful escrow.
6. Re-run or wait for the next compliance evaluation and confirm <HOSTNAME> changes from non-compliant to compliant for disk encryption. Update <PERSON> for regional tracking.

## Recommendation

This issue is resolved by IT support; reference "incomplete BitLocker initialization – disk encryption noncompliance" when reporting it.

---

[← Back to categories](../../index.md)
