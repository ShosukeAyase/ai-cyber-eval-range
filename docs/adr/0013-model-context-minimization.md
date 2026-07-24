# ADR 0013: GPT model context minimization

- Status: Proposed
- Date: 2026-07-24

## Context

Target content is untrusted and model behavior is probabilistic. Minimizing context reduces secret exposure, injection surface, and accidental overreach.

## Decision

Provide redacted, task-specific evidence excerpts and object references. Never include credentials, unrestricted topology, raw approval artifacts, or mutable scope data.

## Alternatives

- Full repository/log dump
- Model-side retrieval with broad access

## Security consequences

- Preserves the four-plane trust model and default-deny posture.
- Requires explicit negative tests and independent telemetry.
- Residual risk is recorded in the risk register rather than hidden by the technology choice.

## Operational consequences

- Requires pinned versions, lifecycle automation, health checks, capacity planning, and documented rollback.
- Increases initial implementation work in exchange for deterministic controls and reproducibility.

## Rejected options

Broad context increases attack surface and makes authorization boundaries ambiguous.

## Revisit conditions

Revisit when secure retrieval, confidential inference, or evaluation evidence supports broader context.
