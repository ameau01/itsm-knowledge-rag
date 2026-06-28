---
hide:
  - navigation
root_cause_id: SML/conditional-access-group-policy-mismatch
family: SML
ticket_count: 7
curated: true
self_serviceable: false
---

# Group-Scope Policy Mismatch Between Okta and Azure AD Causes MFA Loop

[← Back to categories](../../index.md)

## Description

Affected users experience repeated MFA challenge loops when signing in to SaaS applications—including Salesforce, Office 365, Confluence, Workday, and Concur—through Okta SSO portals federated with Azure AD. After successfully completing MFA verification (via Okta Verify push or Microsoft Authenticator code), users are immediately redirected back to another MFA prompt rather than reaching the target application. In some cases, users receive explicit HTTP 401 or 403 access-denied errors instead of the repeated prompt. The issue affects cohorts of users within the same organizational group rather than isolated accounts, and is reproducible across different browsers, devices, and network locations.

Investigation reveals a mismatch between Okta group assignments and the group-based scoping of Azure AD conditional access policies. Okta system logs confirm successful MFA verification, yet Azure AD sign-in logs show conditional access denials—sometimes with error code 53003—or missing group claims in the issued token. The root cause traces to recent administrative changes such as group sync updates, organizational unit restructures, sign-on policy modifications, or conditional access rule changes that cause affected users to fall outside the intended policy scope in Azure AD.

The issue typically emerges shortly after an identity configuration change—such as a directory sync modification, group restructure, or conditional access policy update—and affects multiple users tied to specific group memberships such as contractor access, sales, or broad employee groups. MFA enrollment and factor state are confirmed healthy in the Okta admin console for affected users, confirming the failure is at the policy-evaluation layer rather than the MFA enrollment layer.

!!! note "Reported variations"

    - Some affected users received explicit HTTP 401/403 errors rather than experiencing the MFA prompt loop.
    - In one incident, authenticator device clock drift of approximately five to seven minutes on certain affected users' mobile devices contributed additional sign-in failures alongside the policy mismatch.
    - Some users recovered after MFA factor re-enrollment in the Okta admin console, while others in the same cohort continued to experience the loop due to the underlying conditional access scope mismatch.
    - Azure AD sign-in logs in some cases showed missing group claims in the issued token rather than an explicit conditional access denial, preventing application access without a clear error message.
    - A subset of incidents involved a deprecated or legacy MFA policy reference in the Okta sign-on rule, causing login rejection even though users were correctly assigned to the appropriate application access group.
    - In one case, a location-based conditional access rule scoped to a specific regional group caused denials for on-site and VPN users alike at the affected office.
    - In one instance the issue was triggered by a manual organizational unit restructure, while in another it was triggered by a scheduled identity sync between Azure AD and Okta.
    - Certain users were affected on specific applications while others experienced the loop across a broader set of SaaS applications.

## Affected environment

Distribution across 7 reported cases:

- **Device / platform:** cloud (29%), web (29%), Web SSO (Okta + Azure AD) (14%)
- **Team:** Sales (57%), External Contractors (14%), marketing and sales (14%)
- **Region:** us-east-1 (71%), NA (14%), EMEA (14%)

## Root cause

Azure AD conditional access policy group scoping fell out of alignment with current Okta-sourced group assignments following administrative changes such as directory sync updates, organizational unit restructures, or policy modifications. Affected users were evaluated against incorrect or default conditional access policies during SSO, causing repeated MFA challenges or outright access denials despite valid MFA enrollment. In some incidents, a deprecated sign-on policy reference or an overly strict location-based conditional access rule contributed to the mismatch.

## Diagnostics

Steps used to confirm this root cause:

1. Reproduced the SSO login flow with an affected contractor test account and observed behavior after MFA approval.  
   *Expected:* User completes MFA once and reaches the application landing page.
2. Checked MFA enrollment status and active factor state for impacted users in the identity provider.  
   *Expected:* User has an active factor with no stale or disabled enrollment.
3. Compared affected users' group membership with Azure AD conditional access scope and application assignment mapping.  
   *Expected:* User belongs to the expected access group and policy scope.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Reviewed Okta authentication logs and Azure AD sign-in records for affected contractor accounts (<USER>, <USER>, <USER>, and 9 others in the 'CG-External-East' group) to confirm repeated MFA challenges and missing group claims in issued SAML tokens. Logs were correlated using source IPs <IP> and <IP> from the <LOCATION> office network.
2. Corrected the Azure AD Conditional Access group mapping so the recently synced contractor access group 'CG-External-East' supplied the expected group claim during SSO evaluation, ensuring Okta could properly validate contractor group membership for application access policies.
3. Resynced Azure AD group membership to Okta via Azure AD Connect to refresh policy scope and ensure all 12 affected contractor users in the <LOCATION> office were associated with the proper access group and claim configuration.
4. Reset MFA enrollment and cleared stale session state for two impacted users — <USER> (<EMP_ID>) and <USER> (<EMP_ID>) — to remove invalid challenge loops created before the mapping correction. Both users re-enrolled via Okta Verify successfully.
5. Validated the fix with test user <USER> (<EMP_ID>) from <HOSTNAME> and then confirmed all 12 impacted contractor accounts, verifying successful SSO completion and restored access to Salesforce and Office365 without repeated MFA prompts. <PERSON> (<EMAIL>) confirmed resolution on behalf of the contractor team.

**Example 2**

1. Reviewed the affected Okta sign-on rule and removed the stale reference to 'Legacy MFA Policy v1', replacing it with the active 'MFA Policy v2' mapping. Change executed by <PERSON> (<USER>) and verified in the Okta admin console.
2. Validated that the impacted Sales users (<USER>, <USER>, <USER>, and 12 additional accounts in the <LOCATION> Sales group) were in the expected policy scope and that the corrected sign-on rule applied to their SSO application access path for Salesforce, Office365, and Confluence.
3. Reset MFA enrollment for affected users with stale factor state — starting with <USER>, <USER>, and <USER> — and guided them through re-enrollment against the current 'MFA Policy v2' requirements via Okta Verify. <PERSON> (<EMAIL>) confirmed successful re-enrollment from her workstation.
4. Retested login to Salesforce and Office365 through Okta SSO from <HOSTNAME> (<IP>) and <HOSTNAME> (<IP>) and confirmed successful MFA completion without returning to the login page for <USER> and <USER>.
5. Monitored Okta and downstream Azure AD sign-in activity for 4 hours after the change to confirm successful SAML assertions and no continued MFA loop behavior across all Sales group users. No further LOGIN_REJECTED events observed for the affected accounts.

## Recommendation

Resolved by IT after correcting Azure AD conditional access policy group scoping and Okta sign-on policy references to restore proper SSO evaluation for affected users.

---

[← Back to categories](../../index.md)
