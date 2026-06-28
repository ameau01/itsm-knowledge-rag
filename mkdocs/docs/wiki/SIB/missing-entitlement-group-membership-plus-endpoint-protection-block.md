---
hide:
  - navigation
root_cause_id: SIB/missing-entitlement-group-membership-plus-endpoint-protection-block
family: SIB
ticket_count: 5
curated: true
self_serviceable: false
---

# Missing Entitlement Group Membership With Endpoint Protection Blocking

[← Back to categories](../../index.md)

## Description

Affected users on corporate-managed Windows endpoints attempt to install a required application through Software Center but encounter installation failures. The application either does not appear in the Software Center catalog at all or is visible but immediately blocked when installation is attempted. Common error messages include "user not entitled" (error 0x80180014), "policy check failed" (errors 0x87D00231 and 0x80070490), and "entitlement not found." Standard self-remediation steps such as restarting the device, restarting Software Center, clearing the SCCM cache, and forcing an Intune sync do not resolve the issue. Colleagues in the same team or role have the application available and can install it without difficulty.

Investigation consistently reveals that the affected user's Active Directory account is missing from the security group used to target the application deployment. Because group membership is the criterion for Intune or SCCM policy targeting, the application is either not offered to the device or fails policy evaluation during installation.

In most cases, a compounding factor is also identified: Endpoint Protection on the device actively blocks or quarantines the application installer due to application control policy. This manifests as quarantine notifications from the endpoint protection agent, installer hash denials, or policy check failures that prevent the installer from launching. The endpoint protection block is frequently discovered as a secondary condition that must also be addressed before installation can succeed. In some instances, however, the missing group membership alone accounts for the failure, and endpoint protection approval is noted only as a precautionary verification step.

!!! note "Reported variations"

    - The application is completely absent from the Software Center catalog rather than visible but blocked, with Intune showing the device is not targeted for the app.
    - Endpoint Protection quarantines the installer on execution, producing a visible security notification on the device in addition to the policy check failure.
    - The installer is denied before it ever launches, with Software Center displaying "Installation blocked by Endpoint Protection" and no installer window appearing.
    - The application is visible in Software Center but absent from Intune app approvals under the user's account, indicating a gap between deployment visibility and entitlement targeting.
    - A direct installation attempt from a network share fails with a PolicyCheckFailed error, bypassing Software Center but encountering the same underlying policy restriction.

## Affected environment

Distribution across 5 reported cases:

- **Operating system:** Windows 10 21H2 (100%)
- **Device / platform:** Corporate Laptop (20%), x86_64 (20%), Corporate Managed Endpoint (20%)
- **Team:** Finance (40%), Sales (20%), Marketing (20%)
- **Region:** us-east-1 (80%), EMEA (20%)

## Root cause

The affected user's Active Directory account was not a member of the required application entitlement security group, so the deployment was not targeted correctly and the application remained unavailable or failed policy evaluation. Concurrently, Endpoint Protection application control policy blocked or quarantined the installer, requiring separate security approval and policy refresh before installation could proceed.

## Diagnostics

Steps used to confirm this root cause:

1. Verify whether the affected user is assigned to the required FinanceApp entitlement group.  
   *Expected:* Required entitlement group is present and synchronized to the management platform.
2. Review endpoint policy evaluation after Intune sync and client refresh to confirm app targeting visibility.  
   *Expected:* The application policy is visible and targeted to the endpoint.
3. Check whether endpoint protection or application control requires approval before the installer can run.  
   *Expected:* No active protection rule blocks the approved installer.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Add user <USER> (EMP ID <EMP_ID>) to the Finance-App-Entitlements security group in Active Directory required for FinanceApp deployment, as performed by <PERSON>.
2. Verify the new group membership for <USER> has synchronized to Intune and SCCM (allow up to 30 minutes for AAD Connect delta sync) so the FinanceApp application becomes targeted to the user's managed device <HOSTNAME>.
3. Review Endpoint Protection or application control status for FinanceApp on <HOSTNAME> and approve or allowlist the installer if a security approval is pending in the Endpoint Protection console.
4. Trigger a device sync and policy evaluation cycle from Intune or Software Center on <HOSTNAME> (IP <IP>), then refresh Software Center application inventory on the endpoint to pull the updated targeting.
5. Retry the FinanceApp installation on <HOSTNAME> after policy refresh and confirm the application is visible in Software Center and no longer returns the entitlement error 0x80180014. Notify <USER> at <EMAIL> upon completion.

**Example 2**

1. Review the Endpoint Protection or application control block event for the Contoso Secure Client installer (ContosoSecureClient_4.7.2_x64.msi) on <HOSTNAME> and confirm the installer or publisher is being denied by current security policy. Cross-reference the deny event logged at 08:22 UTC on the endpoint.
2. Escalate to the <PERSON> or security administration team (<PERSON>, <USER>) to approve the installer signature or whitelist the approved publisher for the managed deployment package of Contoso Secure Client v4.7.2 across EMEA-managed endpoints.
3. Verify the user <USER> (<EMP_ID>) or device <HOSTNAME> is assigned to the required 'SG-ContosoSecureClient-EMEA' entitlement group and add the missing entitlement if it is not present. Confirm group membership replication in the Intune portal.
4. Force a policy and inventory refresh in Intune on <HOSTNAME> after the security allow rule and entitlement update have replicated to the endpoint. Verify the new policy assignment appears in the device sync log.
5. Retry the installation of Contoso Secure Client from Software Center on <HOSTNAME> and confirm the application installs without the Endpoint Protection policy check failure. Notify <EMAIL> upon successful completion.

## Recommendation

Resolved by IT by adding the affected user to the required entitlement security group and ensuring Endpoint Protection approval and policy synchronization were completed.

---

[← Back to categories](../../index.md)
