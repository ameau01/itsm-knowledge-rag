---
hide:
  - navigation
root_cause_id: SIB/missing-entitlement-plus-stale-inventory
family: SIB
ticket_count: 5
curated: true
self_serviceable: false
---

# Missing Entitlement Group Membership Combined With Stale Device Inventory

[← Back to categories](../../index.md)

## Description

Affected users on corporate-managed Windows endpoints attempt to install a required application from Software Center but find it either missing from the catalog entirely or listed with the Install button greyed out. When the application is visible and installation is attempted, an entitlement policy failure is returned — reported variously as "EntitlementCheckFailed," an entitlement-related error code, or an "installation blocked" message referencing an entitlement check against the user's account. The application may also be absent from Company Portal with no actionable error displayed. Rebooting and retrying does not resolve the issue.

Investigation reveals two contributing factors. The affected user's account is not a member of the required application-specific entitlement group in Azure AD, so the Intune deployment policy does not target the user or device and the application is not offered or installable. Concurrently, the device's Intune inventory and policy state is stale — last-sync timestamps are often 24 hours or more old — meaning that even after entitlement group membership is corrected, updated policy is not reflected on the endpoint until a manual inventory and policy refresh is performed.

In some cases a prior support action had already added the user to the correct entitlement group, but the change did not propagate to the device due to the stale inventory state, causing the issue to persist or recur. The combination of missing entitlement assignment and outdated device policy sync prevents Software Center from presenting the application as available or allowing installation to proceed.

!!! note "Reported variations"

    - The application appears in Software Center but with the Install button disabled and an explicit entitlement policy failure code displayed upon retry.
    - The application is completely absent from both Software Center and Company Portal, with no error message surfaced to the user.
    - A direct local installer attempt outside Software Center also fails, returning "installation blocked" with an entitlement check error code.
    - The device shows a recent Company Portal sync timestamp, yet Intune inventory remains stale and does not reflect the user's current group membership or role changes.
    - A previous entitlement remediation was applied but the issue returned because the device policy state was not refreshed to reflect the updated group membership.
    - The installation attempt returns a general download or install error code alongside the underlying entitlement policy check failure.

## Affected environment

Distribution across 5 reported cases:

- **Operating system:** Windows 10 21H2 (60%), Windows 10 (40%)
- **Device / platform:** Windows (60%), Corporate-managed endpoint (20%), PC (20%)
- **Team:** Finance (40%), Sales (20%), Engineering (20%)
- **Region:** us-west-2 (60%), US-East (20%), EMEA (20%)

## Root cause

The affected user was not a member of the required application entitlement group in Azure AD, so the deployment policy was not targeted to the endpoint. A stale Intune device inventory and policy state further obscured the issue by preventing updated group membership from being reflected on the device, causing Software Center policy evaluation to continue failing the entitlement check even after the initial access correction.

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

Resolved by IT after adding the affected user to the required entitlement group and refreshing stale device inventory and policy state so Software Center correctly reflected the updated deployment targeting.

---

[← Back to categories](../../index.md)
