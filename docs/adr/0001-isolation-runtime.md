# ADR 0001: Isolation runtime: VM, microVM, and container

- Status: Proposed
- Date: 2026-07-24

## Context

Containers have lowest overhead but share the host kernel. microVMs improve isolation with lower overhead than full VMs. Full VMs support the broadest guest and device models.

## Decision

Use a risk-tiered runtime: hardened containers only for low-risk static analysis; Firecracker microVMs for Linux dynamic tests; full KVM/libvirt VMs for Windows and heterogeneous scenarios.

## Alternatives

- All full VMs
- All microVMs
- All containers

## Security consequences

- Preserves the four-plane trust model and default-deny posture.
- Requires explicit negative tests and independent telemetry.
- Residual risk is recorded in the risk register rather than hidden by the technology choice.

## Operational consequences

- Requires pinned versions, lifecycle automation, health checks, capacity planning, and documented rollback.
- Increases initial implementation work in exchange for deterministic controls and reproducibility.

## Rejected options

Defaulting every workload to one isolation type either wastes resources or creates an unacceptable shared-kernel boundary.

## Revisit conditions

Revisit after measured escape-resistance testing, performance baselines, or a material runtime vulnerability.
