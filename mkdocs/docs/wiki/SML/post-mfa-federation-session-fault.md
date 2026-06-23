---
hide:
  - navigation
root_cause_id: SML/post-mfa-federation-session-fault
family: SML
ticket_count: 1
curated: true
self_serviceable: false
---

# Post-MFA federation redirect failure causing apparent sign-in loop

[← Back to categories](../../index.md)

## Description

Affected users are unable to reach applications such as Salesforce and Office 365 through the SSO portal (sso.corplabs.com). After successfully completing multi-factor authentication — including approving an Okta Verify push notification on their phone — a brief loading screen appears, and the user is then returned to the MFA prompt instead of being directed to the requested application. This cycle repeats on every attempt, giving the strong impression that MFA is failing or not being accepted.

The issue was first observed following an identity platform change window that updated federation trust settings between Okta and Azure AD. It primarily affects contractor accounts that were provisioned through a recently synced Azure AD security group. Users across different devices and network connections in the same office have reported identical behavior, and the loop persists regardless of which target application is selected from the SSO portal.

!!! note "Reported variations"

    - The issue has so far been confirmed only for contractor accounts provisioned through the newly synced Azure AD contractor group; employees outside that group may not be affected.
    - Some users may interpret the loop as an MFA enrollment or policy error, but diagnostics confirm that factor enrollment and conditional access policy assignments are healthy for affected accounts.

## Affected environment

Distribution across 1 reported cases:

- **Device / platform:** cloud (100%)
- **Team:** External Contractors (100%)
- **Region:** us-east-1 (100%)

## Root cause

A change to the federation trust configuration between Okta and Azure AD inadvertently omitted a required contractor group claim from the SAML assertion passed during sign-in. Although MFA completed successfully, the missing claim caused Azure AD to reject the session handoff, which redirected users back to the sign-in flow. The result appeared to be a repeated MFA prompt, but the actual failure occurred after MFA, during the federation redirect step.

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

1. Collected Okta system logs and Azure AD sign-in traces for affected users <USER> and <USER> showing successful MFA completion (verify_factor: SUCCESS) followed by federation redirect failure with error 'Invalid session state — missing group claim in token'. Traces captured from sessions originating at IPs <IP> and <IP> in the <LOCATION> office.
2. Confirmed MFA enrollment and conditional access policy assignment were healthy for <USER> (<EMP_ID>) and <USER> (<EMP_ID>) to rule out account configuration issues. Both had active Okta Verify push factors and correct ExtContractors-West group membership.
3. Escalated the incident to the identity platform vendor and internal SSO engineering team lead <PERSON> (<USER>, <EMAIL>) for federation flow analysis of the SAML claim mapping issue introduced during CHG-20260514-0087.
4. Provided affected users (<USER>, <USER>, and other impacted contractors in the <LOCATION> office) with a temporary direct-app access URL and alternate sign-in workaround via Okta bookmark app where available until the federation claim mapping issue is corrected by the SSO engineering team.

## Recommendation

This issue is resolved by IT support; reference 'post-MFA federation session fault' when reporting it.

---

[← Back to categories](../../index.md)
