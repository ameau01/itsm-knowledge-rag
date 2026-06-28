---
hide:
  - navigation
root_cause_id: SIB/missing-entitlement-group-membership
family: SIB
ticket_count: 11
curated: true
self_serviceable: false
---

# Missing Entitlement Group Membership Blocks Application Install

[← Back to categories](../../index.md)

## Description

Affected users report that a required business application is missing from the Software Center or Company Portal catalog and cannot be installed through normal self-service deployment. When installation is attempted—via a direct link, alternate install path, or after a manual catalog refresh—the request is blocked with an entitlement or policy error. Observed messages include "Entitlement check failed: user/device not authorized," "Not available for this user," "Installation blocked by policy," and "Installation blocked: entitlement check failed." Associated error codes and statuses seen in client logs or on-screen include 0x87D00231, 0x80180014, 0x87D00607, 0x87D1061E, 0xE000020B, and POLICY_CHECK_FAILED.

In some cases the application is entirely absent from the catalog with no error shown until a direct install is attempted. In others, the application appears after a Software Center refresh but still fails on installation. The block may surface in both Software Center and Company Portal simultaneously in co-managed environments.

Investigation consistently confirms that the affected device is properly enrolled and compliant in Intune, with no endpoint protection or security blocks present. The root cause is that the affected user's account is not a member of the required application entitlement security group in Entra ID or Active Directory. Without this membership, the Intune deployment is neither offered nor permitted by policy evaluation. Standard client-side troubleshooting—restarting Software Center, signing out, or forcing a policy sync—does not resolve the issue, as the gap exists at the directory level. In some instances, a stale Intune policy sync state on the device further delays catalog visibility.

!!! note "Reported variations"

    - The application is entirely absent from the catalog with no error shown until a direct install path is attempted.
    - The application appears in Software Center only after a manual refresh but still fails with a policy or entitlement error on install attempt.
    - The block appears in both Software Center and Company Portal simultaneously in co-managed ConfigMgr/Intune environments.
    - Client-side logs surface a POLICY_CHECK_FAILED status rather than a numeric error code.
    - Error code 0x87D1061E ("Installation blocked by policy") returned during the install attempt.
    - Error code 0xE000020B ("Installation blocked: entitlement check failed") returned during the install attempt.
    - Different numeric error codes (0x87D00231, 0x80180014, 0x87D00607) are returned depending on the application and deployment configuration, but all trace to the same missing group membership.
    - Stale Intune device sync contributing to delayed or missing application catalog visibility.

## Affected environment

Distribution across 11 reported cases:

- **Operating system:** Windows 10 21H2 (64%), Windows 10 (18%), Windows 10/11 (9%)
- **Device / platform:** Windows (27%), Corporate Laptop (Managed) (18%), Laptop (Corporate) (9%)
- **Team:** Finance (18%), Sales (18%), Engineering (18%)
- **Region:** US-East (64%), US-West (18%), NA (9%)

## Root cause

The affected user's account was not a member of the required entitlement security group in Entra ID or Active Directory used for Intune application assignment targeting. Because the deployment group membership was missing, policy evaluation did not authorize or present the application, and Software Center blocked the installation.

## Diagnostics

Steps used to confirm this root cause:

1. Verify the user or device is in the required entitlement group for the requested software.  
   *Expected:* Required entitlement group is present and synchronized to the management platform.
2. Run or review the device policy evaluation cycle in the endpoint management client.  
   *Expected:* The application policy is visible and targeted to the endpoint.
3. Check endpoint protection or application control logs for an installer block event.  
   *Expected:* No active protection rule blocks the approved installer.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Verified in Intune and Software Center logs on <HOSTNAME> (IP <IP>) that the ExpenseTracker install attempt by <USER> was failing with error 0x87D00231 and that the deployment was being blocked by policy targeting.
2. Confirmed the affected user <USER> (<PERSON>, EMP ID <EMP_ID>) and device <HOSTNAME> were not members of the required entitlement group Finance-App-Access that controls ExpenseTracker availability in Software Center.
3. Added user <USER> to the Finance-App-Access Intune entitlement group so the ExpenseTracker application assignment would apply to the managed endpoint <HOSTNAME>. Change approved by team lead <PERSON>.
4. Forced an Intune device sync and inventory refresh on <HOSTNAME>, then confirmed the endpoint had checked in from <IP> and received updated application targeting policy.
5. Validated that ExpenseTracker became visible and eligible for installation in Software Center for <USER> on <HOSTNAME>, then reran the install successfully to completion. <PERSON> confirmed the application launched without issues.

**Example 2**

1. Verified that SalesApp was configured to require entitlement-based assignment in the Intune/ConfigMgr co-management environment and confirmed the affected user <USER> (<PERSON>, <EMP_ID>, <LOCATION> office) was missing from the required SG-SalesApp-Entitled group in Azure AD.
2. <PERSON> from the endpoint management team added the user account <EMAIL> to the SG-SalesApp-Entitled entitlement group in Azure AD so the application deployment became available to the user.
3. Requested a device sync and policy refresh on <HOSTNAME> through Company Portal and ConfigMgr client actions to accelerate assignment and inventory propagation to the endpoint.
4. Confirmed the SalesApp application became visible to <USER> in both Company Portal and Software Center after the policy refresh completed, and that Software Center on <HOSTNAME> recognized the updated targeting without the previous 0x80180014 block.
5. Retried the SalesApp installation from Software Center on <HOSTNAME> and verified the install completed successfully without the previous policy block. <PERSON> confirmed the application launched and functioned as expected.

## Recommendation

Resolved by IT by adding the affected user to the required entitlement security group and triggering a policy refresh; missing entitlement group membership blocking application deployment.

---

[← Back to categories](../../index.md)
