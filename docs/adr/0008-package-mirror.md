# ADR 0008: Offline package and image mirror

- Status: Proposed
- Date: 2026-07-24

## Context

The range cannot use public package networks. A promotion workflow supports provenance, SBOM, malware/vulnerability checks, license review, and rollback.

## Decision

Use a quarantine-to-promoted mirror workflow. Prefer a general artifact repository plus OCI registry; engagements consume only signed, pinned, pre-scanned artifacts.

## Alternatives

- Direct internet proxy
- Per-scenario ad hoc caches
- Air-gap media only

## Security consequences

- Preserves the four-plane trust model and default-deny posture.
- Requires explicit negative tests and independent telemetry.
- Residual risk is recorded in the risk register rather than hidden by the technology choice.

## Operational consequences

- Requires pinned versions, lifecycle automation, health checks, capacity planning, and documented rollback.
- Increases initial implementation work in exchange for deterministic controls and reproducibility.

## Rejected options

A transparent internet proxy violates the route invariant. Ad hoc caches are not reproducible or centrally governed.

## Revisit conditions

Revisit if artifact types or air-gap transfer requirements change.
