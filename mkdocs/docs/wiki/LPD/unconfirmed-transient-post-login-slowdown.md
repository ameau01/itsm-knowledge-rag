---
hide:
  - navigation
root_cause_id: LPD/unconfirmed-transient-post-login-slowdown
family: LPD
ticket_count: 1
curated: true
self_serviceable: true
---

# Intermittent post-login laptop slowdown without confirmed root cause

[← Back to categories](../../index.md)

## Description

Affected users may experience significant slowness on their Windows 10 corporate laptop shortly after signing in. When the issue occurs, core applications such as Outlook, web browsers, and File Explorer can take 20–30 seconds each to open, delaying the start of normal work. The slowdown appears to begin immediately after login and is most commonly reported in the morning after the laptop has been powered off overnight.

The issue is intermittent and not consistently reproducible. During affected sessions, the Windows security process (MsMpEng.exe) has been observed consuming very high CPU usage — around 95% — which coincides with the sluggish application launches. However, the behavior may not appear during live diagnostic sessions, making it difficult to capture in real time.

Affected users may notice that the slowdown clears on its own after some time, with the laptop returning to normal performance for the remainder of the session. Previously disabling startup applications has not reliably prevented the issue from recurring.

!!! note "Reported variations"

    - The issue may be more likely to occur when the laptop has been off overnight and is started at a specific office location, though this pattern has not been confirmed across multiple cases.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** Windows 10 (100%)
- **Device / platform:** Corporate Laptop (100%)
- **Team:** Sales (100%)
- **Region:** EMEA (100%)

## Root cause

The exact root cause has not been confirmed. Diagnostics ruled out low disk space as a contributing factor, but available evidence was insufficient to determine whether an intermittent startup task or the Windows security scanning process is responsible for the post-login CPU spike. The issue remains only partially evidenced and requires further monitoring to establish a definitive cause.

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

This issue is resolved by IT support; reference 'intermittent post-login slowdown — unconfirmed cause' when reporting it.

---

[← Back to categories](../../index.md)
