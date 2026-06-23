---
hide:
  - navigation
root_cause_id: EDE/tpm-protector-not-initialized
family: EDE
ticket_count: 32
curated: true
self_serviceable: false
---

# BitLocker unable to start due to uninitialized TPM protector

[← Back to categories](../../index.md)

## Description

Affected users find that their managed Windows laptop is marked noncompliant for disk encryption in Intune or Company Portal. BitLocker shows as "Protection Off" or "Encryption not enabled" on the system drive (C:), and no recovery key is visible in Azure AD or the Intune device record. Manual actions such as rebooting, triggering a Company Portal sync, or attempting to enable BitLocker through the Windows interface do not resolve the issue, and the device remains noncompliant.

The underlying condition is that the device's TPM (Trusted Platform Module) security chip — which BitLocker relies on to protect the encryption key — was never properly set up for BitLocker use. Without this initialization step, BitLocker cannot create the required startup protector, encryption never begins, and no recovery key is generated or uploaded to the organization's management service. In some cases, TPM management tools on the device may display warnings such as "The TPM is not ready for use" or "Troubleshooting recommended," and the BitLocker management interface may show the "Turn on BitLocker" option as greyed out.

This issue commonly appears on newly provisioned or Autopilot-enrolled devices where the TPM setup step did not complete during the initial configuration process, as well as on devices that were recently reimaged, re-enrolled, or had hardware replaced (such as a motherboard swap). Although the Intune encryption policy may be correctly assigned to the device, it cannot take effect because the local TPM prerequisite is not met. As a result, the device remains out of compliance and affected users may be blocked from accessing compliance-gated corporate resources such as VPN, email, or SharePoint sites.

!!! note "Reported variations"

    - On some devices, the TPM hardware reports as present and ready, yet the BitLocker-specific protector was still never created, making the TPM appear healthy while encryption remains blocked.
    - After the TPM protector is corrected locally, the recovery key upload to Azure AD may not occur automatically; a manual backup step may be required before the device reaches compliant status.
    - Recovery key upload attempts may fail intermittently with timeout errors during the first one or two device sync cycles, succeeding only on a subsequent sync.
    - In some cases, the Intune encryption policy was also not assigned or not applied to the device at the time of evaluation, compounding the TPM protector issue and requiring both policy assignment correction and TPM initialization.
    - The "Turn on BitLocker" option in the Windows interface may appear greyed out, preventing the user from enabling encryption manually.
    - On devices that underwent a motherboard replacement, a previously valid TPM protector may have been invalidated, producing the same symptoms as a device that was never initialized.

## Affected environment

Distribution across 32 reported cases:

- **Operating system:** Windows 10 21H2 (59%), Windows 10 Enterprise 21H2 (12%), Windows 11 Enterprise (6%)
- **Device / platform:** laptop (31%), Azure AD Joined (19%), x64 (16%)
- **Team:** Sales (72%), Engineering (9%), Finance (6%)
- **Region:** US-East (34%), us-west-2 (28%), NA (12%)

## Root cause

The TPM protector on the device was not initialized, which prevented BitLocker from creating the security key it needs to start encryption on the system drive. Because encryption never started, no recovery key was generated, and the automatic upload of the recovery key to Azure AD or Intune could not occur. This left the device in a noncompliant state for the organization's disk encryption requirement. The TPM initialization failure typically occurs during device provisioning, reimaging, re-enrollment, or after hardware replacement.

## Diagnostics

Steps used to confirm this root cause:

1. Confirm TPM readiness and whether a BitLocker TPM protector is initialized on the device.  
   *Expected:* TPM is ready and a valid encryption protector exists.
2. Verify the disk encryption policy assignment and latest endpoint sync result.  
   *Expected:* Device receives the active encryption policy without assignment errors.
3. Check whether the BitLocker recovery key is escrowed to Azure AD after encryption is enabled.  
   *Expected:* Current recovery key is escrowed and visible to support.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Verified that the Endpoint Disk Encryption policy ('FS-Encryption-Win10') was assigned to <HOSTNAME> (user <USER>, <EMP_ID>) in Intune and that the device was checking in without policy assignment errors; last successful sync was 2026-01-19T09:12Z from IP <IP>.
2. Confirmed locally on <HOSTNAME> that BitLocker was not enabled by running manage-bde -status C:, which returned 'Fully Decrypted' and no BitLocker protectors present on the OS volume.
3. Initialized the TPM protector on the endpoint using 'manage-bde -protectors -add C: -tpm' so BitLocker could create a valid protector set; command completed successfully with TPM 2.0 chip in ready state.
4. Started BitLocker encryption after protector creation using 'manage-bde -on C:' and verified that protection was active on the system volume; encryption reached 100% and protection status showed 'On'.
5. Forced an Intune device sync on <HOSTNAME> via Company Portal to trigger updated encryption compliance reporting and recovery key escrow to the Device Compliance Service.
6. Confirmed that the recovery key (ID BEK-7A3F) successfully appeared in the Device Compliance Service portal under <USER>'s device record and that the device encryption state reported as 'Compliant' in Intune. Notified <PERSON> (<EMAIL>) and manager <PERSON> that the laptop is now fully encrypted and compliant.

**Example 2**

1. Validated TPM presence and readiness on <HOSTNAME> via tpm.msc, confirmed the TPM chip was ready (version 2.0), then initialized the TPM protector required for BitLocker startup protection using manage-bde -protectors -add C: -tpm.
2. Added a TPM-based BitLocker protector and enabled BitLocker on the OS volume (C:) of <HOSTNAME> using local remediation commands: manage-bde -on C: -RecoveryPassword.
3. Started disk encryption on <HOSTNAME> and confirmed BitLocker protection state changed from Off to 'Encryption in Progress' via manage-bde -status C:, with full encryption completing within the hour.
4. Added <HOSTNAME> (<USER>) to the Sales-Encryption-Required assignment group, forced Intune BitLocker policy assignment (profile BL-Compliance-Sales-NA), and triggered a device sync from Company Portal so the endpoint received the expected encryption configuration.
5. Escrowed the BitLocker recovery key to Azure AD using manage-bde -protectors -adbackup C: -id {recovery-protector-id}, verified the 48-digit recovery key was present in the Azure AD device blade for support retrieval, and confirmed <HOSTNAME> returned to a compliant state in the Device Compliance Service. Notified <PERSON> (<EMAIL>) that the device was now compliant.

## Recommendation

This issue is resolved by IT support; reference 'TPM protector not initialized – BitLocker unable to start' when reporting it.

---

[← Back to categories](../../index.md)
