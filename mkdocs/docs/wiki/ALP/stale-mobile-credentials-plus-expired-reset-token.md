---
hide:
  - navigation
root_cause_id: ALP/stale-mobile-credentials-plus-expired-reset-token
family: ALP
ticket_count: 33
curated: true
self_serviceable: false
---

# Mobile Cached Credentials Trigger AD Lockout With Expired Reset Token

[← Back to categories](../../index.md)

## Description

Affected users experience Active Directory account lockouts triggered by mobile devices—primarily corporate iPhones, though managed Android devices are also represented—that continue submitting stale cached credentials after a password change or reset. Mail and collaboration apps such as Outlook, Teams, native iOS Mail, and Microsoft Authenticator retry authentication in the background using outdated saved passwords, rapidly exceeding the lockout threshold. Domain controller security logs (Event ID 4740/4625) show clusters of failed attempts originating from the mobile device's IP address, in some cases over fourteen failures within a short window.

Compounding the lockout, the self-service password reset token issued by the Password Reset Portal expires before the user can complete the credential update. Token validity windows vary across environments, with observed time-to-live values ranging from fifteen minutes to several hours; in one case the token sat unused for over twenty-four hours. Users who return to the reset link encounter an expired-token error, leaving them without a viable self-service recovery path while the account remains locked and the mobile device continues generating failed attempts.

Even when the Password Reset Portal reports a successful reset, the account may relock almost immediately because the mobile device keeps submitting old credentials before the new password propagates across domain controllers. This self-reinforcing cycle of stale-credential submission, account lockout, and unusable reset token blocks access to all SSO-connected resources—including email, collaboration tools, CRM, and identity platforms—from both mobile and desktop clients. Affected users consistently report urgent business impact, citing time-sensitive deliverables or client commitments. Resolution requires administrative intervention to unlock the account, issue a fresh reset token, and confirm that cached credentials on the mobile device are cleared.

!!! note "Reported variations"

    - Desktop authentication succeeds with the new password while mobile authentication fails, with the lockout triggered exclusively by the mobile device
    - Multiple mobile apps on the same device (e.g., Outlook, native iOS Mail, Teams, Microsoft Authenticator) each independently retry with stale credentials, accelerating the lockout
    - The lockout recurs immediately after an initial account unlock because cached mobile credentials have not yet been cleared on the device
    - A previous device continues submitting stale credentials after the user migrates to a new phone, with old device profiles or backup-restored credentials driving the failures
    - Domain controller replication lag contributes to post-reset SSO failures, with updated credentials not propagating consistently across all domain controllers
    - In at least one case the lockout preceded any password reset attempt; initial sign-in failures on the mobile device triggered the AD lockout policy before self-service recovery was initiated
    - Token time-to-live values varied across environments, with observed windows ranging from fifteen minutes to four or more hours
    - In one case the user removed and re-added the corporate account on the mobile device prior to contacting support, but the reset portal still reported the token as expired and SSO continued rejecting sign-in attempts

## Affected environment

Distribution across 33 reported cases:

- **Operating system:** iOS 15.6 (15%), iOS 16.4 (9%), iOS 15 (6%)
- **Device / platform:** mobile (39%), On-prem Active Directory with cloud SSO proxy (3%), Windows Server AD (on-prem) (3%)
- **Team:** Sales (42%), Engineering (9%), Corporate Users (9%)
- **Region:** us-east-1 (91%), us-west-2 (6%), NA-East (3%)

## Root cause

The Active Directory lockout policy was triggered by repeated failed authentication attempts from a mobile device that continued submitting stale cached credentials after a password change or reset. Simultaneously, the self-service password reset token expired before the credential update could be completed and propagated, preventing the user from resolving the lockout through self-service recovery.

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

Resolved by IT after unlocking the Active Directory account, issuing a new password reset token, and clearing stale cached credentials from the mobile device.

---

[← Back to categories](../../index.md)
