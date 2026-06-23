---
hide:
  - navigation
---

# ITSM Knowledge Wiki {.hero-title}

<div class="category-pane" markdown="1">

**Categories**

- [AD Lockout from Stale Cached Mobile Credentials](#ad-lockout-from-stale-cached-mobile-credentials)
- [BitLocker Not Enabled / Recovery Key Not Escrowed](#bitlocker-not-enabled-recovery-key-not-escrowed)
- [Corporate Wi-Fi 802.1X Authentication Failures](#corporate-wi-fi-8021x-authentication-failures)
- [GlobalProtect VPN Immediate Post-MFA Disconnect](#globalprotect-vpn-immediate-post-mfa-disconnect)
- [Integration Gateway API Timeouts](#integration-gateway-api-timeouts)
- [Internal DNS Resolution Failures](#internal-dns-resolution-failures)
- [Internal Web Service Load-Balancer TLS Certificate Expiry](#internal-web-service-load-balancer-tls-certificate-expiry)
- [Intune Device Non-Compliant Encryption (Conditional Access Block)](#intune-device-non-compliant-encryption-conditional-access-block)
- [Laptop Slow Post-Login (CPU / Disk Contention)](#laptop-slow-post-login-cpu-disk-contention)
- [Outlook / Exchange Online Mailbox Sync Failures](#outlook-exchange-online-mailbox-sync-failures)
- [Print Server Stuck Jobs / Driver Failure](#print-server-stuck-jobs-driver-failure)
- [Shared Drive Access Denied](#shared-drive-access-denied)
- [Software Center Install Blocked (Endpoint Protection)](#software-center-install-blocked-endpoint-protection)
- [SSO / MFA Prompt Loop (Okta / Azure AD)](#sso-mfa-prompt-loop-okta-azure-ad)

</div>

## AD Lockout from Stale Cached Mobile Credentials

- [Account lockout after password reset due to expired reset token](wiki/ALP/expired-reset-token-primary.md)
- [Mobile cached credentials and expired reset token combine to sustain AD lockout](wiki/ALP/stale-mobile-credentials-plus-expired-reset-token.md)
- [Post-reset account lockout caused by stale cached credentials on iOS mobile device](wiki/ALP/stale-mobile-cached-credentials.md)
- [Recurring account lockouts from unidentified stale credential source after password reset](wiki/ALP/stale-credentials-unidentified-source.md)

[↑ Back to top](#itsm-knowledge-wiki)

## BitLocker Not Enabled / Recovery Key Not Escrowed

- [BitLocker activation failure due to stale or missing Intune encryption policy](wiki/EDE/intune-policy-not-assigned-or-stale-deprecated-policy.md)
- [BitLocker compliance mismatch due to MDM sync failure with Intune](wiki/EDE/mdm-sync-failure-causing-state-desync.md)
- [BitLocker recovery key escrow failure despite healthy TPM and policy](wiki/EDE/recovery-key-escrow-failure-despite-healthy-tpm-and-policy.md)
- [BitLocker unable to start due to uninitialized TPM protector](wiki/EDE/tpm-protector-not-initialized.md)
- [Disk encryption noncompliance due to incomplete BitLocker initialization on endpoint](wiki/EDE/inconclusive-evidence-bitlocker-not-fully-enabled.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Corporate Wi-Fi 802.1X Authentication Failures

- [Corporate Wi-Fi access blocked by incorrect NAC policy assignment after policy change](wiki/WCI/incorrect-nac-policy-assignment.md)
- [Corporate Wi-Fi authentication failures after incomplete certificate rollover propagation](wiki/WCI/cert-rollover-incomplete-trust-propagation.md)
- [Corporate Wi-Fi connectivity loss from stale or corrupt endpoint wireless profile](wiki/WCI/stale-or-corrupt-client-wifi-profile.md)
- [Corporate Wi-Fi outage caused by expired wireless controller authentication certificate](wiki/WCI/expired-radius-controller-eap-tls-certificate.md)
- [Intermittent corporate Wi-Fi authentication failures with unclear combined root cause](wiki/WCI/unclassified-insufficient-evidence.md)
- [Wi-Fi session drops caused by wireless access point radio instability](wiki/WCI/wireless-rf-controller-instability.md)

[↑ Back to top](#itsm-knowledge-wiki)

## GlobalProtect VPN Immediate Post-MFA Disconnect

- [Expired device certificate causes VPN tunnel teardown after MFA approval](wiki/VDA/expired-device-certificate-post-mfa-validation-failure.md)
- [GlobalProtect VPN disconnects seconds after successful MFA authentication](wiki/VDA/gateway-portal-post-auth-instability.md)
- [GlobalProtect profile update referencing wrong certificate causes post-auth disconnects](wiki/VDA/globalprotect-profile-cert-mapping-misconfiguration.md)
- [Intermittent VPN disconnects with no confirmed root cause](wiki/VDA/indeterminate-intermittent-disconnect.md)
- [Stale VPN profile blocking renewed device certificate after renewal](wiki/VDA/stale-vpn-profile-blocking-renewed-certificate.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Integration Gateway API Timeouts

- [Downstream API rate limiting causes integration job timeouts](wiki/AIT/downstream-rate-limiting-throttling.md)
- [Expired Integration Gateway API token causes sync job timeouts](wiki/AIT/expired-api-token-auth-failures.md)
- [Integration Gateway 504 timeouts caused by downstream API latency spikes](wiki/AIT/downstream-api-latency-exceeds-timeout.md)
- [Integration Gateway job failures from mixed credential and throttling conditions](wiki/AIT/unconfirmed-mixed-credential-latency-throttling.md)
- [Stale gateway retry policy amplifies downstream latency into timeout storms](wiki/AIT/stale-retry-backoff-amplifies-latency.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Internal DNS Resolution Failures

- [Hostname resolution failures caused by client-side DNS cache or transient conditions](wiki/DRF/no-server-side-fault-client-side-or-transient.md)
- [Intermittent internal DNS failures due to resolver path inconsistency after maintenance](wiki/DRF/resolver-path-inconsistency-mixed-cause.md)
- [Missing or incorrect conditional forwarder causing intermittent internal DNS failures](wiki/DRF/missing-or-incorrect-conditional-forwarder.md)
- [Stale A record in authoritative internal DNS zone causing intermittent resolution failures](wiki/DRF/stale-authoritative-zone-record.md)
- [Stale DNS resolver cache serving outdated records after internal zone change](wiki/DRF/stale-resolver-cache-after-record-change.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Internal Web Service Load-Balancer TLS Certificate Expiry

- [Expired certificate persisted on load balancer due to incomplete chain deployment and monitoring gap](wiki/CES/renewed-chain-not-deployed-to-lb-with-monitoring-gap.md)
- [Expired certificate served by load balancer after automated renewal failure](wiki/CES/automated-renewal-process-failed-to-complete.md)
- [Expired or missing intermediate certificate in load balancer chain breaks TLS](wiki/CES/valid-leaf-but-stale-or-missing-intermediate-served.md)
- [Mismatched certificate bound to load balancer causing hostname validation failures](wiki/CES/wrong-certificate-bound-to-endpoint.md)
- [Unconfirmed TLS certificate presentation issue with insufficient diagnostic evidence](wiki/CES/unconfirmed-tls-presentation-issue-evidence-gap.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Intune Device Non-Compliant Encryption (Conditional Access Block)

- [Conditional Access block due to indeterminate compliance refresh failure](wiki/DCP/indeterminate-compliance-refresh-failure.md)
- [Conditional Access block due to missing or inactive BitLocker encryption on endpoint](wiki/DCP/encryption-actually-disabled-or-attestation-failed.md)
- [Encryption compliance signal lost after OS update or policy change](wiki/DCP/encryption-telemetry-broken-after-os-or-hardware-change.md)
- [Noncompliance caused by stale deprecated Intune compliance policy reference](wiki/DCP/stale-deprecated-compliance-policy-reference.md)
- [Stale Intune check-in prevents encryption signal from reaching compliance evaluation](wiki/DCP/stale-checkin-missing-encryption-signal.md)
- [Stale compliance cache mismatch between Intune and Conditional Access](wiki/DCP/stale-compliance-state-mismatch-ca-cache.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Laptop Slow Post-Login (CPU / Disk Contention)

- [Intermittent post-login laptop slowdown without confirmed root cause](wiki/LPD/unconfirmed-transient-post-login-slowdown.md) · self-service
- [Post-login laptop slowdown caused by endpoint protection scan backlog and disk contention](wiki/LPD/endpoint-scan-backlog-startup-disk-contention.md)
- [Post-login laptop slowdown caused by temporary file buildup and low disk space](wiki/LPD/low-disk-temp-file-accumulation.md) · self-service
- [Post-login slowdown caused by resource-heavy corporate startup policy](wiki/LPD/resource-heavy-startup-policy.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Outlook / Exchange Online Mailbox Sync Failures

- [Exchange Online mailbox throttling disrupting Outlook desktop and mobile sync](wiki/OES/exchange-online-mailbox-throttling.md)
- [Exchange Online mailbox-side sync fault affecting multiple client devices](wiki/OES/suspected-server-side-mailbox-fault.md)
- [Intune device compliance block disrupting Exchange Online mobile and desktop sync](wiki/OES/intune-mdm-device-compliance-block.md)
- [Outlook desktop and mobile sync failure due to endpoint client state corruption](wiki/OES/unresolved-endpoint-client-sync-state.md)
- [Outlook desktop disconnection due to stale or corrupted local profile cache](wiki/OES/stale-corrupted-outlook-desktop-profile-cache.md)
- [Outlook sync failure due to expired Microsoft 365 authentication tokens](wiki/OES/expired-m365-auth-tokens.md)
- [Stale Outlook Mobile Sync Partnership Blocking Exchange Online Email](wiki/OES/stale-mobile-sync-partnership.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Print Server Stuck Jobs / Driver Failure

- [Corrupt printer driver package on print server blocks shared queue processing](wiki/PDQ/corrupt-driver-package-spooler-load-failure.md)
- [Intermittent print job stalling linked to document rendering or printer-side processing](wiki/PDQ/unresolved-rendering-escalation-holding.md) · self-service
- [Shared printer queue failures due to spool directory permission changes](wiki/PDQ/spool-directory-permissions.md)
- [Shared printer queues left paused after maintenance window](wiki/PDQ/queue-left-paused.md) · self-service
- [Stale print queue-to-driver mapping causes stuck jobs and driver unavailable errors](wiki/PDQ/stale-queue-driver-mapping.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Shared Drive Access Denied

- [Finance shared drive access denied due to broken NTFS permission inheritance or conflicting deny entries](wiki/SDA/broken-ntfs-acl-inheritance-or-deny-ace.md)
- [Mapped drive targeting retired file server path causes access denial](wiki/SDA/stale-or-wrong-mapped-share-path.md) · self-service
- [Shared drive access denied due to missing AD group and stale credentials combined](wiki/SDA/missing-group-plus-stale-credential-or-acl-compound.md)
- [Shared drive access denied due to missing Active Directory security group membership](wiki/SDA/missing-ad-security-group-membership.md)
- [Shared drive access denied due to stale cached SMB credentials](wiki/SDA/stale-cached-smb-credentials.md)
- [Shared drive access denied due to unresolved backend replication or authentication issue](wiki/SDA/unconfirmed-backend-replication-or-auth-escalated.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Software Center Install Blocked (Endpoint Protection)

- [Application install blocked by missing entitlement, stale inventory, and endpoint protection](wiki/SIB/missing-entitlement-plus-endpoint-protection-and-stale-inventory.md)
- [Endpoint protection application control blocking approved software installer](wiki/SIB/endpoint-protection-app-control-block.md)
- [FinanceApp deployment failure with incomplete endpoint telemetry during diagnostics](wiki/SIB/indeterminate-incomplete-telemetry.md)
- [Software Center application hidden by stale device inventory and policy state](wiki/SIB/stale-inventory-policy-targeting-only.md)
- [Software Center install blocked due to missing entitlement group membership](wiki/SIB/missing-entitlement-group-membership.md)
- [Software install blocked by missing entitlement and stale device inventory](wiki/SIB/missing-entitlement-plus-stale-inventory.md)
- [Software installation blocked by endpoint protection with stale device inventory](wiki/SIB/endpoint-protection-block-plus-stale-inventory.md)
- [Software installation blocked by missing entitlement group and endpoint protection policy](wiki/SIB/missing-entitlement-group-membership-plus-endpoint-protection-block.md)

[↑ Back to top](#itsm-knowledge-wiki)

## SSO / MFA Prompt Loop (Okta / Azure AD)

- [Authenticator clock drift and stale enrollment causing MFA prompt loop](wiki/SML/authenticator-clock-drift-totp-mismatch.md)
- [MFA prompt loop caused by stale Okta factor enrollment records](wiki/SML/stale-mfa-factor-enrollment.md)
- [MFA prompt loop from combined stale enrollment and conditional access policy desync](wiki/SML/combined-stale-enrollment-and-policy-desync.md)
- [Post-MFA federation redirect failure causing apparent sign-in loop](wiki/SML/post-mfa-federation-session-fault.md)
- [Repeated MFA prompts due to conditional access and group policy mismatch](wiki/SML/conditional-access-group-policy-mismatch.md)

[↑ Back to top](#itsm-knowledge-wiki)
