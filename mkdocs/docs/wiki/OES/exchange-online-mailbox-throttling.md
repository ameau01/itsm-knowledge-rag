---
hide:
  - navigation
root_cause_id: OES/exchange-online-mailbox-throttling
family: OES
ticket_count: 3
curated: true
self_serviceable: false
---

# Exchange Online mailbox throttling disrupting Outlook desktop and mobile sync

[← Back to categories](../../index.md)

## Description

Affected users experience a sudden loss of email synchronization in both Outlook desktop and Outlook mobile, typically beginning in the morning hours. On the desktop client, Outlook displays a "Disconnected" status in the status bar, which may appear persistently or flicker intermittently between connected and disconnected states. On mobile devices, the Outlook app reports sync errors, displays "Last synced: never," or shows a persistent disconnected indicator despite normal network connectivity on both Wi-Fi and cellular.

Notably, webmail access through Outlook on the Web (OWA) continues to function normally during the disruption, with new messages visible in the browser. This contrast between working OWA and failing desktop/mobile clients is a key characteristic of the issue. Standard user-side troubleshooting steps such as restarting devices, toggling airplane mode, or relaunching the Outlook app do not resolve the problem.

Rebuilding the Outlook desktop profile or resetting the mobile ActiveSync partnership may produce brief, temporary recovery — new mail may flow for a short period before synchronization fails again. The persistence of the issue after these client-side fixes, combined with continued OWA availability, distinguishes this condition from a purely local profile corruption or a full mailbox outage. Affected users may also encounter ActiveSync error codes such as 0x800CCC0E on mobile devices.

!!! note "Reported variations"

    - Some affected users experience the issue only on mobile after a desktop Outlook profile rebuild restores desktop sync, with mobile ActiveSync connections continuing to receive throttling responses.
    - A brief mobile device compliance hold reported by the organization's device management system may coincide with the throttling event, temporarily compounding the mobile sync failure before the device is confirmed compliant.
    - In some cases, the desktop Outlook client intermittently flips between Connected and Disconnected states rather than remaining fully disconnected, making the issue appear transient on the desktop side.

## Affected environment

Distribution across 3 reported cases:

- **Operating system:** Windows 10 (67%), iOS 16.5 (33%)
- **Device / platform:** iOS / Android / Desktop Windows 10 (33%), desktop and mobile (33%), Office 365 (33%)
- **Team:** Sales (67%), Corporate Mobile Users (33%)
- **Region:** us-east-1 (100%)

## Root cause

The primary cause is a throttling condition applied by Exchange Online against the affected user's mailbox, which limits or blocks client synchronization requests. This throttling generates HTTP 429 (too many requests) responses to desktop EWS and mobile ActiveSync connections, preventing Outlook desktop and mobile from maintaining a stable sync. While stale or corrupted local Outlook profiles and temporary mobile device compliance issues may contribute to the initial symptoms or create conflicting evidence, the lasting synchronization failure is driven by the server-side throttling rather than client-side factors alone.

## Diagnostics

Steps used to confirm this root cause:

1. Checked Outlook connection state on desktop and mobile and compared mailbox sync behavior against Exchange Online diagnostics.  
   *Expected:* Outlook shows connected and mailbox folders update without sync delay.
2. Tested mailbox behavior with a rebuilt desktop Outlook profile to determine whether the local client profile was stale or corrupted.  
   *Expected:* Clean profile syncs the mailbox without stale cache errors.
3. Reviewed mobile mailbox partnership health and compliance state, then cleared and re-paired the device partnership for retest.  
   *Expected:* Active mobile partnerships are healthy and compliant.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Validated the connection state across desktop (<HOSTNAME>) and mobile (<HOSTNAME>) clients for mailbox <EMAIL> to separate the desktop profile issue from the continuing mobile sync failure.
2. Rebuilt the desktop Outlook profile on <HOSTNAME> for user <USER> and confirmed desktop mailbox synchronization resumed normally with full folder hierarchy and inbox updates.
3. Cleared the mobile ActiveSync partnership for <HOSTNAME> in Exchange Online admin center and re-paired the iOS device to rule out a stale device association or compliance issue. MDM confirmed device compliance throughout.
4. Escalated the mailbox <EMAIL> to Exchange Online support (handled by agent <PERSON>, <EMP_ID>) after diagnostics showed intermittent HTTP 429 throttling on mobile sync sessions originating from <HOSTNAME>.
5. Confirmed Exchange Online support applied a temporary throttle exception for mailbox <EMAIL> and verified mobile Outlook sync on <HOSTNAME> resumed successfully afterward. <PERSON> confirmed new emails arriving on mobile within minutes.
6. Closed the incident with monitoring guidance provided to <PERSON> (<EMAIL>) to re-engage Exchange support if throttling reappears for the mailbox or device <HOSTNAME>. Follow-up scheduled for 2026-02-18 by <PERSON>.

**Example 2**

1. Validated the mailbox sync issue by confirming Outlook desktop on <HOSTNAME> (user: <PERSON>.nguyen, IP <IP>) showed intermittent Disconnected status and Exchange Online logs contained repeated EWS throttling activity (HTTP 429) for the affected mailbox <EMAIL>.
2. Rebuilt <PERSON>'s Outlook profile on <HOSTNAME>, removed the corrupted OST file from the local AppData path, and allowed Outlook to create a fresh OST to remove the stale local cache condition. Profile rebuild was performed by desktop support technician <PERSON> (<USER>).
3. Cleared the existing mobile device partnership for <PERSON>'s iPhone in Exchange Online admin center, re-established the managed mobile mail connection via MDM, and forced an initial mailbox synchronization — confirmed by <PERSON> (security team) that compliance state returned to compliant.
4. Applied a temporary mailbox throttling policy adjustment for <EMAIL> to allow the affected mailbox to complete client re-sync from both desktop and mobile, and monitored Exchange Online EWS behavior during the stabilization window.
5. Verified that new mail appeared normally on Outlook desktop (<HOSTNAME>) and Outlook mobile, confirmed stable mail flow and folder updates over a 2-hour observation period, and received confirmation from <PERSON> (<PHONE>) that both clients were fully operational before closure.

## Recommendation

This issue is resolved by IT support with assistance from the backend Exchange Online support team; reference 'Exchange Online mailbox throttling' when reporting it.

---

[← Back to categories](../../index.md)
