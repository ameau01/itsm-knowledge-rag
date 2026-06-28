---
hide:
  - navigation
root_cause_id: ALP/expired-reset-token-primary
family: ALP
ticket_count: 1
curated: true
self_serviceable: false
---

# Incomplete Password Reset Due to Expired Reset Token

[← Back to categories](../../index.md)

## Description

Affected users experience persistent sign-in failures across the SSO portal and Microsoft 365 applications after completing a corporate password reset through the Password Reset Portal. Despite the reset appearing to finish successfully, the new password is not accepted consistently, and the affected user's Active Directory account becomes locked again shortly afterward.

The issue manifests across multiple devices, such as desktops and mobile devices, rather than being isolated to a single endpoint. Although initial investigation may consider stale cached credentials on mobile devices or other endpoints as a potential locking source, diagnostics rule these out as the cause of the continued lockouts.

The confirmed root cause is an invalid or incomplete prior reset state. Reissuing a valid reset token resolves the issue, restoring normal password propagation and sign-in behavior across all affected services and devices.

!!! note "Reported variations"

    - The affected user's Active Directory account is observed as locked on a specific domain controller shortly after the reset attempt.
    - The affected user has saved or cached credentials on a mobile device, but these are ruled out as the source of the continued lockouts.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** iOS 15.6 (100%)
- **Device / platform:** mobile (100%)
- **Team:** Corp Users (100%)
- **Region:** us-east-1 (100%)

## Root cause

The previous password reset did not complete successfully because the reset token had expired or was no longer valid. This left the affected user attempting authentication with credentials that were not fully updated in directory services.

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

Resolved by IT after reissuing a valid password reset token to complete credential propagation across directory services.

---

[← Back to categories](../../index.md)
