---
hide:
  - navigation
root_cause_id: OES/exchange-online-mailbox-throttling
family: OES
ticket_count: 3
curated: true
self_serviceable: false
---

# Exchange Online Mailbox Throttling Disrupting Client Synchronization

[← Back to categories](../../index.md)

## Description

Affected users experience a sudden loss of email synchronization across Outlook desktop and Outlook mobile clients connected to their Exchange Online mailboxes. Desktop clients display a "Disconnected" status in the status bar, while mobile clients report sync errors or show a "last synced: never" indication. Outlook on the Web (OWA) typically continues to display incoming messages normally, confirming that the mailbox remains available at the service level even as thick clients fail to sync. The disruption often begins in the morning hours and persists through standard troubleshooting steps such as app restarts, device reboots, and toggling airplane mode.

Exchange Online diagnostics consistently reveal HTTP 429 throttling responses or EWS throttling entries against the affected mailboxes during sync attempts. Error code 0x800CCC0E has been observed during mobile sync failures alongside the throttling indicators. Rebuilding the Outlook desktop profile may restore mail flow on the desktop side, suggesting stale local profile or OST involvement, but the mobile client typically continues to fail even after the desktop recovers. Clearing and re-pairing the mobile ActiveSync partnership produces only brief or partial reconnection before sync breaks down again.

Cases in this category were escalated to Exchange Online backend support for throttle policy review and, where applicable, to MDM administrators after device non-compliance states were identified against affected mobile device partnerships.

!!! note "Reported variations"

    - Desktop Outlook intermittently toggling between Connected and Disconnected states rather than remaining fully disconnected
    - Split-client experience in which a desktop profile rebuild restores desktop sync while the mobile client remains in a failed state
    - MDM reporting a brief device non-compliance hold on the mobile device partnership, compounding the sync failure
    - Transient recovery of both desktop and mobile clients after ActiveSync re-pairing, followed by relapse into sync failure
    - Error code 0x800CCC0E observed during mobile sync failures concurrent with HTTP 429 throttling responses

## Affected environment

Distribution across 3 reported cases:

- **Operating system:** Windows 10 (67%), iOS 16.5 (33%)
- **Device / platform:** iOS / Android / Desktop Windows 10 (33%), desktop and mobile (33%), Office 365 (33%)
- **Team:** Sales (67%), Corporate Mobile Users (33%)
- **Region:** us-east-1 (100%)

## Root cause

Exchange Online backend throttling was the primary cause, generating intermittent HTTP 429 responses and EWS throttling entries that interrupted ActiveSync and Outlook mobile connections. A stale or corrupted Outlook desktop profile and local OST file contributed to desktop-side disconnection, creating conflicting evidence, but were not the root cause of the persistent mobile sync failure. Recovery was achieved after a temporary throttle exception was applied at the service level.

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

Resolved by IT after Exchange Online backend support applied a temporary throttle exception and the desktop Outlook profile and mobile device partnership were reset.

---

[← Back to categories](../../index.md)
