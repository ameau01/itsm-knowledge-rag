---
hide:
  - navigation
root_cause_id: SML/combined-stale-enrollment-and-policy-desync
family: SML
ticket_count: 15
curated: true
self_serviceable: false
---

# MFA prompt loop from combined stale enrollment and conditional access policy desync

[← Back to categories](../../index.md)

## Description

Affected users attempting to sign in to SaaS applications — such as Salesforce, Confluence, Office 365, Concur, and others — through the corporate SSO portal are repeatedly returned to the MFA challenge screen after successfully completing primary authentication and approving the MFA prompt (typically via Okta Verify push). Instead of reaching the target application, the sign-in flow cycles back to another MFA challenge or displays an authentication rejection message such as "Sign-in rejected," "Login rejected," or "401 MFA required." The loop persists regardless of browser, device, or network, and clearing cookies or switching browsers does not resolve it.

The issue has been observed across multiple departments and groups, including Sales, Engineering, Finance, Marketing, and external contractor populations. It typically emerges shortly after a scheduled identity configuration change, group synchronization, or conditional access policy update — often within hours of the change window. Affected users may number from a handful to over a hundred, depending on the scope of the group or policy involved.

Okta authentication logs for affected accounts show repeated MFA challenge events with no successful session token issued, and in some cases display specific errors such as enrollment token mismatches or SAML assertion rejections. Azure AD sign-in logs may simultaneously show successful upstream token issuance for the same sessions, creating an apparent contradiction where authentication succeeds at one layer but fails to complete downstream. The net effect is that affected users are fully blocked from accessing business-critical applications through SSO for the duration of the issue.

!!! note "Reported variations"

    - Some users see a "verification failed" message instead of being returned to the MFA prompt, particularly when the stale enrollment is the dominant factor.
    - In some cases, Azure AD sign-in logs show token rejection errors (such as AADSTS50020) tied to a specific group — such as an external contractors group — that require separate policy review even after the primary MFA loop is resolved.
    - A deprecated or legacy conditional access policy (referencing outdated enrollment mappings or policy versions) may be the specific source of the policy mismatch, rather than a newly pushed change.
    - Users who recently re-enrolled their authenticator may be disproportionately affected when a legacy policy evaluates outdated enrollment attributes against the new factor registration.
    - Intermittent authenticator clock skew warnings may appear alongside the stale enrollment and policy mismatch, though clock drift is not the primary cause of the loop.

## Affected environment

Distribution across 15 reported cases:

- **Operating system:** Windows 10 (20%), iOS 16.4 / Windows 10 (mixed) (7%)
- **Device / platform:** web (67%), Okta SSO federated with Azure AD (7%), cloud (7%)
- **Team:** Sales (33%), External Contractors (7%), SSO-Portal-Users (7%)
- **Region:** us-east-1 (73%), us-west-2 (13%), US-East (primary), EMEA partial impact (7%)

## Root cause

A combination of two identity-layer issues causes the authentication loop. First, affected user accounts retain stale MFA enrollment records in Okta — factor bindings that are outdated, tied to decommissioned devices, or inconsistent with the current policy version — which cause MFA verification to fail or loop even after the user approves the prompt. Second, a concurrent conditional access policy or group mapping change (such as a group synchronization between Azure AD and Okta, a policy scope update, or a claim mapping modification) results in affected users being evaluated against incorrect, deprecated, or misaligned access rules. Neither issue alone fully explains the behavior; the stale enrollments cause MFA verification failures, while the policy or group mismatch prevents the SSO session from completing even when MFA would otherwise succeed, together creating a persistent authentication loop.

## Diagnostics

Steps used to confirm this root cause:

1. Reproduced the affected user login flow through the SSO Portal to verify whether the MFA prompt loop occurred after challenge completion.  
   *Expected:* User completes MFA once and reaches the application landing page.
2. Checked MFA enrollment state and active factor records for impacted users in Okta after the identity sync.  
   *Expected:* User has an active factor with no stale or disabled enrollment.
3. Compared affected user group membership with conditional access and application assignment policy scope between Azure AD and Okta.  
   *Expected:* User belongs to the expected access group and policy scope.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Reviewed Okta authentication logs and isolated impacted users showing MFA enrollment mismatches and repeated challenge events during SSO attempts. Six affected accounts were identified, including <USER> (<EMP_ID>), <USER> (<EMP_ID>), and <USER> (<EMP_ID>), all in the <LOCATION> Sales team.
2. Reset MFA enrollment for affected users in Okta, including <USER>, <USER>, and <USER>, and required fresh authenticator enrollment to remove stale factor records that persisted after the morning identity sync.
3. Validated that users successfully re-enrolled their authenticators from their devices and confirmed the new factor status was active in the identity provider. <PERSON> confirmed successful Okta Verify push enrollment from <HOSTNAME>, and <USER> and <USER> confirmed enrollment from their respective workstations.
4. Reviewed Azure AD to Okta group synchronization and corrected the group-based conditional access mapping that was contributing to policy and enrollment mismatch for affected users. The SalesForce_SSO_Access group was re-synced and all six Sales users were confirmed as active members in both Azure AD and Okta.
5. Retested SSO access to the SSO Portal and downstream SaaS applications, then confirmed impacted users could complete MFA once and reach Salesforce and other assigned apps. Verification was performed by agent <PERSON> with <USER> and <USER> completing end-to-end login to Salesforce and Concur without repeated prompts.

**Example 2**

1. Reviewed Okta sign-on activity for affected users (<USER>, <USER>, <USER>) and confirmed repeated MFA challenge behavior followed by rejected assertions during Salesforce and Confluence launches — <USER> alone had 7 failed MFA cycles logged between 15:45–16:10 UTC on 2026-04-09.
2. Cleared active Okta sessions for impacted accounts (<USER>, <USER>, <USER>, and 3 additional Sales-External users identified in the <LOCATION> office) to remove stale authentication state before retesting sign-in.
3. Reset MFA enrollment for confirmed affected users so they could re-register a valid active factor and complete a clean challenge flow — <USER> re-enrolled successfully from <HOSTNAME> at 16:48 UTC and confirmed Salesforce access.
4. Corrected the Azure AD group-to-Okta assignment for the Sales-External mapping (reconciling the 14-member Azure AD group with Okta's 9-member assignment) so users were evaluated against the intended access policy and application assignment. <PERSON> (<EMAIL>) confirmed the sync configuration has been updated to prevent future drift.
5. Validated successful SSO access with test accounts <USER> and <USER> after MFA re-enrollment and mapping correction, then monitored sign-on logs for one business day to confirm no recurrence across all Sales-External users in the <LOCATION> region.

## Recommendation

This issue is resolved by IT support; reference "stale MFA enrollment and conditional access policy desync" when reporting it.

---

[← Back to categories](../../index.md)
