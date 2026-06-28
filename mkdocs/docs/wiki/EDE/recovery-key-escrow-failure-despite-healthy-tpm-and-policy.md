---
hide:
  - navigation
root_cause_id: EDE/recovery-key-escrow-failure-despite-healthy-tpm-and-policy
family: EDE
ticket_count: 7
curated: true
self_serviceable: false
---

# Recovery Key Escrow Failure Leaves Device Noncompliant Despite Healthy TPM

[← Back to categories](../../index.md)

## Description

Affected users with Intune-managed Windows 10 corporate endpoints experience a persistent noncompliant encryption state in the Device Compliance Service or Company Portal, despite having a functional TPM 2.0 module and a correctly assigned BitLocker encryption policy. The core issue is that the BitLocker recovery key fails to escrow to Azure AD or Intune during or after the encryption process, leaving the recovery key absent from the cloud device record. Without a successfully escrowed key, the compliance service does not recognize the device as meeting corporate encryption requirements.

The failure manifests at different points in the device lifecycle. In some cases, the recovery key backup fails during initial enrollment; in others it occurs after a subsequent policy push on an already-enrolled device. Affected devices may display BitLocker protection as suspended, show BitLocker as not enabled in Windows Settings, or appear to have BitLocker components present locally while no key is visible in the management tenant. In at least one instance, BitLocker was confirmed entirely inactive on the system drive with no protectors found, meaning encryption had never been initiated despite correct policy assignment.

In all scenarios, the Company Portal compliance tile continues to report disk encryption as noncompliant, and affected users are unable to self-resolve the issue through manual sync attempts. The compliance block prevents affected users from meeting corporate endpoint encryption baselines and can restrict access to organizational resources. The issue has been observed across different business groups and office locations.

!!! note "Reported variations"

    - Recovery key backup fails during initial Intune enrollment with error code 0x87D1FDE8 (KeyBackupError).
    - Recovery key escrow upload fails with error code 0x80090010 recorded in MDM/BitLocker event logs after BitLocker is started locally.
    - Recovery key escrow fails with access-denied error 0x80070005 despite a valid TPM protector and corporate account enrollment.
    - An escrow upload timeout (BitLocker-API Event ID 846) occurs before TPM protector initialization completes, resulting in a timing mismatch between local encryption state and cloud compliance status.
    - BitLocker protection shows as suspended on the OS drive rather than disabled, yet the device is still flagged noncompliant due to the missing escrowed key.
    - Compliance remains noncompliant even after a local TPM protector initialization and Intune sync because the recovery key escrow step itself has not succeeded.
    - BitLocker components appear present locally but the escrow gap cannot be definitively attributed to either an endpoint failure or a management-side reporting delay.
    - BitLocker is confirmed entirely inactive on the system drive with no protectors found, meaning encryption was never initiated despite correct policy assignment.

## Affected environment

Distribution across 7 reported cases:

- **Operating system:** Windows 10 21H2 (71%), Windows 10 22H2 (14%), Windows 11 Enterprise (14%)
- **Device / platform:** laptop (43%), Windows (29%), Corporate laptop (14%)
- **Team:** Sales (86%), Engineering (14%)
- **Region:** NA (43%), EMEA (29%), US-West (14%)

## Root cause

BitLocker recovery key escrow failed or never completed during MDM enrollment or subsequent policy processing, leaving the device with a local protector present (or BitLocker still suspended) but no recovery key recorded in the management service. Errors such as key protection service failures, access-denied responses, or transient escrow timeouts prevented the recovery key from being uploaded to Azure AD or Intune, causing the cloud compliance state to remain out of sync with local encryption status.

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

Resolved by IT after reprocessing encryption policy, rotating the recovery key, and confirming successful escrow to the management tenant.

---

[← Back to categories](../../index.md)
