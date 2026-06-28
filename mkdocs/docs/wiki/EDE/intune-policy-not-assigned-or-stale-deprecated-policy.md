---
hide:
  - navigation
root_cause_id: EDE/intune-policy-not-assigned-or-stale-deprecated-policy
family: EDE
ticket_count: 6
curated: true
self_serviceable: false
---

# Deprecated Intune Encryption Policy Prevents BitLocker Activation and Key Escrow

[← Back to categories](../../index.md)

## Description

Affected users with corporate-managed Windows 10 or Windows 11 devices report that BitLocker disk encryption does not activate following Intune enrollment. The devices appear as noncompliant for encryption in Company Portal and Intune compliance dashboards, and in most cases no recovery key is visible in the management portal. Investigation consistently reveals that the affected devices are assigned to a deprecated or legacy encryption policy rather than the current active policy version, preventing the encryption configuration from being applied or enforced.

The TPM protector and key escrow state varied across affected devices. Some devices showed the TPM as not initialized, others had the TPM protector present but encryption protection still disabled, and in one case no key protectors were found at all. Where the TPM was uninitialized, encryption could not start and recovery key escrow failed entirely. Where the TPM protector existed but the policy was stale, conflicting telemetry arose — Intune reported noncompliance while a recovery key appeared escrowed in the tenant, yet local status showed protection off. In one case, a TPM initialization error was observed during an earlier provisioning attempt, though the TPM was later confirmed functional.

The issue affected devices across multiple offices and user groups. Affected users were unable to meet endpoint security compliance requirements, which blocked access to corporate resources or created gaps in recovery-key visibility for IT administrators. Other laptops within the same device groups were confirmed unaffected.

!!! note "Reported variations"

    - One device was inadvertently excluded from its intended device group during onboarding, resulting in no encryption policy assignment rather than a stale one.
    - One case exhibited conflicting telemetry: Intune showed encryption noncompliance while a recovery key was already escrowed in the tenant and the TPM protector existed locally, indicating partial but unenforced policy application.
    - One device had no key protectors at all on the encrypted volume, with local status returning protection off and no protectors found.
    - One ticket was raised by the affected user's manager rather than the user themselves, due to an upcoming client visit requiring compliance.
    - One device had not completed an MDM sync since before the most recent policy rollout, compounding the stale policy assignment.
    - A TPM initialization error was initially observed during an earlier provisioning attempt, though the TPM was subsequently found to be present and initialized.
    - Peer devices in the same assigned group were confirmed unaffected and did not display the noncompliant encryption status.

## Affected environment

Distribution across 6 reported cases:

- **Operating system:** Windows 10 21H2 (50%), Windows 10 Enterprise 21H2 (17%), Windows 11 (17%)
- **Device / platform:** Corporate-managed laptop (17%), Endpoint (laptop) (17%), Surface Pro (17%)
- **Team:** Sales (33%), Corporate Laptops (33%), Sales - Mobile Devices (17%)
- **Region:** US-West (50%), us-east-1 (33%), EMEA (17%)

## Root cause

A deprecated or stale Intune Endpoint Encryption Policy reference remained associated with the affected devices, preventing the current active encryption policy from being received and applied. Without the correct policy, the TPM protector was not properly initialized or enforced, BitLocker encryption did not start, and recovery key escrow to the management service failed.

## Diagnostics

Steps used to confirm this root cause:

1. Confirm TPM readiness and whether a protector is initialized on the affected endpoint.  
   *Expected:* TPM is ready and a valid encryption protector exists.
2. Verify the disk encryption policy assignment and latest endpoint sync result.  
   *Expected:* Device receives the active encryption policy without assignment errors.
3. Check whether the recovery key has escrowed to the management service.  
   *Expected:* Current recovery key is escrowed and visible to support.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Removed the stale Intune encryption policy reference (EEP-Legacy-2024) from <HOSTNAME> and reassigned the device to the current Endpoint Encryption Policy v2.0 under the <LOCATION> Sales device group.
2. Forced an Intune device sync on <HOSTNAME> (triggered by agent <USER>) and confirmed the updated Endpoint Encryption Policy v2.0 assignment was successfully received without assignment errors in the Intune compliance dashboard.
3. Initialized the TPM protector on <HOSTNAME> using manage-bde -protectors -add C: -tpm so BitLocker could create a valid protector set for OS drive encryption.
4. Started BitLocker encryption on <HOSTNAME> (manage-bde -on C:) and verified the protection status progressed from 'not enabled' to active encryption in progress, reaching full encryption within approximately 45 minutes.
5. Rotated the recovery key on <HOSTNAME> and confirmed the current key escrowed successfully to Azure AD under <EMAIL>'s device record and became visible for support recovery operations.
6. Rechecked device compliance for <HOSTNAME> in Intune/Device Compliance Service and verified the endpoint moved to a compliant encryption state. Confirmed with <PERSON> (<USER>) that BitLocker shows active protection in Windows Security.

**Example 2**

1. Assigned the correct Intune BitLocker encryption policy 'BL-Sales-Mobile-West' to device <HOSTNAME> (W10-123, user <USER>) by adding the device to the 'Sales - Mobile Devices' Intune group so the endpoint could receive the required disk encryption settings.
2. Initialized the TPM protector on <HOSTNAME> by running Initialize-Tpm in an elevated PowerShell session after confirming the TPM chip was present (TpmPresent: True) but not ready for BitLocker use (TpmReady: False). Post-initialization, Get-Tpm confirmed <PERSON>: True.
3. Forced an Intune device sync on <HOSTNAME> via Sync-IntuneDevice to refresh policy application and update the endpoint with the current encryption configuration. Sync completed successfully within 90 seconds.
4. Initiated BitLocker encryption on the device using Enable-BitLocker -MountPoint C: -EncryptionMethod XtsAes256 -RecoveryPasswordProtector and verified the status changed from not enabled to encryption pending and then enabled. Full volume encryption completed in approximately 18 minutes.
5. Rotated the BitLocker recovery key via BackupToAAD-BitLockerKeyProtector, confirmed escrow to Azure AD/Intune (recovery key ID 7F2A91xx visible under <USER>'s device record), and verified the device <HOSTNAME> returned to a compliant encryption state in the Device Compliance Service. Notified <PERSON> at <EMAIL> that the device is now fully compliant.

## Recommendation

Resolved by IT; reference: deprecated or stale Intune encryption policy association preventing BitLocker activation and recovery key escrow.

---

[← Back to categories](../../index.md)
