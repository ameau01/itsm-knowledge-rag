---
hide:
  - navigation
root_cause_id: EDE/intune-policy-not-assigned-or-stale-deprecated-policy
family: EDE
ticket_count: 6
curated: true
self_serviceable: false
---

# BitLocker activation failure due to stale or missing Intune encryption policy

[← Back to categories](../../index.md)

## Description

Affected users find that their Intune-managed Windows device remains noncompliant for disk encryption after enrollment or a policy rollout. Company Portal or the Intune compliance dashboard reports that encryption is not enabled, and BitLocker does not activate automatically as expected. In many cases, no recovery key is visible in Azure AD or the Intune portal for the device, and the device is blocked from meeting corporate endpoint security requirements.

The local BitLocker status on the affected device typically shows "Protection Off" on the operating system drive, with no key protectors found. In some instances the TPM protector is reported as not initialized, which prevents encryption from starting entirely. In other cases, a TPM protector may be present and a recovery key may even appear escrowed in the tenant, yet local protection remains off and the device is still flagged as noncompliant — creating conflicting signals between local status and management-side telemetry.

Attempts to resolve the issue through device restarts, manual Intune syncs, or remote encryption commands from the Intune console do not bring the device into a compliant, encrypted state. The problem persists until the underlying policy assignment is corrected by IT support. Affected devices have been observed across multiple device groups, office locations, and both Windows 10 and Windows 11 hardware including Surface Pro devices.

!!! note "Reported variations"

    - Some devices show a fully initialized TPM protector and a successfully escrowed recovery key in the tenant, yet BitLocker protection remains locally disabled and the device is marked noncompliant — indicating the policy was partially but not fully enforced.
    - In certain cases the device was never assigned the correct policy at all (e.g., excluded from the target device group during onboarding) rather than being linked to a deprecated policy version.
    - On at least one device, an assignment filter mismatch on the management side prevented the encryption profile from applying despite the device having full hardware readiness, including an initialized TPM.
    - The TPM protector not-initialized state appears as a downstream effect of the missing policy in many cases, but is not always present — some devices have a healthy TPM yet still fail to encrypt due to the policy gap.

## Affected environment

Distribution across 6 reported cases:

- **Operating system:** Windows 10 21H2 (50%), Windows 10 Enterprise 21H2 (17%), Windows 11 (17%)
- **Device / platform:** Corporate-managed laptop (17%), Endpoint (laptop) (17%), Surface Pro (17%)
- **Team:** Sales (33%), Corporate Laptops (33%), Sales - Mobile Devices (17%)
- **Region:** US-West (50%), us-east-1 (33%), EMEA (17%)

## Root cause

The device is associated with a stale, deprecated, or incorrectly targeted Intune disk encryption policy rather than the current active policy. Because the effective encryption configuration never reaches the device, BitLocker cannot activate properly, the TPM protector may not initialize, and recovery key escrow to Azure AD or Intune fails or remains incomplete. This can occur when a device retains a reference to a retired policy version, is inadvertently excluded from the correct device group, or is affected by an assignment filter mismatch that prevents the current policy from applying.

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

This issue is resolved by IT support; reference "Intune encryption policy not assigned or stale/deprecated policy" when reporting it.

---

[← Back to categories](../../index.md)
