# ADR 0002: Firecracker, Kata Containers, and KVM/libvirt

- Status: Proposed
- Date: 2026-07-24

## Context

Firecracker has a minimal device model and one microVM per process, but requires host-level egress filtering. Kata integrates VM isolation with container orchestration. KVM/libvirt is flexible but operationally heavier.

## Decision

Adopt Firecracker for standalone Linux runners, Kata as an optional Kubernetes RuntimeClass, and KVM/libvirt for Windows/domain and complex-network scenarios.

## Alternatives

- Firecracker only
- Kata only
- KVM/libvirt only

## Security consequences

- Preserves the four-plane trust model and default-deny posture.
- Requires explicit negative tests and independent telemetry.
- Residual risk is recorded in the risk register rather than hidden by the technology choice.

## Operational consequences

- Requires pinned versions, lifecycle automation, health checks, capacity planning, and documented rollback.
- Increases initial implementation work in exchange for deterministic controls and reproducibility.

## Rejected options

No single option covers Linux density, Kubernetes ergonomics, Windows support, and complex labs equally well.

## Revisit conditions

Revisit when Kata 4.x operational maturity, confidential-computing support, or Windows runtime requirements change.
