---
hide:
  - navigation
root_cause_id: DCP/encryption-actually-disabled-or-attestation-failed
family: DCP
ticket_count: 3
curated: true
self_serviceable: false
---

# Conditional Access block due to missing or inactive BitLocker encryption on endpoint

[← Back to categories](../../index.md)

## Description

Affected users on corporate-managed Windows 10 or Windows 11 devices find themselves unable to access protected Microsoft 365 resources such as Outlook, SharePoint Online, Exchange Online, or Dynamics 365. When attempting to connect, Conditional Access denies the request because the device is marked as noncompliant in Intune. The Company Portal application also displays the device as noncompliant.

The issue typically surfaces after a compliance policy requiring BitLocker device encryption is rolled out or updated. Although the affected devices may have current check-in timestamps and are receiving compliance evaluations normally, the encryption compliance signal is either missing entirely or reports an unhealthy state — for example, BitLocker protection may be suspended or encryption setup may not have completed. This distinguishes the issue from problems involving stale check-ins or incorrect policy targeting.

The scope of impact can range from a single device to multiple endpoints across one or more offices. In some cases, encryption stalled during initial provisioning and was never completed; in others, BitLocker protection was suspended on a device that had previously been encrypted. Until the endpoint reports a valid, active encryption status back to Intune, the compliance evaluation continues to fail and Conditional Access continues to block access to protected applications.

!!! note "Reported variations"

    - On some devices, BitLocker encryption stalled during initial provisioning and required local user interaction to complete setup and reboot before the encryption signal could be reported.
    - In certain cases, BitLocker protection was found to be suspended rather than absent, causing the endpoint to report an unhealthy encryption state even though encryption had been configured previously.
    - A forced remote sync and remote BitLocker enablement resolved the issue for a majority of affected devices, but a subset still required hands-on local action to complete encryption before compliance cleared.

## Affected environment

Distribution across 3 reported cases:

- **Operating system:** Windows 10 21H2 (67%), Windows 10/11 mixed (33%)
- **Device / platform:** Corporate-managed endpoints (MDM) (33%), Windows (33%), PC (33%)
- **Team:** Sales and Field Engineers (33%), Sales (33%), Marketing (33%)
- **Region:** US-East (67%), EMEA (33%)

## Root cause

The affected endpoints either did not have BitLocker disk encryption fully enabled or had BitLocker protection in a suspended or incomplete state. Because the compliance policy requires active encryption, these devices could not pass the encryption check during compliance evaluation. Without a valid encryption attestation reported back to Intune, the devices remained noncompliant and Conditional Access denied access to protected resources.

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

1. Confirmed local BitLocker status on device <HOSTNAME> via remote PowerShell (manage-bde -status C:) and identified that protection was suspended rather than missing due to stale reporting. Agent <PERSON> (<USER>) coordinated with <PERSON> to perform the remediation.
2. Re-enabled BitLocker protection on <HOSTNAME> by running 'manage-bde -protectors -enable C:' and verified the encryption state returned to healthy on the endpoint. Protection status confirmed as 'Protection On' after the command completed.
3. Triggered a device sync from Company Portal on <HOSTNAME> and confirmed Intune marked the device Compliant again within approximately 5 minutes. Validated that <PERSON> (<EMAIL>) could successfully sign in to Exchange Online without Conditional Access blocks. Ticket closed by agent <USER>.

## Recommendation

This issue is resolved by IT support; reference 'BitLocker encryption noncompliance — Conditional Access block' when reporting it.

---

[← Back to categories](../../index.md)
