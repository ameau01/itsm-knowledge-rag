---
hide:
  - navigation
root_cause_id: EDE/mdm-sync-failure-causing-state-desync
family: EDE
ticket_count: 3
curated: true
self_serviceable: false
---

# BitLocker Enabled Locally but Intune Reports Noncompliant Due to Escrow and Compliance Reporting Desynchronization

[← Back to categories](../../index.md)

## Description

Affected users with managed Windows 10 laptops — including at least one Surface Laptop 4 — report that BitLocker disk encryption is confirmed as fully enabled locally on the OS volume, yet Microsoft Intune continues to display the device as noncompliant with an "EncryptionNotEnabled" status. Recovery keys are not visible in Azure AD or Intune escrow, preventing support teams from confirming key availability and leaving the devices in a blocked compliance state. In each case, the local endpoint shows BitLocker active on the system drive with encryption complete, but the management console does not reflect this.

The underlying causes documented across these tickets differ. In one case, Azure AD confirmed a recovery key escrow event, but the Intune compliance service backend continued to report the device as not encrypted — a reporting synchronization mismatch that persisted after all endpoint-side remediation was confirmed complete and required escalation to the backend compliance service team. In a second case, local BitLocker was active but the key protector configuration was incomplete: manage-bde output revealed only a Numerical Password protector with no TPM protector bound, explaining why Intune still reported the device as unencrypted. In a third case, the device had a valid TPM 2.0 protector and full local encryption, but the recovery key failed to escrow because the device encountered an MDM sync error (0x80180014) during its last several scheduled check-ins, preventing the compliance state from updating.

Despite differing technical causes, the user-facing presentation is consistent: Intune shows noncompliant encryption status, recovery keys are absent from the management portal, and affected devices are flagged during compliance reviews.

!!! note "Reported variations"

    - In one case, the Intune compliance backend continued to report "NotEncrypted" even after Azure AD confirmed a successful recovery key escrow event, indicating a backend reporting desync rather than an endpoint-side issue.
    - One affected device (Surface Laptop 4) had BitLocker enabled locally but lacked a TPM protector binding, with only a Numerical Password protector present, representing a protector initialization gap.
    - One device logged MDM sync error 0x80180014 across multiple consecutive scheduled check-ins, directly preventing recovery key escrow to Azure AD.
    - In one case, the Company Portal app explicitly displayed a "last sync failed" status to the affected user.

## Affected environment

Distribution across 3 reported cases:

- **Operating system:** Windows 10 21H2 (33%), Windows 11 (33%), Windows 10 20H2 (33%)
- **Device / platform:** laptop (67%), Surface Laptop 4 (33%)
- **Team:** Sales (100%)
- **Region:** us-west-2 (67%), us-east-1 (33%)

## Root cause

Three distinct root causes were identified across affected devices. First, a backend compliance reporting desync occurred where Azure AD had successfully received a recovery key escrow event, yet the Intune compliance service continued to report the device as not encrypted — a mismatch between backend services rather than an endpoint-side failure. Second, BitLocker activated before the management state had fully reconciled, resulting in an incomplete protector configuration: the TPM protector binding was never established, leaving only a Numerical Password protector, which caused Intune to treat the device as noncompliant. Third, an MDM sync error (0x80180014) prevented the device from communicating with Intune across multiple consecutive check-ins, blocking recovery key escrow to Azure AD entirely and leaving the compliance state stale.

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

Resolved by IT through backend compliance service escalation, protector re-initialization, or MDM sync remediation depending on the underlying cause; reference "BitLocker escrow and compliance reporting desynchronization" when reporting.

---

[← Back to categories](../../index.md)
