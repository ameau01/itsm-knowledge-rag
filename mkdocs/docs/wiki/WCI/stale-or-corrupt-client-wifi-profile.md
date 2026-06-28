---
hide:
  - navigation
root_cause_id: WCI/stale-or-corrupt-client-wifi-profile
family: WCI
ticket_count: 5
curated: true
self_serviceable: false
---

# Corrupted Endpoint Wireless Profile Causes Intermittent 802.1X Authentication Failure

[← Back to categories](../../index.md)

## Description

Affected users on Windows 10 laptops report that their devices successfully associate with the corporate Wi-Fi SSID but lose network access shortly after joining — typically within one minute. The wireless adapter displays a status of "Connected, no network access" or "No Internet," and internal resources such as wikis, repositories, file shares, and email become unreachable. Rebooting or forgetting and rejoining the SSID may temporarily restore connectivity, but the failure recurs within minutes to roughly 30 minutes. The issue is device-specific; personal devices and other corporate endpoints on the same floor and access points connect without difficulty.

Investigation consistently reveals a stale or corrupted client-side wireless profile on the affected endpoint. The local 802.1X supplicant references outdated certificate thumbprints or retains cached authentication state that causes EAP-TLS negotiation to fail after initial association. Wireless controller and RADIUS/NAC logs confirm dropped 802.1X sessions — typically with a "Session-Timeout" reason or an outright Access-Reject — along with stale entries in the NAC session table for the affected device. Prior remediation attempts such as certificate renewals provide only temporary relief when the underlying profile corruption is not fully addressed.

The issue has been observed on individual endpoints as well as in small clusters of managed laptops (up to approximately six devices) on the same office floor, particularly following scheduled wireless profile updates or certificate renewal events. In multi-device occurrences, the root cause traces to endpoint configuration drift where devices lack the current managed Wi-Fi profile and consequently fail NAC evaluation, rather than a broader infrastructure outage.

!!! note "Reported variations"

    - Some affected devices experience intermittent disconnects specifically when roaming near certain access points, with transient controller-side instability observed during the recovery window but normalizing after endpoint remediation.
    - In a subset of cases, the issue resurfaces the day after a prior certificate renewal that had only temporarily restored service, indicating the renewed certificate alone did not resolve the underlying stale profile state.
    - A small cluster of managed laptops on the same office floor may be affected simultaneously following a scheduled wireless profile update, presenting as endpoint configuration drift rather than an isolated single-device problem.
    - Some devices receive an outright RADIUS Access-Reject during EAP-TLS authentication rather than connecting briefly before losing access.

## Affected environment

Distribution across 5 reported cases:

- **Operating system:** Windows 10 (80%)
- **Device / platform:** laptop (80%), Cisco WLC 8.10 (20%)
- **Team:** Engineering (40%), Finance (20%), Sales (20%)
- **Region:** us-east-1 (60%), EMEA (40%)

## Root cause

A corrupted or stale corporate wireless profile on the endpoint retained outdated certificate thumbprints and cached supplicant state, causing inconsistent 802.1X EAP-TLS authentication. This prevented full NAC authorization and resulted in repeated session drops or access rejections by the RADIUS infrastructure. In multi-device cases, scheduled profile updates introduced configuration drift across a subset of managed laptops.

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

1. Removed the existing Corporate Wi-Fi profile from the affected laptop (<HOSTNAME>, user <USER>) to clear corrupted supplicant settings and the outdated certificate thumbprint that was causing EAP-TLS negotiation failures.
2. Re-enrolled the device to the CorpWiFi-5G SSID using the standard Onboarding Client flow and confirmed the active corporate Wi-Fi profile and valid wireless certificate were present and matched the current issuing CA thumbprint.
3. Cleared the device's stale wireless/NAC session (MAC 4C:77:A3:1E:9D:02) on WLC-EAST-01 so the endpoint could establish a fresh authenticated 802.1X session and receive the correct Engineering VLAN (VLAN 142) assignment.
4. Reconnected the laptop to Corporate Wi-Fi and verified that network access remained available beyond the previous one-minute failure window — confirmed stable connectivity for over 15 minutes with successful pings to gateway <IP> and internal resource access.
5. Advised the user (<USER>) to report recurrence immediately to the Wireless Team or contact agent <PERSON> at <EMAIL> / <PHONE> so the team can review roaming or controller-side behavior on WLC-EAST-01 if the issue returns.

**Example 2**

1. Removed the existing corporate Wi-Fi profile (CorpWiFi-5G) from the Windows 10 endpoint <HOSTNAME> and cleared locally cached wireless authentication data tied to the affected SSID, including the stale client certificate for CN=<USER>,OU=Finance,DC=corp,DC=internal.
2. Re-enrolled the laptop <HOSTNAME> with the corporate Wi-Fi onboarding process to deploy a fresh wireless profile and valid client certificate for EAP-TLS authentication under user <USER>. New certificate was issued and bound to the CorpWiFi-5G profile successfully.
3. Cleared stale session state for MAC 5C:E0:C5:3A:17:D2 (<USER>) on the RADIUS/NAC side (nac-east-01.corp.internal) so the endpoint could perform a clean authentication attempt without prior cached session conflicts. This was performed by <PERSON> on the network team.
4. Retested wireless connectivity by reconnecting <HOSTNAME> to the Corporate Wi-Fi SSID (CorpWiFi-5G) and verified successful 802.1X authentication, correct Finance VLAN 142 policy application, and DHCP address assignment (<IP>). <PERSON> confirmed access to internal finance applications and file shares.
5. Confirmed user <USER> (<PERSON>) could maintain stable network access after multiple reconnect and roaming tests across 4th-floor APs in the <LOCATION> office, and documented follow-up recommendation for broader scheduled profile refresh on similar Finance group endpoints to prevent recurrence.

## Recommendation

Resolved by IT through removal and re-provisioning of the corrupted corporate wireless profile and clearance of stale NAC session state on the affected endpoints.

---

[← Back to categories](../../index.md)
