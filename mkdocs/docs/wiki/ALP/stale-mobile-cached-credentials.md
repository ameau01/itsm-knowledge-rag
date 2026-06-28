---
hide:
  - navigation
root_cause_id: ALP/stale-mobile-cached-credentials
family: ALP
ticket_count: 23
curated: true
self_serviceable: false
---

# Recurring AD Lockouts From Stale Cached Credentials on iOS Mobile Devices

[← Back to categories](../../index.md)

## Description

After completing a password reset through the corporate Password Reset Portal, affected users experience repeated Active Directory account lockouts. The new password functions correctly for desktop sign-in, but mobile devices — typically company iPhones running apps such as Outlook, Teams, Mail, and Safari — continue submitting the old cached credentials in the background. These stale authentication attempts rapidly exceed the AD lockout threshold, triggering Event ID 4740 lockout entries on the domain controller and re-locking the account within minutes of each unlock.

The issue creates a persistent lockout cycle: each time the account is unlocked, the mobile device resumes retrying with outdated credentials, exhausting the failed-attempt counter again. Domain controller logs confirm the repeated failures originate from the mobile device's IP address, with automated retries occurring as frequently as every 60 seconds. In some cases, 14 or more failed attempts were recorded within a 25-minute window from a single device. Users remain locked out of all SSO-protected corporate resources — including Exchange Online, Teams, and internal tools — until the stale credentials on the mobile device are cleared.

A secondary symptom compounds the problem: the lockout may block access to the Password Reset Portal itself, preventing self-service recovery. In some cases the reset token has also expired, leaving affected users unable to resolve the issue without direct service desk intervention. The lockout cycle has persisted for extended periods — in one case spanning over eleven hours across multiple unlock attempts — affecting users across multiple departments, office locations, and network environments.

!!! note "Reported variations"

    - Desktop sign-in succeeds normally after the password reset while only the mobile device triggers lockouts, giving the impression the reset was partially successful.
    - The lockout prevents access to both the SSO Portal and the Password Reset Portal simultaneously, leaving the user unable to self-remediate.
    - Multiple lockout-and-unlock cycles occur over an extended period (e.g., overnight) when the mobile device continues retrying cached credentials at regular sync intervals.
    - Saved passwords in the mobile browser (e.g., Safari) contribute to the lockout in addition to credentials stored in mail and collaboration apps.
    - A previously issued password reset token became expired or unusable due to the repeated lockouts, requiring a fresh token to be generated.
    - Some affected users were traveling or connecting from remote or home networks, indicating the issue is not tied to a specific network location.
    - Some tickets required escalation to Identity Tier 2 to validate reset propagation across directory services and clear the mobile credential source.
    - In at least one case the affected device was running an older mobile OS version, which may have contributed to credential caching behavior.

## Affected environment

Distribution across 23 reported cases:

- **Operating system:** iOS 15.6 (22%), iOS 15 (17%), iOS (13%)
- **Device / platform:** mobile (61%), Hybrid Azure AD / On-prem AD (9%), On-prem Active Directory with Azure AD Connect (4%)
- **Team:** Sales (48%), Engineering (13%), Finance (9%)
- **Region:** us-east-1 (96%), NA (4%)

## Root cause

Cached credentials on the affected user's iOS mobile device continued submitting the old password to Active Directory and SSO-connected services after the password reset. The repeated failed authentication attempts triggered the AD lockout policy before the new password could be used successfully, creating a recurring lockout cycle until the stale credentials were removed from the device.

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

1. Reviewed Active Directory lockout evidence on DC-EAST-03.corplabs.internal for account CN=<USER>,OU=Corp Users,DC=corplabs,DC=internal, verified Event ID 4740 with lockout status 0xC0000234 showing 14 failed attempts from IP <IP>, and unlocked <PERSON>'s AD account using the Active Directory Users and Computers console.
2. Issued a fresh password reset token to <EMAIL> and confirmed the user (<USER>, <EMP_ID>) successfully completed the password reset flow in the Password Reset Portal at 08:06 UTC with propagation verified across domain controllers.
3. Guided <PERSON> to remove and re-add the corporate account on her iPhone (<HOSTNAME>) and clear saved browser credentials in Safari so the old password would no longer be retried by iOS Mail or the browser against Active Directory.
4. Revoked stale SSO sessions and tokens associated with <USER>'s prior sign-in state on the SSO Portal at https://sso.corplabs.com to ensure all subsequent authentication used the new password exclusively.
5. Validated successful sign-in to the SSO Portal for <USER> at 08:14 UTC from IP <IP> after mobile credential cleanup and documented <HOSTNAME> as the lockout source in the incident record for follow-up monitoring by <PERSON> on the identity team.

**Example 2**

1. Reviewed account lockout activity for <USER> (<PERSON> <PERSON>, <EMP_ID>) on DC-EAST-03.corplabs.internal and confirmed repeated failed authentication attempts were originating from the user's mobile device (<HOSTNAME>, IP <IP>) after the password reset.
2. Unlocked the user's Active Directory account (CN=<USER>,OU=Corp Users,DC=corplabs,DC=internal) so access could be restored after the repeated lockout events triggered by the mobile device.
3. Issued a new password reset token via the Password Reset Portal and completed a fresh password reset to ensure the current credential was valid in directory-backed services including Active Directory and SSO Portal for <USER>.
4. Instructed the user to remove the corporate account from the mobile device (<HOSTNAME>), clear saved credentials in mobile mail and collaboration apps, and re-add the account using the new password. <PERSON> <PERSON> confirmed completion of these steps at 15:25 UTC.
5. Invalidated existing SSO sessions at https://sso.corplabs.com and revoked prior authentication tokens for <USER> to stop stale sessions from retrying with old credentials across all SSO-connected services.
6. Confirmed successful sign-in from both <HOSTNAME> and <HOSTNAME> after mobile reconfiguration and monitored for additional failed authentication attempts from IP <IP> to verify lockouts had stopped. No further incidents observed through end of business day.

## Recommendation

Resolved by IT after unlocking the Active Directory account and clearing stale cached credentials from the affected mobile device.

---

[← Back to categories](../../index.md)
