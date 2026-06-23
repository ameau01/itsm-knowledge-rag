---
hide:
  - navigation
root_cause_id: VDA/globalprotect-profile-cert-mapping-misconfiguration
family: VDA
ticket_count: 1
curated: true
self_serviceable: false
---

# GlobalProtect profile update referencing wrong certificate causes post-auth disconnects

[← Back to categories](../../index.md)

## Description

Affected users on managed Windows 10 laptops experience VPN disconnections shortly after completing multi-factor authentication through Okta. GlobalProtect briefly shows a connected status — typically lasting only 10 to 20 seconds — before the session drops automatically. During the brief window of connectivity, internal applications such as the corporate intranet and Confluence may begin loading but become unreachable once the tunnel terminates.

The issue is reproducible across multiple reconnect attempts and is not resolved by retrying the MFA prompt. It has been observed on devices in the Sales and Marketing group that received a VPN profile update pushed on 2026-05-06. Multiple users working remotely from different locations and home networks have reported the same behavior, confirming the issue is not tied to a single device or network environment.

Notably, the MFA step itself completes without error, and the device certificates issued by the corporate certificate service remain valid and unexpired. The disconnection occurs only after authentication succeeds, during the policy evaluation phase that follows login.

!!! note "Reported variations"

    - Some affected users may see internal pages partially load during the brief connected window before the tunnel drops, while others lose connectivity too quickly for any page content to appear.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** Windows 10 21H2 (100%)
- **Device / platform:** GlobalProtect 5.2.6 (100%)
- **Team:** Sales and Marketing (100%)
- **Region:** EMEA (100%)

## Root cause

A GlobalProtect VPN profile update pushed on 2026-05-06 introduced a misconfiguration on affected endpoints. The updated profile references an outdated certificate thumbprint from a previous enrollment rather than the currently active device certificate. Because the certificate cited in the profile does not match the one actually enrolled on the device, the post-authentication policy check fails and the VPN client immediately terminates the session after login.

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

This issue is resolved by IT support; reference "GlobalProtect profile certificate mapping mismatch" when reporting it.

---

[← Back to categories](../../index.md)
