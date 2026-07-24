# ADR 0009: Secret and credential management

- Status: Proposed
- Date: 2026-07-24

## Context

The broker must prevent model exposure, issue short-lived credentials, revoke rapidly, and produce issuance audit records.

## Decision

Use a dedicated Credential Broker backed by an HSM-capable secrets system and workload identity. Prefer dynamic, target-bound credentials; use OpenBao/Vault-class capability or cloud equivalent.

## Alternatives

- Kubernetes Secrets
- Environment variables
- Static encrypted files

## Security consequences

- Preserves the four-plane trust model and default-deny posture.
- Requires explicit negative tests and independent telemetry.
- Residual risk is recorded in the risk register rather than hidden by the technology choice.

## Operational consequences

- Requires pinned versions, lifecycle automation, health checks, capacity planning, and documented rollback.
- Increases initial implementation work in exchange for deterministic controls and reproducibility.

## Rejected options

These options expose secrets too broadly or lack target/action binding and rapid lifecycle control.

## Revisit conditions

Revisit after IAM provider, HSM, and dynamic-secret support are selected.
