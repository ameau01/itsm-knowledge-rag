---
hide:
  - navigation
root_cause_id: ALP/expired-reset-token-primary
family: ALP
ticket_count: 1
curated: true
self_serviceable: false
---

# Account lockout after password reset due to expired reset token

[← Back to categories](../../index.md)

## Description

Affected users experience continued sign-in failures after completing a corporate password reset through the Password Reset Portal. Despite following the reset process, authentication to the SSO Portal and Microsoft 365 applications does not succeed, and the account may become locked again shortly after the reset attempt.

The issue typically manifests across multiple devices — for example, both a desktop and a mobile device — rather than being isolated to a single endpoint. Users report that the new password does not appear to be accepted consistently, even though the reset process itself seemed to complete. Account lockouts in Active Directory may recur in quick succession, preventing access to corporate resources.

Because the symptoms resemble those of a stale cached credential on a secondary device, initial investigation may explore that possibility. However, authentication logs in these cases do not show a persistent stale-credential source from mobile or other endpoints; the lockouts stem from the reset itself not having completed successfully.

!!! note "Reported variations"

    - Initial triage may suspect a stale cached credential on a mobile device (e.g., a saved password in a mail app or browser), but diagnostics confirm no continuing stale-credential source from any endpoint.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** iOS 15.6 (100%)
- **Device / platform:** mobile (100%)
- **Team:** Corp Users (100%)
- **Region:** us-east-1 (100%)

## Root cause

The password reset token used during the prior reset attempt had expired or was otherwise invalid, so the reset did not fully complete. As a result, the user's credentials were not properly updated in directory services, and subsequent sign-in attempts continued to fail and trigger account lockouts. Reissuing a valid reset token allowed the password change to propagate correctly and restored normal authentication.

## Diagnostics

Steps used to confirm this root cause:

1. Reviewed account lockout records and authentication evidence to determine whether a device was still sending failed sign-in attempts after the password reset.  
   *Expected:* No active device or service continues to submit stale credentials.
2. Verified the password reset token state and reissued a current token to ensure the reset portal accepted the change and propagated it correctly.  
   *Expected:* Reset token is valid and password change propagates to directory services.
3. Asked the user to remove saved credentials from mobile mail and browser applications by removing and re-adding the corporate account on the iPhone.  
   *Expected:* Cached credentials no longer trigger new failed sign-in attempts.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

1. Reissued a fresh password reset token for <EMAIL> (<EMP_ID>) and walked the user <PERSON> through a new password reset in the Password Reset Portal, confirming the token was accepted and the new password propagated to Active Directory on DC-EAST-03.corplabs.internal.
2. Unlocked the account <USER> (CN=<USER>,OU=Corp Users,DC=corplabs,DC=internal) after the failed sign-in attempts and confirmed directory services accepted the updated password by verifying authentication from IP <IP>.
3. Validated successful sign-in to SSO at https://sso.corplabs.com and Microsoft 365 from a test session on <HOSTNAME> and advised the user to update any saved credentials on <HOSTNAME> if prompted.

## Recommendation

This issue is resolved by IT support; reference 'expired reset token causing account lockout' when reporting it.

---

[← Back to categories](../../index.md)
