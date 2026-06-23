---
hide:
  - navigation
root_cause_id: OES/stale-mobile-sync-partnership
family: OES
ticket_count: 9
curated: true
self_serviceable: false
---

# Stale Outlook Mobile Sync Partnership Blocking Exchange Online Email

[← Back to categories](../../index.md)

## Description

Affected users experience Outlook on their mobile device (iPhone or Android) entering a "Disconnected" state or displaying stale inbox content, with new messages no longer appearing on the device. The issue typically begins without a clear in-app error message, and standard self-service steps such as restarting the Outlook app, rebooting the device, or removing and re-adding the account may not restore sync. In most cases the mobile inbox appears frozen at a point in time — sometimes hours or a full day behind — while the user's other mail access points continue to work normally.

Desktop Outlook and Outlook on the web (OWA) remain fully functional for the same mailbox, which confirms that the Exchange Online mailbox itself is healthy and that the problem is isolated to the mobile client path. Colleagues on the same network and mail platform are typically unaffected, further narrowing the issue to the individual device rather than a broader service disruption.

The issue has been observed following iOS updates, Intune device compliance changes, and desktop Outlook profile rebuilds, though in some cases no specific triggering event is apparent. Affected users are generally on managed (Intune-enrolled) devices and rely on mobile Outlook for field or travel-based work, making the loss of mobile email access operationally disruptive.

!!! note "Reported variations"

    - Both mobile devices (iPhone and Android) may be affected simultaneously for users who access the same mailbox from multiple mobile clients, with each device requiring its own partnership reset.
    - The issue may follow a desktop Outlook profile rebuild, where the desktop client recovers but the mobile sync partnership remains stale and requires separate remediation.
    - An Intune compliance update or policy change may trigger the stale partnership condition, with the device returning to compliant status in Intune while Exchange Online continues to log mobile client disconnects.
    - Some users report the Outlook mobile app intermittently flipping between Connected and Disconnected states rather than remaining consistently disconnected.
    - In dual-client failure scenarios, the desktop Outlook client may also show a disconnected state with credential prompts, requiring a separate desktop profile rebuild alongside the mobile partnership reset.

## Affected environment

Distribution across 9 reported cases:

- **Operating system:** Android 11 (22%), iOS 17.3 (11%), Windows 10 (desktop), Android 12 (mobile) (11%)
- **Device / platform:** mobile (67%), desktop and mobile (11%), Exchange Online / Outlook Mobile (11%)
- **Team:** Sales (56%), sales_team (11%), Field Sales (11%)
- **Region:** us-east-1 (56%), EMEA (22%), unknown (22%)

## Root cause

The mobile device's sync relationship (ActiveSync partnership) with Exchange Online becomes stale or invalid, preventing the Outlook mobile app from maintaining a healthy connection to the mailbox. This can occur after an iOS or Android update, a device compliance state change in Intune, or a desktop Outlook profile rebuild that does not automatically refresh the mobile-side partnership. In some cases a minor device compliance status drift also needs to be refreshed before the mobile sync session can fully recover.

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

This issue is resolved by IT support; reference 'stale mobile sync partnership' when reporting it.

---

[← Back to categories](../../index.md)
