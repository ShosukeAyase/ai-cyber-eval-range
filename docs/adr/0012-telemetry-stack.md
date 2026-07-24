# ADR 0012: Logs, metrics, and traces

- Status: Proposed
- Date: 2026-07-24

## Context

OpenTelemetry reduces instrumentation coupling. Security evidence requires stricter retention and access than operational metrics.

## Decision

Standardize instrumentation on OpenTelemetry. Store security logs/evidence in a SIEM-capable backend; keep metrics and traces in purpose-built stores under the observability plane.

## Alternatives

- Single all-in-one vendor
- Prometheus-only
- Application logs only

## Security consequences

- Preserves the four-plane trust model and default-deny posture.
- Requires explicit negative tests and independent telemetry.
- Residual risk is recorded in the risk register rather than hidden by the technology choice.

## Operational consequences

- Requires pinned versions, lifecycle automation, health checks, capacity planning, and documented rollback.
- Increases initial implementation work in exchange for deterministic controls and reproducibility.

## Rejected options

A single backend may be acceptable operationally but must not collapse evidence custody. Metrics alone are insufficient for investigation.

## Revisit conditions

Revisit after scale tests, query requirements, and retention cost analysis.
