---
hide:
  - navigation
root_cause_id: OES/unresolved-endpoint-client-sync-state
family: OES
ticket_count: 7
curated: true
self_serviceable: false
---

# Outlook desktop and mobile sync failure due to endpoint client state corruption

[← Back to categories](../../index.md)

## Description

Affected users experience a simultaneous loss of email synchronization on both Outlook desktop (Windows 10) and Outlook mobile (iOS), while Exchange Online webmail (OWA) continues to display current messages normally. On the desktop, Outlook shows a "Disconnected" status in the status bar, and the inbox remains frozen at the last successful sync timestamp — often hours or days old. On mobile, new mail stops arriving entirely, and in some cases the Outlook mobile app displays an "Account requires attention" message.

The issue has been observed across multiple users and offices, particularly within the Sales and Field Ops groups. It is not associated with a Microsoft 365 service-wide outage or tenant-level throttling, and affected users can confirm that their mailbox is current by logging into OWA. Restarting Outlook or removing and re-adding the account on the mobile device does not resolve the problem on its own.

In some cases, the managed mobile device (typically an iPhone enrolled via MDM) appears as non-compliant in the Company Portal app or shows an unhealthy sync partnership in the MDM console. Desktop Outlook may show intermittent disconnection rather than a continuous outage, and Exchange Online server-side telemetry may reflect partial or intermittent sync success even while the user's clients remain stale. The issue can affect individual users or groups of users simultaneously, particularly following a tenant maintenance window.

!!! note "Reported variations"

    - In some cases, the mobile device is explicitly flagged as non-compliant in the MDM console or Company Portal app, while in others no compliance warning is visible to the user.
    - An outdated MDM legacy-block rule originally scoped for decommissioned iOS 12 endpoints was found matching current iOS 14 devices after a tenant maintenance window, causing sync failures for otherwise compliant mobile devices.
    - Some users experience intermittent rather than continuous disconnection on Outlook desktop, with Exchange Online telemetry showing partial sync success even though the client remains effectively stale.
    - The issue has occurred as an isolated single-user incident as well as a multi-user event affecting several accounts across multiple office locations simultaneously.

## Affected environment

Distribution across 7 reported cases:

- **Operating system:** Windows 10; iOS 15 (29%), Windows 10 (29%), Windows 10 and iOS 14 (14%)
- **Device / platform:** Desktop and Mobile (29%), Microsoft 365 / Exchange Online (14%), mixed (desktop and mobile) (14%)
- **Team:** Sales (71%), Sales and Field Ops (14%), Corporate Sales (14%)
- **Region:** us-east-1 (57%), NA (29%), unknown (14%)

## Root cause

The issue is caused by a combination of problems on the user's own devices rather than a failure of the Exchange Online mail service itself. On the desktop side, the local Outlook profile and cached mailbox data become stale or corrupted, preventing the client from maintaining a healthy connection to Exchange Online. On the mobile side, the device's sync partnership with Exchange Online becomes outdated or the device falls out of compliance with the organization's mobile device management (MDM) policy, which blocks the phone from synchronizing mail. In at least one instance, an outdated MDM policy rule originally intended for decommissioned older devices was incorrectly matching current devices after a maintenance window, contributing to the sync failure.

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

This issue is resolved by IT support; reference 'Outlook desktop and mobile endpoint sync failure' when reporting it.

---

[← Back to categories](../../index.md)
