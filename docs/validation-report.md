# Validation Report

Date: 2026-07-26

## Phase 04 final operator-laptop validation

Phase 04 completed on the operator laptop using rootless Podman and the digest-pinned
Runner image `sha256:c811c3181bc063a443f2b0182f503fb2a95b28efd05ae81c86c95c5da15d3fc6`.

- Rootless Podman preflight: PASS.
- Ruff format/lint: PASS.
- mypy strict type check: PASS.
- Complete pytest suite: PASS.
- Live isolated Runner smoke test: PASS.
- The writable Runner area is a disposable host-staged directory bind-mounted at
  `/workspace` with `rw,noexec,nosuid,nodev`; it is not an in-container tmpfs.
- The root filesystem and input mounts remain read-only, and the host-staged workspace is
  removed after evidence collection.

## Phase 05 deterministic validation executed

| Command | Result |
|---|---|
| `python -m pytest -o addopts=''` | PASS: 128 tests |
| `python -m pytest tests/schemas` | PASS: 12 tests |
| `python -m pytest tests/policy tests/unit/test_policy_gateway.py` | PASS: 14 tests |
| `python -m pytest tests/unit` | PASS: 24 tests |
| `python -m pytest tests/integration` | PASS: 45 tests |
| `python -m pytest tests/architecture` | PASS: 41 tests |
| Phase 05 range subset | PASS: 42 tests |
| `python scripts/verify_phase5_catalog.py` | PASS: seven scenarios |
| `python -m compileall -q src scripts tests` | PASS |
| source line-length check (`src`, `tests`, `scripts`) | PASS: no lines over 100 characters |
| lightweight secret-pattern scan | PASS: no credential material detected |

## Phase 05 completion evidence

- Twenty-three JSON Schemas conform to JSON Schema Draft 2020-12 and have synthetic examples.
- The catalog contains exactly the seven approved scenario IDs.
- Every scenario declares its initial state, allowlist, denylist, synthetic-data profile,
  expected findings, expected detections, stop conditions, 100-point scoring criteria,
  deterministic reset, complete destruction, no-network policy, and lateral-movement scope.
- Public range action contracts contain registered object IDs only and have no URL, IP address,
  hostname, port, command, shell, path, package, plugin, or arbitrary payload field.
- Range source imports no network client/server or process-execution library.
- Scenario packages contain no real credential, active payload, external destination, deployable
  IaC, applicable Kubernetes resource, or real dependency advisory.
- Every proof is a harmless `RANGE-MARKER-*` observation.
- Concurrent instances use disjoint roots, and different scenarios cannot reference each
  other's operation or asset IDs.
- An explicit external-communication operation is stopped before a successful observation.
- Scope/ROE deviation and unregistered operations stop the instance before action count changes.
- Audit insertion failure prevents range creation.
- All seven scenarios reset to their exact SHA-256 baseline.
- All seven scenarios can be automatically scored to 100 points using host-side answer keys.
- All seven scenarios produce successful destruction attestations with no remaining instance root
  or active runtime entry.
- Emergency Stop blocks new range actions without model participation.

## Artifact-build environment limitations

Ruff, mypy, Podman, OPA, OpenTofu/Terraform, markdownlint, pip-audit, CycloneDX, Trivy,
Syft, Grype, Cosign, and Gitleaks were unavailable in this artifact-build environment.
Phase 05 itself has no Podman or network-runtime dependency. The operator-laptop completion
script makes Ruff and mypy mandatory before changing the Phase 05 plan to `completed`.

## Executed but not passed

`python -m pip check` reported a pre-existing shared-environment conflict:

```text
moviepy 2.2.1 requires pillow<12.0,>=9.2.0, but pillow 12.2.0 is installed.
```

The project declares no runtime dependencies. The conflict belongs to the shared artifact-build
environment and is not caused by the repository, but dependency consistency is not reported as
passed in this environment.

## Phase status

Phase 05 implementation, deterministic validation, and operator-laptop quality gates are complete. Phase 05 formal status: complete for the approved non-networked local synthetic profile.

## Operator-laptop Phase 05 quality gates

- Completed at: `2026-07-26T00:45:45.611448+00:00`.
- Ruff format check and lint: PASS.
- mypy strict type check: PASS.
- Complete pytest suite: PASS.
- Python compilation: PASS.
- Git whitespace validation: PASS.
- Phase 05 status: complete for the local non-networked synthetic profile.

## Phase 06 deterministic validation executed

| Command | Result |
|---|---|
| `python -m pytest -o addopts=''` | PASS: 157 tests |
| `python -m pytest tests/unit/test_agent_contracts.py` | PASS: 18 tests |
| `python -m pytest tests/integration/test_agent_workflow.py` | PASS: 3 tests |
| `python -m pytest tests/architecture/test_phase_06_agent.py` | PASS: 8 tests |
| `python -m compileall -q src scripts tests` | PASS |
| source line-length check (`src`, `tests`, `scripts`) | PASS after normalization |
| lightweight secret-pattern scan | PASS: no credential material detected |

## Phase 06 completion evidence

- The GPT model is a proposal-only component and receives no executable provider tools.
- The OpenAI adapter is restricted to the fixed Responses endpoint, the explicit `gpt-5.6-sol` model profile,
  `store=false`, `tool_choice=none`, disabled parallel tool calls, and strict JSON Schema output.
- Provider authentication is attached by the transport and is absent from model input and audit.
- Agent run state creation requires a run-ID-bound independently approved grant.
- Every accepted tool proposal is reconstructed as an internal `ToolRequest` and evaluated through
  the existing Tool Gateway and Policy Engine.
- Scope expansion, self-approval, audit deletion, credential acquisition, general Internet access,
  forbidden tools, arbitrary commands, Kill Switch control, and automatic patch merge are blocked.
- Indirect prompt-injection content is labeled untrusted and cannot grant authority.
- Repeated identical denied requests and excessive turns terminate the Agent run.
- Findings without registered or Tool Gateway-derived evidence are rejected.
- Model-supplied Tool Gateway receipts and forged evidence identifiers are rejected.
- Model transport failure leaves a terminal failed Agent record and performs no further tool call.
- Deterministic tests observed an executed Scope violation rate of zero.

## Phase 06 artifact-build limitations

Ruff and mypy were unavailable in the artifact-build environment. No live OpenAI request was made,
and no provider credential was present. The operator-laptop completion script makes Ruff, mypy,
full regression tests, compilation, and Git whitespace checks mandatory before recording Phase 06
as completed. A live provider smoke test is available but remains an explicit operator action.

## Phase 06 status

Phase 06 implementation, deterministic adversarial validation, and operator-laptop quality gates are complete. Phase 06 formal status: complete for the proposal-only Agent integration profile.

## Operator-laptop Phase 06 quality gates

- Completed at: `2026-07-26T02:15:29.953565+00:00`.
- Ruff format check and lint: PASS.
- mypy strict type check: PASS.
- Complete pytest suite: PASS.
- Python compilation: PASS.
- Git whitespace validation: PASS.
- Phase 06 status: complete for the proposal-only Agent integration profile.
