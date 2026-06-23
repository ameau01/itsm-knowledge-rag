---
hide:
  - navigation
root_cause_id: SIB/missing-entitlement-plus-stale-inventory
family: SIB
ticket_count: 5
curated: true
self_serviceable: false
---

# Software install blocked by missing entitlement and stale device inventory

[← Back to categories](../../index.md)

## Description

Affected users attempting to install a required application from Software Center find that the application is either missing from the catalog entirely or listed with the Install button greyed out. Attempts to proceed with installation return entitlement-related error messages such as "EntitlementCheckFailed," "installation blocked," or error codes like 0x80246002 and ERR_ENT_403. The application may also be absent from Company Portal. In some cases, the app is not returned by any search in Software Center.

An initial remediation step — such as refreshing the device inventory or triggering a policy sync — may appear to partially resolve the issue by clearing a transient policy mismatch, but the application remains unavailable or blocked afterward. This can give the impression that the fix was only partially successful or that the problem has recurred. The underlying entitlement gap is not addressed by an inventory refresh alone.

The issue affects users across different applications and departments. Reported examples include finance, sales, and marketing applications on Windows 10 managed devices. In each case, the user's account is not reflected as a member of the required software entitlement group for the application, and the device's management inventory or policy data has not been updated recently — sometimes for more than 24 to 48 hours — which compounds the problem by preventing timely policy reevaluation even after the entitlement is corrected.

!!! note "Reported variations"

    - The application may appear listed in Software Center with the Install button greyed out rather than being completely absent from the catalog.
    - A prior support action may have already added entitlement access, but the change is not reflected on the device due to stale inventory, causing the issue to appear to recur.
    - Error messages vary by application and may include "EntitlementCheckFailed," error code 0x80246002, error code 0x87D00324, or ERR_ENT_403.
    - In some cases, a direct local installer attempt also fails with an entitlement block, not only the Software Center path.
    - The application may be missing from both Software Center and Company Portal simultaneously.

## Affected environment

Distribution across 5 reported cases:

- **Operating system:** Windows 10 21H2 (60%), Windows 10 (40%)
- **Device / platform:** Windows (60%), Corporate-managed endpoint (20%), PC (20%)
- **Team:** Finance (40%), Sales (20%), Engineering (20%)
- **Region:** us-west-2 (60%), US-East (20%), EMEA (20%)

## Root cause

The affected user is not assigned to the required software entitlement group in the directory, so the application deployment policy is never targeted to their device. At the same time, the device's management inventory and policy data is stale (often not synced for 24 hours or more), which prevents Software Center from recognizing any entitlement or policy changes. Both issues must be resolved together — adding the entitlement group membership alone is insufficient until the device inventory is refreshed and policy is reevaluated.

## Diagnostics

Steps used to confirm this root cause:

1. Verify whether the user is assigned to the required Contoso App entitlement group and that the assignment is synchronized.  
   *Expected:* Required entitlement group is present and synchronized to the management platform.
2. Run or review the endpoint policy evaluation and inventory refresh cycle after the blocked installation report.  
   *Expected:* The application policy is visible and targeted to the endpoint.
3. Check endpoint protection or application control logs to confirm whether security policy is actively blocking the installer.  
   *Expected:* No active protection rule blocks the approved installer.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Verified that the user <USER> (<PERSON>, <EMP_ID>) was missing membership in the required Contoso App entitlement group SG-ContosoApp-Entitlement that controls Software Center and Company Portal availability.
2. Added the user <USER> to the Contoso App entitlement group SG-ContosoApp-Entitlement and allowed the assignment to synchronize to Intune policy targeting for device <HOSTNAME>.
3. Refreshed the device inventory on <HOSTNAME> (IP <IP>) and initiated a policy evaluation cycle so the endpoint could receive the corrected application assignment for <USER>.
4. Retried the installation from Software Center on <HOSTNAME> after policy refresh and confirmed the application became visible to the user <PERSON> in both Software Center and Company Portal.
5. Validated that Contoso App installed successfully on <HOSTNAME> for <USER> and documented entitlement verification plus inventory refresh as the standard remediation path for similar blocked install cases. Notified <PERSON> at <EMAIL> of the resolution.

**Example 2**

1. Validated that FinanceTools requires membership in the "FinanceApp Entitlement" group for Software Center targeting and installer policy approval; confirmed user <USER> (<EMP_ID>) was absent from this group.
2. Added user <USER> to the required FinanceApp Entitlement group in the Azure AD/Intune entitlement mapping, as requested by manager <PERSON> (<EMAIL>).
3. Triggered a refresh of Intune device inventory on <HOSTNAME> (IP <IP>) and forced a Software Center policy/application sync on the endpoint to update stale targeting data (previous sync: 2026-03-27T22:14Z).
4. Confirmed that the FinanceTools deployment became visible in Software Center on <HOSTNAME> after entitlement and policy propagation completed at approximately 2026-03-29T08:10Z.
5. Retried the installation from Software Center on <HOSTNAME> and verified that the application installed successfully without the entitlement block. Notified <PERSON> and <PERSON> of resolution via email.

## Recommendation

This issue is resolved by IT support; reference "missing entitlement plus stale inventory" when reporting it.

---

[← Back to categories](../../index.md)
