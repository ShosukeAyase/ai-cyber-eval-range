# ADR-0015: Local synthetic non-networked range

## Context

Phase 05 must cover web, API, dependency, IaC, Kubernetes RBAC, prompt-injection, and scope-redirection scenarios on one free laptop without exposing vulnerable services or connecting to external networks.

## Decision

Use a deterministic filesystem-backed range engine. Scenario packages contain reviewed synthetic files, object-ID operation allowlists, harmless markers, reset digests, destruction requirements, and host-side answer keys. The MVP creates no listener and executes no scenario content.

## Alternatives

- Rootless containers running intentionally vulnerable services.
- Disposable microVMs with internal-only services.
- Full local Kubernetes and cloud simulators.

## Security consequences

The selected profile removes remote exploitability and outbound communication from the MVP. It also limits realism: findings are marker-driven representations rather than proof against running vulnerable software.

## Operational consequences

The range is free, deterministic, fast to reset, and portable across Python-capable laptops. No container image is required for Phase 05 deterministic validation.

## Rejected options

Publicly reachable vulnerable applications, live cloud accounts, real CVEs requiring active exploitation, external package retrieval, and host-network service exposure are rejected.

## Revisit conditions

Revisit when a dedicated microVM host, signed offline artifacts, isolated internal networking, independent observability, and explicit approval for live service emulation are available.
