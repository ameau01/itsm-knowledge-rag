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

- [Incomplete Password Reset Due to Expired Reset Token](wiki/ALP/expired-reset-token-primary.md)
- [Mobile Cached Credentials Trigger AD Lockout With Expired Reset Token](wiki/ALP/stale-mobile-credentials-plus-expired-reset-token.md)
- [Recurring AD Lockouts From Stale Cached Credentials on iOS Mobile Devices](wiki/ALP/stale-mobile-cached-credentials.md)
- [Recurring AD Lockouts from Unidentified Stale Credential Source Post-Reset](wiki/ALP/stale-credentials-unidentified-source.md)

[↑ Back to top](#itsm-knowledge-wiki)

## BitLocker Not Enabled / Recovery Key Not Escrowed

- [BitLocker Enabled Locally but Intune Reports Noncompliant Due to Escrow and Compliance Reporting Desynchronization](wiki/EDE/mdm-sync-failure-causing-state-desync.md)
- [BitLocker Not Initialized on Endpoint Preventing Recovery Key Escrow](wiki/EDE/inconclusive-evidence-bitlocker-not-fully-enabled.md)
- [Deprecated Intune Encryption Policy Prevents BitLocker Activation and Key Escrow](wiki/EDE/intune-policy-not-assigned-or-stale-deprecated-policy.md)
- [Recovery Key Escrow Failure Leaves Device Noncompliant Despite Healthy TPM](wiki/EDE/recovery-key-escrow-failure-despite-healthy-tpm-and-policy.md)
- [Uninitialized TPM Protector Prevents BitLocker Encryption and Recovery Key Escrow](wiki/EDE/tpm-protector-not-initialized.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Corporate Wi-Fi 802.1X Authentication Failures

- [Corrupted Endpoint Wireless Profile Causes Intermittent 802.1X Authentication Failure](wiki/WCI/stale-or-corrupt-client-wifi-profile.md)
- [Expired Wireless Controller or RADIUS Certificate Blocks 802.1X Authentication](wiki/WCI/expired-radius-controller-eap-tls-certificate.md)
- [Incomplete EAP-TLS Certificate Propagation Across Wireless Controller Cluster](wiki/WCI/cert-rollover-incomplete-trust-propagation.md)
- [Incorrect NAC Policy Mapping Causes Post-Authentication VLAN Misassignment](wiki/WCI/incorrect-nac-policy-assignment.md)
- [Intermittent 802.1X Wi-Fi Rejection After Certificate Rotation and Profile Mismatch](wiki/WCI/unclassified-insufficient-evidence.md)
- [Wireless AP Radio Instability Causing Repeated Client Deauthentication](wiki/WCI/wireless-rf-controller-instability.md)

[↑ Back to top](#itsm-knowledge-wiki)

## GlobalProtect VPN Immediate Post-MFA Disconnect

- [Expired Device Certificate Causes Post-MFA GlobalProtect Tunnel Teardown](wiki/VDA/expired-device-certificate-post-mfa-validation-failure.md)
- [GlobalProtect Profile Certificate Mapping Mismatch Causing Post-Auth Disconnects](wiki/VDA/globalprotect-profile-cert-mapping-misconfiguration.md)
- [Intermittent GlobalProtect VPN Disconnections After Successful MFA Authentication](wiki/VDA/indeterminate-intermittent-disconnect.md)
- [Post-Authentication GlobalProtect Gateway Instability Terminating VPN Sessions](wiki/VDA/gateway-portal-post-auth-instability.md)
- [Stale VPN Profile After Certificate Renewal Causes Tunnel Teardown](wiki/VDA/stale-vpn-profile-blocking-renewed-certificate.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Integration Gateway API Timeouts

- [Downstream API Latency Exceeds Integration Gateway Timeout Causing 504 Errors](wiki/AIT/downstream-api-latency-exceeds-timeout.md)
- [Downstream API Rate-Limit Throttling Causes Gateway Timeout Integration Failures](wiki/AIT/downstream-rate-limiting-throttling.md)
- [Expired Integration Gateway API Token Causes Sync Timeouts](wiki/AIT/expired-api-token-auth-failures.md)
- [Integration Gateway Timeout and Sync Failures During Scheduled Batch Windows](wiki/AIT/unconfirmed-mixed-credential-latency-throttling.md)
- [Stale Retry Policy Amplifies Downstream Latency Into Gateway Timeout Storms](wiki/AIT/stale-retry-backoff-amplifies-latency.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Internal DNS Resolution Failures

- [Client-Side DNS Cache or Local Network Condition Causing Resolution Failures](wiki/DRF/no-server-side-fault-client-side-or-transient.md)
- [Inconsistent Internal Resolver Cache or Forwarder State After DNS Maintenance](wiki/DRF/resolver-path-inconsistency-mixed-cause.md)
- [Missing or Incorrect Conditional Forwarder on Internal DNS Resolver](wiki/DRF/missing-or-incorrect-conditional-forwarder.md)
- [Stale A Record in Authoritative Internal DNS Zone](wiki/DRF/stale-authoritative-zone-record.md)
- [Stale Resolver Cache Serving Outdated Records After Internal Zone Update](wiki/DRF/stale-resolver-cache-after-record-change.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Internal Web Service Load-Balancer TLS Certificate Expiry

- [Expired Certificate on Load Balancer After Automated Renewal Failure](wiki/CES/automated-renewal-process-failed-to-complete.md)
- [Expired or Incomplete TLS Certificate Chain Served by Load Balancer](wiki/CES/valid-leaf-but-stale-or-missing-intermediate-served.md)
- [Renewed Certificate Chain Not Deployed to Load Balancer Before Expiry](wiki/CES/renewed-chain-not-deployed-to-lb-with-monitoring-gap.md)
- [Suspected Transient Certificate-Serving Fault on Load Balancer Unconfirmed](wiki/CES/unconfirmed-tls-presentation-issue-evidence-gap.md)
- [Wrong Certificate Bound to Load Balancer Causing Hostname Validation Failures](wiki/CES/wrong-certificate-bound-to-endpoint.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Intune Device Non-Compliant Encryption (Conditional Access Block)

- [BitLocker Encryption Not Active or Attested Causing Noncompliance Block](wiki/DCP/encryption-actually-disabled-or-attestation-failed.md)
- [Deprecated Compliance Policy Reference Causes False Encryption Noncompliance](wiki/DCP/stale-deprecated-compliance-policy-reference.md)
- [Intermittent Encryption Signal Loss After OS Update Causes False Noncompliance](wiki/DCP/encryption-telemetry-broken-after-os-or-hardware-change.md)
- [Stale Compliance Refresh Leaves Devices Noncompliant Despite Sync Attempts](wiki/DCP/indeterminate-compliance-refresh-failure.md)
- [Stale Compliance Signal Mismatch Between Intune and Conditional Access](wiki/DCP/stale-compliance-state-mismatch-ca-cache.md)
- [Stale Intune Check-In Causes Missing Encryption Signal and Noncompliance](wiki/DCP/stale-checkin-missing-encryption-signal.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Laptop Slow Post-Login (CPU / Disk Contention)

- [Endpoint Protection Scan Backlog Causing Post-Login CPU Saturation](wiki/LPD/endpoint-scan-backlog-startup-disk-contention.md)
- [Intermittent Post-Login Slowdown With High Antimalware CPU Usage](wiki/LPD/unconfirmed-transient-post-login-slowdown.md) · self-service
- [Post-Login CPU Contention From Resource-Heavy Startup Policy Deployment](wiki/LPD/resource-heavy-startup-policy.md)
- [Post-Login Laptop Sluggishness Due to Temp File Disk Exhaustion](wiki/LPD/low-disk-temp-file-accumulation.md) · self-service

[↑ Back to top](#itsm-knowledge-wiki)

## Outlook / Exchange Online Mailbox Sync Failures

- [Corrupted Microsoft 365 Authentication Tokens Blocking Outlook Sync](wiki/OES/expired-m365-auth-tokens.md)
- [Exchange Online Mailbox Throttling Disrupting Client Synchronization](wiki/OES/exchange-online-mailbox-throttling.md)
- [Exchange Online Mailbox-Side Sync Fault Across Multiple Clients](wiki/OES/suspected-server-side-mailbox-fault.md)
- [Intune Device Compliance Block Disrupts Exchange Online Mobile Sync](wiki/OES/intune-mdm-device-compliance-block.md)
- [Stale Mobile Sync Partnership Blocks Outlook Mobile Email](wiki/OES/stale-mobile-sync-partnership.md)
- [Stale Outlook Profile and Unhealthy Mobile Sync Partnership Block Mailbox Access](wiki/OES/unresolved-endpoint-client-sync-state.md)
- [Stale or Corrupted Outlook Desktop Profile Blocks Exchange Online Sync](wiki/OES/stale-corrupted-outlook-desktop-profile-cache.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Print Server Stuck Jobs / Driver Failure

- [Corrupt Printer Driver Package Causes Queue Failures and Driver Unavailable Errors](wiki/PDQ/corrupt-driver-package-spooler-load-failure.md)
- [Intermittent Print Job Stalling on Complex Documents](wiki/PDQ/unresolved-rendering-escalation-holding.md) · self-service
- [Print Spooler Fails Due to Incorrect Queue or Spool Directory Permissions](wiki/PDQ/spool-directory-permissions.md)
- [Shared Print Queues Left Paused After Maintenance Window](wiki/PDQ/queue-left-paused.md) · self-service
- [Stale Queue-to-Driver Mapping Causes Stuck Print Jobs](wiki/PDQ/stale-queue-driver-mapping.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Shared Drive Access Denied

- [Broken NTFS Inheritance or Explicit Deny ACE on Shared Folder](wiki/SDA/broken-ntfs-acl-inheritance-or-deny-ace.md)
- [Compound Missing AD Group Membership and Stale Cached Credentials Block Share Access](wiki/SDA/missing-group-plus-stale-credential-or-acl-compound.md)
- [Kerberos Token Not Reflecting AD Group Despite Confirmed Membership](wiki/SDA/unconfirmed-backend-replication-or-auth-escalated.md)
- [Mapped Drive Targeting Retired UNC Path After File Server Migration](wiki/SDA/stale-or-wrong-mapped-share-path.md) · self-service
- [Missing AD Security Group Membership Denies Department Share Access](wiki/SDA/missing-ad-security-group-membership.md)
- [Stale Cached SMB Credentials Cause Mapped Drive Access Denial](wiki/SDA/stale-cached-smb-credentials.md)

[↑ Back to top](#itsm-knowledge-wiki)

## Software Center Install Blocked (Endpoint Protection)

- [Endpoint Protection Application Control Blocking Software Center Installer](wiki/SIB/endpoint-protection-app-control-block.md)
- [Endpoint Protection Installer Block Combined With Stale Intune Inventory](wiki/SIB/endpoint-protection-block-plus-stale-inventory.md)
- [FinanceApp Unavailable in Software Center Despite Valid Entitlement](wiki/SIB/indeterminate-incomplete-telemetry.md)
- [Missing Entitlement Group Membership Blocks Application Install](wiki/SIB/missing-entitlement-group-membership.md)
- [Missing Entitlement Group Membership Combined With Stale Device Inventory](wiki/SIB/missing-entitlement-plus-stale-inventory.md)
- [Missing Entitlement Group Membership With Endpoint Protection Blocking](wiki/SIB/missing-entitlement-group-membership-plus-endpoint-protection-block.md)
- [Missing Entitlement, Stale Inventory, and Endpoint Protection Block Combined](wiki/SIB/missing-entitlement-plus-endpoint-protection-and-stale-inventory.md)
- [Stale Endpoint Inventory and Policy State Blocking Application Deployment](wiki/SIB/stale-inventory-policy-targeting-only.md)

[↑ Back to top](#itsm-knowledge-wiki)

## SSO / MFA Prompt Loop (Okta / Azure AD)

- [Federated SSO Claim Mapping Fault Causes Post-MFA Session Loop](wiki/SML/post-mfa-federation-session-fault.md)
- [Group-Scope Policy Mismatch Between Okta and Azure AD Causes MFA Loop](wiki/SML/conditional-access-group-policy-mismatch.md)
- [Stale MFA Enrollment and Group Policy Mismatch Cause SSO Authentication Loop](wiki/SML/combined-stale-enrollment-and-policy-desync.md)
- [Stale Okta MFA Enrollment Records Cause SSO Challenge Loop](wiki/SML/stale-mfa-factor-enrollment.md)
- [TOTP Clock Drift and Stale Factor Enrollment MFA Prompt Loop](wiki/SML/authenticator-clock-drift-totp-mismatch.md)

[↑ Back to top](#itsm-knowledge-wiki)
