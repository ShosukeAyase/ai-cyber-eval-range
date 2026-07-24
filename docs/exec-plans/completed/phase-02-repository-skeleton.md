# Phase 02 Repository Skeleton Plan

Status: completed

## Purpose

Create a reviewable, testable, and deliberately non-executable repository skeleton from the approved Phase 01 design. This phase establishes contracts and negative controls only. It must not provision infrastructure, contact targets, execute tools, validate exploits, or process credentials.

## Scope

- Repository/package directory structure.
- JSON Schema contracts and synthetic examples.
- Typed Python domain definitions.
- Protocol-based API boundaries.
- Policy Engine rule templates and a local fail-closed stub.
- Pure state-transition validation.
- Pytest harness and negative tests.
- GitHub Actions CI definition.
- Documentation and architecture validation.
- Requirements-to-design-to-test traceability.

## Explicit exclusions

- Shell or subprocess execution.
- Network clients or external target connectivity.
- Cloud SDKs, IaC modules, or resource creation.
- Exploit or proof-of-concept execution.
- Credential, secret, token, key, or certificate handling.
- Container, VM, Kubernetes, or cyber-range lifecycle implementation.
- Real policy bundle distribution or production OPA connectivity.

## Trust boundaries affected

- **Control plane:** contract-only policy, scope, approval, and gateway interfaces.
- **Execution plane:** no implementation; only a dispatch method that always fails closed.
- **Cyber range:** no implementation or network route.
- **Observability plane:** schema references only; no storage or telemetry implementation.

## Work items

- [x] Move Phase 01 plan to `completed/`.
- [x] Add Python package skeleton with typed, immutable domain contracts.
- [x] Add non-executable API protocols and Tool Gateway stub.
- [x] Add fail-closed local Policy Engine stub.
- [x] Add pure approval, job, engagement, and runner state machines.
- [x] Add tool-request, policy-input, policy-decision, and transition schemas.
- [x] Add a valid synthetic example for every schema.
- [x] Add policy, scope, approval, fail-closed, and transition negative tests.
- [x] Add architecture tests prohibiting execution, cloud SDKs, network clients, and credential fields.
- [x] Add CI and document validation targets.
- [x] Update traceability, documentation index, validation report, and manifest.
- [x] Execute repository validation and record exact results.

## Completion criteria

- Every JSON Schema is Draft 2020-12-valid and has a validating synthetic example.
- An out-of-scope target receives a deny decision.
- A dangerous action without independent valid approval receives a deny decision.
- Policy Engine unavailability and evaluation errors receive deny decisions.
- Invalid state transitions raise a deterministic error and negative tests pass.
- Architecture tests prove the skeleton contains no shell, subprocess, network, cloud, exploit, or credential implementation.
- Traceability links each Phase 02 requirement to design evidence and an automated test.

## Risks and controls

- **Skeleton accidentally becomes executable:** architecture tests reject execution and network primitives; dispatch always raises `ExecutionDisabledError`.
- **Mocks are mistaken for production controls:** package and documents label all implementations as stubs; policy version uses a skeleton identifier.
- **Schema/code drift:** examples, enums, and traceability are tested in CI.
- **Fail-open exception path:** gateway converts Policy Engine exceptions into explicit deny decisions.

## ADR impact

No ADR changes are required. Phase 02 implements the already approved boundaries in ADR-0003, ADR-0013, and ADR-0014 without selecting production technologies beyond the existing OPA decision.

## Completion record

- Contract skeleton created without runtime adapters.
- `make validate` passed 49 tests; schema, policy, architecture, and documentation subsets also passed.
- External policy/IaC/security tooling remains a Phase 03 gate and is not reported as executed.
