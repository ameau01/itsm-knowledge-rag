---
hide:
  - navigation
root_cause_id: SIB/endpoint-protection-app-control-block
family: SIB
ticket_count: 7
curated: true
self_serviceable: false
---

# Endpoint Protection Application Control Blocking Software Center Installer

[← Back to categories](../../index.md)

## Description

Affected users on managed Windows 10 corporate endpoints experience application installation failures when attempting to deploy software through Software Center. The endpoint protection application control policy actively blocks the installer, producing error messages such as "Installation blocked by policy," "Installation blocked by Endpoint Protection," or policy-related error codes including INSTALL_BLOCKED_POLICY_CHECK (0x80070005), 0x87D00324, or EP-4031. Device enrollment, Intune compliance status, and entitlement group membership are confirmed as healthy in all cases — the block originates solely from the endpoint protection allowlist or approval policy.

A common secondary symptom is that the requested application either does not appear in the Software Center catalog, disappears from the available applications list after a failed installation attempt, or is intermittently visible but consistently fails upon install initiation. Retrying the installation without a policy change produces the same denial. Endpoint protection logs on affected devices confirm a quarantine or deny action triggered by an application control rule against the installer package, intercepting it before Software Center can complete the deployment.

The issue has been observed across multiple offices, departments, and application types — including VPN clients, productivity suites, line-of-business tools, and finance applications. Multiple users within the same deployment group can be simultaneously affected when the installer approval entry is missing from the relevant endpoint protection policy. Local IT personnel attempting a manual push of the installer encounter the same block, confirming the issue is not limited to the self-service Software Center workflow.

!!! note "Reported variations"

    - In some cases the endpoint protection block message specifically cites an unapproved or unknown publisher signature as the reason for denial.
    - The application may briefly appear in Software Center before vanishing from the catalog after the initial blocked install attempt, rather than being absent from the start.
    - Multiple users within the same deployment group can be affected simultaneously when the installer approval entry is missing from the endpoint protection application control policy assigned to that group.
    - The block may reference a named policy (e.g., "BlockUnsignedInstallers" or a block-unknown-installers rule) rather than a generic policy-check failure code.
    - Local IT personnel attempting a manual push of the installer encounter the same policy block, confirming the issue is not limited to the self-service Software Center workflow.
    - In one case, endpoint protection logs specifically identified the installer hash value as the attribute triggering the deny action.
    - One affected user reported inconsistent Software Center behavior during troubleshooting, with the application intermittently appearing or not appearing in the catalog.

## Affected environment

Distribution across 7 reported cases:

- **Operating system:** Windows 10 21H2 (86%), Windows 10 Enterprise (14%)
- **Device / platform:** Corporate laptop (29%), Windows (14%), Managed Corporate Laptop (14%)
- **Team:** Finance (29%), Engineering (29%), Corporate - Finance (14%)
- **Region:** us-east-1 (71%), US-West (29%)

## Root cause

An endpoint protection application control policy blocked the application installer because the installer's hash, publisher signature, or approval entry was not present in the approved-applications allowlist assigned to the affected devices. This prevented Software Center from completing or presenting the deployment despite valid entitlement and targeting.

## Diagnostics

Steps used to confirm this root cause:

1. Verified the device and user targeting for the Contoso VPN deployment in endpoint management.  
   *Expected:* Required entitlement group is present and synchronized to the management platform.
2. Reviewed the device policy evaluation cycle and triggered a fresh management sync to confirm application policy processing.  
   *Expected:* The application policy is visible and targeted to the endpoint.
3. Check endpoint protection or application control logs for an installer block event affecting the requested software.  
   *Expected:* No active protection rule blocks the approved installer.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Reviewed Endpoint Protection application control logs on <HOSTNAME> and confirmed the Contoso VPN installer (ContosoVPN_v3.8.1.msi) was being blocked by policy during installation validation, matching error INSTALL_BLOCKED_POLICY_CHECK / 0x80070005.
2. Security analyst <PERSON> approved Contoso VPN (ContosoVPN_v3.8.1.msi) in the Endpoint Protection allowlist so the installer would pass policy checks on managed endpoints in the Finance user group.
3. Triggered an Intune sync and inventory/policy refresh on <HOSTNAME> (IP <IP>) so the updated Endpoint Protection application approval and deployment state would be reevaluated by the device.
4. Had user <PERSON> restart <HOSTNAME> and reopen Software Center, then retry the Contoso VPN installation from the refreshed application list.
5. Verified that Contoso VPN became visible in Software Center on <HOSTNAME> and that the installation completed successfully without the policy block. User <EMAIL> confirmed VPN connectivity was functional.

**Example 2**

1. Reviewed the Endpoint Protection BlockUntrustedInstall policy and confirmed the CorporateTime installer (CorporateTime_Setup_v3.2.1.exe) was being denied on <HOSTNAME> because its publisher/signature was not in the approved trust list for the <LOCATION> device scope.
2. Added the application's approved publisher/signature to the Endpoint Protection allowlist and saved the policy change for the <LOCATION> device scope, as approved by <PERSON> (security_team).
3. Republished the updated security policy and triggered a device policy refresh so the managed laptop <HOSTNAME> (IP <IP>) received the new trust configuration.
4. Forced an Intune inventory and Software Center policy sync on <HOSTNAME> for user <USER> to refresh application targeting and client-side policy evaluation after the security policy change.
5. Retried the CorporateTime installation from Software Center on <HOSTNAME> and verified the installer was no longer blocked and the application completed installation successfully. Confirmed with <PERSON> (<EMAIL>) that the application launched without issues.

## Recommendation

Resolved by the security team updating the endpoint protection allowlist to approve the blocked installer and refreshing policy on affected devices.

---

[← Back to categories](../../index.md)
