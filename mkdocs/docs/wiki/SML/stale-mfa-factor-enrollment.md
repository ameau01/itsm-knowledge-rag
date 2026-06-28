---
hide:
  - navigation
root_cause_id: SML/stale-mfa-factor-enrollment
family: SML
ticket_count: 20
curated: true
self_serviceable: false
---

# Stale Okta MFA Enrollment Records Cause SSO Challenge Loop

[← Back to categories](../../index.md)

## Description

Affected users attempting to sign in to the corporate Okta-backed SSO portal are unable to complete authentication. After entering primary credentials and approving the MFA challenge (via Okta Verify push or TOTP), the browser immediately returns to the MFA prompt rather than granting a session. This loop prevents access to downstream SaaS applications such as Salesforce, Workday, Confluence, Office 365, Google Workspace, and Slack. In some cases an explicit "Authentication failed" or AUTH-401 error appears between iterations; in others the prompt silently reappears with no error displayed. The behavior persists across multiple browsers, incognito sessions, alternate devices, and after client-side steps such as clearing cache or reinstalling the authenticator app.

The issue affects individual accounts and groups of up to approximately 14 users simultaneously, spanning multiple office locations, departments, and both internal employees and recently onboarded contractor accounts. Some affected users report that certain federated applications (e.g., ServiceNow) remain accessible while others are blocked, giving the appearance of an application-specific problem.

Okta system logs for impacted accounts consistently show successful primary authentication followed by repeated factor challenge events, token validation failures (AUTH-401, ERR_MFA_ENROLL_STALE, invalid_token, access_denied, invalid_grant), factor-mismatch errors, and rejected SAML assertions. Investigation confirms that enrolled MFA factor identifiers no longer match the users' current authenticator state, with access policy memberships and application assignments verified as correct in each case.

!!! note "Reported variations"

    - In one incident, approximately 14 Sales group accounts were affected simultaneously following a scheduled MFA factor migration from legacy TOTP to Okta Verify push.
    - Some accounts contained duplicate TOTP factor enrollments (one stale, one current), with the stale entry triggering factor-mismatch events on each authentication attempt.
    - In one case, the affected user's phone clock was not set to automatic; correcting this alone did not resolve the loop.
    - A mobile device OS update initially suggested an authenticator or clock-drift issue but was ultimately traced to stale factor enrollment.
    - Certain federated applications such as ServiceNow remained accessible while others were blocked, giving the appearance of an application-specific problem.
    - Contractor accounts exhibited intermittent behavior, with at least one user able to complete sign-in on one occasion but failing on subsequent attempts.
    - The issue affected users whose Okta Verify factor enrollment predated a recent Azure AD group migration, suggesting the migration contributed to enrollment staleness.
    - Prior self-service remediation attempts by users — including cache cleanup and re-adding the authenticator — did not resolve the loop, consistent with a server-side enrollment problem.

## Affected environment

Distribution across 20 reported cases:

- **Operating system:** Windows 10 (40%), Windows 11 (5%), Windows 10 (user reported) and iOS (mobile attempts) (5%)
- **Device / platform:** web (30%), Web - Chrome (15%), cloud (10%)
- **Team:** Sales (25%), Engineering (15%), AllEmployees (10%)
- **Region:** us-east-1 (80%), us-west-2 (10%), unknown (5%)

## Root cause

Stale or mismatched MFA factor enrollment records within the Okta tenant caused device and credential bindings to fall out of sync with affected users' current authenticator state. The condition has been observed following organizational MFA migrations (e.g., legacy TOTP to Okta Verify push), mobile device changes, authenticator app reinstallations, and directory synchronization events such as Azure AD Connect syncs or group migrations. In each scenario, the factor enrollment retained by Okta no longer matched the active authenticator instance, causing the identity provider to reject verification and re-issue the MFA challenge in a continuous loop.

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

Affected users and their managers typically open tickets describing an inability to complete SSO login due to a repeating MFA prompt, often referencing a stale MFA enrollment prompt loop or endless MFA challenge after sign-in.

---

[← Back to categories](../../index.md)
