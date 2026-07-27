# ADR 0016: Separate OIDC Human Identity from SPIFFE Workload Identity

Status: Accepted for Phase 08 implementation; live deployment pending.

## Context

The local MVP uses caller-supplied actor identifiers. This is suitable only for deterministic local demonstrations and cannot establish a production security principal. Human and workload identities have different lifecycle, authentication, revocation, and trust requirements.

## Decision

- Use enterprise OIDC for human authentication.
- Require phishing-resistant MFA for privileged human access.
- Use SPIFFE/SPIRE-compatible identities and short-lived SVIDs for workloads.
- Separate Control, Execution, Range, Evidence, and Management trust domains.
- Use mTLS for service-to-service channels in the live profile.
- Normalize both identity classes into a typed `VerifiedPrincipal` and canonical authorization context.
- Keep roles and engagement attributes as policy inputs; do not accept them from request bodies or model output.
- Require JIT/PAM grants for privileged elevation.
- Fail closed on identity, revocation, replay, audit, or Workload API failure.

## Alternatives

- Platform-native cloud workload identity for every deployment.
- Mutual TLS with manually managed service certificates.
- A single enterprise directory contract for both humans and workloads.
- Long-lived bearer tokens for service authentication.

## Security consequences

Positive consequences include cryptographically attributable principals, short-lived workload credentials, explicit trust-domain separation, replay and revocation checks, and identity-level separation of duties. New risks include IdP/SPIRE dependency failure, trust-bundle or signing-key compromise, incorrect federation, and identity-cache staleness. All such failures must deny state changes.

## Operational consequences

Live completion requires enterprise IdP registration, SPIRE server/agent operation, trust-bundle rotation, service mTLS, revocation distribution, PAM/JIT integration, and independently administered identity audit storage. Operators require runbooks for outage, rotation, revocation, break-glass use, and rollback to production NO-GO.

## Rejected options

### Long-lived static service tokens

Rejected because rotation, attribution, blast-radius control, and revocation are inadequate.

### Network location as identity

Rejected because network reachability does not authenticate a workload and does not survive modern multi-tenant or cloud trust boundaries.

### One identity contract for humans and workloads

Rejected because it conflates interactive authentication, device posture, human roles, workload attestation, and service identity.

### Caller-supplied actor identifiers

Retained only in the explicitly local Phase 03 compatibility profile. Rejected for production-facing APIs.

## Revisit conditions

Revisit if an equivalent open standard supersedes OIDC or SPIFFE, or if a platform-native identity system can demonstrate equivalent cryptographic identity, short-lived credentials, workload attestation, revocation, federation, and portability.
