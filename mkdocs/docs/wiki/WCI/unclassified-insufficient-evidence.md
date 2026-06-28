---
hide:
  - navigation
root_cause_id: WCI/unclassified-insufficient-evidence
family: WCI
ticket_count: 2
curated: true
self_serviceable: false
---

# Intermittent 802.1X Wi-Fi Rejection After Certificate Rotation and Profile Mismatch

[← Back to categories](../../index.md)

## Description

Affected users on managed Windows laptops reported intermittent failures connecting to or remaining on the corporate Wi-Fi SSID using 802.1X authentication. Devices could typically join the SSID but were then rejected by the Network Access Control system or failed to obtain an IP address, resulting in a loss of network connectivity. In some cases, connection prompts failed immediately with an authentication error, while in others devices connected briefly before dropping. The issue often required multiple reconnection attempts and was not consistently resolved by retrying alone.

Across both incidents, the scope was limited — one affected roughly seven users in a Sales group following a wireless controller certificate rotation, and the other affected approximately four to five users on a single office floor. Diagnostic evidence was mixed: some endpoints exhibited expired EAP certificates or outdated Wi-Fi profile revisions, while others with current profiles and certificates still experienced post-association drops. RADIUS and NAC logs showed sporadic 802.1X timeouts and endpoint rejections for some users but clean sessions for others on the same network, making it difficult to isolate a single failing layer.

!!! note "Reported variations"

    - Some devices received an immediate "Authentication Failed" message upon joining the SSID, rather than connecting and then losing access
    - In one incident, a wireless controller certificate rotation preceded the onset of failures; renewing the controller certificate restored service for a subset of devices but not all
    - Certain endpoints required both certificate renewal and Wi-Fi profile re-push via MDM to restore connectivity
    - RADIUS logs showed sporadic 802.1X timeouts for specific users while sessions for other users on the same SSID completed cleanly
    - One endpoint had an outdated Wi-Fi profile revision while a neighboring device with the current profile still experienced drops

## Affected environment

Distribution across 2 reported cases:

- **Operating system:** Windows 10 (50%)
- **Device / platform:** Laptop (50%), Cisco Wireless Controller (WLC) (50%)
- **Team:** Sales (50%), Corporate employees (50%)
- **Region:** US-West (50%), US-East (50%)

## Root cause

Wireless controller certificate rotation restored only part of the 802.1X trust chain. Several endpoints still carried stale corporate Wi-Fi profiles or certificate bindings, and NAC policy evaluation continued rejecting some Sales devices until profiles were re-enrolled and policy alignment was corrected. Insufficient evidence existed to confirm whether the primary cause was endpoint Wi-Fi profile inconsistency, intermittent NAC rejection, or short-lived wireless infrastructure instability.

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

**Example 1**

1. Renewed and validated the wireless controller certificate on WLC-WEST-01 so the 802.1X authentication service presented the correct server certificate chain to all connecting Sales endpoints in the <LOCATION> office.
2. Reviewed NAC authentication results for affected Sales devices (<USER>, <USER>, <USER>, and others) and confirmed policy rejections were tied to stale endpoint wireless profile or certificate state after the certificate change. <PERSON> (<USER>) from the network team verified the NAC audit logs.
3. Re-enrolled the corporate Wi-Fi profile on impacted laptops — including <HOSTNAME> and <HOSTNAME> — to refresh the SSID configuration, trust settings, and device certificate association used for 802.1X authentication. Users <USER>, <USER>, and <USER> confirmed reconnection.
4. Confirmed affected devices could authenticate successfully, receive the expected network access policy, and obtain IP addressing (verified 10.42.17.x range) after rejoining Corporate Wi-Fi. <PERSON> and <PERSON> both validated stable connectivity over a 30-minute observation window.
5. Prepared and scheduled an MDM push of the updated wireless profile targeting all Sales laptops in the <LOCATION> region, and coordinated follow-up NAC policy cleanup with <PERSON> (<USER>) so temporary exceptions can be removed without reintroducing authentication failures. Follow-up review scheduled for 2026-04-27.

**Example 2**

1. Capture fresh logs from an actively failing device (prioritize <HOSTNAME> or <USER>'s endpoint), including Wi-Fi profile state, EAP certificate validity, and exact connection timestamps, if the issue recurs. Contact <PERSON> (<EMAIL>, ext. 4-7823) or <PERSON> (<EMAIL>) to coordinate log collection.
2. Monitor NAC/RADIUS and controller events on the <LOCATION> 3rd-floor east-wing APs (AP-CLT-3E-01, AP-CLT-3E-02) during the next reported failure window to correlate authentication results with local AP behavior. Network team lead <PERSON> (<USER>) to set up enhanced logging on the WLC for the affected AP group.
3. Provide interim user guidance to affected employees (<USER>, <USER>, <USER>) to retry after forgetting and rejoining the corp-employee SSID, or move to a nearby coverage area on the 3rd floor west wing while additional evidence is gathered. For <USER>'s device, the expired certificate was renewed and the Wi-Fi profile was re-pushed to v2.4 — confirm stable connectivity at next check-in.

## Recommendation

Resolved by IT through a combination of wireless controller certificate renewal, endpoint Wi-Fi profile re-enrollment via MDM, and NAC policy realignment.

---

[← Back to categories](../../index.md)
