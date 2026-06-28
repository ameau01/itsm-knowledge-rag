---
hide:
  - navigation
root_cause_id: SML/combined-stale-enrollment-and-policy-desync
family: SML
ticket_count: 15
curated: true
self_serviceable: false
---

# Stale MFA Enrollment and Group Policy Mismatch Cause SSO Authentication Loop

[← Back to categories](../../index.md)

## Description

Affected users across multiple departments—including Sales, Marketing, Engineering, Operations, and external contractor groups—were unable to complete sign-in to SaaS applications (such as Salesforce, Office 365, Concur, Confluence, Slack, Workday, and G Suite) through the corporate SSO portal federated with Okta and Azure AD. After entering valid credentials and approving the Okta Verify MFA prompt, users were immediately returned to another MFA challenge rather than being granted access. The loop persisted regardless of the application selected, the device used, or whether browser caches were cleared. In some cases, explicit error messages appeared, including "Sign-in rejected," "Authentication rejected," "verification failed," or HTTP 401 MFA_REQUIRED responses.

Okta system logs for affected accounts consistently showed repeated MFA challenge events with no successful verification callback, including token mismatch errors and SAML assertion rejections. Azure AD sign-in logs reflected corresponding conditional access denial events. In several instances, Azure AD showed successful token issuance for sessions that Okta simultaneously rejected, highlighting a desynchronization between the two identity platforms.

The issue consistently emerged following recent identity infrastructure changes—conditional access policy updates, Azure AD group attribute modifications, or scheduled identity sync operations. Investigation across all reported cases identified two co-occurring conditions: stale MFA factor enrollments on affected Okta accounts (sometimes tied to previously decommissioned devices or pre-migration factor schemas) and a group-based conditional access policy mismatch in Azure AD caused by incomplete group membership propagation or references to deprecated policy versions. Together, these conditions caused the authentication flow to loop indefinitely without completing the SSO handoff.

!!! note "Reported variations"

    - Some affected users received an explicit "Sign-in rejected" or "access_denied" message rather than a silent MFA loop, with no corresponding approval activity visible in the authenticator app.
    - Azure AD logs for certain external contractor accounts showed token rejection errors specific to the contractor group conditional access rule set, confirming the issue was not limited to internal employees.
    - In one case, temporarily reassigning an affected user to a legacy access group immediately restored access, confirming the policy scope mismatch.
    - A legacy conditional access policy referencing deprecated enrollment mapping attributes from a pre-migration factor schema remained enabled, causing the loop specifically for users who re-enrolled after a factor migration.
    - Some affected users experienced intermittent access rather than a complete block, with the MFA loop occurring inconsistently across sign-in attempts.
    - One affected user confirmed that a colleague in the same Azure AD access group could sign in normally, indicating the issue was account-specific on a subset of group members.
    - A subset of users required individual MFA enrollment resets even after the policy-level fix was applied, due to factor enrollment metadata recorded under the old policy version.
    - An authenticator clock skew warning was observed on one affected device during the failure window, though the loop persisted independent of time synchronization.

## Affected environment

Distribution across 15 reported cases:

- **Operating system:** Windows 10 (20%), iOS 16.4 / Windows 10 (mixed) (7%)
- **Device / platform:** web (67%), Okta SSO federated with Azure AD (7%), cloud (7%)
- **Team:** Sales (33%), External Contractors (7%), SSO-Portal-Users (7%)
- **Region:** us-east-1 (73%), us-west-2 (13%), US-East (primary), EMEA partial impact (7%)

## Root cause

Stale MFA enrollment records persisted on affected user accounts following identity sync operations or policy migrations between Azure AD and Okta. Concurrently, group-based conditional access policies referenced outdated group mappings, deprecated policy versions, or stale group object identifiers introduced during scheduled sync cycles or policy change windows. The combination of mismatched factor enrollment state and incorrect policy scope evaluation caused repeated MFA challenges without successful session completion.

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

1. Reviewed Okta authentication logs for affected users (<USER>, <USER>, <USER>, <USER>) and confirmed repeated factor verification failures consistent with stale MFA enrollment bindings across all four Sales accounts in the <LOCATION> office.
2. Reset MFA enrollment for impacted user accounts in Okta to remove the invalid factor associations. Identity team lead <PERSON> (<USER>, <EMP_ID>) performed the bulk reset for all affected Sales users.
3. Guided users through re-enrolling Okta Verify or their approved authenticator method and confirmed successful factor registration. <PERSON> (<USER>), <PERSON> (<USER>), <PERSON> (<USER>), and <PERSON> (<USER>) each completed re-enrollment and verified a successful push notification.
4. Validated successful SSO login to Salesforce and other affected SaaS applications after re-enrollment. Each user confirmed access to Salesforce, Concur, and Office 365 from their respective workstations without further MFA loop behavior.
5. Reviewed and corrected group membership alignment with the conditional access policy so affected users matched the intended access scope. The Sales-SSO-Access group in Azure AD was reconciled by <USER> to ensure all <LOCATION> Sales team members were properly targeted.

## Recommendation

Resolved by IT after resetting stale MFA factor enrollments and correcting the Azure AD group-based conditional access policy scope to restore SSO authentication.

---

[← Back to categories](../../index.md)
