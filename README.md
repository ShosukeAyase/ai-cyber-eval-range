# Authorized AI Cyber-Evaluation Platform and Isolated Cyber Range

This repository contains the **design-phase artifacts** for a defensive cyber-evaluation platform that uses GPT-5.6 for analysis, planning, evidence organization, and patch proposals while keeping authorization and execution control outside the model.

The repository also defines a disposable cyber range for Web/API, Linux, Windows, containers, Kubernetes, and simulated cloud IAM/storage scenarios. It must not be connected to public targets, production systems, corporate networks, or the general internet.

## Current phase

Phase 01 design and the Phase 02 non-executable contract skeleton are complete. Phase 03 adds a local-only Control Plane MVP using Python and SQLite. It provides engagement, Scope/ROE, approval, policy, model-mock, tool-mock, credential-reference, Emergency Stop, and transactional audit services. Phase 04 adds a rootless, no-network, fixed-workload Runner for synthetic repositories. It still contains no arbitrary command API, external target access, exploit validation, real credential material, or cloud-resource creation.

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
- `src/cyber_eval/`: typed Control Plane services, mocks, and the fixed isolated Runner adapter.
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

The default validation uses Python, `pytest`, `jsonschema`, and PyYAML. The local demo runs with `make demo`. Optional targets document checks that require external tools such as OPA, OpenTofu, secret scanners, SBOM generators, and image scanners.

## Local Control Plane MVP

The Phase 03 demonstration uses only Python and SQLite:

```sh
python -m pip install -e ".[dev]"
python -m cyber_eval.demo
```

PowerShell after installation:

```powershell
py -m cyber_eval.demo
```

The demo uses synthetic identifiers, an in-memory database, deterministic mocks, and no network
connection. See [`docs/design/control-plane-mvp.md`](docs/design/control-plane-mvp.md).

## Non-goals

This repository does not provide weaponized exploit code, unrestricted shells, internet scanning, credential dumping, persistence, evasion, denial-of-service testing, automated deployment, or automated patch application.
