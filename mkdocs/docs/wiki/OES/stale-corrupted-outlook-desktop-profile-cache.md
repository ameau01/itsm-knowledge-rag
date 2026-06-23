---
hide:
  - navigation
root_cause_id: OES/stale-corrupted-outlook-desktop-profile-cache
family: OES
ticket_count: 11
curated: true
self_serviceable: false
---

# Outlook desktop disconnection due to stale or corrupted local profile cache

[← Back to categories](../../index.md)

## Description

Affected users experience Outlook for Windows entering a persistent "Disconnected" state, with the inbox, calendar, and sent items ceasing to update. New messages do not appear in the desktop client, and manual Send/Receive attempts do not restore synchronization. The issue typically becomes apparent after a recent Office update, weekend patch cycle, profile update rollout, or local profile restore, though some users notice it without a clear triggering event. Throughout the disruption, Exchange Online webmail (OWA) at outlook.office365.com continues to display current mailbox content normally, confirming that the mailbox itself remains healthy on the server side.

In many cases, Outlook Mobile on iPhones or other devices is also affected. Mobile clients may show stale messages — sometimes hours behind — or stop syncing entirely alongside the desktop client. Temporarily re-adding the mobile account may briefly restore mail delivery on the phone, but the desktop client remains disconnected. The combination of a non-functional desktop client and delayed or stale mobile mail can give the impression of a broader mailbox or service outage, even though tenant-level Exchange Online health dashboards show no degradation.

The issue has been reported by individual users as well as groups of users in the same office or team, sometimes affecting multiple workstations simultaneously after a coordinated patch or profile update. Restarting Outlook, signing out and back in, or restarting the workstation does not resolve the disconnected state. Affected users are unable to reliably read, send, or respond to email from their primary desktop client, which can block time-sensitive business communication until the local profile and device sync state are repaired.

!!! note "Reported variations"

    - Some affected users' mobile devices are flagged as noncompliant in Intune, contributing to intermittent rather than fully absent mobile synchronization.
    - In isolated cases, backend Exchange Online telemetry shows transient HTTP 503 throttling during the same incident window, adding intermittent server-side delays on top of the client-side profile issue.
    - After a local Windows profile restore, the desktop client may return Autodiscover 401 authentication errors tied to an outdated profile identifier stored locally, rather than simply showing a generic disconnected state.
    - Temporarily re-adding the mobile email account may briefly restore mobile mail delivery, but the desktop client remains disconnected until the profile is rebuilt.

## Affected environment

Distribution across 11 reported cases:

- **Operating system:** Windows 10 (55%), Windows 10; iOS 15 (27%), Windows 10 / iOS 15 (9%)
- **Device / platform:** Office 365 / Exchange Online (18%), Microsoft 365 (18%), Outlook Desktop (MS Office 365) (9%)
- **Team:** Sales (64%), Corporate Messaging Users (9%), Corporate Sales Users (9%)
- **Region:** us-east-1 (73%), EMEA (18%), US (9%)

## Root cause

A stale or corrupted Outlook desktop profile — including outdated cached connection settings, invalid local OST (offline data) files, and mismatched authentication tokens — prevents the desktop client from establishing a working session with Exchange Online. This condition is typically introduced or exposed by Office updates, weekend patch cycles, profile update rollouts, or local profile restores that leave the cached Autodiscover configuration and mailbox sync data in an inconsistent state. In many instances, the affected user's mobile device also holds a stale ActiveSync sync partnership that must be cleared before mobile mail delivery fully resumes.

## Diagnostics

Steps used to confirm this root cause:

1. Checked Outlook connection state and send/receive behavior to confirm whether the mailbox session was connected or disconnected.  
   *Expected:* Outlook shows connected and mailbox folders update without sync delay.
2. Compared behavior after rebuilding the Outlook profile to determine whether the original profile had stale cache or configuration issues.  
   *Expected:* Clean profile syncs the mailbox without stale cache errors.
3. Reviewed whether a mobile device sync or compliance issue was likely contributing to the Outlook desktop mailbox problem.  
   *Expected:* Active mobile partnerships are healthy and compliant.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Validated that Outlook desktop on <HOSTNAME> (IP <IP>) was in a disconnected state for user <USER> and confirmed the <EMAIL> mailbox had stopped updating on both desktop and mobile clients since approximately 02:15 EST.
2. Created a new Outlook profile on <HOSTNAME> under the <USER> Windows session and re-added the Exchange Online mailbox (<EMAIL>) to replace the stale local profile and cached .ost state.
3. Allowed the mailbox to rehydrate in the new profile and verified Outlook returned to a connected state with current folder updates and successful send/receive. Full folder sync completed within approximately 4 minutes for the <EMAIL> mailbox.
4. Cleared the existing mobile ActiveSync partnership for <PERSON>' iPhone using Remove-MobileDevice in Exchange Online PowerShell and re-added the mailbox on the mobile client to establish a fresh sync relationship.
5. Confirmed current mail flow and successful synchronization on both desktop (<HOSTNAME>) and mobile before closing the incident. Advised <PERSON> to contact the Service Desk at <PHONE> if sync issues recur.

**Example 2**

1. Verified new mail was present in Exchange Online through OWA for <EMAIL> to confirm mailbox delivery and isolate the issue to Outlook client synchronization on <HOSTNAME> rather than a server-side mail flow outage.
2. Reviewed Outlook client behavior and sync evidence on <HOSTNAME> (IP <IP>), including the disconnected state and sync error 0x8004010F, which indicated local profile and cached folder state corruption for user <USER>.
3. Recreated the Outlook desktop mail profile for <USER> on <HOSTNAME> and cleared the local OST cache so the client could establish a fresh Exchange Online connection and rebuild mailbox data. Performed by <USER> from desktop support.
4. Reset the mobile sync partnership for <HOSTNAME> through Mobile Device Management and re-initiated account synchronization on the mobile client to remove stale device-side sync state for <PERSON> (<EMP_ID>).
5. Validated that Outlook desktop on <HOSTNAME> reconnected successfully, recent messages populated on both desktop and mobile clients for <EMAIL>, and mail synchronization remained stable during post-fix monitoring. <PERSON> confirmed full functionality at <PHONE>.

## Recommendation

This issue is resolved by IT support; reference "stale or corrupted Outlook desktop profile cache" when reporting it.

---

[← Back to categories](../../index.md)
