---
hide:
  - navigation
root_cause_id: WCI/wireless-rf-controller-instability
family: WCI
ticket_count: 1
curated: true
self_serviceable: false
---

# Wireless AP Radio Instability Causing Repeated Client Deauthentication

[← Back to categories](../../index.md)

## Description

Affected users on a single floor of an office building reported that their managed Windows 10 laptops could successfully join the corporate 5 GHz Wi-Fi SSID but were repeatedly dropped within two to five minutes of connecting. The disconnections interrupted access to internal applications and the corporate intranet. Users could sometimes reconnect briefly, but the cycle of association followed by disconnection recurred persistently. The issue was concentrated to one floor and did not affect wireless users on other floors or at other sites.

Initial investigation considered certificate renewal and 802.1X authentication problems, but diagnostic analysis confirmed that clients were authenticating correctly against RADIUS. Controller-side logs revealed unstable behavior on two specific access points serving the affected floor. These APs were issuing repeated deauthentication events with reason code 6 (Class 2 frame received from nonauthenticated station) shortly after client association. Affected devices were observed bouncing between the two unstable APs every one to three minutes, preventing any sustained network session.

The issue presented as a localized connectivity disruption tied to radio and controller instability rather than a broader authentication or network access control failure. Multiple members of the same team on the affected floor reported identical symptoms during a narrow time window, while colleagues on adjacent floors remained unaffected.

!!! note "Reported variations"

    - Some affected laptops appeared connected to the SSID but had no network access or no IP address assigned, rather than being fully disconnected.
    - A subset of users required multiple manual reconnection attempts before achieving even brief connectivity.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** Windows 10 (100%)
- **Device / platform:** Laptop (100%)
- **Team:** Sales (100%)
- **Region:** US-West (100%)

## Root cause

Wireless access point or controller radio instability in the affected area caused repeated client deauthentication and session drops after otherwise successful Wi-Fi authentication.

## Diagnostics

Steps used to confirm this root cause:

1. Verify affected laptops have the current corporate Wi-Fi profile and valid certificate binding for 802.1X authentication.  
   *Expected:* Device has the active Wi-Fi profile and valid wireless certificate.
2. Review NAC authentication logs for rejected Sales devices to identify certificate, posture, or policy assignment failures.  
   *Expected:* Device authenticates and receives the correct network access policy.
3. Check wireless controller logs and post-renewal behavior for repeated disconnects and authentication stability after certificate replacement.  
   *Expected:* Controller shows stable association and no repeated disconnect reason.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

1. Escalate to the wireless infrastructure team (network engineer <PERSON>, <EMAIL>) to remediate the unstable APs AP-PDX-3F-04 and AP-PDX-3F-06 or controller radio conditions affecting the <LOCATION> Building C 3rd floor.
2. Remove or restart the affected APs (AP-PDX-3F-04 and AP-PDX-3F-06) from service as needed and correct the underlying controller or RF issue on WLC-PDX-01.corp.internal causing repeated deauth events. <PERSON> disabled both APs and rebalanced 3rd-floor clients to adjacent healthy APs while scheduling hardware replacement.
3. Verify clients in the affected <LOCATION> 3rd-floor location can stay associated and maintain normal network access without repeated disconnects. Confirmed with <PERSON> (<USER>), <PERSON> (<USER>), and <PERSON> (<USER>) that their laptops maintained stable Wi-Fi connectivity for over 30 minutes after the AP remediation, with no further deauth events observed in controller logs.

## Recommendation

Resolved by IT after identifying and addressing access point radio instability on the affected floor; reference wireless AP deauthentication and session drop issue.

---

[← Back to categories](../../index.md)
