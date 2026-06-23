---
hide:
  - navigation
root_cause_id: VDA/gateway-portal-post-auth-instability
family: VDA
ticket_count: 1
curated: true
self_serviceable: false
---

# GlobalProtect VPN disconnects seconds after successful MFA authentication

[← Back to categories](../../index.md)

## Description

Affected users on managed Windows 10 laptops experience a brief connection to the corporate network through GlobalProtect VPN, followed by an automatic disconnect within approximately three to five seconds. The issue occurs after the Okta MFA push notification is successfully approved — authentication itself completes without error, and the GlobalProtect client momentarily displays a "Connected" status before the session drops.

Once the disconnection occurs, all internal resources become unreachable, including the corporate intranet, Confluence, and Salesforce. Repeated sign-in attempts produce the same result: successful MFA approval, a fleeting connection, and then an immediate drop. The behavior is consistent across multiple users in different geographic regions and is not isolated to a single device or office location.

The issue has been reported by several remote workers simultaneously, suggesting a widespread service disruption rather than a problem with any individual laptop or user account. Affected users confirm that the disconnect happens only after MFA approval, not before, and that no changes were made to their devices or VPN configuration prior to the onset of the problem.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** Windows 10 (100%)
- **Device / platform:** laptop (100%)
- **Team:** remote_workers (100%)
- **Region:** global (100%)

## Root cause

The GlobalProtect VPN gateway and portal were experiencing instability during the post-authentication phase of session establishment. Although users completed multi-factor authentication successfully and their endpoint certificates were valid, the VPN infrastructure was resetting connections and timing out immediately after authentication. This was a service-side issue on the VPN platform rather than a problem with individual devices, certificates, or user credentials.

## Diagnostics

Steps used to confirm this root cause:

1. Confirmed <PERSON> approval completed successfully and checked whether the tunnel drop occurred before or after post-authentication token exchange.  
   *Expected:* MFA approval succeeds and the VPN tunnel remains established.
2. Collected GlobalProtect client log details, gateway connection outcome, and disconnect timing from affected endpoints.  
   *Expected:* Client logs show a successful gateway connection without certificate or policy errors.
3. Verified the device certificate validity and enrolled VPN profile on an affected endpoint and tested re-enrollment.  
   *Expected:* Device certificate is current and matches the active VPN profile.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

1. Correlated client disconnect timing across affected users (<USER> in <LOCATION>, <USER> in <LOCATION>, <USER> in <LOCATION>) using PanGPA.log timestamps and Okta audit events, and confirmed a shared service-side pattern on gp-gateway-us-east.corplabs.internal rather than isolated endpoint failure.
2. Escalated the incident to the VPN platform/network team (assigned to <PERSON>, emp ID <EMP_ID>) with collected client logs from <HOSTNAME>, <HOSTNAME>, and <HOSTNAME>, disconnect timestamps (03:41–03:52 UTC), and impacted regions (<LOCATION>, <LOCATION>, <LOCATION>) for gateway-side review of gp-gateway-us-east.corplabs.internal.
3. Monitored service recovery following gateway-side remediation and validated with affected users <PERSON>, <PERSON>, and <PERSON> that VPN sessions remained stable after gateway remediation. All three confirmed sustained connectivity to intranet, Confluence, and Salesforce by 05:15 UTC.

## Recommendation

This issue is resolved by IT support; reference 'GlobalProtect post-authentication disconnect' when reporting it.

---

[← Back to categories](../../index.md)
