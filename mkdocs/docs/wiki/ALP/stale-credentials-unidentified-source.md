---
hide:
  - navigation
root_cause_id: ALP/stale-credentials-unidentified-source
family: ALP
ticket_count: 2
curated: true
self_serviceable: false
---

# Recurring account lockouts from unidentified stale credential source after password reset

[← Back to categories](../../index.md)

## Description

After completing a corporate password reset through the Password Reset Portal, affected users experience repeated Active Directory account lockouts that begin almost immediately. Desktop sign-in and SSO Portal access may work briefly after each unlock, but the account locks again within minutes — often on a regular interval of roughly every three to fifteen minutes — blocking access to corporate applications including the SSO Portal, Outlook, and OWA mailbox services.

Initial investigation typically points toward mobile devices (such as an iPhone running cached credentials in Mail or Teams apps) because failed authentication attempts may correlate with a mobile IP address. However, the lockouts persist even after the user removes and re-adds the corporate account on the mobile device, indicating that the phone is not the sole or actual source of the problem.

The account remains unstable despite a successful password change and correct replication across Active Directory domain controllers. Users may see repeated "account locked" or "invalid password" errors across multiple services and are effectively unable to maintain access to any corporate application until the underlying lockout source is identified and remediated.

!!! note "Reported variations"

    - Mobile cached credentials may initially appear to be the lockout source based on IP correlation, but lockouts continue after the user fully removes and re-adds the corporate account on the mobile device.
    - The caller computer name in Active Directory lockout events may be intermittently blank, preventing definitive attribution of the lockout source to any single endpoint or application.
    - In some cases, the lockout source logs point to a non-interactive caller rather than a mobile user-agent such as ActiveSync, suggesting a background service or legacy application is responsible.

## Affected environment

Distribution across 2 reported cases:

- **Operating system:** iOS 15.6 (50%), iOS 15 (50%)
- **Device / platform:** mobile (100%)
- **Team:** Sales (100%)
- **Region:** us-east-1 (100%)

## Root cause

A non-mobile service, legacy client, or integrated application continues to authenticate using the old stored credentials after a password reset, repeatedly triggering Active Directory lockouts. The exact source of the stale credentials cannot be definitively identified from the available authentication logs because the caller computer name field in the lockout events is intermittently blank or points to a non-interactive process rather than a recognizable device. This requires broader investigation and service-side remediation beyond a standard password reset and mobile credential cleanup.

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

This issue is resolved by IT support; reference 'recurring account lockout from unidentified stale credential source' when reporting it.

---

[← Back to categories](../../index.md)
