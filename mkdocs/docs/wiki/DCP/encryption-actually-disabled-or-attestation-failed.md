---
hide:
  - navigation
root_cause_id: DCP/encryption-actually-disabled-or-attestation-failed
family: DCP
ticket_count: 3
curated: true
self_serviceable: false
---

# BitLocker Encryption Not Active or Attested Causing Noncompliance Block

[← Back to categories](../../index.md)

## Description

Affected users on corporate-managed Windows 10 and Windows 11 devices experience blocks when accessing protected Microsoft 365 resources — including SharePoint Online, Outlook, Exchange Online, and Dynamics 365. Conditional Access evaluates the devices as noncompliant in Intune because a healthy BitLocker encryption attestation signal is not being reported. Company Portal or the Intune admin console shows the affected devices as noncompliant, and users cannot reach protected applications until encryption status is correctly reported.

The underlying condition varies but consistently involves BitLocker encryption not being in a fully enabled and attested state. In some cases, encryption stalled during initial device provisioning and required local user interaction to complete setup. In other cases, BitLocker protection was found to be suspended on the endpoint, causing the compliance evaluation to return an unhealthy encryption state even though the device was otherwise online and scoped to the correct policy. A third presentation involves devices where encryption began only after a policy sync, with no prior encryption signal present.

The issue has been observed following the rollout of new or updated compliance policies requiring BitLocker device encryption. Multiple users and devices may be affected simultaneously within the same office or policy scope. In at least one case, a stale device check-in compounded the problem by further delaying the reporting of encryption status to Intune.

!!! note "Reported variations"

    - Encryption setup stalled during initial device provisioning and required local user interaction (e.g., completing BitLocker setup and rebooting) before the device could report compliance.
    - BitLocker protection was found to be suspended on the endpoint rather than absent, resulting in the compliance evaluation returning an unhealthy encryption state despite the device being online and scoped to the correct policy.
    - A stale device check-in (over 24 hours) compounded the issue by delaying the reporting of encryption status to Intune, prolonging the Conditional Access block.
    - Multiple devices across more than one office were affected simultaneously following a compliance policy rollout requiring BitLocker encryption.
    - Some devices began encryption only after a forced sync with the new compliance policy, indicating encryption had not previously been initiated on those endpoints.

## Affected environment

Distribution across 3 reported cases:

- **Operating system:** Windows 10 21H2 (67%), Windows 10/11 mixed (33%)
- **Device / platform:** Corporate-managed endpoints (MDM) (33%), Windows (33%), PC (33%)
- **Team:** Sales and Field Engineers (33%), Sales (33%), Marketing (33%)
- **Region:** US-East (67%), EMEA (33%)

## Root cause

After an encryption compliance requirement was enforced, a subset of managed endpoints either had BitLocker encryption disabled, suspended, or incomplete — or did not successfully report encryption attestation back to Intune. This caused device compliance to remain noncompliant and Conditional Access to deny access to protected resources. Once BitLocker was fully active and a successful policy refresh reported the encryption telemetry, compliance was restored.

## Diagnostics

Steps used to confirm this root cause:

1. Confirmed recent Intune device check-in and compliance evaluation timestamps for affected endpoints.  
   *Expected:* Device check-in timestamp is current and compliance evaluation has run.
2. Reviewed the encryption compliance signal in Intune for impacted devices and compared it with remediation behavior after forced check-in and encryption enablement.  
   *Expected:* Required compliance signals report healthy values.
3. Validated that affected users and devices were targeted by the intended encryption compliance policy after the recent rollout.  
   *Expected:* Device is in the intended policy scope with no stale assignment.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Reviewed affected devices in Intune (including <HOSTNAME> assigned to <PERSON> and <HOSTNAME> assigned to <PERSON>) to confirm the failing compliance condition was the BitLocker encryption requirement under policy ENC-REQ-2025-Q4, and verified recent check-in and compliance evaluation timestamps for all impacted endpoints.
2. Issued remote sync and forced device check-in actions from Intune to retrigger compliance evaluation on impacted endpoints that had stale or missing encryption status, starting with the <LOCATION> office devices (10.47.22.x subnet) and then <LOCATION> endpoints assigned to <PERSON> (<USER>) and others.
3. Applied remote BitLocker encryption enablement on devices that supported it (including <HOSTNAME> at <IP>) so full-disk encryption could begin and the required compliance signal could be generated. Approximately 70% of affected endpoints transitioned to compliant status within 15 minutes.
4. Provided user guidance via email to <PERSON> (<EMAIL>), <PERSON> (<USER>), and remaining affected users for endpoints that required local interaction to complete BitLocker encryption enablement, including allowing encryption to finish and reconnecting to trigger a fresh compliance report. <PERSON> (<USER>) coordinated on-site assistance in <LOCATION>.
5. Re-ran compliance evaluation and confirmed affected devices reported encryption attestation to Intune, after which Conditional Access permitted normal access for remediated endpoints. Final verification completed for all impacted users including <USER>, <USER>, and <USER> by 2025-12-29T01:15Z.

**Example 2**

1. Triggered a remote Intune sync on <HOSTNAME> (enrolled under <EMAIL>) to refresh the stale device check-in and force a new compliance evaluation.
2. Reviewed the compliance record for <HOSTNAME> in the Intune portal, identified the missing encryption signal (RequireDeviceEncryption: Not reported, ErrorCode: 0x87d1041c) as the only failing control, and re-applied the corporate RequireDeviceEncryption and BitLocker configuration to the device.
3. Had <PERSON> complete the local BitLocker enablement process on the laptop <HOSTNAME> and reboot so the operating system could finalize encryption status and submit updated telemetry to Intune.
4. Confirmed the device checked in again after reboot at 2026-01-03T18:02Z, the encryption state populated correctly in Intune (BitLocker XTS-AES 256), and the compliance evaluation changed from Noncompliant to Compliant for <USER>.
5. Validated that Conditional Access was no longer blocking the managed device <HOSTNAME> and that access to Outlook and SharePoint Online was restored for <PERSON> (<EMAIL>) at the <LOCATION> office.

## Recommendation

Resolved by IT after confirming BitLocker encryption was fully active and ensuring the device reported healthy encryption attestation to Intune following a policy refresh.

---

[← Back to categories](../../index.md)
