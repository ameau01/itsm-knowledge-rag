---
hide:
  - navigation
root_cause_id: SIB/missing-entitlement-plus-endpoint-protection-and-stale-inventory
family: SIB
ticket_count: 7
curated: true
self_serviceable: false
---

# Application install blocked by missing entitlement, stale inventory, and endpoint protection

[← Back to categories](../../index.md)

## Description

Affected users attempting to install a required application from Software Center find that the application is either not visible at all or appears intermittently but fails immediately when installation is attempted. Error messages vary but commonly include "blocked by policy," "blocked by Endpoint Protection," "installation blocked by policy check," or specific error codes such as 0x80070490 or 0x87D1041C. In some cases the application briefly appears after a sync or reboot but then disappears again or returns the same block on the next attempt.

The issue typically presents as a combination of symptoms rather than a single failure. Users may see the application listed in Software Center but receive a policy block when clicking Install, or the application may be entirely absent from the available software list. In either scenario, no download or installation progress occurs and the status remains at "Blocked" or returns a policy check failure. Attempts to install directly from a network installer path produce the same policy error.

The problem has been observed across multiple applications and office locations on managed Windows 10 devices. In several cases, affected users report that colleagues on the same floor or team were able to install the same application without difficulty, making the issue appear inconsistent. Rebooting the device, restarting Software Center, or performing a Company Portal sync does not resolve the issue on its own, and in some instances the ticket was reopened after an initial fix attempt failed to take full effect.

!!! note "Reported variations"

    - The application may appear briefly in Software Center after an inventory refresh or policy re-push but revert to a blocked or missing state after a reboot, indicating that entitlement or security changes have not fully propagated.
    - Some affected users see the application listed but blocked, while others on the same device or account find it entirely absent from Software Center, depending on the timing of stale inventory relative to the entitlement gap.
    - In certain cases the device inventory gap spans 14 days or more, significantly delaying the visibility of any corrective changes made to entitlement group membership.
    - Attempting installation via a direct network share path rather than Software Center produces the same policy block error, confirming the endpoint protection component of the issue.

## Affected environment

Distribution across 7 reported cases:

- **Operating system:** Windows 10 21H2 (57%), Windows 10 (29%), Windows 10 Enterprise (14%)
- **Device / platform:** Laptop (29%), Windows (14%), Corporate Laptop (14%)
- **Team:** Sales (29%), Marketing (29%), VPN Users (29%)
- **Region:** US-West (43%), EMEA (29%), US-East (29%)

## Root cause

The application deployment is blocked by three overlapping conditions on the affected device. First, the user or device is not a member of the required entitlement group in Intune, so the application is not properly targeted for deployment. Second, the device's inventory and policy data in Intune is stale — often days or weeks out of date — which prevents any entitlement corrections or policy changes from reaching the endpoint promptly. Third, Endpoint Protection's application control policy is actively blocking or quarantining the installer, adding a security-layer denial on top of the targeting failure. All three conditions must be resolved and re-synchronized before the application becomes available and installable.

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

This issue is resolved by IT support; reference 'application blocked by missing entitlement, stale inventory, and endpoint protection' when reporting it.

---

[← Back to categories](../../index.md)
