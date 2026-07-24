# ADR 0007: Independent observability plane

- Status: Proposed
- Date: 2026-07-24

## Context

Execution compromise must not allow deletion or alteration of audit records. Independent custody also improves incident investigation and scoring integrity.

## Decision

Run observability in a separate administrative and identity domain with write-only ingestion and WORM evidence storage.

## Alternatives

- Shared logging stack
- Runner-local logs only

## Security consequences

- Preserves the four-plane trust model and default-deny posture.
- Requires explicit negative tests and independent telemetry.
- Residual risk is recorded in the risk register rather than hidden by the technology choice.

## Operational consequences

- Requires pinned versions, lifecycle automation, health checks, capacity planning, and documented rollback.
- Increases initial implementation work in exchange for deterministic controls and reproducibility.

## Rejected options

Shared administration and mutable local logs fail the non-repudiation and fail-closed requirements.

## Revisit conditions

Revisit only if an equivalent cryptographically verifiable one-way design is demonstrated.
