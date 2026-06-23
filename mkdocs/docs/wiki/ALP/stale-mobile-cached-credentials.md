---
hide:
  - navigation
root_cause_id: ALP/stale-mobile-cached-credentials
family: ALP
ticket_count: 23
curated: true
self_serviceable: false
---

# Post-reset account lockout caused by stale cached credentials on iOS mobile device

[← Back to categories](../../index.md)

## Description

Affected users complete a corporate password reset through the Password Reset Portal and may initially be able to sign in successfully from a desktop or laptop. However, within minutes of the password change, the Active Directory account becomes locked again, and the SSO Portal at https://sso.corplabs.com returns an "account locked" or "account locked due to too many failed sign-in attempts" message. Access to corporate resources — including email, Outlook, Teams, SharePoint, and other SSO-connected applications — is blocked across all devices once the lockout takes effect.

The lockout is tied to the affected user's company-issued or personal iPhone, which continues submitting the previous password in the background after the reset. Corporate mail, Outlook, Teams, and other collaboration apps configured on the iOS device retain the old saved credentials and repeatedly attempt to authenticate against Active Directory without user intervention. These failed attempts accumulate rapidly — often reaching the lockout threshold within minutes — and trigger the Active Directory lockout policy (Event ID 4740), re-locking the account each time it is unlocked.

In many cases, desktop or laptop sign-in works normally with the new password, confirming that the reset itself completed successfully. The lockout cycle recurs each time the account is unlocked because the mobile device continues retrying with stale credentials until those cached credentials are cleared from the device. Some affected users also encounter expired password reset tokens when attempting self-service recovery while the account is in a locked state, further delaying access restoration.

The issue has been reported across multiple offices and departments, affecting users connecting from both corporate Wi-Fi and remote networks. Authentication logs on the domain controller consistently trace the failed sign-in attempts back to the mobile device's IP address, with repeated failures logged at short intervals corresponding to app sync cycles such as Exchange ActiveSync.

!!! note "Reported variations"

    - In some cases, the affected user's self-service password reset token has expired by the time they attempt recovery, requiring a new token to be issued by IT support before the password can be updated.
    - Some users experience the lockout cycle recurring multiple times over several hours or across multiple days, with the account re-locking shortly after each unlock because the mobile credential source was not addressed during earlier remediation.
    - Occasionally, the stale device entry in the mobile device management system (Intune) must be disabled in addition to clearing cached credentials to fully stop the repeated authentication failures.
    - A small number of affected users report that both SSO Portal access and Password Reset Portal access are simultaneously blocked, as the account lockout prevents authentication to either service.

## Affected environment

Distribution across 23 reported cases:

- **Operating system:** iOS 15.6 (22%), iOS 15 (17%), iOS (13%)
- **Device / platform:** mobile (61%), Hybrid Azure AD / On-prem AD (9%), On-prem Active Directory with Azure AD Connect (4%)
- **Team:** Sales (48%), Engineering (13%), Finance (9%)
- **Region:** us-east-1 (96%), NA (4%)

## Root cause

After a corporate password reset, iOS mobile devices retain the previous password in cached credentials used by mail, Outlook, Teams, and other corporate apps. These apps continue attempting to authenticate against Active Directory using the old password in the background, generating repeated failed sign-in attempts that exceed the lockout threshold and trigger the Active Directory account lockout policy. The lockout recurs each time the account is unlocked until the outdated credentials stored on the mobile device are removed and the corporate accounts are reconfigured with the new password.

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

This issue is resolved by IT support; reference 'mobile cached credentials lockout after password reset' when reporting it.

---

[← Back to categories](../../index.md)
