---
hide:
  - navigation
root_cause_id: WCI/incorrect-nac-policy-assignment
family: WCI
ticket_count: 6
curated: true
self_serviceable: false
---

# Incorrect NAC Policy Mapping Causes Post-Authentication VLAN Misassignment

[← Back to categories](../../index.md)

## Description

Affected users on managed corporate devices—including Windows laptops, iOS, and Android mobile devices—are able to associate with the corporate Wi-Fi SSID and successfully complete 802.1X (EAP-TLS or WPA2-Enterprise) authentication. However, immediately or shortly after authentication, devices either lose network access entirely, are placed into a quarantine or guest VLAN, or experience repeated disconnects. Users typically observe a brief period of apparent connectivity followed by "No network access" or "Limited connectivity" indicators, EAP timeout messages, and 802.1X authentication failure events in system logs. Reconnection attempts cycle between "authenticating" and "disconnected" states without restoring normal corporate access.

The issue consistently traces to a recent NAC policy change or scheduled configuration push. Following the update, the authorization profile mapping for one or more device groups is incorrect—valid, authenticated corporate endpoints are matched against the wrong policy rule, resulting in assignment to a quarantine role, guest VLAN, or deny profile instead of the intended corporate access profile. NAC and RADIUS session logs confirm successful authentication but show an erroneous enforcement profile being applied. The misconfiguration typically involves an altered Active Directory group-to-policy mapping or an incorrectly remapped organizational unit path.

The impact spans multiple users and device types within a given site or device group, often affecting entire floors or functional teams. In some cases the affected device obtains guest-range network connectivity that lacks access to internal resources while appearing connected. Stale VLAN bindings on the wireless controller may allow the misassignment to persist intermittently even after temporary remediation. Once the correct group-to-policy assignment is restored and stale session bindings are cleared, affected users regain full corporate network access.

!!! note "Reported variations"

    - Some affected devices are placed into a guest VLAN (receiving a guest-range IP address) rather than a quarantine VLAN, resulting in Wi-Fi connectivity but no access to internal resources such as file shares, intranet portals, or CRM systems.
    - In certain cases, 802.1X authentication itself fails outright with RADIUS reject responses, preventing devices from completing the join process rather than connecting with restricted access.
    - The issue may present as intermittent disconnects with repeated EAP timeout errors rather than a persistent quarantine or guest VLAN assignment.
    - Both managed laptops and enrolled mobile devices (iOS and Android) are affected at the same site, confirming the issue is policy-based rather than platform- or certificate-specific.
    - Removing and rejoining the wireless profile, renewing device certificates, or rebooting does not resolve the VLAN misassignment, as the fault lies in the NAC policy configuration rather than the endpoint state.
    - Contractors authenticated via the same corporate SSID are affected alongside regular staff when their accounts fall under the misconfigured group mapping.

## Affected environment

Distribution across 6 reported cases:

- **Operating system:** Windows 10 (50%), mixed (Windows, iOS, Android) (17%)
- **Device / platform:** laptop (33%), Aruba WLC / ClearPass NAC (17%), ArubaOS / ClearPass (17%)
- **Team:** Sales (33%), Engineering (17%), Corporate staff and contractors (17%)
- **Region:** EMEA (50%), US-East (17%), London (17%)

## Root cause

An incorrect Active Directory group-to-NAC policy mapping, introduced during a scheduled configuration push, caused successfully authenticated corporate endpoints to be evaluated against a quarantine, guest, or deny policy instead of the intended corporate access policy. Stale VLAN bindings on the wireless controller allowed the misassignment to persist intermittently for some devices after initial remediation attempts.

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

Resolved by IT after correcting the NAC policy group-to-VLAN mapping and clearing stale session bindings on the wireless controller.

---

[← Back to categories](../../index.md)
