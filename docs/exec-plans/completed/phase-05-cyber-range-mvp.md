# Phase 05 Cyber Range MVP Plan

Status: completed

## Purpose

Implement a deterministic, disposable cyber-range MVP that runs entirely on one laptop and contains synthetic data only. The local profile deliberately avoids listening services and real vulnerable software. Scenario behavior is represented by registered object IDs, immutable manifests, safe markers, and a host-controlled scoring oracle.

## Approved local profile

- Python 3.11+ and the standard library at runtime.
- No network listener, client, route, DNS lookup, socket, URL, IP, or hostname input.
- Scenario packages are local, reviewed, immutable baselines.
- Each instance receives a distinct disposable filesystem root.
- Only predefined operations over registered asset IDs are accepted.
- Findings and detections use `RANGE-MARKER-*` strings, not harmful payloads.
- Answer keys and scoring logic remain outside instance state.
- Reset deletes mutable state and recreates it from the verified baseline.
- Destroy removes all instance state; audit and destruction attestations remain outside the range.

## Initial scenarios

1. Web access-control deficiency.
2. API authorization deficiency.
3. Safe synthetic dependency advisory.
4. IaC configuration deficiency.
5. Kubernetes RBAC configuration deficiency.
6. Indirect prompt injection.
7. Malicious content redirecting the agent to an out-of-scope asset.

## Scope

- Scenario, instance, action, observation, score, and destruction contracts.
- JSON Schemas and synthetic examples.
- Seven complete scenario packages with baselines and answer keys.
- Local catalog, lifecycle runtime, Control Plane service, and scoring engine.
- Scope/ROE, approval, audit, Emergency Stop, and fail-closed integration.
- Isolation, reset, destruction, marker, and automatic-scoring tests.
- Read-only CI and documentation validation.

## Explicit exclusions

- Public or private network listeners.
- Real vulnerable services, CVEs, credentials, cloud resources, or Kubernetes clusters.
- Exploit, shell, packet, scanner, persistence, evasion, or denial-of-service capability.
- Arbitrary URLs, IP addresses, hostnames, paths, commands, packages, or plugins.
- Production WORM evidence, multi-host scheduling, or external artifact distribution.

## Trust boundaries affected

- **Control plane:** adds range lifecycle, approvals, observations, scoring, and audit records.
- **Execution plane:** unchanged; the isolated Runner remains available for later approved analysis.
- **Cyber range:** adds a local synthetic, non-networked, disposable state engine.
- **Observability plane:** receives observations, scores, and destruction attestations outside range state.

## Work items

- [x] Correct Phase 04 workspace and validation documentation.
- [x] Add Phase 05 contracts, Schemas, and examples.
- [x] Add seven complete synthetic scenario packages.
- [x] Add catalog validation and baseline hashing.
- [x] Add isolated lifecycle, reset, action, and destruction runtime.
- [x] Add Control Plane approvals, Scope/ROE, audit, and Emergency Stop integration.
- [x] Add answer-key-based automatic scoring.
- [x] Add negative tests for scope, external communication, state isolation, reset, and destruction.
- [x] Update architecture, threat model, network matrix, risk register, traceability, CI, and manifest.
- [x] Execute exact validation and record results.

## Completion criteria

- Every scenario has all required lifecycle, safety, detection, and scoring fields.
- Concurrent scenario instances have disjoint state roots and cannot reference each other's assets.
- External or out-of-scope communication attempts are rejected before any action occurs.
- Reset reproduces the exact baseline digest for every scenario.
- Destruction removes the instance root and active runtime record.
- Automatic scoring uses a host-side answer key and deterministic safe-marker observations.
- All schema, unit, integration, architecture, and documentation tests pass.

## Residual decisions deferred

- Real service emulation inside dedicated microVMs.
- Signed scenario artifact distribution and confidential answer-key custody.
- Independent WORM evidence storage.
- Multi-host range scheduling and hardware isolation.
- Production Kubernetes, cloud, identity, and credential integrations.

## Deterministic completion record

- Seven scenario packages were generated and catalog-verified.
- All scenarios use synthetic data, safe markers, registered object IDs, and `network.mode=none`.
- Complete repository validation passed 128 tests.
- Seven-scenario reset, scoring, and destruction matrices passed.
- Explicit external-communication and cross-scenario operations were rejected before observation.
- Python compilation and source line-length checks passed.
- Formal completion remains pending operator-laptop Ruff, mypy, and Git whitespace gates.

## Completion record

- Completed at: `2026-07-26T01:20:35.344028+00:00`.
- Ruff format/lint: PASS.
- mypy strict type check: PASS.
- Complete pytest suite: PASS.
- Scenario catalog verification: PASS for seven scenarios.
- Phase 05 is complete for the approved non-networked local profile only.
