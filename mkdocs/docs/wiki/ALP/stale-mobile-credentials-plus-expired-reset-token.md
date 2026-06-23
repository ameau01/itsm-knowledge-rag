---
hide:
  - navigation
root_cause_id: ALP/stale-mobile-credentials-plus-expired-reset-token
family: ALP
ticket_count: 33
curated: true
self_serviceable: false
---

# Mobile cached credentials and expired reset token combine to sustain AD lockout

[← Back to categories](../../index.md)

## Description

Affected users find themselves unable to sign in to the corporate SSO Portal after a recent password change or password reset attempt. The SSO Portal displays an "account locked" message, and authentication fails from both mobile devices and, in some cases, desktop workstations. The issue typically begins when a mobile device — most commonly a corporate iPhone running iOS mail, Outlook, or Teams — continues submitting the previous password in the background after the user has changed or reset their credentials.

At the same time, attempts to recover through the self-service Password Reset Portal are unsuccessful because the originally issued reset token has expired. The portal returns an "expired token" or equivalent error message, preventing the user from completing a clean password reset. Because the mobile device keeps retrying with stale cached credentials, the Active Directory account relocks shortly after any manual unlock, creating a cycle in which neither the new password nor the reset workflow restores access.

The result is a complete loss of access to SSO-connected applications — including email, collaboration tools, and line-of-business systems — until both the lockout source and the expired token state are addressed together. The issue affects individual accounts rather than broad groups of users, and it has been observed across multiple office locations and network paths, including corporate Wi-Fi and home networks. In some cases, users who have recently switched phones find that credentials restored from a backup or still present on an old device contribute to the repeated failures.

!!! note "Reported variations"

    - Users who recently switched phones may encounter the issue when credentials carried over from a device backup or still active on the old device continue submitting stale authentication attempts.
    - In some cases, desktop sign-in works normally with the new password while mobile access alone triggers the lockout cycle, causing the account to relock before the desktop session can be used effectively.
    - One instance involved a managed Android device rather than an iOS device, with the same pattern of cached credential replay and expired reset token.
    - The expired reset token error message may vary in wording across attempts, with some users seeing "token expired," others seeing a named-error code such as TOKEN_EXPIRED_0041, and others receiving a generic prompt to request a new reset link.

## Affected environment

Distribution across 33 reported cases:

- **Operating system:** iOS 15.6 (15%), iOS 16.4 (9%), iOS 15 (6%)
- **Device / platform:** mobile (39%), On-prem Active Directory with cloud SSO proxy (3%), Windows Server AD (on-prem) (3%)
- **Team:** Sales (42%), Engineering (9%), Corporate Users (9%)
- **Region:** us-east-1 (91%), us-west-2 (6%), NA-East (3%)

## Root cause

A mobile device retains the user's previous password in its cached credentials after a password change and continues automatically submitting failed sign-in attempts against Active Directory. These repeated failures trigger the Active Directory account lockout policy, locking the account. In parallel, the self-service password reset token that was issued earlier expires before the user can successfully complete the reset and before the updated password propagates to Active Directory and the SSO platform. The combination of the ongoing mobile lockout source and the invalid reset token prevents normal recovery until both issues are resolved together.

## Diagnostics

Steps used to confirm this root cause:

1. Review lockout logs to identify the device or service causing repeated failed authentication.  
   *Expected:* No active device or service continues to submit stale credentials.
2. Verify that the password reset token is current and accepted by the reset portal.  
   *Expected:* Reset token is valid and password change propagates to directory services.
3. Ask the user to disable saved credentials on mobile mail and collaboration clients.  
   *Expected:* Cached credentials no longer trigger new failed sign-in attempts.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Reviewed account lockout events (Event ID 4740) on DC-EAST-03.corplabs.internal for account CN=<USER>,OU=Sales,DC=corplabs,DC=internal and confirmed the repeated failed authentication source was the user's mobile device <HOSTNAME> (IP <IP>) using cached stale credentials in Outlook and iOS Mail.
2. Unlocked the Active Directory account for <USER> via the AD Admin Console on DC-EAST-03.corplabs.internal and reset the lockout counters (badPwdCount) to restore eligibility for authentication.
3. Guided <PERSON> through clearing saved credentials and active session tokens on device <HOSTNAME> — removed stored passwords from Outlook and iOS Mail — and instructed the user to reauthenticate with current credentials only.
4. Issued a new password reset token (RST-88455) through the Password Reset Portal to <EMAIL> and had the user complete the password reset within the 30-minute token window before expiry.
5. Verified successful sign-in by <USER> to the SSO Portal at https://sso.corplabs.com at 19:01 UTC after the reset, and monitored AD authentication logs on DC-EAST-03.corplabs.internal for an additional 30 minutes to confirm no further failed attempts and that the lockout condition did not recur.

**Example 2**

1. Reviewed Active Directory lockout events on DC-EAST-03.corplabs.internal to confirm the failed authentication source was the user's corporate mobile device (<HOSTNAME>, IP <IP>) rather than the desktop session on <HOSTNAME>.
2. Unlocked the user's account (<USER>) in Active Directory via the identity_team (<PERSON>) after confirming the lockout was caused by repeated stale credential submissions from the mobile device.
3. Issued a new password reset token (RST-88501) through the Password Reset Portal and verified that the token was active and accepted for account <EMAIL>.
4. Guided the user to remove saved credentials and clear cached sign-in data on the mobile device (<HOSTNAME>) before retrying SSO authentication at https://sso.corplabs.com.
5. Had the user re-authenticate on mobile with the updated password and confirmed successful SSO sign-in on <HOSTNAME> without new lockout events for account <USER>.
6. Monitored lockout counters on DC-EAST-03.corplabs.internal for 30 minutes to verify that no device or service continued submitting invalid credentials for <USER>; <PERSON> confirmed all clear at 01:25 UTC.

## Recommendation

This issue is resolved by IT support; reference 'mobile cached credentials with expired reset token lockout' when reporting it.

---

[← Back to categories](../../index.md)
