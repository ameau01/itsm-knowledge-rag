---
hide:
  - navigation
root_cause_id: VDA/expired-device-certificate-post-mfa-validation-failure
family: VDA
ticket_count: 53
curated: true
self_serviceable: false
---

# Expired Device Certificate Causes Post-MFA GlobalProtect Tunnel Teardown

[← Back to categories](../../index.md)

## Description

Affected users on corporate-managed Windows 10, Windows 11, and macOS endpoints experience immediate GlobalProtect VPN disconnections after successfully completing Okta MFA authentication. The VPN client briefly displays a "Connected" status for approximately 2 to 40 seconds following a successful push approval, then the tunnel tears down automatically. Once disconnected, all internal resources — including intranet portals, HR and finance systems, CRM, Confluence, Jira, SharePoint, Salesforce, SMB file shares, email, and SSH bastion access — become completely unreachable. Repeated reconnection attempts reproduce the same cycle of successful MFA followed by momentary connectivity and rapid disconnection.

Gateway and client-side log analysis consistently reveals that the tunnel teardown is triggered by a TLS handshake or device certificate validation failure occurring during the post-authentication phase. The affected endpoints present expired device certificates issued by the organization's internal Device Certificate Service. The gateway rejects the session with a certificate-expired error despite valid user-level MFA credentials. In several cases, the certificate expirations aligned with scheduled rotation windows that failed to complete renewals on all endpoints, or followed Windows cumulative updates that prevented automatic certificate renewal.

The issue has been observed across multiple offices, geographic regions, and VPN gateways, affecting individual users as well as groups of users whose certificates expired around the same date. It is not related to network connection type and reproduces on both wired and wireless connections. In some cases, stale GlobalProtect VPN profiles cached on affected endpoints — referencing outdated certificate thumbprints — compound the failure or cause recurrence after initial remediation. Standard user-side troubleshooting such as client restarts, device reboots, and local profile refreshes does not resolve the problem while the expired certificate remains in the endpoint's certificate store.

!!! note "Reported variations"

    - Tunnel uptime before disconnection varied from as little as 2 seconds to as long as 40 seconds after reaching "Connected" status, depending on when post-MFA certificate validation occurred.
    - Some affected endpoints also carried stale GlobalProtect VPN profiles referencing outdated certificate thumbprints, requiring both certificate renewal and profile refresh to fully resolve.
    - In some cases the GlobalProtect client entered a persistent reauthentication loop after disconnection rather than simply dropping the session.
    - The issue was observed on macOS 12 endpoints in addition to Windows 10 and Windows 11 managed laptops, requiring platform-specific re-enrollment workflows.
    - In at least one case the device certificate was not expired but had been improperly re-enrolled during a previous rotation cycle, producing the same validation failure.
    - Some users reported seeing device certificate expiration warnings in the system tray days before the VPN connectivity issue manifested.
    - In certain instances, Windows cumulative security updates prevented automatic certificate renewal, leaving the endpoint certificate in an expired state.
    - The issue affected both individual endpoints and clusters of users within the same team or certificate rotation batch simultaneously.

## Affected environment

Distribution across 53 reported cases:

- **Operating system:** Windows 10 (55%), Windows 10 21H2 (19%), Windows 11 (9%)
- **Device / platform:** laptop (26%), Corporate-managed laptop (9%), GlobalProtect 5.2.6 (8%)
- **Team:** Sales (23%), Remote Workers (19%), Remote Workforce (13%)
- **Region:** EMEA (49%), us-east-1 (26%), us-west-2 (13%)

## Root cause

Expired device certificates on affected managed endpoints caused GlobalProtect post-authentication certificate validation to fail immediately after successful Okta MFA approval, triggering VPN tunnel teardown. In some cases, stale GlobalProtect VPN profiles that referenced outdated certificate thumbprints compounded the issue or caused recurrence after initial certificate renewal.

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

Resolved by IT through device certificate renewal via the Device Certificate Service and, where applicable, a GlobalProtect VPN profile refresh on the affected endpoint.

---

[← Back to categories](../../index.md)
