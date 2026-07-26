# Authorized AI Cyber-Evaluation Platform and Isolated Cyber Range

This repository contains the **design-phase artifacts** for a defensive cyber-evaluation platform that uses GPT-5.6 for analysis, planning, evidence organization, and patch proposals while keeping authorization and execution control outside the model.

The repository also defines a disposable cyber range for Web/API, Linux, Windows, containers, Kubernetes, and simulated cloud IAM/storage scenarios. It must not be connected to public targets, production systems, corporate networks, or the general internet.

## Current phase

Phase 01 through Phase 06 are complete. Phase 07 performed an independent assurance review and issued a production **NO-GO** because unresolved high risks remain. Phase 06 adds a proposal-only GPT Agent behind the existing Control Plane. The model can plan, select from approved tool IDs, analyze authenticated results, organize evidence, and propose remediation or revalidation. It cannot decide Scope, approve itself, receive secrets, execute commands, select network destinations, control Emergency Stop, mutate audit records, or merge patches. Every accepted tool proposal is reconstructed by the Control Plane and evaluated through the Tool Gateway and Policy Engine.

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
- `src/cyber_eval/`: typed Control Plane, proposal-only Agent, fixed Runner, and synthetic range components.
- `range-scenarios/`: seven reviewed synthetic baselines and host-side answer keys.
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

## Local Cyber Range MVP

The Phase 05 range uses no listening service or external connection. Run its deterministic tests:

```sh
python -m pytest tests/integration/test_cyber_range_mvp.py tests/architecture/test_phase_05_range.py
```

See [`docs/design/cyber-range-mvp.md`](docs/design/cyber-range-mvp.md).

## Proposal-only GPT Agent

Phase 06 integrates an optional OpenAI Responses adapter at one fixed endpoint. Automated tests use
a scripted transport and never require a provider credential or external network. The model receives
strictly registered, redacted context and returns a closed JSON proposal; it receives no provider
tools and cannot directly call an execution adapter.

```sh
python -m pytest tests/integration/test_agent_workflow.py tests/architecture/test_phase_06_agent.py
```

See [`docs/design/agent-integration.md`](docs/design/agent-integration.md).

## Independent assurance review

Phase 07 reviewed the complete system, executed 157 regression tests and targeted negative suites,
and recorded a production **NO-GO**. The local synthetic MVP remains usable only within its
documented constraints. See [`docs/assurance/assurance-report.md`](docs/assurance/assurance-report.md)
and [`docs/assurance/go-no-go-checklist.md`](docs/assurance/go-no-go-checklist.md).

## Non-goals

This repository does not provide weaponized exploit code, unrestricted shells, internet scanning, credential dumping, persistence, evasion, denial-of-service testing, automated deployment, or automated patch application.
