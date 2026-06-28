---
hide:
  - navigation
root_cause_id: OES/unresolved-endpoint-client-sync-state
family: OES
ticket_count: 7
curated: true
self_serviceable: false
---

# Stale Outlook Profile and Unhealthy Mobile Sync Partnership Block Mailbox Access

[← Back to categories](../../index.md)

## Description

Affected users — primarily in Sales, Field Ops, and Corporate Sales organizational units — report that both Outlook desktop (Windows 10) and Outlook mobile (managed iPhones) simultaneously stop synchronizing mailbox content. The desktop client displays a "Disconnected" or intermittently cycling disconnection status in the status bar, while mobile devices cease receiving new mail entirely, with the account flagged as requiring attention. Last-sync timestamps remain stale, ranging from several hours to approximately 48 hours. Despite client-side failures, Outlook on the web (OWA) continues to display current messages for the same mailboxes, confirming that Exchange Online availability is not impacted.

The issue has been observed following scheduled Microsoft 365 tenant maintenance windows, with multiple users across different office locations affected in close succession. Exchange Online server-side telemetry may show intermittent successful sync activity for affected mailboxes, presenting a mixed-state condition rather than a complete outage. Microsoft 365 service health dashboards do not report a broader service disruption, and colleagues on the same team remain unaffected.

On the mobile side, managed devices enrolled via Intune may display a non-compliant status in the Company Portal app, and stale or unhealthy device partnerships are found registered against affected mailboxes in the Exchange Online administration console. In at least one instance, an outdated MDM legacy-block rule originally scoped for decommissioned older iOS endpoints was found incorrectly matching current devices post-maintenance. On the desktop side, the Outlook profile enters a corrupted or unhealthy state; creating a clean profile on the same workstation restores synchronization immediately.

!!! note "Reported variations"

    - Some affected users report the issue beginning immediately on the first business day following a weekend maintenance window, while others experience onset mid-week with no obvious triggering event.
    - In certain cases, Intune explicitly reports the mobile device as non-compliant, whereas other affected users see no compliance warning in the Company Portal despite experiencing the same sync failure.
    - Exchange Online logs for some mailboxes show intermittent successful sync activity from the server side, presenting a mixed-state condition rather than a complete synchronization failure.
    - An outdated MDM legacy-block policy originally targeting decommissioned older iOS devices was found matching current iOS devices post-maintenance, contributing to mobile sync failures for compliant endpoints.
    - The duration of the sync outage varies, with some users experiencing stale mail for several hours and others reporting no client updates for up to approximately 48 hours before remediation.
    - Desktop Outlook showed intermittent disconnection cycling rather than a persistent disconnected state in some cases.
    - In one case, forcing a resync via Exchange Online PowerShell restored partial header updates on the desktop, but full folder synchronization required a complete profile rebuild.
    - One affected user had not recently changed their password or rebuilt their profile prior to the issue onset.

## Affected environment

Distribution across 7 reported cases:

- **Operating system:** Windows 10; iOS 15 (29%), Windows 10 (29%), Windows 10 and iOS 14 (14%)
- **Device / platform:** Desktop and Mobile (29%), Microsoft 365 / Exchange Online (14%), mixed (desktop and mobile) (14%)
- **Team:** Sales (71%), Sales and Field Ops (14%), Corporate Sales (14%)
- **Region:** us-east-1 (57%), NA (29%), unknown (14%)

## Root cause

Mailbox sync failures were caused by a corrupted or stale Outlook desktop profile combined with an unhealthy mobile sync partnership and device compliance state on the mobile endpoint. An outdated MDM legacy-block rule in the sync policy, originally targeting decommissioned iOS devices, was found interfering with current device synchronization after a tenant maintenance window. These endpoint-side conditions disrupted Exchange Online reauthentication and synchronization while server-side mailbox availability remained healthy.

## Diagnostics

Steps used to confirm this root cause:

1. Check Outlook connection status and whether the mailbox is connected, disconnected, or throttled.  
   *Expected:* Outlook shows connected and mailbox folders update without sync delay.
2. Start Outlook in safe mode or a clean profile to compare sync behavior.  
   *Expected:* Clean profile syncs the mailbox without stale cache errors.
3. Review mobile sync partnerships and device compliance state for the mailbox.  
   *Expected:* Active mobile partnerships are healthy and compliant.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Validated that the Exchange Online mailbox for <EMAIL> was current in OWA, confirming the mailbox itself was available and narrowing the issue to Outlook client synchronization on <HOSTNAME> and <HOSTNAME> rather than a server-side mail flow outage.
2. Compared Outlook connection behavior on <HOSTNAME> (IP <IP>) and isolated the desktop symptom to a client sync/connectivity issue after Outlook remained disconnected while OWA continued to update normally for <EMAIL>.
3. Rebuilt the Outlook desktop profile for <USER> on <HOSTNAME> by removing the existing mail profile via Control Panel > Mail > Show Profiles, deleting the stale OST cache file, and creating a fresh profile pointing to <EMAIL> so the client could establish a clean Exchange synchronization session.
4. Reset the affected mobile mail sync relationship for <HOSTNAME> by removing the existing mobile device partnership in Exchange Online admin center (Remove-MobileDevice) and instructing <PERSON> to re-establish the mailbox connection in Outlook Mobile after verifying device access prerequisites and Intune enrollment.
5. Confirmed the mobile device <HOSTNAME> needed to be compliant with Intune management policy for Exchange Online mail access; <PERSON> (<USER>) verified the device compliance state in the Intune portal and instructed remediation of a pending OS update compliance alert before retrying sync.
6. After profile and partnership remediation, verified that new messages appeared in Outlook desktop on <HOSTNAME> and <PERSON> on <HOSTNAME> within 10 minutes, and confirmed with <PERSON> (<EMAIL>) that the disconnected and stale-sync symptoms no longer occurred. Ticket closed by <PERSON>.

**Example 2**

1. Validated that Exchange Online had no tenant-wide throttling or service disruption affecting mailbox connectivity for caboratech.com, confirming OWA access for <USER>@caboratech.com was functional, thereby narrowing the issue to <PERSON>' devices and client configuration on <HOSTNAME> and his iPhone.
2. Reviewed the reported mobile symptom of 'Account requires attention' on the iPhone (IP <IP>) and directed remediation of the MDM device compliance state for employee <EMP_ID> so the mailbox was no longer blocked by the mobile client compliance condition.
3. Removed and re-added the <USER>@caboratech.com mailbox on the iPhone's Outlook Mobile app to refresh the sync partnership and force a new authenticated connection to Exchange Online, clearing the stale mobile sync state.
4. Rebuilt the Outlook desktop profile on <HOSTNAME> under the <USER> Windows account to replace the stale client configuration that was presenting intermittent 'Disconnected' status, allowing a fresh OST cache and autodiscover negotiation.
5. Reopened Outlook on <HOSTNAME> and confirmed the <USER>@caboratech.com mailbox reconnected and resumed normal folder synchronization on both desktop and mobile after profile recreation and mobile account refresh. <PERSON> confirmed emails were flowing on both devices as of 2026-02-19T16:05:00Z.

## Recommendation

Resolved by IT through remediation of the stale Outlook desktop profile and reset of the mobile sync partnership and device compliance state.

---

[← Back to categories](../../index.md)
