---
hide:
  - navigation
root_cause_id: OES/suspected-server-side-mailbox-fault
family: OES
ticket_count: 2
curated: true
self_serviceable: false
---

# Exchange Online mailbox-side sync fault affecting multiple client devices

[← Back to categories](../../index.md)

## Description

Affected users experience inconsistent or failed email and calendar synchronization across multiple devices connected to the same Exchange Online mailbox. On the desktop Outlook client, the connection status may flicker between "Connected" and "Disconnected" throughout the day rather than dropping permanently, and new mail items may not appear reliably. On mobile devices (such as the iPhone Outlook app), the client may show a persistent "Disconnected" status with no new mail arriving, and the displayed data becomes stale.

The issue is notable because it affects more than one client type — both desktop and mobile — for the same mailbox at the same time. Standard local troubleshooting steps such as rebuilding the Outlook desktop profile, toggling airplane mode, or restarting the mobile app do not fully resolve the problem. In some cases, the desktop client may temporarily resume syncing after a profile rebuild, but the mobile client remains stuck, or both clients continue to exhibit unreliable sync.

No broader Microsoft 365 service outage is reported, and colleagues using other Exchange Online mailboxes in the same office and on the same network are unaffected. Mobile device compliance checks through the organization's device management platform return normal results, and there is no endpoint policy block preventing access. The failure is isolated to the individual mailbox rather than to a specific device, network, or compliance condition.

!!! note "Reported variations"

    - Desktop Outlook may temporarily resume syncing after a local profile rebuild while the mobile client remains disconnected, giving the initial appearance of a mobile-only issue before the desktop symptoms return.
    - Exchange Online message tracking may reveal HTTP 429 throttling responses during peak sync windows for the affected mailbox, suggesting server-side rate limiting as a contributing factor.

## Affected environment

Distribution across 2 reported cases:

- **Operating system:** iOS 16.5 (50%), Windows 10 and iOS 15 (50%)
- **Device / platform:** iOS / Android / Desktop Windows 10 (50%), Desktop and Mobile (50%)
- **Team:** Corporate Mobile Users (50%), Sales (50%)
- **Region:** us-east-1 (100%)

## Root cause

The issue stems from a synchronization fault or service condition on the Exchange Online mailbox itself, rather than from a problem with the local Outlook profile, mobile device compliance, or network connectivity. Because multiple client types (desktop and mobile) are affected for the same mailbox and local remediation steps do not restore reliable sync, the root cause lies on the server side of the mail platform. In diagnosed cases, Exchange Online message tracking for the affected mailbox has shown throttling responses during peak synchronization windows, which can contribute to the sync failures seen across devices.

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

1. Documented the inconsistent client sync behavior on both <HOSTNAME> and <HOSTNAME> for user <USER> (<EMAIL>) and confirmed that profile rebuild on the desktop did not resolve the mailbox update issue — HTTP 429 throttling persisted across both clients.
2. Collected client and mailbox sync symptoms from desktop (<HOSTNAME>, Windows 10) and mobile (<HOSTNAME>, iOS 16.5) to rule out a simple endpoint-specific failure. Cleared the stale ActiveSync partnership for <HOSTNAME> and re-paired the device, which temporarily restored mobile connectivity before throttling resumed.
3. Escalated the incident to Exchange Online support for mailbox-level investigation of throttling on <EMAIL> (case ref attached) and advised <PERSON> to use Outlook on the web (https://outlook.office365.com) as a temporary workaround pending vendor findings. Notified manager <PERSON> (<EMAIL>) of the escalation status.

**Example 2**

1. Collect current Outlook connection state, client logs, and mailbox symptoms from both desktop (<HOSTNAME>, IP <IP>) and mobile to document the cross-client impact for mailbox <EMAIL> (<EMP_ID>, <LOCATION> office).
2. Escalate to Exchange Online or messaging support (assigned to <PERSON>, <USER>) to review mailbox health, service diagnostics, and mobile partnership state from the server side for <EMAIL>.
3. Maintain desktop webmail or alternate access as a workaround if available (user <PERSON> confirmed Outlook on the web at https://outlook.office365.com was functional during the outage), and confirm synchronization recovery after backend remediation by verifying both <HOSTNAME> and iPhone resume normal sync.

## Recommendation

This issue is resolved by IT support with escalation to the Exchange Online messaging team; reference "suspected server-side mailbox sync fault" when reporting it.

---

[← Back to categories](../../index.md)
