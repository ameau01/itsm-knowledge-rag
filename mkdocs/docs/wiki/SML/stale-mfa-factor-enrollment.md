---
hide:
  - navigation
root_cause_id: SML/stale-mfa-factor-enrollment
family: SML
ticket_count: 20
curated: true
self_serviceable: false
---

# MFA prompt loop caused by stale Okta factor enrollment records

[← Back to categories](../../index.md)

## Description

Affected users are unable to complete sign-in through the corporate SSO Portal. After entering primary credentials successfully, the authentication flow advances to the multi-factor authentication (MFA) step, but once the user approves the push notification or enters a verification code, the session returns to the MFA challenge again instead of granting access. This loop repeats indefinitely, and no successful session is established regardless of how many times the factor is approved.

The issue blocks access to all downstream applications delivered through the SSO Portal, including Salesforce, Workday, Confluence, Office 365, Google Workspace, and other federated services. It is not limited to a single application — affected users encounter the same loop across every app launched from the portal. In some cases, the browser displays an "Authentication failed" or similar message before cycling back to the MFA prompt; in other cases, no explicit error is shown.

The MFA loop persists across browsers (Chrome, Edge, Firefox), across incognito and private browsing sessions, and across entirely separate devices such as a personal computer or mobile phone browser. Clearing browser cache and cookies, reinstalling the authenticator app, and rebooting the workstation do not resolve the behavior. This cross-device, cross-browser persistence distinguishes the issue from a local browser or endpoint problem.

Reports have involved both individual users and groups of users across multiple offices and departments, including Sales, Engineering, Marketing, and contractor populations. The onset has been linked to events such as MFA migrations, directory synchronizations, authenticator app reinstalls, phone replacements, or device changes — any event that can leave the identity provider's factor enrollment records out of alignment with the user's current authenticator state.

!!! note "Reported variations"

    - Some affected users see explicit authentication failure messages (e.g., "Authentication failed" or HTTP 401/403 responses) between MFA loop cycles, while others see no error at all and are silently returned to the challenge screen.
    - In multi-user incidents following a migration or directory sync, a subset of users in the same group may retain access to certain applications (e.g., ServiceNow) while being blocked from others delivered through the SSO Portal.
    - Contractor or externally onboarded accounts may experience the loop intermittently rather than consistently, with occasional successful sign-ins interspersed among failures.
    - In some cases, duplicate factor enrollment records (e.g., two TOTP entries from different dates) are present on the account, producing explicit factor-mismatch events in authentication logs.
    - Clock drift on the authenticator device may compound the issue when stale TOTP-based enrollments are involved, though correcting the device clock alone does not resolve the loop.

## Affected environment

Distribution across 20 reported cases:

- **Operating system:** Windows 10 (40%), Windows 11 (5%), Windows 10 (user reported) and iOS (mobile attempts) (5%)
- **Device / platform:** web (30%), Web - Chrome (15%), cloud (10%)
- **Team:** Sales (25%), Engineering (15%), AllEmployees (10%)
- **Region:** us-east-1 (80%), us-west-2 (10%), unknown (5%)

## Root cause

The identity provider (Okta or Azure AD) retains outdated, duplicate, or mismatched MFA factor enrollment records for the affected user accounts. These stale records cause the system to challenge against a factor state that no longer matches the user's current authenticator registration, so each MFA verification attempt fails to satisfy the session requirement and triggers a new challenge. The condition typically arises after events such as an MFA migration, a directory synchronization, a device change, or an authenticator app reinstall that leaves old enrollment data in place without a clean re-registration.

## Diagnostics

Steps used to confirm this root cause:

1. Reproduced the affected user login flow through the SSO Portal and observed behavior after MFA approval.  
   *Expected:* User completes MFA once and reaches the application landing page.
2. Reviewed Okta MFA enrollment state and active factor registration for impacted users and compared with authenticator status.  
   *Expected:* User has an active factor with no stale or disabled enrollment.
3. Compared impacted users' Sales group membership with Azure AD to Okta assignment and application access policy scope.  
   *Expected:* User belongs to the expected access group and policy scope.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Reviewed the Okta authentication activity for user <USER> (employee ID <EMP_ID>) and confirmed repeated MFA challenge success events followed by HTTP 403 token exchange failures, consistent with an enrollment mismatch between the stale factor record and the user's current authenticator device.
2. Reset the MFA enrollment for <USER> in the Okta admin console to remove the stale Okta Verify factor registration tied to the prior device state (originally enrolled 2025-11-18).
3. Guided <PERSON> through enrolling the Microsoft Authenticator app again via the Okta self-service portal and verified a fresh MFA registration was successfully completed and linked to the current device.
4. Retested login through the SSO Portal from <HOSTNAME> (IP <IP>) and confirmed the user passed MFA once via push approval and received a valid session token without looping back to the challenge screen.
5. Validated access to required SaaS applications (Salesforce, ServiceNow) after sign-in and documented the MFA reset and successful re-enrollment in identity support notes under INC-SML-0011. Advised <PERSON> to contact the service desk if any further authentication issues arise after future device changes.

**Example 2**

1. Identified 14 affected Sales users in Okta sign-on logs showing repeated MFA challenges without successful factor completion, including <USER>, <USER>, and <USER> as initial confirmed cases from the <LOCATION> office.
2. Reset MFA enrollment for all 14 impacted accounts via the Okta Admin Console (Users > Multifactor > Reset Factors) so stale device bindings and outdated authenticator registrations from the March 28 TOTP migration were removed.
3. Had affected users re-enroll their Okta Verify authenticator app and complete a fresh device binding in Okta. Coordinated with Sales team lead <PERSON> to schedule re-enrollment in small batches to minimize disruption during business hours.
4. Cleared active Okta sessions for all 14 impacted users (Admin > People > Clear User Sessions) to force a clean authentication flow with the new MFA enrollment state, ensuring no cached stale tokens persisted.
5. Validated Azure AD group mapping (Sales-SSO-Access) and application assignment for Salesforce and Workday, then confirmed successful login and app access for <USER> (<IP>), <USER> (<HOSTNAME>), and <USER> (<IP>) after re-enrollment.
6. Monitored Okta sign-on activity for 24 hours (2026-04-01T00:00Z through 2026-04-02T00:00Z) to verify the MFA loop did not recur for any of the 14 re-enrolled users. No further authentication failures were observed, and ticket was closed by agent <PERSON> (<USER>).

## Recommendation

This issue is resolved by IT support; reference "stale MFA factor enrollment" when reporting it.

---

[← Back to categories](../../index.md)
