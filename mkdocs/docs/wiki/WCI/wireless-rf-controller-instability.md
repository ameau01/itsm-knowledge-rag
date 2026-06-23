---
hide:
  - navigation
root_cause_id: WCI/wireless-rf-controller-instability
family: WCI
ticket_count: 1
curated: true
self_serviceable: false
---

# Wi-Fi session drops caused by wireless access point radio instability

[← Back to categories](../../index.md)

## Description

Affected users experience repeated disconnections from the corporate Wi-Fi network (CorpNet-5G) shortly after successfully connecting. Laptops are able to join the wireless network and initially appear connected, but within two to five minutes the connection drops. This cycle of connecting and disconnecting repeats each time the user attempts to rejoin, interrupting access to internal applications such as Salesforce and the corporate intranet.

The issue is localized to a specific floor or area rather than affecting all wireless users across the organization. Users in nearby areas of the same building typically remain unaffected. Multiple users in the impacted zone report the same pattern simultaneously, and the disruptions are concentrated within a narrow time window.

Some users may be able to maintain a brief connection before being dropped again, while others find that repeated reconnection attempts are necessary to regain even temporary access. The laptops do not display a traditional authentication failure message — the Wi-Fi association appears to succeed before the session is abruptly terminated.

!!! note "Reported variations"

    - Some affected devices may show a connected status with no internet access or no assigned IP address rather than a full disconnection.
    - Devices may silently roam back and forth between two or more degraded access points every one to three minutes, making the issue appear intermittent rather than a complete outage.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** Windows 10 (100%)
- **Device / platform:** Laptop (100%)
- **Team:** Sales (100%)
- **Region:** US-West (100%)

## Root cause

Wireless access points serving the affected area became unstable, causing the wireless controller to repeatedly disconnect (deauthenticate) client devices shortly after they successfully joined the network. Although users were passing authentication correctly, the access points' radio-level health issues triggered forced disconnections unrelated to any credential, certificate, or network access policy problem. Affected devices were continuously bouncing between the degraded access points, preventing a stable session from being maintained.

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

This issue is resolved by IT support; reference "wireless AP radio instability" when reporting it.

---

[← Back to categories](../../index.md)
