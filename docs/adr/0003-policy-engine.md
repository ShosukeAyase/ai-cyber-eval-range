# ADR 0003: Policy engine

- Status: Proposed
- Date: 2026-07-24

## Context

OPA separates decision from enforcement, evaluates structured input, supports signed/versioned bundles and decision logs, and can run close to enforcement points.

## Decision

Use OPA/Rego as the Policy Decision Point. Enforcement remains in Tool Gateway, scheduler, lifecycle manager, and network controls.

## Alternatives

- Custom policy library
- Cloud-vendor IAM only
- Cedar or other policy language

## Security consequences

- Preserves the four-plane trust model and default-deny posture.
- Requires explicit negative tests and independent telemetry.
- Residual risk is recorded in the risk register rather than hidden by the technology choice.

## Operational consequences

- Requires pinned versions, lifecycle automation, health checks, capacity planning, and documented rollback.
- Increases initial implementation work in exchange for deterministic controls and reproducibility.

## Rejected options

Custom authorization logic increases review burden and inconsistency. Cloud IAM alone cannot express engagement/test-case/approval semantics.

## Revisit conditions

Revisit if Rego maintainability, formal verification needs, or latency/availability targets are not met.
