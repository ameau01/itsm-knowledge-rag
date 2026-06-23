---
hide:
  - navigation
root_cause_id: WCI/incorrect-nac-policy-assignment
family: WCI
ticket_count: 6
curated: true
self_serviceable: false
---

# Corporate Wi-Fi access blocked by incorrect NAC policy assignment after policy change

[← Back to categories](../../index.md)

## Description

Affected users are able to see and join the corporate Wi-Fi network, and their devices complete 802.1X authentication successfully. However, immediately after connecting, devices either show "No network access," receive limited or no internal connectivity, or are disconnected and forced to reconnect repeatedly. In many cases, the device appears connected to the corporate Wi-Fi but is silently placed onto a guest or quarantine network segment, preventing access to internal resources such as file shares, intranet portals, and business applications. EAP timeout messages and 802.1X authentication failure notifications may appear in the system tray or system event logs during reconnection attempts.

The issue typically affects multiple users and device types — including Windows laptops, iOS devices, and Android phones — across one or more floors or office locations, rather than being limited to a single device. Entire device groups or organizational units (such as Sales or Engineering teams) may be impacted simultaneously. Users in the same group generally experience the same symptoms, which helps distinguish this from an individual device or certificate problem.

Symptoms begin shortly after a scheduled or overnight network access control (NAC) policy change and do not resolve with standard troubleshooting steps such as removing and rejoining the Wi-Fi network, renewing device certificates, or rebooting. Temporary workarounds such as profile re-enrollment or manual access exceptions may briefly restore connectivity, but the issue recurs until the underlying policy configuration is corrected by the network team.

!!! note "Reported variations"

    - Some devices were assigned to a guest VLAN instead of the corporate VLAN, resulting in a valid Wi-Fi connection but no access to internal resources, rather than an outright disconnection.
    - In some cases, stale session bindings on the wireless controller caused the incorrect VLAN assignment to persist intermittently for certain devices even after a temporary policy correction was applied.
    - Some users experienced repeated EAP timeouts and 802.1X failure messages in system event logs, while others saw a stable connection with silently restricted access and no explicit error notifications.
    - The issue occasionally presented as post-authentication disconnects with rapid reconnect cycling rather than a persistent but restricted connection.

## Affected environment

Distribution across 6 reported cases:

- **Operating system:** Windows 10 (50%), mixed (Windows, iOS, Android) (17%)
- **Device / platform:** laptop (33%), Aruba WLC / ClearPass NAC (17%), ArubaOS / ClearPass (17%)
- **Team:** Sales (33%), Engineering (17%), Corporate staff and contractors (17%)
- **Region:** EMEA (50%), US-East (17%), London (17%)

## Root cause

A network access control (NAC) policy change introduced an incorrect mapping between device groups or organizational units and their intended network access policies. As a result, devices that authenticated successfully were evaluated against the wrong policy rule — such as a guest, quarantine, or deny rule — instead of the intended corporate access policy. This caused authenticated corporate devices to be placed onto a restricted network segment (e.g., a guest or quarantine VLAN) or to be denied access entirely, despite valid credentials and certificates.

## Diagnostics

Steps used to confirm this root cause:

1. Verified the laptop wireless profile state and cleared/re-enrolled the corporate Wi-Fi profile and cached 802.1X settings.  
   *Expected:* Device has the active Wi-Fi profile and valid wireless certificate.
2. Reviewed NAC authentication behavior for the affected device group and compared it against the recent policy change and rollback state.  
   *Expected:* Device authenticates and receives the correct network access policy.
3. Checked Wireless Controller behavior for reconnect attempts and repeated disconnection patterns during the affected sessions.  
   *Expected:* Controller shows stable association and no repeated disconnect reason.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Corrected the NAC policy assignment on ClearPass for the ENG-East device group so corporate laptops (including <HOSTNAME>, user <USER>) receive the intended Corp-Full-Access 802.1X authorization and network access policy after Wi-Fi join, replacing the erroneous Guest-Restricted mapping. Change performed by <PERSON> (<EMAIL>).
2. Validated the matching policy behavior on the Wireless Controller to confirm successful authentication flow and proper post-join authorization handling for the CorpNet-Secure SSID, verifying that RADIUS Accept responses were returned for ENG-East group members including <USER>.
3. Removed the temporary rollback state from the 2026-04-24 ClearPass policy change after confirming the corrected policy no longer triggered the intermittent authentication failure pattern for the ENG-East device group.
4. Reset and re-enrolled the affected laptop's (<HOSTNAME>) corporate wireless profile for user <PERSON> so stale 802.1X credentials and cached profile data did not continue to interfere with NAC policy evaluation on CorpNet-Secure.
5. Retested connectivity on <HOSTNAME> for user <USER> and confirmed stable Wi-Fi association to CorpNet-Secure (assigned IP <IP>), successful 802.1X authentication via ClearPass, and restored full network access without repeated disconnects over a 30-minute monitoring window. <PERSON> confirmed the issue was resolved at 03:45 UTC.

**Example 2**

1. Updated the ClearPass enforcement and role-mapping policy on cppm-emea-01.corplabs.internal so the Corporate device group (Role: Corp-Managed) matched the correct Corp-Allow enforcement profile instead of the Quarantine-Deny policy after successful 802.1X EAP-TLS authentication. Change performed by <PERSON> (<USER>, <EMP_ID>).
2. Validated and corrected SSID-to-policy mapping with the Wireless Controller team on WLC-FRA-02 to ensure the Corporate SSID (CorpNet-5G) was sending the expected RADIUS attributes (including NAS-Identifier and Called-Station-Id) used by ClearPass policy evaluation.
3. Removed affected endpoints — including <HOSTNAME> (<IP>) and <HOSTNAME> (<IP>) — from NAC quarantine and re-enrolled devices that had stale or mismatched posture/group state so they could be re-evaluated under the corrected Corp-Allow policy.
4. Retested representative affected clients on the Corporate SSID, including <PERSON>'s and <PERSON>'s devices, and confirmed they received normal network access (correct VLAN, full connectivity) without repeated disconnects or quarantine placement.
5. Monitored ClearPass Access Tracker and WLC-FRA-02 client events for 48 hours after the change to verify policy decisions remained consistent and no new deny mismatches were occurring for the Corporate device group. <PERSON> (<EMP_ID>) confirmed no further user reports were received.

## Recommendation

This issue is resolved by IT support; reference 'incorrect NAC policy assignment after policy change' when reporting it.

---

[← Back to categories](../../index.md)
