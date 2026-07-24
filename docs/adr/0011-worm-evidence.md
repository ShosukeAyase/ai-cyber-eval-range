# ADR 0011: WORM evidence storage

- Status: Proposed
- Date: 2026-07-24

## Context

Immutability must be enforced below the application and outside execution IAM. Hashes alone detect alteration but do not prevent deletion.

## Decision

Use retention-locked object storage in the observability domain, with signed evidence manifests and a separate offline copy for high-value incidents.

## Alternatives

- Mutable object storage plus hashes
- Database-only evidence
- Filesystem append-only flag

## Security consequences

- Preserves the four-plane trust model and default-deny posture.
- Requires explicit negative tests and independent telemetry.
- Residual risk is recorded in the risk register rather than hidden by the technology choice.

## Operational consequences

- Requires pinned versions, lifecycle automation, health checks, capacity planning, and documented rollback.
- Increases initial implementation work in exchange for deterministic controls and reproducibility.

## Rejected options

These can be overridden by administrators or provide weaker retention guarantees.

## Revisit conditions

Revisit after legal retention periods and selected storage capabilities are approved.
