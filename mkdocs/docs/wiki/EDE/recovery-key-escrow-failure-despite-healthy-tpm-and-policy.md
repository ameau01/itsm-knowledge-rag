---
hide:
  - navigation
root_cause_id: EDE/recovery-key-escrow-failure-despite-healthy-tpm-and-policy
family: EDE
ticket_count: 7
curated: true
self_serviceable: false
---

# BitLocker recovery key escrow failure despite healthy TPM and policy

[← Back to categories](../../index.md)

## Description

Affected users find that their corporate Windows laptop is flagged as noncompliant for disk encryption in the Intune or Endpoint Compliance portal, even though the device has a functioning TPM module and the correct encryption policy assigned. Company Portal displays disk encryption as noncompliant, and in some cases BitLocker may show as "Off" or "not enabled" in Windows Settings or via local status checks, while in other cases encryption has partially started or a protector exists locally. The common thread is that no recovery key is visible in Azure AD, Intune, or Microsoft Endpoint Manager for the affected device.

The missing recovery key prevents the device from reaching a fully compliant managed encryption state, because corporate encryption policy requires both local BitLocker enablement and successful backup of the recovery key to the management service. As a result, affected users may be blocked from accessing compliance-gated corporate resources or flagged during routine compliance audits, even though the device hardware and policy targeting are functioning normally.

In some cases, the escrow failure occurs during initial device enrollment, while in others it follows a policy push or a restart-triggered encryption attempt that partially succeeds. Affected devices may show error codes such as 0x87D1FDE8 (key backup failure), 0x80090010 (key upload error), or 0x80070005 (access denied) in BitLocker or MDM event logs, though these specific errors are not always surfaced to the end user. The compliance status remains stuck as noncompliant until the recovery key is successfully rotated, escrowed to the management service, and a device sync refreshes the compliance state.

!!! note "Reported variations"

    - The escrow failure occurs during initial MDM enrollment, leaving BitLocker protection suspended with no recovery key recorded in the management service from the outset.
    - An escrow upload timeout (e.g., Event ID 846) is followed by a later TPM protector reinitialization, creating conflicting local and cloud state that requires both key rotation and a forced sync to reconcile.
    - Local checks show no BitLocker protectors listed on the OS drive despite TPM readiness and successful policy delivery, indicating the recovery key was never generated or backed up.
    - The exact failure point in the escrow process cannot be conclusively identified from available diagnostics, though the practical impact — missing recovery key and noncompliant status — is the same.

## Affected environment

Distribution across 7 reported cases:

- **Operating system:** Windows 10 21H2 (71%), Windows 10 22H2 (14%), Windows 11 Enterprise (14%)
- **Device / platform:** laptop (43%), Windows (29%), Corporate laptop (14%)
- **Team:** Sales (86%), Engineering (14%)
- **Region:** NA (43%), EMEA (29%), US-West (14%)

## Root cause

BitLocker encryption either started or was ready to start after the TPM protector was initialized, but the recovery key failed to upload (escrow) to the cloud management service. Because corporate encryption policy requires both local encryption and a confirmed recovery key backup, the device remained noncompliant even though the hardware and policy delivery were working correctly. The escrow failure can be caused by access-denied errors, upload timeouts, or transient service issues during the key backup step, leaving the local encryption status and the cloud compliance record out of sync until the key is rotated and successfully backed up.

## Diagnostics

Steps used to confirm this root cause:

1. Confirm TPM readiness and whether a BitLocker protector is initialized on the endpoint.  
   *Expected:* TPM is ready and a valid encryption protector exists.
2. Verify the assigned disk encryption policy and review the latest MDM enrollment and sync results for escrow-related failures.  
   *Expected:* Device receives the active encryption policy without assignment errors.
3. Check whether the current BitLocker recovery key is escrowed to the management service and visible to support.  
   *Expected:* Current recovery key is escrowed and visible to support.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Confirmed TPM 2.0 availability and existing BitLocker protector state on <HOSTNAME> (PC-1234, user <USER>, <EMP_ID>), then verified the device was receiving the assigned encryption policy EMEA-Sales-Encryption-v3 in Intune.
2. Rotated the BitLocker recovery key on <HOSTNAME> using manage-bde -protectors -delete C: followed by manage-bde -protectors -add C: -RecoveryPassword, and triggered a fresh recovery key backup to the Device Compliance Service to replace the missing escrow record for <USER>.
3. Forced an Intune/Windows MDM sync from <HOSTNAME> (IP <IP>) via Company Portal so the updated protector and escrow status were reported to compliance services. Sync completed successfully at 2026-01-17T18:38Z.
4. Validated that the new recovery key was visible in the Device Compliance Service under <PERSON>'s device record (<HOSTNAME>) and available for support recovery operations. Confirmed with agent <PERSON> (<EMAIL>) that the key was accessible.
5. Re-enabled BitLocker protection on the OS drive C: using manage-bde -protectors -enable C:, verified encryption protection was active (AES-256, full volume), and confirmed the device returned to compliant status in Intune. Notified <PERSON> at <EMAIL> that the issue was resolved.

**Example 2**

1. Verified the active BitLocker policy was assigned to device <HOSTNAME> in Intune under the <LOCATION> Sales device group and confirmed the device registered to <USER> (<EMP_ID>) had received the encryption configuration.
2. Rotated the local BitLocker recovery key on <HOSTNAME> and manually escrowed the current key to Azure AD/Intune from the endpoint under <USER>'s session so support could confirm a valid recovery key record existed. Key rotation approved and executed by <PERSON> (<USER>).
3. Reinitialized the TPM protector on <HOSTNAME> and restarted BitLocker protection/encryption to correct the incomplete local protector state seen in event history from 2026-01-22T09:15:00Z.
4. Forced an Intune device sync from <HOSTNAME> (IP <IP>) and triggered a fresh compliance evaluation so encryption status and escrow inventory could be re-read by the Device Compliance Service.
5. Validated that the rotated recovery key was present in Azure AD under <USER>'s device record and confirmed the device compliance state updated to Compliant after the final sync. Notified <PERSON> at <EMAIL> and manager <PERSON> (<EMAIL>) that the incident was resolved, then closed the incident once telemetry aligned.

## Recommendation

This issue is resolved by IT support; reference 'BitLocker recovery key escrow failure' when reporting it.

---

[← Back to categories](../../index.md)
