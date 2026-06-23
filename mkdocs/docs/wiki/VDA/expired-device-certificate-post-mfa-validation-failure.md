---
hide:
  - navigation
root_cause_id: VDA/expired-device-certificate-post-mfa-validation-failure
family: VDA
ticket_count: 53
curated: true
self_serviceable: false
---

# Expired device certificate causes VPN tunnel teardown after MFA approval

[← Back to categories](../../index.md)

## Description

Affected users on corporate-managed Windows 10, Windows 11, and macOS laptops are unable to maintain a GlobalProtect VPN connection despite successfully completing Okta MFA authentication. After approving the Okta push notification — which completes without error and shows a green checkmark — the GlobalProtect client briefly displays a "Connected" status for anywhere from two to forty seconds before the tunnel disconnects automatically. Once the tunnel drops, all internal applications and resources, including intranet portals, Confluence, Jira, HR portals, CRM systems, Salesforce, file shares, and email, become completely unreachable. Repeated reconnection attempts produce the same cycle of successful MFA approval followed by immediate disconnection.

The issue has been observed across multiple offices and regions, affecting users in Sales, Engineering, Finance, Marketing, and other groups. In many cases, several users on the same team or in the same location experience the problem simultaneously. The behavior typically begins shortly after a scheduled device certificate rotation window or maintenance period, and affected users may notice a certificate expiration warning in the system tray or endpoint certificate store. The GlobalProtect client itself does not always display a visible error message — some users report the status simply flips back to "Disconnected" without explanation, while others see a brief error flash in the status bar.

Some affected endpoints also carry a stale GlobalProtect VPN profile that references an outdated certificate thumbprint. In those cases, even after a certificate renewal is performed, the tunnel may continue to fail until the cached VPN profile is also refreshed. A subset of users have experienced a recurrence of the issue after an initial fix when the certificate was renewed but the local VPN profile was not updated to reflect the new certificate.

!!! note "Reported variations"

    - On some endpoints, a stale GlobalProtect VPN profile cached locally continued to reference the old certificate thumbprint, causing the tunnel to fail even after the device certificate was renewed until the profile was also refreshed.
    - A subset of users experienced the issue recurring after an initial resolution because the earlier certificate renewal was performed without a corresponding VPN profile refresh on the endpoint.
    - In at least one case, an improperly re-enrolled certificate combined with an inconsistent conditional access group assignment prevented the renewed certificate and active VPN profile from aligning with the expected access policy.
    - Some users reported the tunnel staying connected for as little as two to three seconds, while others observed connections lasting up to forty seconds before teardown, depending on the timing of the post-authentication certificate validation step.
    - The issue was observed on both macOS 12 and Windows (10 and 11) managed endpoints, though the majority of reports involved Windows devices.

## Affected environment

Distribution across 53 reported cases:

- **Operating system:** Windows 10 (55%), Windows 10 21H2 (19%), Windows 11 (9%)
- **Device / platform:** laptop (26%), Corporate-managed laptop (9%), GlobalProtect 5.2.6 (8%)
- **Team:** Sales (23%), Remote Workers (19%), Remote Workforce (13%)
- **Region:** EMEA (49%), us-east-1 (26%), us-west-2 (13%)

## Root cause

The device certificate installed on the affected endpoint has expired, causing GlobalProtect to fail certificate validation during the post-authentication stage that follows a successful Okta MFA approval. Although the MFA step completes normally, the VPN gateway rejects the expired device certificate during the subsequent security handshake and immediately terminates the tunnel. On some endpoints, a stale locally cached VPN profile that still references the old certificate compounds the problem, preventing the renewed certificate from being used correctly during reconnection.

## Diagnostics

Steps used to confirm this root cause:

1. Confirm the MFA approval succeeds and determine whether the VPN tunnel drops before or after token exchange.  
   *Expected:* MFA approval succeeds and the VPN tunnel remains established.
2. Collect the VPN client error message, gateway, and disconnect timestamp from the client log.  
   *Expected:* Client logs show a successful gateway connection without certificate or policy errors.
3. Verify the device certificate validity and enrolled profile on the affected endpoint.  
   *Expected:* Device certificate is current and matches the active VPN profile.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Verified in firewall and client logs on gw-emea-01.corplabs.internal and <HOSTNAME> (IP <IP>) that the VPN tunnel was dropping after successful MFA because device certificate validation returned a certificate expired failure for certificate serial 7A:3F:01:CC (expired 2026-03-28).
2. Renewed the endpoint device certificate through the Device Certificate Service for the affected laptop <HOSTNAME> assigned to <PERSON> (<USER>, <EMP_ID>), replacing expired serial 7A:3F:01:CC with new certificate valid through 2027-04-11.
3. Refreshed the GlobalProtect VPN profile on the endpoint <HOSTNAME> and re-enrolled the renewed device certificate so the active profile matched the current certificate for user <USER>.
4. Had the user <PERSON> reconnect to GlobalProtect from <HOSTNAME> and complete Okta MFA again via <EMAIL>, then confirmed the TLS handshake completed successfully and the tunnel remained established on gateway gw-emea-01.corplabs.internal.
5. Validated access to internal applications (intranet, finance portal, and email over VPN) from <HOSTNAME> at IP <IP> and monitored the connection for 30 minutes to confirm the disconnect did not recur.

**Example 2**

1. Verified from client behavior and GlobalProtect logs on <HOSTNAME> that Okta MFA approval completed successfully for <USER> but the GlobalProtect tunnel disconnected immediately afterward due to client-side certificate validation failure against the us-east-1 gateway.
2. Renewed the expired device certificate (expired 2026-03-31) through MDM on the affected managed endpoint <HOSTNAME> so the VPN client could present a current certificate during post-authentication validation with the Device Certificate Service.
3. Pushed a refreshed GlobalProtect profile to <HOSTNAME> to remove the stale profile and align the client configuration with the renewed device certificate and current us-east-1 gateway settings.
4. Confirmed user <USER> remained in the required 'Engineering - Remote' conditional access group and revalidated that policy assignment in Okta was not blocking VPN access for the account CN=<USER>,OU=Engineering,DC=corplabs,DC=internal.
5. Tested the VPN connection after remediation from IP <IP> and verified a sustained tunnel with restored access to internal CRM, Confluence, and the SAML-protected intranet, then documented the same certificate renewal and profile refresh process for bulk remediation of other Engineering - Remote endpoints in the <LOCATION> region approaching certificate expiry.

## Recommendation

This issue is resolved by IT support; reference 'expired device certificate post-MFA VPN disconnect' when reporting it.

---

[← Back to categories](../../index.md)
