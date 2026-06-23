---
hide:
  - navigation
root_cause_id: DCP/stale-compliance-state-mismatch-ca-cache
family: DCP
ticket_count: 4
curated: true
self_serviceable: false
---

# Stale compliance cache mismatch between Intune and Conditional Access

[← Back to categories](../../index.md)

## Description

Affected users find themselves blocked from accessing Microsoft 365 resources — including Outlook, Exchange Online, Teams, and SharePoint — because Conditional Access evaluates their device as noncompliant for missing encryption. At the same time, the Intune portal and Company Portal both show the device as compliant, and BitLocker encryption appears active locally on the device. This creates a confusing situation in which the device appears healthy from every angle the user can see, yet sign-in attempts are denied with a device-not-compliant result.

The issue has been observed on both Windows 10 and Windows 11 managed laptops, affecting users across multiple offices and remote locations. In some cases the block is persistent, while in others it is intermittent — sign-in attempts may succeed briefly and then fail again. Manual sync attempts and reboots performed by the user do not immediately resolve the problem, and the conflicting status can persist for an extended period (an hour or more in reported cases).

Affected users typically notice the issue when core productivity applications such as Outlook or Teams stop connecting, or when browser-based access to SharePoint or Exchange is denied at sign-in. The Conditional Access denial may reference a missing encryption signal even though the device's local encryption status has not changed.

!!! note "Reported variations"

    - In some cases the block is intermittent rather than persistent, with sign-in attempts alternating between success and failure as Conditional Access evaluates different cached compliance snapshots.
    - Some affected users see the device marked as noncompliant in Intune itself (rather than only in Conditional Access), even though the local encryption state is healthy and the device has synced recently.
    - Propagation time after the stale state is cleared has varied, with some cases resolving within a few minutes and others requiring approximately 12 minutes of cache propagation before access is fully restored.

## Affected environment

Distribution across 4 reported cases:

- **Operating system:** Windows 10 21H2 (75%), Windows 11 22H2 (25%)
- **Device / platform:** Endpoint (laptop) (25%), Corporate laptop (25%), laptop (25%)
- **Team:** Remote Workers (25%), Sales-APAC (25%), Engineering (25%)
- **Region:** us-east-1 (50%), NA (25%), EMEA (25%)

## Root cause

A mismatch develops between the device compliance state recorded in Intune and the compliance signal consumed by Conditional Access during sign-in evaluation. Although the device has checked in successfully and Intune recognizes it as compliant with encryption enabled, Conditional Access continues to reference an older, stale copy of the compliance data that still indicates encryption is missing. This outdated signal persists until the compliance record is refreshed at the service layer and the updated status fully propagates through to the Conditional Access token evaluation path, which can take several minutes.

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

This issue is resolved by IT support; reference "stale compliance cache mismatch between Intune and Conditional Access" when reporting it.

---

[← Back to categories](../../index.md)
