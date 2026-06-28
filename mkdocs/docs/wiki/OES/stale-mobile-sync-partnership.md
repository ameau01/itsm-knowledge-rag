---
hide:
  - navigation
root_cause_id: OES/stale-mobile-sync-partnership
family: OES
ticket_count: 9
curated: true
self_serviceable: false
---

# Stale Mobile Sync Partnership Blocks Outlook Mobile Email

[← Back to categories](../../index.md)

## Description

Affected users experience a failure of Outlook mobile to synchronize their Exchange Online mailbox on managed iOS or Android devices. The Outlook mobile app displays a persistent or intermittent "Disconnected" status, and new messages stop appearing on the device. The mobile inbox appears frozen, showing only older messages, with the last-synced timestamp falling progressively behind. Restarting the app, force-closing it, or rebooting the device does not restore synchronization, and typically no explicit error code is presented to the user.

The issue is isolated to the mobile sync path. Other clients — desktop Outlook, Outlook on the web — continue to function normally for the same mailbox. Exchange Online service health dashboards show no active incidents, no mailbox throttling is present, and Intune device compliance checks return a compliant status with no pending policy violations. The combination of healthy webmail access, normal desktop connectivity, and compliant device status narrows the fault to the mobile sync relationship between the Outlook mobile app and Exchange Online.

Diagnostic evidence in these cases includes stale last-sync timestamps on the Exchange Online mobile device partnership entries, HTTP 401 authentication errors in sync logs, and repeated failed sync sessions — all occurring despite the device reporting as compliant in Intune. In several cases the condition appears to have been triggered by a device-level change such as an iOS update, an Intune compliance policy transition, or a preceding desktop Outlook profile rebuild, after which the existing mobile partnership fails to re-establish properly.

!!! note "Reported variations"

    - In one case, both the desktop Outlook client and the mobile client were affected simultaneously, with the desktop showing a disconnected state, repeated credential prompts, and send/receive failures due to an outdated cached profile alongside the stale mobile partnership.
    - Some users reported the issue began immediately after accepting an Intune device compliance update, suggesting the compliance transition disrupted the existing mobile sync partnership.
    - In at least one instance, the onset coincided with a major iOS version update, after which the mobile inbox ceased receiving new messages.
    - Exchange Online sync logs in one case showed repeated HTTP 401 authentication errors tied to the stale mobile partnership.
    - A minor Intune compliance refresh was required on one device alongside the partnership rebuild, though no active conditional access block was in effect.
    - A prior desktop Outlook profile rebuild was identified as a preceding event in one case, after which desktop sync recovered but mobile devices did not.
    - In one case, a user's self-service account removal and re-add on the mobile client did not resolve the issue; server-side ActiveSync partnership clearance and profile rebuild were required. In a separate case, removing and re-adding the account on the mobile client alone resolved the issue without documented server-side partnership removal.
    - One incident involved both an iOS and an Android device simultaneously stuck in a disconnected state for the same mailbox, with both mobile partnership entries showing stale last-sync timestamps.

## Affected environment

Distribution across 9 reported cases:

- **Operating system:** Android 11 (22%), iOS 17.3 (11%), Windows 10 (desktop), Android 12 (mobile) (11%)
- **Device / platform:** mobile (67%), desktop and mobile (11%), Exchange Online / Outlook Mobile (11%)
- **Team:** Sales (56%), sales_team (11%), Field Sales (11%)
- **Region:** us-east-1 (56%), EMEA (22%), unknown (22%)

## Root cause

A stale Outlook mobile profile or invalid Exchange Online ActiveSync device partnership prevents the mobile client from maintaining a healthy sync session. The condition affects both iOS and Android platforms and is isolated to the mobile sync path rather than indicating a mailbox-wide Exchange Online outage. In observed cases the staleness was triggered by events such as an iOS update, an Intune compliance policy change, or a desktop profile rebuild, after which the existing mobile partnership failed to re-negotiate authentication successfully.

## Diagnostics

Steps used to confirm this root cause:

1. Checked whether the mailbox issue was client-specific by comparing Outlook for iOS behavior with desktop Outlook connectivity and folder updates.  
   *Expected:* Outlook shows connected and mailbox folders update without sync delay.
2. Assessed whether the mobile Outlook profile required rebuild by reviewing prior restart attempts and the lack of recovery after app and device restart.  
   *Expected:* Clean profile syncs the mailbox without stale cache errors.
3. Review mobile sync partnerships and device compliance state for the mailbox.  
   *Expected:* Active mobile partnerships are healthy and compliant.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Validated that the Outlook desktop client on <HOSTNAME> (IP <IP>) was in a disconnected state and confirmed the mailbox for <EMAIL> was not updating normally against Exchange Online.
2. Rebuilt the affected desktop Outlook profile on <HOSTNAME> to remove stale cached configuration (expired autodiscover and OAuth token data) and forced a fresh account reauthentication for <EMAIL>. This was performed by <PERSON> from desktop support.
3. Cleared the stale mobile ActiveSync partnership for <EMAIL> via the Exchange admin center, removed and re-added the mailbox in Outlook mobile on <PERSON>'s Android device, and completed sign-in again with current credentials.
4. Checked the device compliance state in Intune to ensure the managed mobile device enrolled under <EMAIL> was not being blocked by conditional access policy during mailbox access. Compliance status confirmed as passing.
5. Verified that mailbox sync resumed on both desktop (<HOSTNAME>) and mobile clients for <PERSON> and that new mail flow and send/receive completed successfully. User confirmed receipt of test email sent by agent at 20:18 UTC.

**Example 2**

1. Confirmed the device (<HOSTNAME>, registered to <PERSON>, <EMP_ID>) had returned to a compliant state in Intune and triggered a device policy sync so conditional access requirements were fully reapplied.
2. Reviewed the mailbox mobile partnership for <EMAIL> in Exchange Online and cleared the stale mobile sync partnership associated with the affected device (<HOSTNAME>) that had been disconnecting from IP <IP>.
3. Removed the existing Outlook mobile profile from <PERSON>'s device (<HOSTNAME>) and re-added the <EMAIL> account to create a clean mobile profile with fresh sync state.
4. Validated that Outlook mobile on <HOSTNAME> changed from Disconnected to a normal connected state and that mailbox folders for <EMAIL> began receiving current mail again within one minute of the profile rebuild.
5. Advised <PERSON> to monitor sync behavior after the rebuild and confirmed mail was available in mobile Outlook as well as OWA; also notified <PERSON> (<USER>) of the resolution for MDM tracking purposes.

## Recommendation

Resolved by IT clearing the stale Exchange Online mobile device partnership and rebuilding the Outlook mobile profile, after which synchronization resumed and current mail began flowing to the device.

---

[← Back to categories](../../index.md)
