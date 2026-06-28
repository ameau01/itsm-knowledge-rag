---
hide:
  - navigation
root_cause_id: SIB/endpoint-protection-block-plus-stale-inventory
family: SIB
ticket_count: 21
curated: true
self_serviceable: false
---

# Endpoint Protection Installer Block Combined With Stale Intune Inventory

[← Back to categories](../../index.md)

## Description

Affected users on corporate-managed Windows endpoints report that approved applications are either missing from the Software Center catalog or fail immediately upon installation with a security policy block. Error messages consistently reference Endpoint Protection or application control denial, with common indicators including "Installation blocked by Endpoint Protection," "blocked by security policy," or specific coded failures such as "PolicyCheckFailed:EP-403," accompanied by error codes including 0x80070005, 0x80070490, 0x800704EC, 0x87D13B3, 0x87D00607, 0x87D1FDE8, or 0xD0000247. In some cases the application is visible but fails instantly upon launch; in others it is entirely absent from the catalog or appears intermittently across sessions.

Investigation consistently reveals two co-occurring conditions. First, Endpoint Protection or Defender Application Control policy is actively blocking the installer due to a hash mismatch, missing publisher signature approval, heuristic detection, or the installer not appearing on the security allowlist. Second, the device's Intune inventory is stale—with last-sync timestamps ranging from 36 hours to approximately 30 days behind—preventing updated allowlist approvals, entitlement targeting, and application assignments from propagating to the endpoint. Neither condition alone fully accounts for the reported behavior.

The issue affects multiple departments, offices, and application titles rather than a single software package. In recurring instances, a prior inventory refresh temporarily restores visibility, but the issue returns because the Endpoint Protection effective policy on the device still lacks the necessary approval. In some cases, the application is visible under an administrative account but absent under the affected user's standard account due to stale entitlement state. Multiple users within the same teams are typically affected concurrently.

!!! note "Reported variations"

    - The application is completely absent from the Software Center catalog, with no error shown until the user attempts to run the installer manually.
    - The application is visible in Software Center but fails immediately upon clicking Install, without ever beginning the installation process.
    - The Endpoint Protection block references a specific policy name or coded failure rather than a generic "blocked by policy" message.
    - The block is triggered by a publisher signature or certificate mismatch, or by heuristic behavioral detection, rather than an unapproved installer hash.
    - The issue recurs after a previous resolution due to a new installer version introducing an updated hash not yet added to the allowlist.
    - The application appears intermittently or is visible under an administrative account but absent under the affected user's standard account.
    - Multiple users within the same office or device group experience the issue simultaneously, indicating a broader policy or sync gap affecting a collection of devices.
    - A recently re-enrolled or hardware-replaced device did not trigger a full Intune inventory sync, resulting in stale inventory despite the recent enrollment date.

## Affected environment

Distribution across 21 reported cases:

- **Operating system:** Windows 10 21H2 (67%), Windows 10 (19%), Windows 10 Enterprise 21H2 (5%)
- **Device / platform:** Windows (33%), x86_64 (24%), x64 (10%)
- **Team:** Finance (24%), Engineering (24%), Standard Users (10%)
- **Region:** us-east-1 (43%), us-west-2 (33%), EMEA (19%)

## Root cause

Endpoint Protection or Defender Application Control policy was blocking the approved application installer because the required publisher signature, hash, or allowlist approval had not propagated to the endpoint. Concurrently, the device's Intune inventory and policy state were stale, preventing current entitlement targeting, application assignments, and updated security approvals from reaching the device. The combination of the active security block and outdated device policy caused both catalog visibility failures and installation denials in Software Center.

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

Resolved by IT by updating the Endpoint Protection allowlist to approve the installer and forcing an Intune device inventory sync and policy refresh on the affected endpoint.

---

[← Back to categories](../../index.md)
