# Phase 04 Isolated Runner MVP Plan

Status: completed

## Purpose

Implement a disposable, local-laptop Runner that accepts only approved object-ID-based jobs from the Phase 03 Control Plane. The real runtime profile uses rootless Podman with a preloaded digest-pinned local image and no network. Tests use deterministic fakes and never contact external systems.

## Approved local profile

- Python 3.11+ orchestration and workload code.
- Rootless Podman on the same laptop; Windows uses the free Podman Desktop WSL2 machine.
- No registry pull during execution (`--pull=never`); only a preloaded image referenced by digest.
- Synthetic repositories registered by object ID and mounted read-only.
- One writable in-container tmpfs at `/workspace`; root filesystem and all input mounts are read-only.
- Evidence copied out after execution; the container and workspace are then forcibly removed.
- No Docker socket, Kubernetes token, cloud metadata, host network, host PID, root user, privileged mode, or arbitrary command API.

## Scope

- Runner job/profile/resource-limit contracts and JSON Schemas.
- Synthetic repository registry using registered IDs only.
- Fixed static-analysis and predefined-test workload.
- Podman command-plan builder with fixed arguments and security controls.
- Deterministic runtime fake for integration tests.
- Disposable workspace, evidence collection, hashing, and destruction attestation.
- Runner Coordinator with approval, Scope/ROE, policy, audit, and Kill Switch enforcement.
- Independent Kill Switch monitor that terminates active jobs without model participation.
- Unit, integration, schema, architecture, and documentation tests.
- Read-only CI validation.

## Explicit exclusions

- Arbitrary shell commands, command strings, package installation, dynamic plugins, or repository-supplied test execution.
- Internet, corporate, production, host, metadata, Docker, or Kubernetes API access.
- Real credentials or secret values.
- Exploit, PoC, scanner, active network discovery, patch application, or destructive testing.
- Cloud resources, remote runners, Kubernetes workloads, or external artifact registries.
- Production WORM evidence storage or multi-host isolation.

## Trust boundaries affected

- **Control plane:** adds Runner Coordinator contracts and job/audit state.
- **Execution plane:** adds a local rootless-container adapter and fixed workload.
- **Cyber range:** still absent; only synthetic local repositories are allowed.
- **Observability plane:** evidence is copied to a host-controlled directory; Runner receives no audit database mount or mutation API.

## Work items

- [x] Add Phase 04 domain contracts, Schemas, and examples.
- [x] Add synthetic repository/profile registries.
- [x] Add fixed workload for repository reading, static analysis, predefined tests, and evidence generation.
- [x] Add secure Podman execution plan and CLI adapter.
- [x] Add deterministic fake runtime and execution harness.
- [x] Add Runner Coordinator and Kill Switch monitor.
- [x] Add transactional job/audit persistence and destruction records.
- [x] Add negative tests for scope, network, resource, audit, Kill Switch, and destruction controls.
- [x] Update architecture, threat model, network matrix, risk register, traceability, CI, manifest, and validation report.
- [x] Execute deterministic validation and record exact results.
- [x] Execute the live rootless-Podman smoke test on the operator laptop.

## Completion criteria

- Prohibited communication is blocked by the generated runtime profile and tested.
- Out-of-scope repository/target IDs are rejected before runtime creation.
- CPU, memory, wall time, PID count, open-file count, and writable-byte limits are encoded and enforced/tested.
- Runner has no audit-store mount or audit mutation API.
- Independent Kill Switch terminates an active job and seals a terminal audit record.
- Container/workspace/ephemeral credential metadata are absent after destruction.
- Evidence remains available outside the Runner and includes hashes and destruction attestation.
- All integration and architecture tests pass.

## Residual decisions deferred

- Signed OCI image distribution and offline artifact acquisition process.
- Production microVM backend and hardware separation.
- Independent WORM evidence store.
- Remote scheduler, workload identity, and production credential broker.
- Strong host-owner resistance on a single personally administered laptop.

## Live completion record

- Completed at: `2026-07-26T00:03:03.895362+00:00`
- Runner image: `sha256:c811c3181bc063a443f2b0182f503fb2a95b28efd05ae81c86c95c5da15d3fc6`
- Rootless Podman preflight: PASS.
- Ruff format/lint, mypy, complete pytest suite, and live isolated Runner smoke: PASS.
- Phase 04 is complete for the approved single-laptop local profile only.
