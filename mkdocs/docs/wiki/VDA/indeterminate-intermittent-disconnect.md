---
hide:
  - navigation
root_cause_id: VDA/indeterminate-intermittent-disconnect
family: VDA
ticket_count: 1
curated: true
self_serviceable: false
---

# Intermittent VPN disconnects with no confirmed root cause

[← Back to categories](../../index.md)

## Description

Affected users experience intermittent disconnections from the GlobalProtect VPN shortly after completing multi-factor authentication. The VPN client may briefly show a successful connection — indicated by the GlobalProtect icon turning green — before disconnecting within approximately five to ten seconds. During these brief connected moments, internal resources such as the corporate intranet and line-of-business applications remain unreachable or lose connectivity almost immediately.

The disconnections do not follow a consistent pattern and may not be reproducible on demand during a support session. The issue has been observed across different network environments (for example, home networks and co-working spaces), suggesting it is not tied to a specific external connection. Okta multi-factor authentication itself completes successfully each time — the push notification is approved and confirmed — yet the VPN session fails to persist afterward.

Because the behavior is intermittent and the available diagnostic evidence does not point to a single failure, affected users may perceive the issue as unpredictable. The VPN connection may occasionally succeed on a subsequent attempt without any user-side changes.

!!! note "Reported variations"

    - In some cases the VPN icon may not turn green at all before the session drops, making the disconnect appear to occur during — rather than after — the authentication step.
    - The issue may temporarily resolve on its own after switching to an alternate access path, without any configuration change on the user's device.

## Affected environment

Distribution across 1 reported cases:

- **Operating system:** Windows 10 21H2 (100%)
- **Device / platform:** Corporate laptop (managed) (100%)
- **Team:** Remote Workers (100%)
- **Region:** us-west-2 (100%)

## Root cause

The root cause of the disconnections could not be definitively determined from the available evidence. Certificate-related causes — such as an expired or mismatched device certificate — were investigated and ruled out. The remaining diagnostic data did not isolate whether the disconnects stemmed from transient VPN client behavior, a network interruption between the user's device and the gateway, or an event on the gateway side itself.

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

This issue is resolved by IT support; reference "intermittent VPN disconnect after MFA" when reporting it.

---

[← Back to categories](../../index.md)
