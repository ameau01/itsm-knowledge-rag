---
hide:
  - navigation
root_cause_id: DCP/stale-checkin-missing-encryption-signal
family: DCP
ticket_count: 27
curated: true
self_serviceable: false
---

# Stale Intune check-in prevents encryption signal from reaching compliance evaluation

[← Back to categories](../../index.md)

## Description

Affected users find that their managed devices — including Windows, macOS, iOS, and Android endpoints — are marked as Noncompliant in Intune Company Portal, and Conditional Access blocks access to corporate resources such as Exchange Online, SharePoint, Teams, Outlook, VPN, Dynamics 365, and other protected applications. The block page typically states that the device does not meet organizational compliance requirements or is not compliant, and the Company Portal compliance details show the encryption status as "Not reported," "Unknown," "Not Encrypted," or blank.

The common thread across affected devices is a stale Intune check-in — the device has not successfully communicated its status to Intune for a period ranging from roughly 36 hours to 14 or more days. Because the check-in is outdated, the required encryption compliance signal (BitLocker on Windows, FileVault on macOS, or device encryption on iOS and Android) is never delivered to the compliance service, and the device remains in a noncompliant state. Conditional Access then enforces the "require compliant device" policy and denies access.

In some cases, a manual sync from Company Portal updates the check-in timestamp but does not immediately restore the encryption signal, leaving the device noncompliant even after the sync appears to complete. In other cases, Intune may briefly show the device as compliant while Conditional Access continues to use an older noncompliant evaluation, creating a temporary mismatch between what Company Portal displays and what Conditional Access enforces. The issue has been observed on individual devices as well as in larger groups of endpoints — sometimes affecting a dozen or more devices simultaneously — particularly after a compliance policy update or scheduled policy re-evaluation.

!!! note "Reported variations"

    - After a hardware component replacement (such as a motherboard swap), the device's encryption attestation data may be invalidated, causing the encryption signal to remain missing even though BitLocker appears enabled locally.
    - On newly enrolled devices, the post-enrollment check-in may fail to deliver the encryption signal, leaving the device in a noncompliant state immediately after enrollment rather than after a period of inactivity.
    - Conditional Access may continue to enforce a noncompliant evaluation for a period even after Intune Company Portal shows the device as compliant, due to a propagation delay between the compliance service and Conditional Access.
    - A manual Company Portal sync may complete successfully and update the check-in timestamp without refreshing the encryption compliance signal, requiring additional steps such as a reboot or a server-side re-evaluation to restore reporting.
    - Some devices require local encryption to be enabled or re-enabled (for example, BitLocker was paused or never fully activated) before the compliance signal can be reported, rather than the issue being purely a check-in delay.

## Affected environment

Distribution across 27 reported cases:

- **Operating system:** Windows 10 21H2 (37%), Windows 10 22H2 (7%), Android 11 (4%)
- **Device / platform:** Windows (19%), laptop (15%), macOS (7%)
- **Team:** Sales (44%), Marketing (7%), RemoteWorkers (7%)
- **Region:** US-East (41%), EMEA (41%), NA (7%)

## Root cause

Devices that have not checked in to Intune for an extended period retain stale compliance data, which prevents the required encryption status (such as BitLocker, FileVault, or mobile device encryption) from being reported to the compliance service. Without a current encryption signal, the compliance policy evaluates the device as noncompliant, and Conditional Access enforces that result by blocking access to protected corporate resources. In some instances, a subset of devices also required local encryption enablement, operating system updates, or re-enrollment before consistent encryption reporting could be permanently restored.

## Diagnostics

Steps used to confirm this root cause:

1. Confirmed the device's recent Intune check-in status and whether compliance evaluation had run after the reported access issue.  
   *Expected:* Device check-in timestamp is current and compliance evaluation has run.
2. Reviewed the failing compliance signal for device encryption to determine why the endpoint was marked noncompliant.  
   *Expected:* Required compliance signals report healthy values.
3. Compared the assigned compliance policy with the device's intended scope and assignment to rule out stale or incorrect targeting.  
   *Expected:* Device is in the intended policy scope with no stale assignment.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Validated that <HOSTNAME>'s Intune check-in was stale (last seen 2025-12-27T05:32:00Z) and that the active compliance failure for <USER> (<EMP_ID>) was tied to the missing BitLocker encryption signal rather than a broader enrollment failure.
2. Had <PERSON> run a manual Company Portal sync on <HOSTNAME> and reboot the device to trigger a fresh management check-in and compliance evaluation cycle against the 'Sales-Win10-Standard' policy.
3. Verified BitLocker status on <HOSTNAME> via the manage-bde -status command and confirmed full disk encryption was enabled on the OS drive (C:), so the required encryption compliance signal could be reported back to Intune's Device Compliance Service.
4. Triggered a follow-up Intune sync on <HOSTNAME> after encryption status was confirmed active, allowing the device record to refresh and the compliance state to be recalculated by Device Compliance Service. Agent <PERSON> monitored the sync from the Intune admin console.
5. Confirmed <HOSTNAME> returned to compliant status in Intune at approximately 06:45 UTC and that Conditional Access no longer blocked <EMAIL> access to Exchange Online email and SharePoint Online. <PERSON> verified he could open Outlook and SharePoint successfully.
6. Used the documented temporary access exception (applied by <PERSON> for <USER>'s account) only during the remediation window and removed reliance on the workaround once compliant reporting was restored on <HOSTNAME>.

**Example 2**

1. Validated that <HOSTNAME> (enrolled under <USER>, <EMP_ID>) had not checked in to Intune for approximately 72 hours (last check-in 2025-12-24T22:48:00Z) and confirmed the missing BitLocker encryption attribute was the compliance signal causing the Noncompliant state.
2. Triggered a remote device sync from the Intune admin console targeting <HOSTNAME> and had <PERSON> retry local sync from Company Portal to force a fresh compliance evaluation.
3. Reapplied the assigned encryption/compliance policy (ENG-RemoteWorkers-Compliance-v3) so the endpoint <HOSTNAME> could submit the required BitLocker status back to Intune device inventory.
4. Used re-enrollment as the remediation path for devices that still failed to report encryption after sync. <PERSON> guided <USER> through the re-enrollment steps, then verified <HOSTNAME> resumed normal management check-in from IP <IP>.
5. Confirmed the device compliance state for <HOSTNAME> returned to Compliant and removed the temporary Conditional Access exemption for <USER> after SharePoint and Teams access was restored. <PERSON> confirmed full access at 2025-12-28T01:45:00Z.

## Recommendation

This issue is resolved by IT support; reference 'stale check-in missing encryption signal' when reporting it.

---

[← Back to categories](../../index.md)
