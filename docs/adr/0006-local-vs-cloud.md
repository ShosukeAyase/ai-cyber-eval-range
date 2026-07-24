# ADR 0006: Local-first versus cloud deployment

- Status: Proposed
- Date: 2026-07-24

## Context

Local-first makes physical routing and offline package mirrors inspectable. Cloud can provide stronger account-level isolation and managed WORM/IAM but introduces metadata, service-control, and egress complexity.

## Decision

Start local-first on dedicated hosts and isolated switching. Define but do not implement a later cloud profile with separate accounts/projects for each plane.

## Alternatives

- Cloud-first
- Single-host developer deployment

## Security consequences

- Preserves the four-plane trust model and default-deny posture.
- Requires explicit negative tests and independent telemetry.
- Residual risk is recorded in the risk register rather than hidden by the technology choice.

## Operational consequences

- Requires pinned versions, lifecycle automation, health checks, capacity planning, and documented rollback.
- Increases initial implementation work in exchange for deterministic controls and reproducibility.

## Rejected options

Single-host deployment cannot satisfy independent trust boundaries. Cloud-first delays core safety validation behind provider-specific design.

## Revisit conditions

Revisit after phase-01 review and selection of an approved cloud/provider account model.
