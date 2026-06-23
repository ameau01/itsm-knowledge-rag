---
hide:
  - navigation
root_cause_id: SIB/endpoint-protection-block-plus-stale-inventory
family: SIB
ticket_count: 21
curated: true
self_serviceable: false
---

# Software installation blocked by endpoint protection with stale device inventory

[← Back to categories](../../index.md)

## Description

Affected users attempting to install approved applications from Software Center on managed Windows 10 or Windows 11 devices find that the installation is blocked by an endpoint protection or application control policy. The error messages vary but commonly include "Installation blocked by Endpoint Protection," "Installer fails policy check," "Installation blocked by security policy," or "blocked by policy," sometimes accompanied by error codes such as 0x80070005, 0x800704EC, 0x87D13B3, 0x87D1FDE8, or 0xD0000247. In some cases, the endpoint protection engine quarantines the installer outright, preventing any execution attempt.

In addition to the security block, the application may not appear in the Software Center catalog at all, or it may appear intermittently — visible in one view or session and missing after a refresh. This catalog visibility issue stems from the affected device having a stale inventory or policy state in Intune, with devices sometimes not having synchronized for days or even weeks. Because the device record is outdated, Software Center cannot correctly resolve the application's entitlement or deployment targeting for the user, so the app either does not display or is treated as unavailable.

The combination of these two conditions — an active endpoint protection block on the installer and stale device inventory preventing proper policy evaluation — means that neither a manual install attempt nor a catalog refresh alone resolves the problem. Users across various departments and office locations have reported this issue on corporate-managed endpoints, often in connection with time-sensitive work such as quarter-end reporting or project deadlines. In several cases, a prior partial fix (such as an inventory refresh or entitlement group correction alone) temporarily restored access, but the issue recurred because the endpoint protection approval had not fully propagated to the device or the inventory fell stale again before the updated allow-policy could take effect.

!!! note "Reported variations"

    - On recently re-enrolled devices, the re-enrollment process may not trigger a full inventory sync, causing the application to be visible under an administrator account but missing for the standard user account.
    - In some cases, the application appears in Software Center and is selectable but fails immediately upon clicking Install, rather than being absent from the catalog entirely.
    - The issue has recurred after a previous ticket closure when the earlier remediation (such as an inventory refresh alone) did not fully propagate the endpoint protection approval to the device, causing both the security block and intermittent catalog visibility to return within days.
    - Multiple users on the same team or in the same office may be affected simultaneously when the same installer is flagged by endpoint protection across several devices with stale inventory.

## Affected environment

Distribution across 21 reported cases:

- **Operating system:** Windows 10 21H2 (67%), Windows 10 (19%), Windows 10 Enterprise 21H2 (5%)
- **Device / platform:** Windows (33%), x86_64 (24%), x64 (10%)
- **Team:** Finance (24%), Engineering (24%), Standard Users (10%)
- **Region:** us-east-1 (43%), us-west-2 (33%), EMEA (19%)

## Root cause

The approved application installer is being blocked by the endpoint protection or application control policy on the device because the installer's signature, hash, or publisher information is not present in the effective allowlist on that endpoint. At the same time, the device's Intune inventory and policy state are stale — often due to a missed or delayed check-in — so Software Center cannot evaluate the correct application targeting or entitlement for the user. Both conditions must be addressed together: the security allowlist must be updated to permit the installer, and the device must complete an inventory and policy synchronization so that the updated approval state and application assignment are reflected on the endpoint.

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

1. Validated that FinanceApp was an approved application for the Finance-Analysts group (which includes <USER>, <EMP_ID>) and confirmed the endpoint protection block on <HOSTNAME> was caused by policy BlockUnapprovedInstall targeting the FinanceApp_Setup.msi installer.
2. Submitted and completed an Endpoint Protection policy change request (handled by security analyst <PERSON>, <EMAIL>) to add FinanceApp to the allowed application list as an approved exception under policy BlockUnapprovedInstall.
3. Triggered a device inventory and policy refresh for <HOSTNAME> through the Intune portal so the endpoint could receive the updated allow policy and refreshed Software Center catalog. Sync completed successfully within minutes.
4. Rechecked Software Center on <HOSTNAME> after the refresh and confirmed FinanceApp became visible in the catalog for user <USER>.
5. Retried the installation of FinanceApp from Software Center on <HOSTNAME> and verified the application installed successfully without further Endpoint Protection policy blocks. Confirmed with <PERSON> via phone (ext. <PHONE>) that the application is functioning correctly.

**Example 2**

1. Confirmed the ContosoApp deployment (DEP-88421) was intended for the affected device <HOSTNAME> belonging to user <USER> (<EMP_ID>) in the <LOCATION> office, and reviewed Software Center catalog visibility and Endpoint Protection block symptoms to rule out a generic packaging failure.
2. Checked Endpoint Protection application control findings on <HOSTNAME> and verified the ContosoApp installer (ContosoAppSetup_v4.2.1.exe) was being blocked by quarantine/allowlist policy rule EP-RULE-2041 on the device, as confirmed by security analyst <PERSON> (<USER>).
3. Approved the ContosoApp installer hash in the applicable Endpoint Protection allowlist policy via the security management console so the trusted package could execute without triggering application control blocks on managed endpoints.
4. Refreshed device inventory on <HOSTNAME> and forced an Intune policy sync (via Company Portal > Sync) so the latest application targeting, security policy state, and updated allowlist were applied to the endpoint. Last sync updated from 2026-03-16T08:12:00Z to current.
5. Triggered a Software Center machine policy refresh on <HOSTNAME> and re-ran the ContosoApp installation after the Endpoint Protection policy change and Intune device sync completed. User <USER> confirmed the installation prompt appeared.
6. Verified that ContosoApp became available to <HOSTNAME> in Software Center and that the installation completed successfully (exit code 0) without further Endpoint Protection blocks. Confirmed with <PERSON> via email at <EMAIL> that the application is functioning as expected.

## Recommendation

This issue is resolved by IT support; reference 'endpoint protection block with stale device inventory' when reporting it.

---

[← Back to categories](../../index.md)
