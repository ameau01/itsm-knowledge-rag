---
hide:
  - navigation
root_cause_id: SIB/missing-entitlement-group-membership
family: SIB
ticket_count: 11
curated: true
self_serviceable: false
---

# Software Center install blocked due to missing entitlement group membership

[← Back to categories](../../index.md)

## Description

Affected users attempting to install an application from Software Center on a managed Windows device find that the application is either missing entirely from the Software Center catalog or present but blocked when installation is attempted. Error messages vary but commonly include phrases such as "Installation blocked by policy," "Entitlement check failed: user/device not authorized to install this application," or "Not available for this user," sometimes accompanied by error codes such as 0x87D00231, 0x80180014, 0x87D1061E, 0x87D00607, or 0xE000020B. The application may also be absent from Company Portal. In all cases the device is enrolled, compliant, and otherwise healthy — the block is specific to the application in question rather than a general device or security issue.

The issue typically surfaces when a user searches or browses for the application in Software Center and cannot find it, or when the user follows a direct link or install path and receives a policy or entitlement error. Standard self-help steps — restarting Software Center, signing out and back in, forcing a policy sync through Configuration Manager client actions, or clearing the local Software Center cache — do not resolve the problem.

The affected applications span a range of business software (finance tools, productivity suites, creative applications, line-of-business utilities, and others). The common thread is that the user's account or device has not been added to the specific entitlement or deployment group required for the application's policy assignment, so the managed software deployment system does not target or authorize the installation for that user.

!!! note "Reported variations"

    - The application may initially be completely absent from the Software Center catalog and then, after a refresh attempt, appear but still fail with a policy or entitlement error rather than installing successfully.
    - In co-managed environments the application may also be missing from Company Portal in addition to Software Center.
    - The specific error code displayed varies by application and environment configuration (e.g., 0x87D00231, 0x80180014, 0x87D1061E, 0x87D00607, 0xE000020B, or a POLICY_CHECK_FAILED message), but all trace back to the same missing entitlement group membership.
    - In some cases the client log references "PolicyCheckFailed" rather than displaying a user-facing error message in the Software Center interface.

## Affected environment

Distribution across 11 reported cases:

- **Operating system:** Windows 10 21H2 (64%), Windows 10 (18%), Windows 10/11 (9%)
- **Device / platform:** Windows (27%), Corporate Laptop (Managed) (18%), Laptop (Corporate) (9%)
- **Team:** Finance (18%), Sales (18%), Engineering (18%)
- **Region:** US-East (64%), US-West (18%), NA (9%)

## Root cause

The affected user's account or device is not a member of the entitlement group (an Azure AD or Intune security group) that controls which users and devices receive the application deployment. Because the account is absent from this group, the management platform does not target the application to the device, and Software Center either hides the application from the catalog or blocks the installation during its policy entitlement check. Once the correct group membership is added and a policy refresh completes, the application becomes visible and installs normally.

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

1. Validated that the user <USER> (<EMP_ID>) was missing from the ContosoApp entitlement group (ContosoApp_Users) required for Software Center eligibility on device <HOSTNAME>.
2. Added the user <USER> to the ContosoApp Entitlement group in AD/Intune (CN=<USER>,OU=Corp Users,DC=corplabs,DC=internal added to ContosoApp_Users) and allowed the membership change to synchronize to endpoint management policy.
3. Refreshed device inventory on <HOSTNAME> and triggered a client policy sync so the updated application targeting would be reevaluated on the laptop at the <LOCATION> office.
4. Verified the ContosoApp assignment was correctly published and visible to the entitled endpoint <HOSTNAME> in Software Center after policy refresh, confirming <USER> now appeared in the targeted user collection.
5. Retried the install and confirmed <PERSON> was no longer blocked by policy and installed successfully on the endpoint <HOSTNAME> for user <USER>.

## Recommendation

This issue is resolved by IT support; reference 'Software Center install blocked – missing entitlement group membership' when reporting it.

---

[← Back to categories](../../index.md)
