---
hide:
  - navigation
root_cause_id: EDE/tpm-protector-not-initialized
family: EDE
ticket_count: 32
curated: true
self_serviceable: false
---

# Uninitialized TPM Protector Prevents BitLocker Encryption and Recovery Key Escrow

[← Back to categories](../../index.md)

## Description

Affected users on corporate-managed Windows 10 and Windows 11 laptops report that their devices are flagged as noncompliant for disk encryption in Microsoft Intune, Company Portal, or the Device Compliance Service. BitLocker remains in a "Protection Off" state on the system drive with no key protectors configured, and no recovery key is visible in Azure AD or the Intune escrow portal. The noncompliant state blocks access to compliance-gated corporate resources such as VPN, email, SharePoint, and line-of-business applications.

Investigation consistently reveals that the TPM protector was never initialized on the affected endpoint. Although the TPM hardware is physically present and may report as ready in the management console, protector initialization did not complete during provisioning, Autopilot enrollment, or reimaging. Without an initialized TPM protector, BitLocker cannot create key protectors on the OS volume, and no recovery key is generated or escrowed to Azure AD. The Intune encryption policy is typically confirmed as correctly assigned, indicating the failure is a local TPM prerequisite issue — though in some cases the device was also missing from the required Azure AD security group or lacked the policy assignment after re-enrollment, compounding the problem.

The condition has been observed following reimaging without a TPM initialization step, motherboard replacements that invalidate a previously initialized protector, and Autopilot provisioning flows where TPM initialization was skipped. Affected users report never receiving a BitLocker PIN prompt or encryption setup during provisioning. Manual remediation attempts such as rebooting, forcing an Intune sync, or enabling BitLocker through the control panel do not resolve the issue. Even after the TPM protector is initialized and encryption starts, automatic recovery key escrow may fail intermittently across several MDM sync cycles before succeeding.

!!! note "Reported variations"

    - The Intune device compliance status intermittently toggles between noncompliant and pending despite encryption remaining off locally.
    - The TPM management console reports a specific initialization error (e.g., 0x80070057 or 0xC0000200) rather than simply showing the protector as uninitialized.
    - Recovery key escrow to Azure AD fails with a timeout error or a "KeyPackage not found" error after the TPM protector is initialized, requiring a forced manual backup.
    - The device was not added to the required Azure AD security group or lacked the Intune encryption policy assignment after re-enrollment or reimaging.
    - The TPM protector was previously initialized but became invalidated after a motherboard replacement, causing a formerly encrypted device to lose compliant status.
    - The device was provisioned through Windows Autopilot and the TPM protector initialization step was skipped during the automated flow.
    - An MDM sync or enrollment token error (e.g., 0x80180014 or 0x80180026) is logged alongside the escrow failure.
    - The BitLocker management UI displayed the "Turn on BitLocker" option as greyed out, preventing the user from enabling encryption manually.

## Affected environment

Distribution across 32 reported cases:

- **Operating system:** Windows 10 21H2 (59%), Windows 10 Enterprise 21H2 (12%), Windows 11 Enterprise (6%)
- **Device / platform:** laptop (31%), Azure AD Joined (19%), x64 (16%)
- **Team:** Sales (72%), Engineering (9%), Finance (6%)
- **Region:** US-East (34%), us-west-2 (28%), NA (12%)

## Root cause

The TPM protector was not initialized on the affected endpoint, preventing BitLocker from creating the required TPM-backed protector on the OS volume. Without this protector, encryption could not start and recovery key escrow to Azure AD or Intune could not complete. In some cases, the Intune BitLocker policy was also not assigned or had not successfully applied, further compounding the failure.

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

Resolved by IT through TPM protector initialization, BitLocker encryption enablement, and recovery key escrow verification to Azure AD.

---

[← Back to categories](../../index.md)
