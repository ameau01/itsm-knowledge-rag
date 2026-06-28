---
hide:
  - navigation
root_cause_id: EDE/inconclusive-evidence-bitlocker-not-fully-enabled
family: EDE
ticket_count: 3
curated: true
self_serviceable: false
---

# BitLocker Not Initialized on Endpoint Preventing Recovery Key Escrow

[← Back to categories](../../index.md)

## Description

Affected users operate corporate-managed Windows 10 laptops that are flagged as noncompliant for disk encryption in Intune. In each case, the management console reports encryption as not enabled on the device, and no BitLocker recovery key is visible in Azure AD or tenant escrow for the associated user account. This noncompliant status prevents the devices from meeting organizational endpoint encryption requirements for normal corporate use.

For two of the three reported cases, the initial intake established only that encryption was not enabled and no recovery key was present, without confirming whether the BitLocker enablement prompt had ever been presented to or acted upon by the user; the underlying cause of the missing encryption remained undetermined at triage. In the remaining case, the affected user specifically reported having accepted the BitLocker enablement prompt approximately two weeks prior, but encryption never progressed — the drive icon never displayed a lock symbol, no completion notification appeared, and the device continued to report as unencrypted in Intune.

Across all three tickets, initial reports lacked sufficient device-level detail to confirm the underlying cause of the encryption failure. This limited the ability to validate policy delivery, TPM readiness, or key escrow status at the time of intake.

!!! note "Reported variations"

    - In one case, the affected user confirmed having accepted the BitLocker enablement prompt approximately two weeks before filing the ticket, with no subsequent encryption progress observed on the device during that interval.
    - One ticket was submitted on behalf of the affected user by a third party via email rather than by the user directly.
    - In one instance, the affected device was associated with a specific business group (Finance), and the noncompliance was identified under that group's enrollment context.

## Affected environment

Distribution across 3 reported cases:

- **Operating system:** Windows 10 21H2 (67%), Windows 10 (33%)
- **Device / platform:** Corporate laptop (33%), Corporate managed laptop (33%), x86_64 (33%)
- **Team:** Sales (67%), Finance (33%)
- **Region:** us-west-2 (33%), NA (33%), us-east-1 (33%)

## Root cause

BitLocker was not fully initialized on the affected endpoints, so no valid recovery key had been escrowed to Azure AD or Intune. The most likely contributing conditions were missing or unapplied Intune BitLocker policy and unverified TPM/protector readiness, which left devices reporting encryption as disabled and therefore noncompliant, though TPM initialization, policy application, and escrow sync state could not be fully confirmed from the available evidence.

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

Escalated to IT for investigation into incomplete BitLocker enablement conditions including policy application and TPM/protector readiness; resolution outcome was not documented in the available ticket evidence.

---

[← Back to categories](../../index.md)
