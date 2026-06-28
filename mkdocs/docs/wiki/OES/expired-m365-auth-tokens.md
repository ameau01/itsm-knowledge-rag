---
hide:
  - navigation
root_cause_id: OES/expired-m365-auth-tokens
family: OES
ticket_count: 1
curated: true
self_serviceable: false
---

# Corrupted Microsoft 365 Authentication Tokens Blocking Outlook Sync

[← Back to categories](../../index.md)

## Description

Affected users experience inconsistent email synchronization in Outlook Desktop on Windows 10, where the mailbox does not fully disconnect but messages fail to update reliably. The issue typically follows repeated sign-in prompts and recent account changes. Outlook may display a "Disconnected" status intermittently, and messages stop arriving despite the client maintaining partial connectivity to Exchange Online.

The sync failure extends beyond the desktop client, also affecting mobile mail access on managed iOS devices. The mobile application reports a "sync failed" error message. In some cases, affected users are initially uncertain whether mobile mail is impacted until both platforms are individually confirmed as failing. Messages may stop arriving approximately two days before the issue is reported.

Diagnostic investigation reveals that the mailbox can reach Exchange Online and that mobile device partnership health appears normal. Rebuilding the Outlook profile does not resolve the issue, distinguishing it from a stale-profile scenario. The persistence of authentication prompts and sync failures across multiple platforms indicates an underlying account authentication token problem preventing Outlook from maintaining a valid mailbox session.

!!! note "Reported variations"

    - Outlook Desktop displayed a "Disconnected" status with intermittent connectivity rather than a complete and sustained connection loss.
    - The mobile mail client presented an explicit "sync failed" error message rather than silently failing to update.
    - Repeated authentication prompts preceded the sustained sync failure on the desktop client.
    - Profile rebuild on the desktop did not resolve the issue, distinguishing the behavior from a stale-profile scenario.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** iOS 15.4 and Windows 10 (100%)
- **Device / platform:** mobile and desktop (100%)
- **Team:** global-sales (100%)
- **Region:** us-east-1 (100%)

## Root cause

Corrupted or invalid stored Microsoft 365 authentication tokens caused Outlook to repeatedly fail reauthentication. This prevented stable mailbox synchronization despite a healthy profile and compliant mobile partnership. The issue affected both desktop and mobile platforms simultaneously.

## Diagnostics

Steps used to confirm this root cause:

1. Checked Outlook desktop connection state and mailbox sync behavior to confirm whether the client was actively connected to Exchange Online.  
   *Expected:* Outlook shows connected and mailbox folders update without sync delay.
2. Compared reported behavior against a profile-side issue and prioritized service/device access investigation because both desktop and mobile were impacted at the same time.  
   *Expected:* Clean profile syncs the mailbox without stale cache errors.
3. Reviewed Exchange Online mobile partnership status and the device compliance state for the user's mailbox and managed iOS device.  
   *Expected:* Active mobile partnerships are healthy and compliant.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

1. Cleared stored Office credentials and invalid authentication tokens from Windows Credential Manager on <HOSTNAME> for user <USER>, including cached entries for <EMAIL> in the Office sign-in cache under the user's Windows profile.
2. Forced a fresh Microsoft 365 sign-in for <EMAIL> and completed the required modern authentication and MFA prompt to re-establish the mailbox session on <HOSTNAME> from client IP <IP>.
3. Relaunched Outlook on <HOSTNAME> and verified send/receive completed without new authentication prompts and that current email and calendar items for <EMAIL> began syncing normally on both desktop and the user's managed iPhone. Confirmed with <PERSON> that mail flow was restored.

## Recommendation

Resolved by IT by clearing cached credentials from Windows Credential Manager and forcing a fresh Modern Authentication sign-in, restoring service on both desktop and mobile.

---

[← Back to categories](../../index.md)
