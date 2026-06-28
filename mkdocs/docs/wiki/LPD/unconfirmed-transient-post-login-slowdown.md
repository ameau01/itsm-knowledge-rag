---
hide:
  - navigation
root_cause_id: LPD/unconfirmed-transient-post-login-slowdown
family: LPD
ticket_count: 1
curated: true
self_serviceable: true
---

# Intermittent Post-Login Slowdown With High Antimalware CPU Usage

[← Back to categories](../../index.md)

## Description

The affected user reports intermittent, significant slowness on a corporate Windows 10 laptop immediately after sign-in. When the issue occurs, core productivity applications — including Outlook, a web browser, and File Explorer — take approximately 20–30 seconds each to become responsive, delaying the start of normal work activities such as accessing email and CRM tools. The slowdown is not consistently reproducible and appears to occur most frequently in the morning after the device has been powered off overnight, particularly when the user is working from a specific office location.

During an occurrence, the Windows Defender antimalware service executable (MsMpEng.exe) is observed consuming approximately 95% of CPU resources in Task Manager while applications are slow to open. The user notes that the behavior persists even after previously disabling some startup applications, suggesting the slowdown is not attributable to user-configured startup items alone.

The intermittent nature of the issue prevented full reproduction during a live support session, and available evidence was insufficient to conclusively confirm the underlying trigger.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** Windows 10 (100%)
- **Device / platform:** Corporate Laptop (100%)
- **Team:** Sales (100%)
- **Region:** EMEA (100%)

## Root cause

The affected user experienced intermittent post-login endpoint slowdown that was not reproducible during diagnostic sessions. Transient startup or security scanning activity was suspected, but no confirmed root cause was established.

## Diagnostics

Steps used to confirm this root cause:

1. Review CPU, memory, and disk usage during login and initial application launch.  
   *Expected:* Resource usage returns to normal after startup completes.
2. Check recently applied startup scripts, endpoint policies, and scheduled scans for tasks affecting logon performance.  
   *Expected:* No heavy startup task or scan backlog blocks normal use.
3. Verify available disk space and temporary file growth on the endpoint.  
   *Expected:* Disk has sufficient free space and no runaway temporary files.

## Resolution

Representative resolutions from prior cases:

1. Collected available performance logs from <HOSTNAME> and enabled additional startup-time monitoring via the endpoint management boot telemetry policy to capture CPU, disk, and process activity (especially MsMpEng.exe behavior) during the next occurrence for user <USER>.
2. Advised <PERSON> to leave the device powered on after the next slow login and report the exact time of impact to the service desk (ref INC-LPD-V0009) so telemetry from <HOSTNAME> can be correlated with Endpoint Protection scan schedules and startup policy execution.
3. Escalated for further endpoint analysis by <PERSON> (<EMAIL>) on the endpoint engineering team if recurrence is captured, and documented that disk capacity on <HOSTNAME> was not contributing based on current checks (78 GB free). Case will remain in monitoring status under SLA until next occurrence or 30-day auto-close.

## Recommendation

Intermittent post-login slowdown with high antimalware CPU usage was investigated but could not be conclusively attributed to a confirmed root cause; resolved by IT through monitoring and prior troubleshooting steps.

---

[← Back to categories](../../index.md)
