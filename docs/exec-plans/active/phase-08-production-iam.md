# Phase 08: Production IAM and Workload Identity — Active Plan

Status: **ACTIVE / PRODUCTION NO-GO**  
Started: 2026-07-26

## Objective

Replace caller-asserted actor identifiers at production-facing trust boundaries with cryptographically verified human and workload principals. Preserve the Phase 03 local demo as a clearly marked compatibility profile.

## Security invariants

- Human identity is accepted only after issuer, audience, subject, signature, token identifier, nonce, issued-at, not-before, expiry, authentication strength, role, trust-domain, engagement, and device-posture validation.
- Workload identity is accepted only after SPIFFE ID, trust domain, audience, workload binding, SVID validity, lifetime, and revocation validation.
- IdP, Workload API, replay-cache, revocation, audit, or claim-validation failure denies state-changing operations.
- Request-body `actor_id`, role, claim, or trust-domain values are never an identity source.
- Requester and approver remain distinct verified human principals.
- Privileged elevation is short-lived, engagement-bound, ticket-bound, and approved by two independent principals.
- Break-glass use emits a dedicated high-priority audit event.

## Implementation scope in this branch

1. Typed human/workload principal contracts and canonical authorization context.
2. OIDC-shaped verifier interface and deterministic signed-token fake.
3. SPIFFE/SVID-shaped verifier interface and deterministic fake Workload API boundary.
4. Replay cache, revocation registry, PAM/JIT grant contract, and append-only identity audit interface.
5. Identity boundary that rejects actor spoofing, role escalation, self-approval, trust-domain crossing, and stale credentials.
6. Closed JSON Schemas and synthetic examples.
7. Unit, integration, schema, and architecture tests.
8. Operational runbook, rollback procedure, threat model, ADR, and validation workflow.

## Explicitly out of scope

- Live enterprise IdP registration, discovery, JWKS rotation, logout, or session termination.
- Live SPIRE server/agent deployment, node/workload attestation, X.509-SVID validation, federation, or trust-bundle rotation.
- Production API middleware migration of every existing service method.
- PAM vendor integration and production ticket-system verification.
- Independent WORM identity audit storage.

## Work plan

- [x] Add typed contracts and deterministic fakes.
- [x] Add fail-closed negative tests.
- [x] Add schemas and examples.
- [x] Add architecture and operational documentation.
- [ ] Integrate a live OIDC provider in staging.
- [ ] Integrate SPIRE in isolated staging and validate mTLS service-to-service identity.
- [ ] Migrate every state-changing API from `actor_id` to `VerifiedPrincipal` at the public boundary.
- [ ] Validate revocation and session termination end-to-end.
- [ ] Export identity events to independently administered evidence storage.
- [ ] Execute the full validation and live-gate script.

## Completion gate

This plan must remain under `active/` until all of the following are evidenced:

- 100% state-changing API mediation by verified principals.
- 100% service-to-service calls carry verified workload identity.
- Identity-level requester/approver separation is enforced end-to-end.
- IdP and Workload API outage tests show no unsafe fail-open.
- Live enterprise IdP and SPIRE staging tests pass.
- No Critical or High residual risk remains within Phase 08 scope.

Until then, Phase 08 is **not completed** and the repository retains production **NO-GO**.
