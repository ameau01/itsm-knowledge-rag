---
hide:
  - navigation
root_cause_id: OES/suspected-server-side-mailbox-fault
family: OES
ticket_count: 2
curated: true
self_serviceable: false
---

# Exchange Online Mailbox-Side Sync Fault Across Multiple Clients

[← Back to categories](../../index.md)

## Description

Affected users experience a failure of Outlook to sync new email and calendar data across multiple clients — both desktop and mobile — for the same Exchange Online mailbox. On mobile devices, the Outlook app shows stale data with no new messages arriving, while the desktop client displays a persistent or flickering Disconnected status. The issue is not limited to a single endpoint or platform; the same mailbox exhibits sync failure on both desktop and mobile simultaneously, distinguishing it from a client-side or device-specific problem.

Standard local remediation steps do not resolve the issue. Rebuilding the Outlook profile on the desktop may temporarily restore connectivity on that client, but mobile sync remains broken. Toggling airplane mode, restarting the mobile app, and refreshing client sessions have no effect. MDM compliance checks on enrolled mobile devices return normal results, and no Microsoft 365 service outage is reported by the organization or visible to colleagues on the same network.

The failure is isolated to a single mailbox rather than a broader connectivity or tenant-level problem. Other users in the same office with different Exchange Online mailboxes are unaffected. Affected users are unable to rely on current mailbox data during the workday, impacting time-sensitive activities such as client-facing meetings.

!!! note "Reported variations"

    - In one case the desktop Outlook connection status flickered between Connected and Disconnected throughout the day rather than remaining steadily disconnected.
    - In one case a desktop profile rebuild restored desktop sync, but the mobile client continued to show Disconnected with no new mail, leaving the issue partially resolved on only one platform.
    - In one case the desktop client remained steadily Disconnected even after troubleshooting, with no partial restoration on any platform prior to escalation.

## Affected environment

Distribution across 2 reported cases:

- **Operating system:** iOS 16.5 (50%), Windows 10 and iOS 15 (50%)
- **Device / platform:** iOS / Android / Desktop Windows 10 (50%), Desktop and Mobile (50%)
- **Team:** Corporate Mobile Users (50%), Sales (50%)
- **Region:** us-east-1 (100%)

## Root cause

A suspected Exchange Online service-side mailbox synchronization fault or transient service condition is affecting multiple client sessions for a single user. There is insufficient local evidence to attribute the failure to the Outlook profile, device compliance, or network connectivity. The issue manifests at the mailbox level rather than at the client or tenant level.

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

Resolved by IT; Exchange Online mailbox-level sync fault affecting multiple client platforms for a single user.

---

[← Back to categories](../../index.md)
