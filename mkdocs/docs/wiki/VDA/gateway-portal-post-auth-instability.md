---
hide:
  - navigation
root_cause_id: VDA/gateway-portal-post-auth-instability
family: VDA
ticket_count: 1
curated: true
self_serviceable: false
---

# Post-Authentication GlobalProtect Gateway Instability Terminating VPN Sessions

[← Back to categories](../../index.md)

## Description

Multiple remote users on managed Windows 10 laptops experienced repeated disconnections when connecting to the corporate network through GlobalProtect VPN. After successfully approving the MFA push notification, the VPN client briefly reached a "Connected" state but then dropped the connection within three to five seconds. The rapid disconnection prevented access to internal resources including the corporate intranet, Confluence, and Salesforce. The issue persisted across repeated sign-in attempts throughout the morning.

The problem was not isolated to a single user or region. At least five remote workers across multiple geographic locations reported identical behavior, ruling out endpoint-specific causes. Diagnostics confirmed that MFA authentication completed successfully for all affected users and that no endpoint certificate issues were present on any of the tested devices.

Investigation revealed that the underlying failure occurred during post-authentication session establishment on the VPN gateway. Multiple clients recorded gateway resets, with IKE negotiation being aborted after authentication had already succeeded, along with portal timeout behavior during the post-auth phase. The consistent pattern across all affected regions pointed to a VPN service-side issue on the gateway rather than any endpoint or user-level problem.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** Windows 10 (100%)
- **Device / platform:** laptop (100%)
- **Team:** remote_workers (100%)
- **Region:** global (100%)

## Root cause

Post-authentication instability on the GlobalProtect gateway or portal was terminating VPN sessions after successful MFA validation. The gateway was resetting connections during the session establishment phase, causing widespread disconnects despite valid endpoint certificate configurations across affected devices.

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

The issue was resolved by IT after identifying and correcting post-authentication gateway instability that was terminating GlobalProtect VPN sessions following successful MFA validation.

---

[← Back to categories](../../index.md)
