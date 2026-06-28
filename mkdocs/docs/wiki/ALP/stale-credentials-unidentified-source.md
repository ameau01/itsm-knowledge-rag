---
hide:
  - navigation
root_cause_id: ALP/stale-credentials-unidentified-source
family: ALP
ticket_count: 2
curated: true
self_serviceable: false
---

# Recurring AD Lockouts from Unidentified Stale Credential Source Post-Reset

[← Back to categories](../../index.md)

## Description

Affected users experience repeated Active Directory account lockouts shortly after completing a corporate password reset through the Password Reset Portal. Despite the password change propagating successfully to domain controllers, the account continues to lock at regular intervals — typically every few minutes to every fifteen minutes. Users encounter "account locked" or "invalid password" errors and are unable to access corporate applications including the SSO Portal, Outlook, and OWA mailbox services.

The lockouts persist even when the user's desktop authentication is functioning normally. The recurring lock events are attributed to stale credentials cached on a device or service that continues to authenticate with the old password in the background. However, the exact source of the failed authentication attempts cannot be definitively identified from available logs; the caller computer name field in lockout event entries is sometimes blank or points to a non-interactive caller rather than a clearly identifiable endpoint.

Mobile devices with cached credentials are a common suspected source, but in some cases lockouts continue after the user has removed and re-added corporate accounts on the device, indicating an unidentified background service or legacy application as the true cause.

!!! note "Reported variations"

    - Lockout events correlate with a known mobile device IP address and cease to recur after account unlock and fresh token issuance, with the mobile device remaining the most likely — but unconfirmed — source.
    - Lockouts persist at the same interval even after the user removes and re-adds the corporate account on the suspected mobile device, indicating a separate background service or integrated application authenticating with stale credentials.
    - The caller computer name field in Event ID 4740 lockout logs appears intermittently blank, preventing definitive identification of the offending endpoint.
    - Lockout source logged on the domain controller points to a non-interactive caller ID rather than an ActiveSync or mobile user-agent, requiring escalation to the identity or messaging team for service-side remediation.

## Affected environment

Distribution across 2 reported cases:

- **Operating system:** iOS 15.6 (50%), iOS 15 (50%)
- **Device / platform:** mobile (100%)
- **Team:** Sales (100%)
- **Region:** us-east-1 (100%)

## Root cause

A non-mobile service, legacy client, or integrated application continued using outdated stored credentials after the user's password reset, repeatedly triggering Active Directory lockouts. Insufficient authentication telemetry — such as blank or ambiguous caller computer name fields in lockout logs — prevented definitive identification of the offending source.

## Diagnostics

Steps used to confirm this root cause:

1. Reviewed lockout and failed authentication logs to identify which device was continuing to submit invalid credentials after the password reset.  
   *Expected:* No active device or service continues to submit stale credentials.
2. Verified the replacement password reset token was current and that the updated password was accepted by directory-backed sign-in services.  
   *Expected:* Reset token is valid and password change propagates to directory services.
3. Asked the user to remove saved credentials and reconfigure the account on mobile mail and collaboration clients to eliminate stale password retries.  
   *Expected:* Cached credentials no longer trigger new failed sign-in attempts.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Issued a fresh password reset token via the Password Reset Portal for <USER> (<EMP_ID>), confirmed <PERSON> could sign in successfully on desktop at https://sso.corplabs.com, and unlocked the Active Directory account on DC-EAST-03.corplabs.internal.
2. Instructed <PERSON> to remove saved corporate credentials (<EMAIL>) from the iPhone and any mail, Teams, or browser applications retaining cached passwords, then re-add the account with the new password. Provided step-by-step guidance for iOS 15.6 account removal.
3. Placed the incident in monitoring/follow-up status with a 48-hour observation window and escalated to <PERSON> on the identity_team for additional authentication log review on DC-EAST-03.corplabs.internal if lockouts recur without a clearly identified source. Contact phone for <PERSON>: <PHONE>.

**Example 2**

1. Unlocked the AD account for <USER> (CN=<USER>,OU=Sales,DC=corplabs,DC=internal) via Active Directory Users and Computers and confirmed the newly reset password worked in direct sign-in testing at https://sso.corplabs.com and OWA.
2. Documented that mobile credential cleanup on <HOSTNAME> (<IP>) did not resolve the issue and correlated lockout timing on DC-EAST-03.corplabs.internal to a non-interactive authentication source submitting stale credentials for <USER> every ~3 minutes.
3. Escalated to the messaging/application and identity team (ticket ref INC-ALP-V0006-ESC) to identify and update the stored credential in the connected service authenticating as <USER>, then verify lockouts cease after the service-side fix. Notified <PERSON> (<EMAIL>, ext. <PHONE>) that the immediate access issue is resolved and the root-cause service will be remediated by the escalation team.

## Recommendation

Resolved by IT through account unlock and coordination with identity or messaging teams to isolate and remediate the stale credential source; reference "recurring AD lockout – unidentified stale credential source post-reset."

---

[← Back to categories](../../index.md)
