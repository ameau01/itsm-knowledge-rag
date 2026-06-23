---
hide:
  - navigation
root_cause_id: SIB/missing-entitlement-group-membership-plus-endpoint-protection-block
family: SIB
ticket_count: 5
curated: true
self_serviceable: false
---

# Software installation blocked by missing entitlement group and endpoint protection policy

[← Back to categories](../../index.md)

## Description

Affected users attempting to install a required application from Software Center find that the application is either not visible in the catalog or that the installation fails immediately with a policy check error. Common error messages include "user not entitled," "installation blocked by Endpoint Protection," and "policy check failed: entitlement not found," with error codes such as 0x80180014, 0x87D00231, or 0x80070490. The application may also be absent from Intune or Company Portal approvals, leaving no alternative installation path available.

In some cases the installer never launches at all, with Software Center reporting that Endpoint Protection has blocked the application before execution begins. In other cases the installer starts but is immediately quarantined by the endpoint security software. Affected users typically report that colleagues on the same team already have the application installed and available, suggesting the issue is specific to the individual user's account or device rather than a broader outage.

Standard self-service troubleshooting steps — including restarting the device, restarting Software Center, clearing the configuration manager cache, and forcing an Intune sync from Company Portal or device settings — do not resolve the issue. The block persists across reboots and sync attempts because the underlying conditions require administrative changes that are outside the user's control.

!!! note "Reported variations"

    - The application may appear in Software Center but fail to install, rather than being entirely absent from the catalog.
    - Endpoint Protection may actively quarantine the installer file during execution rather than blocking it before launch.
    - The application may be missing from Intune or Company Portal approvals in addition to being blocked in Software Center, removing all self-service installation paths.
    - The specific error code displayed varies across instances (e.g., 0x80180014, 0x87D00231, 0x80070490), though all reflect the same underlying policy check failure.

## Affected environment

Distribution across 5 reported cases:

- **Operating system:** Windows 10 21H2 (100%)
- **Device / platform:** Corporate Laptop (20%), x86_64 (20%), Corporate Managed Endpoint (20%)
- **Team:** Finance (40%), Sales (20%), Marketing (20%)
- **Region:** us-east-1 (80%), EMEA (20%)

## Root cause

The issue results from two conditions acting together. First, the affected user's account is not a member of the required entitlement or deployment security group in Active Directory or Intune, so the application is not targeted to their device through normal software distribution. Second, the application's installer package has not been approved or allow-listed in the endpoint protection application control policy, causing the security software to block or quarantine the installer when it attempts to run. Both conditions must be corrected — the entitlement group membership must be added and the installer must be approved in the endpoint security policy — before the application can be successfully installed.

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

1. Verified the required SalesApp entitlement assignment in Intune endpoint management and identified that <HOSTNAME> (enrolled to <USER>, <EMP_ID>) was not a member of the SG-SalesApp-Deploy group used to target the application for deployment.
2. Added device <HOSTNAME> and user <USER> to the SG-SalesApp-Deploy entitlement group in Intune so the application would become eligible and visible in Software Center for <PERSON> at the <LOCATION> office.
3. Updated Endpoint Protection application control policy to allow the approved SalesApp installer package (SalesAppSetup.exe) that had been blocked during prior direct install attempts; change approved by <PERSON> on the security team.
4. Forced an Intune device inventory and policy sync on <HOSTNAME> (IP <IP>) to refresh group targeting, application assignment, and Endpoint Protection policy visibility on the endpoint.
5. Retried the installation from Software Center on <HOSTNAME> and confirmed SalesApp installed successfully for <USER> after policy and entitlement updates were applied. <PERSON> confirmed the application launched without issues.

## Recommendation

This issue is resolved by IT support; reference 'missing entitlement group membership plus endpoint protection block' when reporting it.

---

[← Back to categories](../../index.md)
