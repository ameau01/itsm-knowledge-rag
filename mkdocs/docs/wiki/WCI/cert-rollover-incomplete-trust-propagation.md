---
hide:
  - navigation
root_cause_id: WCI/cert-rollover-incomplete-trust-propagation
family: WCI
ticket_count: 5
curated: true
self_serviceable: false
---

# Incomplete EAP-TLS Certificate Propagation Across Wireless Controller Cluster

[← Back to categories](../../index.md)

## Description

Affected users across multiple offices report that managed Windows, macOS, and Android devices fail to authenticate or maintain connectivity on the corporate Wi-Fi SSID following a scheduled wireless certificate rollover. Devices attempting 802.1X/EAP-TLS authentication receive errors such as "EAP-TLS certificate expired," "certificate verification failed," or "Access denied by NAC," and are either unable to join the network or briefly associate before losing all network access. The issue affects users across multiple floors, teams, and device platforms simultaneously.

Investigation consistently reveals that the wireless controller's RADIUS server certificate has either expired or was not fully propagated to all nodes in the controller cluster after renewal. In some cases the renewed certificate is present on the primary controller but absent from secondary cluster members, causing authentication failures to persist even after an initial partial restoration of service. NAC and RADIUS logs confirm EAP-TLS trust chain errors as the root cause of client denials, with affected devices referencing stale or expired certificate data during the authentication handshake.

After the correct certificate is deployed across all controller nodes and authentication services are restarted, most devices reconnect successfully. However, a subset of endpoints — particularly older clients or those with cached wireless profiles — continue to fail until the locally stored Wi-Fi profile is manually removed and the device is re-enrolled or rejoined to the corporate SSID. Temporary NAC exceptions may briefly restore access but do not resolve the underlying authentication failure.

!!! note "Reported variations"

    - Some devices associate to the SSID and briefly obtain a DHCP lease before access is revoked, while others fail authentication immediately and never receive an IP address.
    - A subset of Windows laptops require full wireless profile re-enrollment even after the server-side certificate is corrected, due to cached stale certificate references in the local supplicant configuration.
    - In multi-node controller clusters, service may be restored for users authenticating through the primary controller while users roaming to or served by secondary nodes continue to experience failures.
    - Temporary NAC policy exceptions provide short-lived connectivity but fail to persist across reconnection attempts the following day.
    - Android and older client devices are disproportionately likely to require a manual forget-and-rejoin cycle compared to newer Windows or macOS endpoints.

## Affected environment

Distribution across 5 reported cases:

- **Operating system:** mixed (Windows 10, macOS 11, Android 11) (20%), Windows 10 / macOS 12 (mixed) (20%), Windows 10, macOS 12 (mixed) (20%)
- **Device / platform:** Cisco AireOS/WLC cluster (20%), Corporate mixed Windows/macOS endpoint fleet (20%), Corporate laptops and BYOD (20%)
- **Team:** Engineering and Sales (20%), Engineering and Sales (Corp devices) (20%), Knowledge Workers (20%)
- **Region:** Building A - Floors 2-3 (20%), us-east-1 (20%), EMEA - London office (20%)

## Root cause

The renewed EAP-TLS server certificate and trust chain were not fully propagated across all wireless controller cluster nodes and the NAC/RADIUS authentication infrastructure after a scheduled certificate rotation. As a result, some authentication paths continued to present or validate against expired certificate data, causing 802.1X failures. A subset of managed endpoints also retained stale or corrupt corporate Wi-Fi profiles, perpetuating certificate validation errors even after the primary controller was updated.

## Diagnostics

Steps used to confirm this root cause:

1. Verify affected endpoints have the current Corporate Wi-Fi profile and trust the active wireless certificate chain.  
   *Expected:* Device has the active Wi-Fi profile and valid wireless certificate.
2. Review NAC and 802.1X authentication logs for certificate validation, authentication, and policy assignment outcomes.  
   *Expected:* Device authenticates and receives the correct network access policy.
3. Review wireless controller cluster logs for certificate state, repeated disconnects, and reauthentication behavior after the certificate change.  
   *Expected:* Controller shows stable association and no repeated disconnect reason.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Validated the renewed wireless certificate chain on the primary controller WLC-LON-PRIMARY and confirmed the correct server certificate (CN=wifi.corplabs.com, issued 2026-04-26) and trust chain were present for EAP-TLS authentication. Verification performed by <PERSON> (<USER>).
2. Pushed the renewed certificate and related trust chain to all secondary wireless controller nodes (WLC-LON-SEC02, WLC-LON-SEC03) and verified cluster-wide certificate consistency after service synchronization completed at 06:28 UTC on 2026-04-27.
3. Reviewed Cisco ISE (ise-lon-01.corplabs.internal) and controller authentication logs to confirm failed sessions for <USER>, <USER>, and <USER> were tied to expired-certificate presentation or validation mismatch on nodes that had not fully updated prior to the sync.
4. Removed stale or corrupt Corporate Wi-Fi profiles from affected Windows and macOS endpoints — including <HOSTNAME> (<PERSON>), <HOSTNAME> (<PERSON>), and <HOSTNAME> (<PERSON>) — then re-enrolled devices to the CorpWiFi SSID so the supplicant could rebuild the 802.1X configuration against the current certificate chain.
5. Used the temporary NAC allowance only during the propagation window (approx. 05:50–06:35 UTC), then verified successful EAP-TLS handshakes for all three affected users and restored normal access enforcement after all controller nodes and test clients authenticated successfully. Final confirmation provided by <PERSON> and desktop support lead <PERSON> (<USER>, <EMP_ID>).

**Example 2**

1. Validated and corrected the renewed wireless/RADIUS certificate chain presented by the controller so the full trust chain matched endpoint and NAC expectations after the rollover. <PERSON> verified the intermediate CA was properly included in the chain.
2. Restarted wireless controller authentication services to ensure the updated certificate and chain were actively loaded for new client authentications.
3. Reviewed NAC authentication results and confirmed affected devices (<HOSTNAME>, MACBOOK-KOSEI-12, and others) were being denied during 802.1X/EAP-TLS evaluation rather than at DHCP or RF association stages.
4. Remediated impacted endpoints by refreshing the corporate Wi-Fi profile and re-enrolling device certificates on clients that still held stale trust or profile data after the rollover. Desktop support technician <PERSON> handled the on-site re-enrollment for floors 3-4.
5. Had affected users — including <PERSON> and <PERSON> — forget and reconnect to the corporate SSID, then verified successful NAC authorization and IP assignment on previously failing devices. Both <HOSTNAME> and MACBOOK-KOSEI-12 received valid DHCP leases and full network access.

## Recommendation

Resolved by IT after fully propagating the renewed EAP-TLS certificate across all wireless controller cluster nodes, restarting authentication services, and re-enrolling affected endpoint Wi-Fi profiles.

---

[← Back to categories](../../index.md)
