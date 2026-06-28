---
hide:
  - navigation
root_cause_id: WCI/expired-radius-controller-eap-tls-certificate
family: WCI
ticket_count: 34
curated: true
self_serviceable: false
---

# Expired Wireless Controller or RADIUS Certificate Blocks 802.1X Authentication

[← Back to categories](../../index.md)

## Description

Affected users across multiple office locations report that managed and personal devices (Windows, macOS, iOS, and Android) fail to authenticate to corporate Wi-Fi SSIDs. Devices detect and associate with the network but fail during the 802.1X EAP-TLS handshake, producing errors such as "authentication failed," "certificate expired," or "secure connection failed." Users are left without corporate network access, and the issue impacts large groups simultaneously — spanning multiple floors, departments, and geographic sites served by the same wireless controller or RADIUS infrastructure.

The failure consistently originates from an expired server-side TLS certificate presented during EAP authentication. Some devices fail outright and disconnect immediately, while others briefly associate and display a "Connected, no internet" or "No Internet, secured" status before losing access. In certain cases, devices obtain only a link-local address rather than a valid DHCP lease. Wireless controller, RADIUS, and NAC logs show repeated Access-Reject events with certificate-expired reason codes accumulating after the expiration timestamp. Wired connectivity and guest wireless SSIDs remain fully functional, confirming the issue is isolated to the secured corporate wireless authentication path.

Standard client-side troubleshooting — including rebooting devices, forgetting and rejoining the SSID, or re-entering credentials — does not restore connectivity while the expired certificate remains in place. The onset of failures frequently coincides with a scheduled certificate rotation window during which the renewed certificate was not properly applied or the prior certificate was allowed to lapse.

!!! note "Reported variations"

    - Some devices displayed explicit certificate trust warnings or 802.1X certificate problem alerts (particularly on mobile devices), while others showed only generic authentication failure messages or disconnected silently
    - In at least one instance, the expired certificate was an intermediate certificate in the authentication chain rather than the primary server certificate
    - The issue affected EAP-PEAP authentication in addition to EAP-TLS at some sites, as the expired server certificate impacted both methods
    - BYOD devices (personal smartphones and tablets) were affected alongside managed laptops, with both device types failing identically
    - In multi-node RADIUS cluster deployments, all cluster members presented the same expired certificate, causing site-wide authentication rejection rather than a partial outage
    - At certain sites the certificate expired minutes before a scheduled certificate refresh window opened, creating a narrow gap during which no valid certificate was in place
    - Affected devices sometimes obtained an APIPA (link-local) address instead of a valid DHCP lease, indicating authentication was rejected before network access was granted
    - A subset of endpoints required Wi-Fi profile removal and certificate re-enrollment (sometimes via MDM) after the infrastructure certificate was renewed, due to retained stale trust or profile state on the endpoint

## Affected environment

Distribution across 34 reported cases:

- **Operating system:** Windows 10 (21%), macOS 12.6 (6%), Windows 11 (6%)
- **Device / platform:** laptop (26%), Cisco Wireless Controller (WLC) (12%), Cisco WLC 8.10 (3%)
- **Team:** Sales (29%), Engineering (15%), Employees (12%)
- **Region:** US-East (38%), EMEA (9%), US-West (9%)

## Root cause

The TLS server certificate used by the wireless controller or RADIUS infrastructure for 802.1X EAP-TLS authentication expired, causing all client certificate validation attempts to fail. The RADIUS service continued presenting the expired certificate during EAP handshakes, resulting in Access-Reject responses and NAC denial for every authenticating endpoint. In some incidents, the expiration occurred during or immediately before a scheduled certificate rotation window, indicating the renewed certificate was not applied before the prior certificate lapsed.

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

The issue was resolved after the expired wireless controller and RADIUS server certificate was renewed and applied to the authentication infrastructure, with affected endpoint profiles remediated where necessary.

---

[← Back to categories](../../index.md)
