# Cyber Range MVP

## Purpose

Phase 05 implements a local, deterministic cyber range containing synthetic data only. It does not start a vulnerable web server, API listener, Kubernetes cluster, cloud resource, or external network path. Each scenario is a reviewed package of immutable baseline files, predefined object-ID operations, harmless markers, stop conditions, and a host-side answer key.

This profile proves range lifecycle, scope enforcement, state separation, reproducible reset, destruction, and automatic scoring without publishing vulnerable services.

## Scenario catalog

The catalog under `range-scenarios/` contains exactly seven scenarios:

1. Web access-control deficiency.
2. API authorization deficiency.
3. Fictional dependency advisory.
4. Non-deployable IaC configuration deficiency.
5. Non-applicable Kubernetes RBAC configuration deficiency.
6. Indirect prompt injection in untrusted synthetic content.
7. Malicious exercise content redirecting the evaluator to an out-of-scope asset ID.

Every package contains:

- `scenario.json`: initial state, allowlist, denylist, synthetic-data declaration, expected findings, expected detections, stop conditions, scoring criteria, reset policy, destruction policy, network policy, and lateral-movement scope;
- `synthetic/`: baseline files copied into each disposable instance; and
- `answer-key.json`: host-only safe-marker oracle, never copied into range state.

## Safety model

Public APIs accept only `engagement_id`, `instance_id`, `scenario_id`, `operation_id`, and `asset_id`. They do not accept a URL, IP address, hostname, port, command, shell, path, package, plugin, manifest text, or arbitrary payload.

The runtime imports no network or process-execution library and creates no listener. The effective network policy is stronger than a deny rule: the local range has no network primitive. A later service-emulation profile must use a separate approved plan and a dedicated microVM or equivalent isolation boundary.

All proof uses `RANGE-MARKER-*` strings. The dependency advisory is fictional, IaC is explicitly non-deployable, RBAC is explicitly non-applicable, and prompt-injection content references only synthetic object IDs.

## Lifecycle

1. Control Plane resolves the scenario ID from the reviewed catalog.
2. Scope/ROE validates the scenario target and test case.
3. Independent approval authorizes instance creation.
4. Audit insertion begins before the runtime is created.
5. Runtime copies the verified baseline into a unique `engagement/instance/state` root.
6. Predefined actions return deterministic observations without executing scenario files.
7. Host-side scoring compares observations with the answer key.
8. Reset deletes mutable state and recreates it from the baseline digest.
9. Destroy removes the instance root and active runtime entry, then records attestation.

## State isolation

Each instance has a distinct resolved root below the configured runtime root. Symbolic links are rejected in scenario packages. No instance receives another scenario's path or answer key. Action requests must match an operation and asset declared by the instance's scenario.

An unknown operation, cross-scenario asset, external communication operation, or out-of-scope asset triggers a stop condition before a successful observation is recorded.

## Automatic scoring

Each scenario has criteria totaling 100 points. Criteria reference only safe markers and have one of three types: finding, detection, or behavior. The scoring engine rejects observations containing a marker not present in the host-side answer key. Scope deviation can be represented as a hard fail by a future orchestration profile; the Phase 05 service stops the instance before producing an out-of-scope observation.

## Reset and destruction

Reset is deterministic because the catalog hashes the immutable synthetic baseline and verifies the copied state after every create and reset. Reset also deletes instance observations and scores.

Destruction removes the instance filesystem and active runtime entry. Audit records, score records, and destruction attestations remain in the Control Plane and observability boundary. No credential value exists in the Phase 05 profile.

## Limitations

- This is a marker-driven local simulation, not a realistic vulnerable-service range.
- A laptop administrator can modify local files and SQLite state.
- Answer keys are separated from instance state but are not confidential in a public repository.
- Networked service emulation, microVMs, signed artifacts, WORM storage, and multi-host scheduling remain future gates.
