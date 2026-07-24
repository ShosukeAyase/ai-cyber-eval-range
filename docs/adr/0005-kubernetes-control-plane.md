# ADR 0005: Kubernetes as platform control substrate

- Status: Proposed
- Date: 2026-07-24

## Context

Kubernetes adds API, admission, supply-chain, service-account, and node compromise paths. It also offers scheduling and policy integrations. Initial safety validation benefits from a smaller control substrate.

## Decision

Do not require Kubernetes for the v1 control plane. Permit a dedicated management cluster only after threat-model and operational controls are proven; never share it with range targets.

## Alternatives

- Kubernetes from day one
- No Kubernetes anywhere

## Security consequences

- Preserves the four-plane trust model and default-deny posture.
- Requires explicit negative tests and independent telemetry.
- Residual risk is recorded in the risk register rather than hidden by the technology choice.

## Operational consequences

- Requires pinned versions, lifecycle automation, health checks, capacity planning, and documented rollback.
- Increases initial implementation work in exchange for deterministic controls and reproducibility.

## Rejected options

Using the same cluster for control, execution, and range violates trust separation. Prohibiting Kubernetes entirely would block a required scenario family.

## Revisit conditions

Revisit after management-cluster hardening, runtime isolation, backup, and emergency-stop testing.
