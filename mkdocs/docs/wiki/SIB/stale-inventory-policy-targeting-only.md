---
hide:
  - navigation
root_cause_id: SIB/stale-inventory-policy-targeting-only
family: SIB
ticket_count: 2
curated: true
self_serviceable: false
---

# Software Center application hidden by stale device inventory and policy state

[← Back to categories](../../index.md)

## Description

Affected users find that a required application is missing from the Available applications list in Software Center, even though the application has been correctly assigned to their account. Attempts to install the application from a previously cached listing fail with a policy check error, such as "Installation blocked by policy" or error codes like 0x87D13B5C or 0x87D1041C. The issue is specific to the affected device; colleagues on other machines with the same entitlements can see and install the application without difficulty.

In some cases the application disappears from the Software Center catalog entirely after an earlier remediation, and subsequent installation attempts continue to be blocked. The device may not have completed a successful policy sync for an extended period (72 hours or more), causing it to operate on outdated deployment and availability data. The issue has been observed on Windows 10 21H2 managed endpoints across multiple office locations.

!!! note "Reported variations"

    - The application may initially appear in a cached listing but fail to install, rather than being absent from the catalog from the outset.
    - The error code displayed may vary (e.g., 0x87D13B5C or 0x87D1041C) depending on the specific policy evaluation failure encountered.
    - The issue may recur on the same device after a prior remediation if the policy sync does not complete successfully.

## Affected environment

Distribution across 2 reported cases:

- **Operating system:** Windows 10 21H2 (100%)
- **Device / platform:** Intune / Configuration Manager managed endpoint (50%), desktop (50%)
- **Team:** Sales (100%)
- **Region:** us-west-2 (50%), NA (50%)

## Root cause

The device's inventory and policy state in the management platform (Intune / Software Center) had become stale, meaning the endpoint was not reflecting current application availability or policy evaluation data. Because the local client was working from outdated deployment metadata, it could not correctly determine that the user was entitled to the application, causing it to be hidden from the catalog and blocking installation attempts with a policy error. Refreshing the device inventory, triggering a policy sync, and clearing the local client cache resolved the stale data and restored normal application visibility and installation.

## Diagnostics

Steps used to confirm this root cause:

1. Verify the affected user/device is included in the required Acme CRM entitlement or assignment group in the management platform.  
   *Expected:* Required entitlement group is present and synchronized to the management platform.
2. Review and trigger the endpoint policy evaluation cycle to confirm the Acme CRM deployment is visible to the client.  
   *Expected:* The application policy is visible and targeted to the endpoint.
3. Check endpoint protection or application control indications to determine whether an active security rule is blocking the approved installer.  
   *Expected:* No active protection rule blocks the approved installer.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Forced a device sync/inventory refresh on <HOSTNAME> (IP <IP>) so the endpoint could pull current application assignment and policy data from Intune for user <USER>.
2. Reviewed the Acme CRM deployment assignment in Intune and confirmed the affected user <USER> (<EMP_ID>) in the Sales group was properly targeted for application availability.
3. Triggered and reviewed policy evaluation on <HOSTNAME> to confirm the Acme CRM application policy became visible to the client after the sync cycle completed.
4. Cleared the local Software Center/Configuration Manager application cache at C:\Windows\ccmcache on <HOSTNAME> to remove stale deployment metadata that was contributing to the 0x87D13B5C policy check failure.
5. Retried the install from Software Center on <HOSTNAME> after policy refresh and confirmed Acme CRM appeared in Available apps and installed successfully. Notified <PERSON> at <EMAIL> that the issue was resolved.

**Example 2**

1. Verified the user <USER> (<EMP_ID>) remained in the required SalesTool entitlement group (SG-SalesTool-Users) and confirmed the application assignment was still targeted through the management platform via the Intune admin portal.
2. Initiated a manual Intune device sync to refresh the affected endpoint inventory on <HOSTNAME> (IP <IP>) and update the device state used for application entitlement evaluation.
3. Forced a Software Center machine policy retrieval and application evaluation cycle on the endpoint <HOSTNAME> to refresh available app targeting and deployment policy for user <USER>.
4. Confirmed the SalesTool v2.1 deployment was published correctly to the <LOCATION> region device collection and that no lingering stale policy state was preventing the application from appearing in Software Center for <USER>.
5. Retried the installation from Software Center on <HOSTNAME> after the refresh cycles completed and verified the application installed successfully on the device; <PERSON> confirmed SalesTool v2.1 is now operational.

## Recommendation

This issue is resolved by IT support; reference "stale inventory policy targeting" when reporting it.

---

[← Back to categories](../../index.md)
