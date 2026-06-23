---
hide:
  - navigation
root_cause_id: VDA/stale-vpn-profile-blocking-renewed-certificate
family: VDA
ticket_count: 2
curated: true
self_serviceable: false
---

# Stale VPN profile blocking renewed device certificate after renewal

[← Back to categories](../../index.md)

## Description

Affected users experience a VPN disconnection within seconds of successfully authenticating. The Okta MFA push notification is approved without issue, and the GlobalProtect client briefly displays a "Connected" status — typically for three to ten seconds — before dropping back to "Disconnected." During the brief connection window, internal resources such as the corporate intranet, file shares, and internal email remain unreachable or fail to load before the tunnel is torn down.

The issue has been observed on managed Windows 10 laptops connecting from office locations. Users report that the behavior is fully reproducible across multiple connection attempts in the same session, with identical results each time. Colleagues on the same team and network may not be affected, indicating the problem is specific to the individual endpoint rather than a site-wide outage.

A distinguishing characteristic of this issue is that it recurs after a prior device certificate renewal that initially appeared to restore service. The certificate renewal alone does not permanently resolve the disconnection, and the same post-authentication tunnel teardown returns — sometimes within days — because the underlying profile state on the endpoint was not corrected during the earlier fix.

!!! note "Reported variations"

    - In some cases, a prior certificate renewal by desktop support temporarily restored VPN connectivity, but the issue returned because the stale profile association was not cleared at the time of the renewal.
    - The stale profile has been observed dating back several months before the most recent certificate renewal, indicating the mismatch can persist across multiple renewal cycles if not explicitly corrected.

## Affected environment

Distribution across 2 reported cases:

- **Operating system:** Windows 10 21H2 (100%)
- **Device / platform:** laptop (50%), GlobalProtect 5.2.8 (50%)
- **Team:** Sales - Remote (50%), Corporate VPN Users (50%)
- **Region:** EMEA (100%)

## Root cause

The GlobalProtect client on the affected endpoint retains a stale VPN profile that was associated with the previous device certificate. When the Device Certificate Service renews the device certificate, the endpoint does not automatically update this local profile-to-certificate association. As a result, after successful MFA authentication, the VPN gateway detects a mismatch between the renewed certificate and the outdated profile during post-authentication validation and immediately tears down the tunnel.

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

This issue is resolved by IT support; reference 'stale VPN profile after certificate renewal' when reporting it.

---

[← Back to categories](../../index.md)
