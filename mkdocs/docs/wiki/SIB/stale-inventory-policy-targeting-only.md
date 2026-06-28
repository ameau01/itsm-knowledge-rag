---
hide:
  - navigation
root_cause_id: SIB/stale-inventory-policy-targeting-only
family: SIB
ticket_count: 2
curated: true
self_serviceable: false
---

# Stale Endpoint Inventory and Policy State Blocking Application Deployment

[← Back to categories](../../index.md)

## Description

Affected users on Windows 10 21H2 managed endpoints experience application installation failures when attempting to deploy software through Software Center. The issue manifests as a policy check failure error (error code 0x87D13B5C) or an "Installation blocked by policy" message. In addition to the blocking error, the target application may disappear from the Available applications catalog in Software Center, preventing self-service installation entirely. Application assignments in Intune are confirmed to be correctly targeted to the affected user accounts and devices; the failure is attributable to the endpoint operating on stale inventory and policy data, causing it to fail to recognize valid deployments.

The issue has been observed to recur on the same device after earlier remediation. In one instance, a user's initial incident involving one application was resolved, but the same device subsequently exhibited the identical stale-policy condition affecting a different application. The recurrence persisted until endpoint policy data was refreshed. In both occurrences, the affected user's entitlement group membership and application targeting were verified as correct, confirming that the failure was due to outdated deployment metadata rather than any misconfiguration in assignment or identity. The failure is endpoint-specific; other devices under the same entitlement group are unaffected.

!!! note "Reported variations"

    - The blocked application may differ between occurrences on the same device (e.g., a CRM application in one instance and a sales demonstration tool in another), while the underlying stale-policy condition remains consistent.
    - Some affected users report that colleagues on other devices in the same office and entitlement group can see and install the application without issue, confirming the problem is endpoint-specific rather than tenant-wide.
    - The application may initially appear in a cached or stale Software Center listing but fail with a policy-block error on installation attempt, rather than being absent from the catalog from the outset.

## Affected environment

Distribution across 2 reported cases:

- **Operating system:** Windows 10 21H2 (100%)
- **Device / platform:** Intune / Configuration Manager managed endpoint (50%), desktop (50%)
- **Team:** Sales (100%)
- **Region:** us-west-2 (50%), NA (50%)

## Root cause

Device inventory and policy state in Intune and Software Center were stale, so the endpoint did not have current application availability or policy evaluation data. This caused the entitlement evaluation for deployed applications to fail, meaning the applications were not shown correctly in Software Center and installation attempts were blocked by policy.

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

Resolved by IT; referenced as stale endpoint inventory and policy state causing application deployment failure.

---

[← Back to categories](../../index.md)
