---
hide:
  - navigation
root_cause_id: SML/authenticator-clock-drift-totp-mismatch
family: SML
ticket_count: 3
curated: true
self_serviceable: false
---

# TOTP Clock Drift and Stale Factor Enrollment MFA Prompt Loop

[← Back to categories](../../index.md)

## Description

Affected users experience a repeated MFA challenge loop when attempting to sign in to SaaS applications (such as Office 365, Salesforce, Workday, and Concur) through the SSO portal. After entering their password and submitting a time-based one-time password (TOTP) from their authenticator app, the portal returns them to the MFA prompt rather than completing authentication. The authenticator app continues to generate codes that appear valid, but each submitted code is rejected, effectively blocking access to all federated applications behind the SSO portal.

The issue is traced to a mismatch between the time on the user's authenticator device and the server's expected TOTP window, caused by clock drift on the device. In some cases, stale MFA factor enrollments on the affected accounts compound the problem, preventing recovery even after device time is corrected. Identity provider logs show repeated MFA challenge failures against the affected accounts rather than any tenant-wide authentication error.

The issue has been observed on both mobile devices (iPhones running iOS 16) and desktop platforms (Windows 10), affecting users across multiple office locations. In some instances, the MFA loop appeared following an overnight maintenance window or a same-day mobile OS update, both of which preceded the onset of clock-related TOTP failures. The problem is isolated to individual user accounts and their enrolled devices rather than the identity provider tenant configuration or broader infrastructure.

!!! note "Reported variations"

    - A single user experienced the MFA loop on a personal iPhone with approximately eight minutes of clock drift, while colleagues in the same group were unaffected.
    - Multiple users in a sales group were simultaneously affected across both desktop and mobile authenticator apps, with the issue surfacing the morning after an overnight maintenance window.
    - A user's device clock was corrected to automatic time sync, but the MFA loop persisted due to a stale factor enrollment on the account, requiring MFA reset and re-enrollment.
    - Stale MFA factor enrollments — some not updated for over fourteen months — were identified as a contributing factor alongside clock drift on affected accounts.
    - A same-day iOS update preceded the onset of the issue on a user's mobile device, with the phone's time appearing incorrect until manually set back to automatic.

## Affected environment

Distribution across 3 reported cases:

- **Operating system:** iOS 16.4 (33%), Windows 10 (33%), iOS 16 (user-reported) (33%)
- **Device / platform:** Okta SSO (67%), mobile (33%)
- **Team:** Marketing - North America (33%), Sales (33%), KnowledgeWorkers (33%)
- **Region:** us-east-1 (100%)

## Root cause

Clock drift on affected users' authenticator devices caused TOTP codes to be generated out of sync with the identity provider's expected validation window, resulting in repeated MFA challenge rejections and an SSO prompt loop. In several cases, stale MFA factor enrollment records — some not updated for over fourteen months — compounded the issue, preventing successful verification even after device time was corrected. Available evidence in some incidents did not fully isolate whether time drift alone or factor re-registration was the sole trigger.

## Diagnostics

Steps used to confirm this root cause:

1. Reproduced the user's SSO login flow to verify whether MFA repeatedly prompted instead of completing sign-in.  
   *Expected:* User completes MFA once and reaches the application landing page.
2. Reviewed the user's MFA enrollment state and active Okta factor for stale registration or token mismatch indicators.  
   *Expected:* User has an active factor with no stale or disabled enrollment.
3. Compared the user's group membership and application access policy scope to rule out conditional access or assignment issues.  
   *Expected:* User belongs to the expected access group and policy scope.

## Resolution

Performed by IT support. Representative resolutions from prior cases:

**Example 1**

1. Validated that user <USER>'s (<PERSON> <PERSON>, <EMP_ID>) MFA challenge was looping in Okta after primary credential entry and confirmed the issue affected SSO access to downstream SaaS applications including Office 365 and Salesforce from device <HOSTNAME>.
2. Corrected the authenticator device time by having <PERSON> <PERSON> resync the iPhone clock on <HOSTNAME> with network time and restart the authenticator app so new TOTP values matched server time.
3. Removed the stale MFA enrollment for <USER> and completed a full re-enrollment of the user's Okta factor to ensure a clean trusted TOTP registration tied to <EMP_ID>.
4. Cleared <USER>'s active Okta sessions to remove any cached or incomplete authentication state from prior failed challenges originating from IP <IP>.
5. Retested SSO sign-in with <PERSON> <PERSON> and verified successful MFA completion and application access to Office 365 and Salesforce without the prompt looping. Notified user at <EMAIL> that the issue is resolved.

**Example 2**

1. Reviewed affected Sales user accounts in Okta (<USER>, <USER>, <USER>, <USER>, <USER>, <USER>) and reset MFA enrollment for users showing stale or inconsistent factor state via the Okta admin console.
2. Forced MFA re-enrollment at next sign-in for all six affected users so each could register a fresh authenticator factor and remove invalid prior enrollments. Confirmation emails were sent to each user's corporate address (e.g., <EMAIL>) with re-enrollment instructions.
3. Instructed users — particularly <USER> and <USER> whose devices showed clock drift — to enable automatic time synchronization on their mobile devices and resync or re-register their authenticator app before retrying login. <PERSON> (<USER>, emp ID <EMP_ID>) from the Sales team coordinated user communication.
4. Validated that conditional access and factor policy assignments for the Sales group were aligned after overnight maintenance and updated policy handling to enforce periodic factor re-enrollment, reducing recurrence risk from stale-device enrollments. Change reviewed by <PERSON> on the identity team.
5. Tested sign-in with sampled affected users (<USER> from <HOSTNAME> and <USER> from his mobile device) and confirmed successful access to Salesforce, Workday, and Concur without MFA looping, then monitored Okta authentication logs for 24 hours with no recurring spike in rejected challenges.

## Recommendation

Resolved by IT through device time synchronization correction and, where necessary, MFA factor reset and re-enrollment on the identity provider; reference as "TOTP clock drift / stale factor enrollment MFA loop."

---

[← Back to categories](../../index.md)
