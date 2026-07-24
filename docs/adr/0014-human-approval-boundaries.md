# ADR 0014: Human-in-the-loop approval boundaries

- Status: Proposed
- Date: 2026-07-24

## Context

Human approval is a governance control, not a substitute for policy or sandboxing. Risk-tiered approval limits fatigue and preserves separation of duties.

## Decision

Require independent approval for state changes, credentialed tests, PoC validation, and any action with material availability/integrity impact. Prohibited actions remain non-approvable.

## Alternatives

- Approve every tool call
- Approve only whole engagement
- Model self-approval

## Security consequences

- Preserves the four-plane trust model and default-deny posture.
- Requires explicit negative tests and independent telemetry.
- Residual risk is recorded in the risk register rather than hidden by the technology choice.

## Operational consequences

- Requires pinned versions, lifecycle automation, health checks, capacity planning, and documented rollback.
- Increases initial implementation work in exchange for deterministic controls and reproducibility.

## Rejected options

Per-call approval is unworkable; engagement-only approval is too broad; model self-approval is invalid.

## Revisit conditions

Revisit based on measured false-positive/negative rates and approver workload, without weakening non-approvable prohibitions.
