---
hide:
  - navigation
root_cause_id: SIB/endpoint-protection-app-control-block
family: SIB
ticket_count: 7
curated: true
self_serviceable: false
---

# Endpoint protection application control blocking approved software installer

[← Back to categories](../../index.md)

## Description

Affected users attempting to install approved software from Software Center on managed Windows 10 corporate devices find that the installation is blocked by an endpoint protection or application control policy. The block may present in several ways: the application may fail to install with a policy-check error (such as "Installation blocked by policy," "Installer blocked by Endpoint Protection," or error codes like 0x80070005, 0x87D00324, or EP-4031), or the application may not appear in Software Center at all after the policy evaluation prevents the deployment from being presented.

In some cases, the application initially appears in the Software Center catalog but disappears after a failed installation attempt, and subsequent retries produce the same block. In other cases, the application is never visible in Software Center despite the device being enrolled, compliant, and correctly targeted for the deployment in Intune. Endpoint protection logs on the affected device typically show a quarantine or deny action against the installer, citing reasons such as an unapproved installer hash, an untrusted or unsigned publisher, or the application not being present in the approved applications policy.

The issue has been observed across multiple applications (including finance, productivity, VPN, and engineering tools) and across different offices and departments. It can affect a single user or multiple users on devices sharing the same endpoint protection policy scope. The underlying device management health and Intune compliance status are not impacted — the block is limited to the application installation workflow enforced by the endpoint security layer.

!!! note "Reported variations"

    - The application appears in Software Center and can be selected, but the installer is quarantined by endpoint protection upon execution, resulting in a policy-block message and the application disappearing from the catalog after the failed attempt.
    - The application never appears in Software Center because the endpoint protection policy evaluation blocks the installer before the deployment is presented to the user.
    - Multiple users on devices within the same policy scope (such as a department or office location) are affected simultaneously when the application is missing from a shared approved applications policy.
    - The block is triggered by a specific rule name (such as "BlockUnknownInstallers" or "BlockUnsignedInstallers") rather than a general application approval policy, requiring a targeted security exception rather than a standard allowlist update.

## Affected environment

Distribution across 7 reported cases:

- **Operating system:** Windows 10 21H2 (86%), Windows 10 Enterprise (14%)
- **Device / platform:** Corporate laptop (29%), Windows (14%), Managed Corporate Laptop (14%)
- **Team:** Finance (29%), Engineering (29%), Corporate - Finance (14%)
- **Region:** us-east-1 (71%), US-West (29%)

## Root cause

An endpoint protection or application control policy on the managed device is blocking the software installer because the installer's hash, publisher signature, or application entry has not been added to the approved allowlist in the relevant security policy. This prevents Software Center from completing the installation workflow and, in some configurations, causes the application to disappear from the catalog after the failed attempt. The block occurs even when the user's entitlement, deployment targeting, and device compliance are all correct.

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

This issue is resolved by IT support; reference 'endpoint protection application control block' when reporting it.

---

[← Back to categories](../../index.md)
