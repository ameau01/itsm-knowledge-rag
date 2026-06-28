---
hide:
  - navigation
root_cause_id: DCP/stale-compliance-state-mismatch-ca-cache
family: DCP
ticket_count: 4
curated: true
self_serviceable: false
---

# Stale Compliance Signal Mismatch Between Intune and Conditional Access

[← Back to categories](../../index.md)

## Description

Affected users on Intune-managed Windows 10 and Windows 11 corporate laptops experience access blocks to Microsoft 365 services—including Outlook, Exchange Online, Teams, and SharePoint—due to Conditional Access evaluating their devices as noncompliant. The denial typically cites a missing or absent encryption signal, even though the devices have BitLocker encryption actively enabled and verified both locally and in the Company Portal or Intune portal. The core issue is a mismatch between the compliant state reported by Intune and the stale or outdated compliance signal consumed by Conditional Access during sign-in evaluation.

The block may be persistent or intermittent, with some affected users experiencing consistent denial while others see sporadic failures across sign-in attempts. Manual sync attempts and device reboots do not immediately resolve the discrepancy, as the stale compliance data continues to be referenced during token evaluation. In at least one case, the Intune service-side compliance record itself reflected a noncompliant encryption signal despite the endpoint's local encryption state being healthy, with BitLocker protection on and a TPM key protector present.

The issue affects both remote workers and users connecting from office locations and is not tied to a specific network or IP range. Affected users are unable to perform normal work—including email, collaboration, and document access—until the stale compliance state is cleared and refreshed telemetry propagates to the Conditional Access evaluation layer. Sign-in logs confirm access denials with device-noncompliant error codes during the period of misalignment.

!!! note "Reported variations"

    - In one case, Intune itself displayed a noncompliant signal for the encryption requirement even though the local device state confirmed BitLocker was active with a TPM key protector, suggesting the staleness extended to the Intune compliance record rather than only the Conditional Access cache.
    - Some affected users experienced fully persistent access blocks, while others saw intermittent denials where sign-in attempts alternated between success and failure.
    - One instance involved a Windows 11 22H2 device rather than Windows 10 21H2, indicating the issue is not limited to a single operating system version.
    - In certain cases, temporary Conditional Access exclusion groups or grace windows were applied to restore user productivity while the compliance signal propagation completed.

## Affected environment

Distribution across 4 reported cases:

- **Operating system:** Windows 10 21H2 (75%), Windows 11 22H2 (25%)
- **Device / platform:** Endpoint (laptop) (25%), Corporate laptop (25%), laptop (25%)
- **Team:** Remote Workers (25%), Sales-APAC (25%), Engineering (25%)
- **Region:** us-east-1 (50%), NA (25%), EMEA (25%)

## Root cause

Conditional Access consumed a stale or delayed device compliance signal for BitLocker encryption while Intune already showed the device as compliant. The encryption state had not fully propagated to the Conditional Access evaluation path, creating a temporary mismatch between Intune compliance status and access enforcement. The stale noncompliant signal continued to be used for token evaluation until the compliance record was refreshed and cache propagation completed.

## Diagnostics

Steps used to confirm this root cause:

1. Confirm the device has recently checked in to endpoint management and that a new compliance evaluation was triggered.  
   *Expected:* Device check-in timestamp is current and compliance evaluation has run.
2. Review the encryption compliance signal reported to Conditional Access and compare it with the Intune compliance state.  
   *Expected:* Required compliance signals report healthy values.
3. Compare the assigned compliance policy with the user's device group membership to rule out stale or incorrect policy targeting.  
   *Expected:* Device is in the intended policy scope with no stale assignment.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Forced an Intune device check-in on <HOSTNAME> and initiated a remote sync via the Intune admin center so the endpoint could submit a fresh compliance evaluation for user <USER> (<EMP_ID>).
2. Triggered re-evaluation of the encryption compliance state on <HOSTNAME> and had <PERSON> reboot the device to refresh local BitLocker protection status reporting to the Device Compliance Service.
3. Reviewed Conditional Access sign-in results for <EMAIL> after the new compliance sync to confirm the encryption attribute no longer evaluated as missing. Azure AD sign-in logs from client IP <IP> showed successful authentication post-sync.
4. Validated that <HOSTNAME> returned to an allowed sign-in state for Microsoft 365 after the refreshed compliance signal propagated. <PERSON> confirmed full access to Exchange Online, Teams, and SharePoint from her <LOCATION> location.
5. Advised follow-up OS updating from Windows 10 21H2 to a supported release and monitoring for recurrence because the condition was tied to delayed compliance telemetry rather than a confirmed encryption configuration failure. Ticket details shared with endpoint team lead <PERSON> (<USER>) for awareness.

**Example 2**

1. Validated that the affected endpoint <HOSTNAME> (registered to <PERSON>, <USER>, employee ID <EMP_ID>) was the same AAD-joined Intune-managed device being evaluated by Conditional Access, and confirmed the block was tied to a noncompliant device state originating from a stale encryption signal.
2. Forced a fresh Intune device check-in for <HOSTNAME> from the Intune admin console and triggered immediate compliance policy re-evaluation to refresh the endpoint's current posture, verifying the check-in completed from source IP <IP>.
3. Cleared the stale compliance state associated with the <HOSTNAME> device record in Intune so the current BitLocker encryption signal could be reprocessed by the Device Compliance Service and propagated to Conditional Access.
4. Re-applied the device compliance token/state for <USER>'s device and confirmed the compliant result propagated from Intune to the service consumed by Conditional Access, with the encryption signal now correctly showing as reported and healthy.
5. Used a temporary Conditional Access grace allowance during propagation to restore <PERSON>'s Outlook/Exchange Online access from the <LOCATION> office, then verified sign-in was no longer being rejected for NonCompliant after the device state updated — confirmed via Azure AD sign-in logs showing successful token issuance.
6. Escalated the case to <PERSON> lead <PERSON> (<USER>, phone <PHONE>) for follow-up monitoring of possible recurrence related to compliance evaluation timing or stale service-side state for the <LOCATION> Sales device group over the next 48 hours.

## Recommendation

Resolved by IT after the stale device compliance signal was refreshed and propagation between Intune and Conditional Access completed, restoring normal access evaluation.

---

[← Back to categories](../../index.md)
