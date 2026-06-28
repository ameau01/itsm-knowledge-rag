---
hide:
  - navigation
root_cause_id: OES/stale-corrupted-outlook-desktop-profile-cache
family: OES
ticket_count: 11
curated: true
self_serviceable: false
---

# Stale or Corrupted Outlook Desktop Profile Blocks Exchange Online Sync

[← Back to categories](../../index.md)

## Description

Affected users running Outlook Desktop on Windows with Exchange Online mailboxes experience a persistent "Disconnected" state in the Outlook status bar, preventing the inbox and calendar from updating. Restarting Outlook, signing out and back in, or triggering manual Send/Receive does not resolve the condition. Outlook on the web continues to display current mail for the same mailbox, confirming that the Exchange Online service remains healthy and the failure is isolated to the local desktop client.

In many cases, mobile devices (primarily iOS) also stop syncing or display stale messages, indicating broken or outdated sync partnerships alongside the desktop profile corruption. Other applications on the affected workstations continue to function normally, and the Exchange Online service health dashboard shows no outage or degradation.

The issue has been observed as both isolated single-user incidents and multi-user events affecting teams within the same office. In one case, multiple members of a corporate sales team reported identical disconnected behavior on their laptops following a weekend patch cycle, with local OST inconsistencies identified across all affected machines. Triggering events include Office update or weekend patch cycles, profile update rollouts, and local profile restores. Autodiscover traces on affected workstations may reveal authentication failures (HTTP 401) tied to a stale profile GUID, and backend telemetry has occasionally shown intermittent HTTP 503 throttling during the incident window, complicating initial triage.

!!! note "Reported variations"

    - Manual Send/Receive and Autodiscover verification against the autodiscover endpoint did not restore connectivity on the desktop client.
    - Mobile sync remained delayed even after the desktop profile was successfully rebuilt, requiring a separate mobile sync partnership reset.
    - Backend Exchange Online telemetry showed intermittent HTTP 503 throttling during the incident window for one affected mailbox, complicating initial triage.
    - A group of users in the same office experienced simultaneous disconnected states after a weekend patch cycle, with OST file inconsistencies identified on each machine.
    - Some affected users experienced the issue on desktop only, with mobile email continuing to sync normally.
    - In certain cases, the mobile device was flagged as noncompliant in Intune, contributing to intermittent or blocked mobile email access alongside the desktop disconnection.
    - Autodiscover traces revealed authentication failures tied to a stale profile GUID in the local credential store rather than a broader connectivity or service issue.
    - Mobile sync failure presented as a silent lack of new mail rather than an explicit error message, in contrast to the desktop client's visible "Disconnected" indicator.

## Affected environment

Distribution across 11 reported cases:

- **Operating system:** Windows 10 (55%), Windows 10; iOS 15 (27%), Windows 10 / iOS 15 (9%)
- **Device / platform:** Office 365 / Exchange Online (18%), Microsoft 365 (18%), Outlook Desktop (MS Office 365) (9%)
- **Team:** Sales (64%), Corporate Messaging Users (9%), Corporate Sales Users (9%)
- **Region:** us-east-1 (73%), EMEA (18%), US (9%)

## Root cause

Stale or corrupted Outlook desktop profiles—typically triggered by an Office update, weekend patch cycle, or profile update rollout—caused invalid cached mailbox settings, OST inconsistencies, and sync token mismatches that prevented the desktop client from establishing a healthy MAPI-over-HTTP session with Exchange Online. In several cases, stale mobile sync partnerships or device compliance conditions also required remediation before full mailbox synchronization resumed.

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

Resolved by IT through Outlook desktop profile rebuild and, where applicable, mobile sync partnership reset and credential cache cleanup.

---

[← Back to categories](../../index.md)
