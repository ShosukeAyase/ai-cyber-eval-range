# Phase 03 Control Plane MVP Plan

Status: completed

## Purpose

Implement a local-development-only Control Plane MVP from the approved Phase 02 contracts. The MVP must run on one laptop with no paid service, cloud account, external model API, runner, cyber range, or real credential material.

## Approved local profile

- Python 3.11+ and the standard-library `sqlite3` module.
- One local process and one SQLite database file, or `:memory:` for tests.
- Deterministic in-process Policy Engine adapter; no production OPA connection.
- Deterministic Model Gateway mock; no external model network request.
- Tool Gateway mock; authorization and synthetic results only.
- Credential Broker mock; opaque references only and no credential material.
- Append-only audit rows in the same SQLite transaction as every state mutation.
- Reciprocal local-development administrative approvals seeded at startup as the explicit bootstrap trust root.

## Scope

- Engagement Service.
- Scope/ROE Service.
- Policy Engine adapter.
- Approval Service with independent-approver enforcement.
- Model Gateway protocol and deterministic mock.
- Tool Gateway mock without command, URL, IP, hostname, or network execution.
- Credential Broker mock without secret values.
- Emergency Stop independent of model and runner components.
- Audit-event generation and transactional fail-closed behavior.
- Unit, integration, schema, documentation, and architecture tests.
- Read-only GitHub Actions validation.

## Explicit exclusions

- Shell, subprocess, dynamic-code, exploit, PoC, scanner, or patch execution.
- Network clients, sockets, HTTP servers, arbitrary URLs, IP addresses, or hostnames.
- Cloud SDKs, IaC, containers, VMs, Kubernetes, or external infrastructure.
- Real credentials, secret values, tokens, private keys, or certificates.
- Production OPA, WORM storage, external identity provider, message queue, or SIEM.
- Model-provider API calls.

## Trust boundaries affected

- **Control plane:** local MVP services and SQLite state/audit persistence.
- **Execution plane:** no implementation; Tool Gateway returns synthetic results only.
- **Cyber range:** no implementation or route.
- **Observability plane:** local append-only audit table only; not production WORM.

## Security decisions

1. Every public service operation requires `engagement_id`.
2. Every state-changing public operation requires a valid independent approval record.
3. Local bootstrap creates two reciprocal administrative approval grants for distinct operator and approver identities. This is test/development configuration, not a production trust model.
4. Audit insertion and state mutation share one SQLite transaction. Audit failure rolls back the operation.
5. Policy unavailability, expired ROE, scope mismatch, approval mismatch, and active Emergency Stop return deny decisions.
6. Emergency Stop depends only on local store, audit, approval, and clock abstractions.
7. Model and tool requests contain registered object identifiers only.

## Work items

- [x] Record the approved local-only topology and trust-root assumptions.
- [x] Add local SQLite store and transactional audit generation.
- [x] Implement Engagement and Scope/ROE services.
- [x] Implement Approval Service and self-approval rejection.
- [x] Implement local Policy Engine adapter.
- [x] Implement Model Gateway abstraction and deterministic mock.
- [x] Implement Tool Gateway mock and write-approval enforcement.
- [x] Implement Credential Broker mock with opaque references only.
- [x] Implement independent Emergency Stop.
- [x] Add schemas and synthetic examples for Phase 03 records.
- [x] Add unit, integration, negative, and architecture tests.
- [x] Add read-only Phase 03 CI and local demo.
- [x] Update documentation, traceability, risk register, manifest, and validation report.
- [x] Execute validation and record exact results.

## Completion criteria

- Scope deviation is denied.
- Expired ROE is denied.
- Self-approval is rejected.
- Audit failure prevents and rolls back the operation.
- Emergency Stop works without a model or runner dependency.
- Integration tests pass.
- No external system, real secret, command execution, arbitrary URL, or arbitrary IP path is introduced.

## Residual decisions deferred beyond the MVP

- Production identity provider and workload identity.
- Production OPA deployment and signed policy distribution.
- Production WORM evidence store and retention authority.
- Production credential broker and trust roots.
- Multi-process concurrency, high availability, and disaster recovery.
- External model-provider profile and data-retention controls.

## Completion record

- Local SQLite Control Plane services and deterministic mocks were implemented.
- Scope deviation, expired ROE, self-approval, audit failure, Policy Engine outage, and Emergency Stop behavior are covered by negative and integration tests.
- The Tool Gateway remains non-executable and returns only synthetic results.
- No external model API, network listener/client, cloud resource, real credential material, exploit validation, runner, or cyber range was introduced.
- `make validate` passed 73 tests.
- Ruff, mypy, OPA, dependency scanning, SBOM, signature, IaC, and image tooling were unavailable locally and are not reported as passed.
