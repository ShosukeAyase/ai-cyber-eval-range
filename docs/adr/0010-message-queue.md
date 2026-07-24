# ADR 0010: Message queue

- Status: Proposed
- Date: 2026-07-24

## Context

Jobs need durable scheduling and stop propagation without making the queue an authorization source. Idempotency handles duplicate delivery.

## Decision

Use a durable at-least-once queue with explicit idempotency, bounded retention, per-engagement subjects, and no payload secrets. NATS JetStream is the initial preference; RabbitMQ quorum queues are the fallback.

## Alternatives

- Kafka
- Database polling
- In-memory queue

## Security consequences

- Preserves the four-plane trust model and default-deny posture.
- Requires explicit negative tests and independent telemetry.
- Residual risk is recorded in the risk register rather than hidden by the technology choice.

## Operational consequences

- Requires pinned versions, lifecycle automation, health checks, capacity planning, and documented rollback.
- Increases initial implementation work in exchange for deterministic controls and reproducibility.

## Rejected options

Kafka is operationally heavy for initial control messages; polling raises latency; in-memory delivery loses state.

## Revisit conditions

Revisit if throughput, replay, multi-region, or audit-stream requirements exceed the initial profile.
