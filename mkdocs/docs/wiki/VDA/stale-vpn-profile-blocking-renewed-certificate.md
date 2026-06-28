---
hide:
  - navigation
root_cause_id: VDA/stale-vpn-profile-blocking-renewed-certificate
family: VDA
ticket_count: 2
curated: true
self_serviceable: false
---

# Stale VPN Profile After Certificate Renewal Causes Tunnel Teardown

[← Back to categories](../../index.md)

## Description

Affected users on managed Windows 10 laptops experience repeated GlobalProtect VPN disconnections shortly after successful Okta MFA authentication. The VPN client briefly displays a "Connected" status for approximately three to ten seconds before dropping back to "Disconnected." During the brief connection window, internal resources such as the corporate intranet, SMB file shares, and internal-only email remain unreachable. The disconnection behavior is consistent and reproducible across multiple connection attempts from the same endpoint.

The issue arises after a device certificate renewal has been performed or pushed to the endpoint. Although the renewed certificate is present, the endpoint retains an outdated local VPN profile that references the previous certificate association. This mismatch causes the VPN gateway to tear down the tunnel immediately after authentication succeeds. Gateway and client log review confirms that MFA authentication and tunnel establishment complete successfully before the termination occurs, ruling out credential or MFA issues.

The problem is isolated to specific endpoints rather than being a network-wide or account-wide condition. In observed cases, a colleague on the same team connecting from the same office location did not experience the issue, indicating that the root cause is tied to the individual device's local profile state.

!!! note "Reported variations"

    - In one case, the affected user reported that internal-only email access was also unreachable during the brief connection window, in addition to intranet and file share resources.
    - One affected endpoint retained a stale VPN profile dated approximately two months prior to the most recent certificate push, confirming a significant gap between the profile timestamp and the renewed certificate.
    - Not all devices on the same team or office network were affected; a colleague of one affected user on the same team did not experience the disconnection, underscoring the endpoint-specific nature of the issue.

## Affected environment

Distribution across 2 reported cases:

- **Operating system:** Windows 10 21H2 (100%)
- **Device / platform:** laptop (50%), GlobalProtect 5.2.8 (50%)
- **Team:** Sales - Remote (50%), Corporate VPN Users (50%)
- **Region:** EMEA (100%)

## Root cause

The GlobalProtect client retained a stale local VPN profile after a device certificate renewal, creating a mismatch between the renewed certificate and the active profile's certificate association. After successful MFA authentication, the gateway session failed device certificate validation and posture checks, tearing down the tunnel during reauthentication.

## Diagnostics

Steps used to confirm this root cause:

1. Confirm that Okta MFA approval succeeds and determine whether the tunnel drops after authentication completes.  
   *Expected:* MFA approval succeeds and the VPN tunnel remains established.
2. Review the GlobalProtect client behavior and reported log symptoms around the disconnect for gateway or certificate-related failures.  
   *Expected:* Client logs show a successful gateway connection without certificate or policy errors.
3. Verify the endpoint device certificate validity and whether the active GlobalProtect profile is using the renewed certificate instead of a stale local profile.  
   *Expected:* Device certificate is current and matches the active VPN profile.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Renew the device certificate on the affected endpoint <HOSTNAME> and confirm the active machine certificate is current and available in the local certificate store (certlm.msc). Remove the expired certificate to prevent future ambiguity in certificate selection.
2. Clear the cached GlobalProtect local profile/configuration on <HOSTNAME> (C:\Program Files\Palo Alto Networks\GlobalProtect\PanGPS\) so the client does not continue presenting the stale certificate binding. Desktop support engineer <PERSON> performed this step remotely.
3. Reconnect GlobalProtect for user <USER> and force the client to download a fresh portal/profile configuration tied to the renewed device certificate. Verified the new profile references the correct certificate thumbprint.
4. Verify that user <USER> (<PERSON>) and device <HOSTNAME> still satisfy Okta device posture and Conditional Access group assignment for the 'Sales - Remote' group so post-MFA policy evaluation passes without session termination.
5. Validate that the VPN session for <USER> remains connected and stable for at least 15 minutes, and that <PERSON> can access internal intranet (intranet.corp.internal), SMB file shares (\\filesrv.corp.internal\sales-emea), and other internal-only resources including corporate email before closure. Confirmed with <PERSON> via phone at +44-<PHONE> that all services are operational.

**Example 2**

1. Removed the stale GlobalProtect VPN profile (dated 2026-02-11) from the affected endpoint <HOSTNAME> so the client no longer attempted to use outdated post-renewal settings that referenced the previous certificate thumbprint.
2. Forced a fresh GlobalProtect profile download from the management plane via gw-emea.vpn.corplabs.com to restore the current gateway and certificate mapping on <HOSTNAME>, ensuring the profile now referenced the renewed device certificate issued 2026-04-15.
3. Re-enrolled <HOSTNAME> through the Device Certificate Service to ensure the renewed device certificate was correctly associated with the newly applied VPN profile and that the certificate binding was validated end-to-end.
4. Restarted the GlobalProtect connection flow on <HOSTNAME> and user <USER> completed Okta MFA push approval to confirm the tunnel no longer disconnected after authentication; the tunnel remained stable and the assigned IP <IP> persisted.
5. Validated sustained VPN connectivity for <USER> over a 30-minute observation window and confirmed <PERSON> <PERSON> could again access internal applications including the intranet (https://intranet.corplabs.com) and file shares (\\fs-emea-01.corplabs.internal\shared) from the <LOCATION> office.

## Recommendation

Resolved by IT; stale GlobalProtect VPN profile and certificate association mismatch causing post-MFA tunnel teardown.

---

[← Back to categories](../../index.md)
