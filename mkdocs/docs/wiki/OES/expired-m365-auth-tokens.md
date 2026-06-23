---
hide:
  - navigation
root_cause_id: OES/expired-m365-auth-tokens
family: OES
ticket_count: 1
curated: true
self_serviceable: false
---

# Outlook sync failure due to expired Microsoft 365 authentication tokens

[← Back to categories](../../index.md)

## Description

Affected users experience inconsistent or failed email synchronization in Outlook Desktop on Windows. Outlook may display a "Disconnected" status or cycle between connected and disconnected states, and new messages stop arriving. Repeated sign-in prompts may appear, but completing them does not restore stable mailbox access.

The issue can also affect mobile email on managed devices. In reported cases, iPhone mail stopped updating around the same time as the desktop disruption, displaying a "sync failed" message. Despite the apparent similarity to a profile or device compliance problem, rebuilding the Outlook profile does not resolve the issue, and mobile device partnership health checks return normal results.

Because email access is disrupted on multiple platforms simultaneously, affected users may initially be uncertain which device or application is at fault. The interruption persists until the underlying authentication problem is addressed by IT support.

!!! note "Reported variations"

    - Mobile email on a managed iPhone may stop syncing with a "sync failed" message at the same time as the desktop disruption, even though mobile device partnership health appears normal.
    - Outlook Desktop may not fully disconnect but instead alternate between connected and disconnected states, making the issue appear intermittent rather than a complete outage.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** iOS 15.4 and Windows 10 (100%)
- **Device / platform:** mobile and desktop (100%)
- **Team:** global-sales (100%)
- **Region:** us-east-1 (100%)

## Root cause

Stored Microsoft 365 authentication tokens on the affected device become corrupted or expire in a way that prevents Outlook from successfully reauthenticating. This causes the application to fail repeatedly when trying to establish a valid mailbox session with Exchange Online, even though network connectivity and the user's mailbox are otherwise healthy. Because the token issue affects the account's authentication state rather than a single app profile, it can disrupt email access on both desktop and mobile platforms at the same time.

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

This issue is resolved by IT support; reference 'expired M365 authentication tokens' when reporting it.

---

[← Back to categories](../../index.md)
