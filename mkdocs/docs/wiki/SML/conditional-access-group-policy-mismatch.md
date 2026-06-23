---
hide:
  - navigation
root_cause_id: SML/conditional-access-group-policy-mismatch
family: SML
ticket_count: 7
curated: true
self_serviceable: false
---

# Repeated MFA prompts due to conditional access and group policy mismatch

[← Back to categories](../../index.md)

## Description

Affected users attempting to sign in to SaaS applications — such as Salesforce, Office 365, Google Workspace, Workday, Confluence, or Concur — through the SSO portal are repeatedly returned to the MFA challenge after successfully completing authentication. The MFA prompt loops immediately after the user approves a push notification or enters a code, and no application session is established. In some cases, users receive explicit access-denied or 401/403 errors instead of (or in addition to) the repeated prompt.

The issue typically affects a group of users rather than a single account, often concentrated within a specific office location or organizational unit such as Sales, Contracting, or external contractor teams. It spans multiple applications, browsers, devices, and authenticator platforms, which distinguishes it from a single-device or browser-specific problem. Standard user-side troubleshooting — clearing browser caches, switching browsers, using private browsing, or restarting authenticator apps — does not resolve the loop.

The onset of the issue generally follows a recent identity-related change, such as a directory sync between Azure AD and Okta, a conditional access policy update, a group restructure, or a sign-on policy modification. Okta-side logs may show successful MFA verification, while Azure AD sign-in logs show conditional access denials for the same sign-in attempts, indicating a disconnect between the two identity layers during SSO evaluation.

!!! note "Reported variations"

    - In some cases, the active Okta sign-on rule references a deprecated MFA policy (e.g., a legacy policy version), causing a mismatch between current user MFA enrollments and the policy-required factor flow, which produces repeated MFA-required events followed by rejected sign-in assertions.
    - A subset of affected users may also have stale MFA factor enrollments; resetting their MFA enrollment in Okta may temporarily restore access for those individuals, but the broader loop persists for other users until the underlying policy or group mapping is corrected.
    - Some users' authenticator devices may exhibit clock drift of five minutes or more, contributing additional MFA validation failures on top of the conditional access mismatch.
    - External contractor accounts added through recently synced Azure AD groups may be affected when the conditional access group mapping does not include the new contractor group claim after the sync.

## Affected environment

Distribution across 7 reported cases:

- **Device / platform:** cloud (29%), web (29%), Web SSO (Okta + Azure AD) (14%)
- **Team:** Sales (57%), External Contractors (14%), marketing and sales (14%)
- **Region:** us-east-1 (71%), NA (14%), EMEA (14%)

## Root cause

A mismatch between Azure AD conditional access policy scope and current Okta-sourced group assignments causes affected users to be evaluated against incorrect or outdated group memberships during federated sign-in. This typically occurs after a directory sync, group restructure, or policy update that changes group mappings or policy references without updating the corresponding conditional access rules. As a result, users authenticate successfully at the Okta layer but Azure AD denies token issuance because the expected group claims are missing or the policy scope no longer includes the correct user population, producing repeated MFA challenges and blocked application access.

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

1. Reviewed affected user group membership in Okta and Azure AD — specifically the Okta groups 'Okta-Marketing' and 'Okta-Sales' versus the Azure AD group 'SG-SaaS-Marketing-Sales' — and identified that the Azure AD Conditional Access policy 'CA-SaaS-MFA-Required' scope did not match the intended Okta group mapping for the 14 impacted marketing and sales users in the <LOCATION> office, including <USER>, <USER>, and <USER>.
2. Updated the Azure AD Conditional Access group-based assignment for policy 'CA-SaaS-MFA-Required' to align with the corrected synced group membership from Okta, ensuring all 14 affected users in 'Okta-Marketing' and 'Okta-Sales' were properly reflected in 'SG-SaaS-Marketing-Sales' so the affected cohort was evaluated against the proper MFA and access policy. Change performed by identity engineer <PERSON> (<USER>).
3. Performed targeted <PERSON> re-enrollment only for impacted users with stale or recently reset factor state — specifically <USER>, <USER>, and two additional users (<USER>, <USER>) — to remove residual enrollment inconsistencies after the policy correction. Re-enrollment was confirmed via Okta admin console.
4. Validated end-to-end SSO for representative test accounts <USER> (from <HOSTNAME>, IP <IP>) and <USER> (from <HOSTNAME>, IP <IP>) by confirming a single MFA challenge completed successfully and access was restored to downstream SaaS applications including Salesforce, Google Workspace, and Confluence.
5. Monitored Okta audit events and Azure AD sign-in logs for 4 hours after the change window (09:10–13:10 UTC) to confirm that prior conditional access denials stopped for the corrected user cohort. All 14 <LOCATION> office users showed successful sign-ins with no further MFA loop behavior reported. Ticket closed by <PERSON> and confirmation sent to <PERSON> (<EMAIL>).

**Example 2**

1. Reviewed the Azure AD Conditional Access policy 'CA-SaaS-MFA-Enforce' assignments and identified that the updated Sales group 'SG-EMEA-Sales-2026' was excluded or not included in the intended policy scope. The old group 'SG-EMEA-Sales' had been emptied during the restructure but was still the only group referenced in the policy. Review performed by <PERSON> (<USER>) from the Identity Support team.
2. Updated the Conditional Access policy 'CA-SaaS-MFA-Enforce' to include the correct user group 'SG-EMEA-Sales-2026' and re-published the policy configuration. Change was applied at 22:25 UTC and confirmed active via Azure AD audit log.
3. Validated that affected users (<USER>, <USER>, <USER>, <USER>, and others) had the expected group membership in 'SG-EMEA-Sales-2026' after the recent restructure and confirmed membership synchronization from Okta to Azure AD was complete with no delta sync errors.
4. Retested SSO sign-in to Office 365, Salesforce, and Confluence for previously impacted users. <PERSON> (<USER>) confirmed successful login from <HOSTNAME> at 22:32 UTC, and <PERSON> (<USER>) and <PERSON> (<USER>) verified MFA completed once without looping across all three applications.
5. Documented that MFA re-enrollment could temporarily help an individual user (as observed with <USER> during diagnostics) but was not the systemic fix for the broader access issue. Added a note to the identity team runbook to verify Conditional Access policy group references whenever organizational group restructures are performed. Ticket closed by <PERSON> (<USER>, <EMP_ID>).

## Recommendation

This issue is resolved by IT support; reference 'conditional access group policy mismatch' when reporting it.

---

[← Back to categories](../../index.md)
