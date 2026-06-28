---
hide:
  - navigation
root_cause_id: SML/post-mfa-federation-session-fault
family: SML
ticket_count: 1
curated: true
self_serviceable: false
---

# Federated SSO Claim Mapping Fault Causes Post-MFA Session Loop

[← Back to categories](../../index.md)

## Description

Affected users were unable to access SaaS applications — including Salesforce, Office 365, and other targets — through the corporate SSO portal. The sign-in process appeared to loop back to the multi-factor authentication (MFA) prompt repeatedly: users would approve the Okta Verify push notification, see a brief loading screen, and then be returned to the MFA prompt rather than reaching the intended application. The issue began shortly after a scheduled identity platform change window that updated federation trust settings between Okta and Azure AD.

Diagnostic investigation revealed that the behavior resembled an MFA loop but was not an MFA failure. Okta system logs showed a successful factor verification event followed by an immediate federation redirect failure, with the error indicating an invalid session state due to a missing group claim in the SAML assertion. MFA enrollment and conditional access policy assignments were confirmed healthy for all affected accounts. The root cause was traced to a misconfigured claim mapping in the Okta-to-Azure AD federation trust introduced during the change window, which omitted the contractor group claim from the SAML token.

The issue was observed among contractor accounts provisioned through a recently synced Azure AD contractor access group. Affected users reported the problem from the same office location and across multiple SaaS application targets, confirming the failure was not application-specific but tied to federated session handling for that contractor group.

## Affected environment

Distribution across 1 reported cases:

- **Device / platform:** cloud (100%)
- **Team:** External Contractors (100%)
- **Region:** us-east-1 (100%)

## Root cause

An upstream federated SSO processing fault occurred after MFA completion, preventing session establishment and redirecting users back to the sign-in flow. A misconfigured claim mapping in the Okta-to-Azure AD federation trust, introduced during a scheduled change window, omitted the contractor group claim from the SAML assertion, causing an invalid session state for affected contractor accounts.

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

Resolved by IT after correcting the federated claim mapping configuration that omitted the contractor group claim from the SAML assertion during the Okta-to-Azure AD trust update.

---

[← Back to categories](../../index.md)
