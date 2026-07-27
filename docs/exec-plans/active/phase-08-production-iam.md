# Phase 08: Production IAM and Workload Identity — Active Plan

Status: **ACTIVE / PRODUCTION NO-GO**  
Started: 2026-07-26

## Objective

Replace caller-asserted actor identifiers at production-facing trust boundaries with cryptographically verified human and workload principals. Preserve the Phase 03 local demo as a clearly marked compatibility profile.

## Security invariants

- Human identity is accepted only after issuer, audience, subject, signature or authoritative introspection, token identifier, nonce, issued-at, not-before, expiry, authentication strength, role, trust-domain, engagement, and device-posture validation.
- Workload identity is accepted only after SPIFFE ID, trust domain, workload binding, SVID validity, lifetime, peer authorization, and revocation validation.
- IdP, Workload API, replay-cache, revocation, audit, or claim-validation failure denies state-changing operations.
- Request-body `actor_id`, role, claim, or trust-domain values are never an identity source.
- Requester and approver remain distinct verified human principals.
- Privileged elevation is short-lived, engagement-bound, ticket-bound, and approved by two independent principals.
- Break-glass use emits a dedicated high-priority audit event.
- Evidence collectors never persist bearer tokens, client secrets, or SVID private keys.

## Implementation scope in this branch

1. Typed human/workload principal contracts and canonical authorization context.
2. OIDC-shaped verifier interface and deterministic signed-token fake.
3. Live RFC 7662 introspection adapter with HTTPS enforcement, authoritative inactive-token rejection, claim normalization, temporal checks, phishing-resistant authentication checks, and fail-closed outage behavior.
4. SPIFFE/SVID-shaped verifier interface and deterministic fake Workload API boundary.
5. Replay cache, revocation registry, PAM/JIT grant contract, and append-only identity audit interface.
6. Identity boundary that rejects actor spoofing, role escalation, self-approval, trust-domain crossing, and stale credentials.
7. `ProductionIdentityGateway` binding every `WriteOperation` to a verified human role or workload trust zone.
8. Static complete-mediation coverage generator and CSV inventory.
9. OIDC and SPIRE/mTLS evidence collectors that reject missing or failed cases.
10. Isolated Keycloak reference profile and kind/SPIRE Helm staging bootstrap.
11. Content-validating completion gate; empty evidence directories no longer pass.
12. Unit, integration, schema, architecture, and full regression tests.
13. Operational runbook, rollback procedure, threat model, ADR, and validation workflow.

## Explicitly out of scope

- Automatic creation or administration of an enterprise IdP tenant.
- Storage of enterprise IdP secrets or live user tokens in the repository.
- Automatic declaration that local Keycloak development mode is enterprise-gate eligible.
- Automatic generation of a passing SPIRE/mTLS marker without an executed workload test.
- Production PAM vendor integration and production ticket-system verification.
- Independent WORM identity audit storage.

## Work plan

- [x] Add typed contracts and deterministic fakes.
- [x] Add fail-closed negative tests.
- [x] Add live OIDC introspection adapter and evidence collector.
- [x] Add production write-operation identity gateway and static 100% inventory check.
- [x] Add isolated SPIRE Helm staging bootstrap and strict evidence assembly contract.
- [x] Reject empty or incomplete evidence paths in the completion script.
- [x] Add schemas, examples, architecture, and operational documentation.
- [ ] Execute the live OIDC collector against an enterprise staging IdP using phishing-resistant authentication.
- [ ] Execute signing-key rotation, token/session revocation, and IdP outage tests end-to-end.
- [ ] Execute SPIRE server/agent staging, workload attestation, SVID rotation, revocation, and application-level mTLS peer authorization.
- [ ] Route every deployed production-facing state-changing adapter through `ProductionIdentityGateway` and independently review the generated inventory.
- [ ] Export identity events to independently administered evidence storage and test its outage behavior.
- [ ] Execute the full completion script with content-valid live evidence.

## Completion gate

This plan must remain under `active/` until all of the following are evidenced:

- 100% declared state-changing operation mediation by `VerifiedPrincipal` and no production-boundary `actor_id` parameter.
- 100% deployed service-to-service state-changing calls carry verified workload identity.
- Identity-level requester/approver separation is enforced end-to-end.
- IdP and Workload API outage tests show no unsafe fail-open.
- Enterprise OIDC staging and SPIRE/mTLS staging tests pass with required evidence content.
- Evidence Plane export and outage tests pass.
- No Critical or High residual risk remains within Phase 08 scope.
- An independent reviewer approves completion.

Until then, Phase 08 is **not completed** and the repository retains production **NO-GO**.
