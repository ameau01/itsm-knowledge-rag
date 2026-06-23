---
hide:
  - navigation
root_cause_id: WCI/expired-radius-controller-eap-tls-certificate
family: WCI
ticket_count: 34
curated: true
self_serviceable: false
---

# Corporate Wi-Fi outage caused by expired wireless controller authentication certificate

[← Back to categories](../../index.md)

## Description

Affected users are unable to connect to the corporate Wi-Fi network (typically the secured enterprise SSID) on managed laptops, phones, and BYOD devices. Devices can see and select the corporate wireless network, but the connection fails during the authentication step. Depending on the device and operating system, the failure may present in different ways: some devices display an explicit "authentication failed" or "certificate expired" error immediately after attempting to join, while others appear to connect briefly before showing "Connected, no internet" or "No network access" and then disconnecting. In all cases, the device does not receive a usable network address or access to internal resources.

The issue typically affects a broad group of users across one or more office floors or sites simultaneously, rather than a single device or individual. Both Windows and macOS laptops, as well as iOS and Android mobile devices, are impacted. Wired Ethernet connections and guest Wi-Fi networks continue to work normally, indicating the problem is isolated to the corporate wireless authentication path.

The onset of the issue often coincides with a scheduled certificate rotation or maintenance window, though in some cases the certificate simply reaches its natural expiration date. Users who attempt common self-help steps — such as forgetting and rejoining the wireless network, rebooting their device, or re-entering their credentials — find that these actions do not restore connectivity.

!!! note "Reported variations"

    - A subset of devices continue to fail even after the expired certificate is renewed on the wireless infrastructure, because the device has retained a stale or corrupt cached Wi-Fi profile from the previous certificate state. These devices require the saved wireless profile to be removed and re-enrolled (sometimes through the MDM portal) before they can reconnect successfully.
    - Some older or legacy devices are disproportionately affected and may require manual reprovisioning or a profile refresh after the certificate replacement, even when newer hardware reconnects automatically.
    - In multi-site deployments, the issue may affect more than one office location if the same wireless controller or RADIUS certificate serves multiple sites.
    - Intermittent disconnections may persist briefly after the certificate is renewed, particularly while the updated certificate propagates across all nodes in the RADIUS cluster or controller group.

## Affected environment

Distribution across 34 reported cases:

- **Operating system:** Windows 10 (21%), macOS 12.6 (6%), Windows 11 (6%)
- **Device / platform:** laptop (26%), Cisco Wireless Controller (WLC) (12%), Cisco WLC 8.10 (3%)
- **Team:** Sales (29%), Engineering (15%), Employees (12%)
- **Region:** US-East (38%), EMEA (9%), US-West (9%)

## Root cause

The security certificate used by the wireless controller and RADIUS authentication service to verify its identity during corporate Wi-Fi sign-in has expired. When a device attempts to connect using the standard enterprise authentication method (EAP-TLS), the device detects that the server certificate is no longer valid and rejects the connection, or the network access control system denies the session. This prevents all devices authenticating through the affected controller from completing the wireless sign-in process and obtaining network access. In some cases, the certificate failed to update automatically during a scheduled rotation window, leaving the expired certificate in place.

## Diagnostics

Steps used to confirm this root cause:

1. Verify the endpoint has the current corporate Wi-Fi profile and certificate.  
   *Expected:* Device has the active Wi-Fi profile and valid wireless certificate.
2. Check network access control logs for authentication, posture, or VLAN assignment failures.  
   *Expected:* Device authenticates and receives the correct network access policy.
3. Review wireless controller logs for repeated disconnects or access point roaming failures.  
   *Expected:* Controller shows stable association and no repeated disconnect reason.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Generated and installed a renewed server certificate (CN=wlc-east-01.corp.internal, valid through 2028-04-25) on the wireless controller WLC-EAST-01.corp.internal with the correct trust chain (CorpCA-Intermediate → CorpCA-Root) for corporate Wi-Fi authentication. Certificate renewal performed by <PERSON> (<USER>).
2. Applied the updated certificate and trust configuration to the wireless controller WLC-EAST-01.corp.internal and propagated the change to all 12 dependent access points on the <LOCATION> 4th floor handling the Corporate SSID (CorpNet-Secure).
3. Validated in RADIUS (NAC-EAST-02.corp.internal) and controller logs that EAP-TLS authentication failures for 'certificate expired' stopped after the certificate replacement. Confirmed successful authentications for <USER> (<IP>), <USER>, and <USER> within minutes of propagation.
4. Instructed affected users including <PERSON> (<USER>) and <PERSON> (<USER>) to forget and reconnect to the Corporate Wi-Fi SSID (CorpNet-Secure) so devices would establish a fresh trusted connection profile.
5. For endpoints that still failed after reconnection, removed stale or corrupt wireless profiles and re-enrolled or reinstalled the managed network certificate/profile until authentication succeeded. This was required for <HOSTNAME> (<USER>) and <HOSTNAME> (<USER>), as well as one iOS device belonging to <USER>. All devices confirmed connected by 10:30 UTC.

**Example 2**

1. Renewed the wireless controller server certificate (CN=wlc-east-01.corp.netinfra.local) and verified the certificate chain presented for Corp-Enterprise authentication; new certificate valid through 2028-04-30, uploaded by <PERSON> (<USER>).
2. Restarted the AAA/RADIUS integration on the authentication server so the controller and authentication services began using the renewed certificate for 802.1X transactions; restart performed at 2026-05-02T15:24Z.
3. Validated successful authentication and network access with a pilot device (<HOSTNAME>, user <USER>, IP <IP>) after the certificate replacement and AAA restart — full connectivity confirmed at 15:25Z.
4. Remediated affected endpoints by having users (<USER>, <USER>, and four others in <LOCATION>) forget the Corp-Enterprise SSID and re-enroll the wireless profile, with updated certificate trust delivered through MDM for managed devices such as <HOSTNAME>.
5. Reviewed authentication and NAC logs after remediation to confirm failed certificate-expired rejects cleared and devices were again receiving normal access policy; final verification completed by <PERSON> (<USER>) at 2026-05-02T16:10Z with zero outstanding rejects for the <LOCATION> site.

## Recommendation

This issue is resolved by IT support; reference 'expired wireless controller authentication certificate' when reporting it.

---

[← Back to categories](../../index.md)
