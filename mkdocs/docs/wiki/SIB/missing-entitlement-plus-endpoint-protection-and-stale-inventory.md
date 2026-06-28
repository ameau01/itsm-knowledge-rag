---
hide:
  - navigation
root_cause_id: SIB/missing-entitlement-plus-endpoint-protection-and-stale-inventory
family: SIB
ticket_count: 7
curated: true
self_serviceable: false
---

# Missing Entitlement, Stale Inventory, and Endpoint Protection Block Combined

[← Back to categories](../../index.md)

## Description

Affected users on managed Windows 10 Enterprise devices report that required applications are unavailable or blocked in Software Center. The target application either does not appear in the Software Center interface, appears intermittently, or is listed with a persistent "Blocked" status. When installation is attempted, users receive messages such as "blocked by policy," "blocked by Endpoint Protection," or "installation blocked by policy check," and in some cases error codes such as 0x80070490 or 0x87D1041C are returned. No download or installation proceeds, and the issue persists across Software Center restarts and device reboots.

Investigation consistently reveals three co-occurring factors on affected devices. First, the user's account is missing membership in the required Intune entitlement or deployment group, meaning the application is not correctly targeted. Second, the device's Intune inventory and policy state is stale — with the last successful check-in ranging from 48 hours to 14 days prior — preventing updated assignments from reaching the endpoint. Third, Endpoint Protection application control is actively quarantining or blocking the installer.

Correcting any single factor in isolation does not resolve the issue. In some cases, an entitlement group correction or an Intune inventory refresh temporarily restores application visibility, but the blocked state returns after a reboot because the remaining conditions have not been addressed. Resolution requires remediation of all three factors before the application becomes available and installable through Software Center.

!!! note "Reported variations"

    - In some instances, the application appears listed in Software Center but is marked with a persistent "Blocked" status and no download initiates, rather than being entirely absent from the interface.
    - One affected user received error code 0x80070490 when attempting to run the installer directly from a network deployment share rather than through Software Center.
    - One user reported error code 0x87D1041C accompanying the policy block during each installation attempt, including after an Intune inventory refresh and policy re-push.
    - In at least one case, an initial entitlement group correction was made but did not take effect on the endpoint, leading the user to reopen the ticket after rebooting and retrying without success.
    - In one case the application briefly became available after an Intune refresh but reverted to a blocked state following a device reboot, demonstrating incomplete synchronization of entitlement and assignment data.
    - One user reported the Endpoint Protection component specifically flagged the application installer file during execution, contributing to the installation failure alongside the missing entitlement.
    - The particular application blocked varies across tickets — including line-of-business applications, marketing tools, and VPN clients — but the underlying combination of missing entitlement, stale inventory, and endpoint protection block is consistent.
    - Some affected devices are located at different regional offices, and the application visibility issue may affect multiple devices assigned to the same site when entitlement and inventory conditions overlap.

## Affected environment

Distribution across 7 reported cases:

- **Operating system:** Windows 10 21H2 (57%), Windows 10 (29%), Windows 10 Enterprise (14%)
- **Device / platform:** Laptop (29%), Windows (14%), Corporate Laptop (14%)
- **Team:** Sales (29%), Marketing (29%), VPN Users (29%)
- **Region:** US-West (43%), EMEA (29%), US-East (29%)

## Root cause

Application deployment was blocked by a combination of missing Intune entitlement group membership, stale device inventory preventing current policy targeting from propagating to Software Center, and Endpoint Protection application control quarantining the installer. All three conditions had to be present simultaneously for the issue to manifest, and correcting only one or two factors was insufficient to restore normal application availability.

## Diagnostics

Steps used to confirm this root cause:

1. Verified whether the affected user was assigned to the required AcmeApp entitlement group in Intune.  
   *Expected:* Required entitlement group is present and synchronized to the management platform.
2. Reviewed device management status and policy visibility by checking the endpoint's last inventory check-in and app availability state.  
   *Expected:* The application policy is visible and targeted to the endpoint.
3. Checked endpoint protection records for quarantine or application control events affecting the AcmeApp installer.  
   *Expected:* No active protection rule blocks the approved installer.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Add the affected user <USER> (<EMP_ID>) to the AcmeApp entitlement group in Intune and verify the group membership has synchronized successfully.
2. Confirm the AcmeApp deployment is targeted to the correct user or device collection after entitlement sync completes, ensuring <USER> and <HOSTNAME> are included in the deployment scope.
3. Release the AcmeApp installer from Endpoint Protection quarantine on the affected device <HOSTNAME> and add the approved installer or package to the allow policy so it is no longer blocked — change approved by <PERSON>.
4. Trigger a device sync and inventory refresh from Intune or the endpoint management client on <HOSTNAME> (IP <IP>) so the updated application targeting is reevaluated on the device.
5. Run the client policy evaluation cycle, reopen Software Center, and confirm <PERSON> is visible and installs successfully without the policy block message on <HOSTNAME> for user <USER>.

**Example 2**

1. Reviewed Endpoint Protection application block policy events on <HOSTNAME> and confirmed the AcmeApp v4.2 installer signature (AcmeAppSetup_4.2.0.msi) was being actively blocked during launch from Software Center under EP-Application-Block-Policy.
2. Approved the AcmeApp installer signature and added AcmeAppSetup_4.2.0.msi to the allowed list in the EP-Application-Block-Policy so the package could pass application control checks. Change approved by security analyst <PERSON> (<USER>).
3. Validated deployment targeting and added user <USER>'s device <HOSTNAME> to the <PERSON> group to correct the missing software entitlement assignment for employee <EMP_ID>.
4. Forced an Intune device inventory and policy sync on <HOSTNAME> (IP <IP>) to refresh stale device state and update the endpoint's assignment and protection evaluation. Post-sync last check-in updated to 2026-03-24T17:48:00Z.
5. Retried the Software Center deployment on <HOSTNAME> after sync completion and confirmed <PERSON> v4.2 installed successfully on the affected device. User <USER> (<PERSON>) verified the application launched without issues from the <LOCATION> office.

## Recommendation

Resolved by IT by correcting entitlement group membership, forcing a device inventory synchronization and policy refresh, and clearing the Endpoint Protection application control block.

---

[← Back to categories](../../index.md)
