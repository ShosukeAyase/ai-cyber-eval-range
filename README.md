# Authorized AI Cyber-Evaluation Platform and Isolated Cyber Range

This repository contains the **design-phase artifacts** for a defensive cyber-evaluation platform that uses GPT-5.6 for analysis, planning, evidence organization, and patch proposals while keeping authorization and execution control outside the model.

The repository also defines a disposable cyber range for Web/API, Linux, Windows, containers, Kubernetes, and simulated cloud IAM/storage scenarios. It must not be connected to public targets, production systems, corporate networks, or the general internet.

## Current phase

Phase 01 design is complete. Phase 02 adds a deliberately non-executable contract skeleton. It contains typed interfaces, JSON Schemas, policy templates, state machines, mocks, tests, and CI definitions, but no target deployment, shell execution, network client, exploit validation, credential processing, or cloud-resource creation.

## Core invariants

- Four independent trust domains: control plane, execution plane, cyber range, and observability plane.
- Default-deny networking and complete mediation of every tool request.
- Signed, schema-valid Engagement and Rules of Engagement manifests.
- Object-ID-based tool APIs; no model-supplied arbitrary commands, URLs, IPs, or hostnames.
- Human approval for state change, credential use, and exploit validation.
- Credentials remain inside a Credential Broker and are injected only into a tightly scoped tool adapter.
- Fail-closed emergency termination, credential revocation, runner quarantine, and evidence preservation.
- Immutable audit evidence outside the execution trust boundary.

## Repository map

- `ARCHITECTURE.md`: system-level architecture.
- `src/cyber_eval/`: immutable contracts and non-executable fail-closed stubs.
- `docs/security/`: threat model, boundaries, IAM, credentials, network controls, abuse cases, and risks.
- `docs/governance/`: authorization, ROE, data handling, retention, and incident response.
- `docs/design/`: component and lifecycle designs.
- `docs/adr/`: architecture decision records.
- `schemas/`: machine-readable contracts.
- `examples/`: non-production, synthetic examples.
- `policies/`: policy-as-code design stubs.
- `tests/`: architecture, policy, and schema consistency tests.
- `diagrams/`: standalone Mermaid sources.

## Validate

```sh
make validate
```

The default validation uses Python, `pytest`, `jsonschema`, and PyYAML. Optional targets document checks that require external tools such as OPA, OpenTofu, secret scanners, SBOM generators, and image scanners.

## Non-goals

This repository does not provide weaponized exploit code, unrestricted shells, internet scanning, credential dumping, persistence, evasion, denial-of-service testing, automated deployment, or automated patch application.
