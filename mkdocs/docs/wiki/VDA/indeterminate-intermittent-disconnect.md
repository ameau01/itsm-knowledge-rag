---
hide:
  - navigation
root_cause_id: VDA/indeterminate-intermittent-disconnect
family: VDA
ticket_count: 1
curated: true
self_serviceable: false
---

# Intermittent GlobalProtect VPN Disconnections After Successful MFA Authentication

[← Back to categories](../../index.md)

## Description

An affected remote user experienced intermittent VPN disconnections while connecting to the corporate network via GlobalProtect from a managed Windows laptop. The VPN session dropped around the time of the Okta MFA prompt, rendering internal sites such as the intranet application and line-of-business applications unreachable. The disconnections could not be reproduced consistently during the support session.

The affected user confirmed that the Okta push notification was successfully approved each time, with authentication completing as expected. The GlobalProtect client briefly indicated a successful connection — the system tray icon turned green — before disconnecting within approximately five to ten seconds. Internal applications never became accessible during these brief sessions. The same behavior was observed from two different external networks.

Diagnostic review ruled out an expired or mismatched device certificate on the affected endpoint. However, the remaining collected logs did not isolate whether the disconnect originated from transient client behavior, a network interruption, or a gateway-side event. The root cause could not be confirmed to a single failure point from the available evidence.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** Windows 10 21H2 (100%)
- **Device / platform:** Corporate laptop (managed) (100%)
- **Team:** Remote Workers (100%)
- **Region:** us-west-2 (100%)

## Root cause

Insufficient evidence was available to determine a definitive root cause. Certificate-related causes were ruled out during diagnostic review, and the remaining disconnect behavior appeared intermittent with no single failure point identified.

## Diagnostics

Steps used to confirm this root cause:

1. Confirmed that Okta MFA approval completed successfully and checked whether the VPN tunnel dropped before or after authentication completed.  
   *Expected:* MFA approval succeeds and the VPN tunnel remains established.
2. Collected GlobalProtect client log details, disconnect timing, and error indicators from the affected endpoint.  
   *Expected:* Client logs show a successful gateway connection without certificate or policy errors.
3. Verified the validity of the endpoint device certificate and compared it with the enrolled VPN profile on the laptop.  
   *Expected:* Device certificate is current and matches the active VPN profile.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

1. Enabled verbose GlobalProtect logging on <HOSTNAME> (set PanGPS debug level to 'dump') and instructed <PERSON> to reproduce the issue during the next occurrence, capturing full TLS negotiation and tunnel establishment details.
2. Collected fresh client logs from <HOSTNAME> and coordinated with network engineer <PERSON> (<EMAIL>) to pull gateway-side session records for correlation if the disconnect recurs against user <USER>'s tunnel.
3. Provided a temporary workaround for <PERSON> to reconnect from a stable network or use the alternate web-based access path (Clientless VPN portal) while monitoring for recurrence. Scheduled a follow-up with <PERSON> at <PHONE> for end-of-week status check.

## Recommendation

Resolved by IT; reference intermittent GlobalProtect VPN disconnections following successful Okta MFA authentication with no confirmed root cause.

---

[← Back to categories](../../index.md)
