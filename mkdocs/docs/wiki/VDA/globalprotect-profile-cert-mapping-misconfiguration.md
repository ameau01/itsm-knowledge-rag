---
hide:
  - navigation
root_cause_id: VDA/globalprotect-profile-cert-mapping-misconfiguration
family: VDA
ticket_count: 1
curated: true
self_serviceable: false
---

# GlobalProtect Profile Certificate Mapping Mismatch Causing Post-Auth Disconnects

[← Back to categories](../../index.md)

## Description

Affected users on managed Windows 10 laptops experienced repeated VPN disconnections when connecting to the corporate network via GlobalProtect while working remotely. After successfully approving the MFA prompt, the VPN session appeared to establish briefly — typically for approximately 10 to 20 seconds — before dropping automatically. During the short-lived connection, internal applications such as the corporate intranet and Confluence sometimes began loading partially but became unreachable once the tunnel terminated. The issue was reproducible across multiple reconnect attempts and affected multiple users in the same department whose devices had recently received a VPN profile update.

Diagnostics confirmed that MFA authentication was completing successfully for all affected users and that the device certificates installed on the endpoints remained valid. However, the GlobalProtect profile pushed to affected devices referenced an incorrect enrolled certificate. Specifically, the profile pointed to an old certificate thumbprint that no longer matched the currently enrolled certificate from the Device Certificate Service. This mismatch caused post-authentication policy evaluation to fail, producing a VPN-ERR-201 error in diagnostic logs, which in turn caused the client to terminate the tunnel immediately after login.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** Windows 10 21H2 (100%)
- **Device / platform:** GlobalProtect 5.2.6 (100%)
- **Team:** Sales and Marketing (100%)
- **Region:** EMEA (100%)

## Root cause

A GlobalProtect profile misconfiguration on affected endpoints caused the client to use a certificate mapping that did not match the active enrolled device certificate. This triggered post-authentication policy disconnects after successful MFA validation.

## Diagnostics

Steps used to confirm this root cause:

1. Confirmed <PERSON> approval succeeded and checked whether the VPN tunnel dropped before or after post-auth token exchange.  
   *Expected:* MFA approval succeeds and the VPN tunnel remains established.
2. Collected GlobalProtect client log details, disconnect timing, and observed post-auth error behavior from affected endpoints.  
   *Expected:* Client logs show a successful gateway connection without certificate or policy errors.
3. Verified the endpoint device certificate validity and whether the enrolled certificate matched the active GlobalProtect profile.  
   *Expected:* Device certificate is current and matches the active VPN profile.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

1. Corrected the GlobalProtect profile configuration on <HOSTNAME> and <HOSTNAME> so the active profile referenced the currently enrolled device certificate (thumbprint 8A:3F:…:D1) issued by the Device Certificate Service, replacing the stale reference to 2C:7B:…:E4.
2. Removed the stale local VPN profile from both affected endpoints using the GlobalProtect administrative removal tool and forced a fresh profile retrieval from the EMEA gateway, confirming the new profile XML contained the correct certificate mapping.
3. Retested connection flow for <USER> on <HOSTNAME> and <USER> on <HOSTNAME> with <PERSON> and confirmed the VPN tunnel remained established for over 30 minutes with no post-auth disconnects. Internal applications including the intranet, Confluence, and Salesforce were all reachable and functional.
4. Reviewed the 2026-05-06 VPN profile deployment with the network team and rolled back the incorrect certificate mapping for similarly affected devices in the Sales and Marketing group across the <LOCATION> region. A corrected profile was redeployed and verified by <PERSON>.

## Recommendation

The issue was resolved by IT after correcting the GlobalProtect profile to reference the current enrolled device certificate thumbprint.

---

[← Back to categories](../../index.md)
