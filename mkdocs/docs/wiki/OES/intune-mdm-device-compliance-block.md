---
hide:
  - navigation
root_cause_id: OES/intune-mdm-device-compliance-block
family: OES
ticket_count: 16
curated: true
self_serviceable: false
---

# Intune device compliance block disrupting Exchange Online mobile and desktop sync

[← Back to categories](../../index.md)

## Description

Affected users experience a loss of email synchronization on managed mobile devices (iOS and Android) running Outlook, and in many cases on Outlook for Windows as well. The mobile Outlook app typically displays a "Disconnected" banner or shows a stale "Last synced" timestamp, and new messages stop arriving entirely — sometimes for several hours. Push notifications may also cease. On the desktop, Outlook may show a "Disconnected" status in the bottom status bar, with send/receive operations failing or delivering messages only after significant delay.

A distinguishing characteristic of this issue is a split between clients: Exchange Online webmail (OWA) generally continues to show current mailbox content, confirming that the mailbox itself remains available, while one or both Outlook clients are unable to sync. In some cases desktop Outlook recovers after a profile rebuild or restart, but the mobile client remains stalled until the underlying device compliance state is addressed. Users may also recall seeing an Intune or Company Portal compliance notification on their mobile device that was dismissed or left incomplete before the sync failure began.

The issue has affected individual users as well as groups of users simultaneously — particularly after scheduled compliance policy updates — spanning multiple offices and device platforms. In multi-user incidents, the pattern is consistent: managed devices are flagged as non-compliant in the organization's mobile device management system, and Exchange Online begins returning blocked or denied responses for those devices. Exchange Online server logs may also show repeated throttling (HTTP 429) errors tied to aggressive retry loops from affected clients, which can compound the disruption and create additional log noise even after the primary compliance block is identified.

!!! note "Reported variations"

    - Some users experienced the compliance block only on the mobile device while desktop Outlook continued to sync normally, making the issue appear to be a mobile-only problem until the device compliance state was reviewed.
    - In certain cases, a stale or corrupted Outlook desktop profile was present alongside the compliance block, requiring both a profile rebuild on the desktop and compliance remediation on the mobile device before full sync was restored.
    - Devices that were recently re-enrolled in MDM experienced a transient non-compliant state that triggered a burst of sync requests, leading to Exchange Online mailbox throttling (HTTP 429 errors) as a secondary symptom.
    - Some Android devices appeared connected in Outlook Mobile but silently stopped receiving new messages and push notifications, with no visible "Disconnected" banner — the only indicator was stale inbox content and a non-compliant status in Company Portal.
    - A deprecated or outdated compliance policy reference on the device caused it to be evaluated as non-compliant even though the device otherwise met current security requirements.

## Affected environment

Distribution across 16 reported cases:

- **Operating system:** iOS 16; Windows 10 (12%), iOS 15.4 and Windows 10 (6%), Windows 10; iOS 15 (6%)
- **Device / platform:** mobile (31%), mobile and desktop (25%), Microsoft 365 / Exchange Online (12%)
- **Team:** Sales (62%), Sales - Mobile Users (12%), global-sales (6%)
- **Region:** us-east-1 (50%), EMEA (25%), US-West (12%)

## Root cause

A change or update to an Intune device compliance policy caused affected managed devices — phones and, in some cases, desktops — to be evaluated as non-compliant. Because Exchange Online enforces conditional access based on device compliance status, non-compliant devices were blocked from synchronizing email, resulting in denied mobile sync requests and disconnected Outlook sessions. In some instances, the compliance block also triggered excessive retry attempts from Outlook clients, which led to secondary Exchange Online throttling on the affected mailboxes.

## Diagnostics

Steps used to confirm this root cause:

1. Review the reported Outlook client state and compare mobile disconnected behavior with intermittent desktop access to determine whether the issue is endpoint-specific or mailbox-wide.  
   *Expected:* Outlook shows connected and mailbox folders update without sync delay.
2. Assess whether sign-out/sign-in or account re-add is needed to clear a stale Outlook session after compliance is restored.  
   *Expected:* Clean profile syncs the mailbox without stale cache errors.
3. Review mobile sync partnership health together with device compliance context from the ticket to assess whether Exchange Online mobile access is being blocked by MDM policy.  
   *Expected:* Active mobile partnerships are healthy and compliant.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Reviewed Intune compliance status for the affected iOS device (<HOSTNAME>, user <USER>, EMP <EMP_ID>) and identified that the device was failing the required OS patch compliance policy (minimum iOS 15.4.1 not met).
2. Remediated the device compliance issue by coordinating with <PERSON> (<PHONE>) to update the required OS patch level on the iPhone, then reapplied the Intune compliance profile until the device returned to a compliant state as verified by agent <PERSON>.
3. Cleared the affected device's (<HOSTNAME>) ActiveSync partnership in Exchange Online via Remove-MobileDevice cmdlet to remove the blocked mobile sync relationship for mailbox <EMAIL>.
4. Forced a fresh device/mailbox synchronization after compliance returned to healthy so Exchange Online could establish a new allowed ActiveSync partnership for <HOSTNAME> against the <EMAIL> mailbox.
5. Had <PERSON> restart Outlook on <HOSTNAME> and re-initiate mobile sync on the iPhone, then verified successful send/receive and current mailbox updates on both iOS and Outlook desktop. Confirmed no further 403 blocks in Exchange Online logs.

**Example 2**

1. Reviewed the affected mailbox for <EMAIL> and device state in Exchange Online and Intune to confirm the mobile device registered to <PERSON> (<EMP_ID>) was associated with a deprecated compliance policy reference CP-EMEA-2025-DEPRECATED and that mailbox connectivity was intermittently dropping from client IP <IP>.
2. Cleared the existing mobile sync partnership for the affected device belonging to <USER> so the mailbox could establish a fresh synchronization relationship after compliance was corrected.
3. Rebuilt the user's Outlook profile on the Windows workstation <HOSTNAME> to remove the stale local profile state for <USER> and re-established the Exchange Online mailbox connection to <EMAIL>. This step was performed by desktop support engineer <PERSON>.
4. Updated the device from the deprecated MDM compliance policy reference CP-EMEA-2025-DEPRECATED to the current policy version and forced a new compliance evaluation in Intune for user <PERSON> (<EMP_ID>) in the <LOCATION> office.
5. Validated that the device returned to a compliant state and confirmed mailbox synchronization resumed successfully in Outlook desktop on <HOSTNAME> and on the mobile device for <EMAIL>, then monitored for recurrence. Notified <PERSON> at <PHONE> that service was restored.

## Recommendation

This issue is resolved by IT support; reference 'Intune MDM device compliance block' when reporting it.

---

[← Back to categories](../../index.md)
