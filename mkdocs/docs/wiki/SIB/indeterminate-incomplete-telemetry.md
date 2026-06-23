---
hide:
  - navigation
root_cause_id: SIB/indeterminate-incomplete-telemetry
family: SIB
ticket_count: 2
curated: true
self_serviceable: false
---

# FinanceApp deployment failure with incomplete endpoint telemetry during diagnostics

[← Back to categories](../../index.md)

## Description

Affected users report that FinanceApp v4.2.1 is unavailable in the Software Center catalog on their managed Windows devices. The application does not appear in the list of available software even after multiple manual policy refresh cycles, machine reboots, and sign-out/sign-in attempts. In some cases, attempting to install the application through an alternative method — such as a forwarded deployment link or a manually downloaded installer — results in an authorization or entitlement error, or a security policy block notification.

The issue prevents affected users from completing finance workflows, particularly during time-sensitive periods such as quarter-end reporting and reconciliation. Users may belong to the correct entitlement group (such as FIN-FinanceApp-Entitlement or Finance-Analysts) and their devices may be properly enrolled in the endpoint management platform, yet the application still fails to appear or install.

A distinguishing characteristic of this issue is that standard diagnostic checks do not return sufficient or reliable data to isolate a single root cause. The device management client and the endpoint protection agent on the affected device may both be in a degraded reporting state — for example, showing stale last-contact timestamps — which limits the ability of IT support to determine whether the problem stems from entitlement synchronization, policy processing failure, or a security control action. As a result, the issue may remain open longer than usual while normal endpoint reporting is restored or a deeper platform review is conducted.

!!! note "Reported variations"

    - In some cases, the FinanceApp deployment targeting in the management platform is confirmed to be misconfigured or not evaluating correctly against the device, even though the user holds valid entitlement group membership and no endpoint security block is active.
    - Some affected users report that manually running the FinanceApp installer triggers a security policy block notification (referencing a rule such as "BlockUnapprovedInstall"), though this may be a secondary symptom rather than the primary cause when endpoint telemetry is incomplete.
    - The device management client and endpoint protection agent may show significantly stale reporting timestamps (e.g., several days old), indicating a broader endpoint health issue beyond the FinanceApp installation problem alone.

## Affected environment

Distribution across 2 reported cases:

- **Operating system:** Windows 10 21H2 (50%), Windows 10 (50%)
- **Device / platform:** Laptop (Corporate) (50%), Windows (50%)
- **Team:** Finance (50%), Finance-Analysts (50%)
- **Region:** us-east-1 (50%), EMEA (50%)

## Root cause

The root cause cannot be conclusively determined because the device management client and endpoint protection agent on the affected device are not returning complete or current telemetry during the diagnostic window. This degraded reporting state prevents IT support from isolating whether the FinanceApp installation failure is caused by an entitlement synchronization problem, a policy processing failure on the device, or an endpoint security control action. In at least one instance, the underlying issue was traced to a backend deployment targeting misconfiguration in the endpoint management platform, but this finding could not be generalized across all cases due to the incomplete diagnostic data.

## Diagnostics

Steps used to confirm this root cause:

1. Verify whether the affected user or device is present in the required FinanceApp entitlement group and that membership is synchronized.  
   *Expected:* Required entitlement group is present and synchronized to the management platform.
2. Run and review the device policy evaluation and inventory refresh cycle to determine whether the FinanceApp deployment becomes visible to the endpoint.  
   *Expected:* The application policy is visible and targeted to the endpoint.
3. Check endpoint protection or application control logs for a security rule blocking the approved FinanceApp installer.  
   *Expected:* No active protection rule blocks the approved installer.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Validated that the affected user <PERSON>.nguyen (<EMP_ID>) and device <HOSTNAME> were correctly synchronized in the FIN-FinanceApp-Entitlement Azure AD group and that no local Endpoint Protection or application control policy was blocking the FinanceApp installer.
2. Reviewed the FinanceApp deployment assignment in the Intune management console and identified that the application was not properly targeted to the device scope containing <HOSTNAME> — the deployment's device filter rule was excluding the <LOCATION> office device collection due to a stale scope tag configuration.
3. Corrected the deployment targeting scope tag and assignment rule in the Intune management platform to include the <LOCATION> device collection, then initiated a policy refresh to <HOSTNAME> (IP <IP>) to force re-evaluation of the deployment.
4. Confirmed FinanceApp v4.2.1 became visible in Software Center on <HOSTNAME> after the assignment correction and verified the installation completed successfully. <PERSON> confirmed she could launch FinanceApp and access the required finance workflows.

**Example 2**

1. Documented that Finance-Analysts entitlement group membership for <USER> (<EMP_ID>) appears likely correct in AD and Intune, but could not be fully validated end-to-end on <HOSTNAME> because device sync and SCCM reporting data were incomplete — last successful inventory dated 2026-05-03.
2. Requested endpoint remediation from the desktop engineering team to restore healthy SCCM management client and Endpoint Protection agent reporting on <HOSTNAME> (IP <IP>, <LOCATION> office). Once the agents are healthy, rerun full policy evaluation cycle and Endpoint Protection log collection to capture any BlockUnapprovedInstall events for FinanceApp.
3. Escalated the case (assigned to endpoint engineering lead <PERSON>) for follow-up once <HOSTNAME> can complete a full inventory and policy refresh successfully, and verify whether FinanceApp v4.2.1 becomes visible in Software Center for <USER> or if a BlockUnapprovedInstall event is then recorded in Endpoint Protection logs. User notified at <EMAIL> and via phone <PHONE>.

## Recommendation

This issue is resolved by IT support; reference "FinanceApp install failure – incomplete telemetry" when reporting it.

---

[← Back to categories](../../index.md)
