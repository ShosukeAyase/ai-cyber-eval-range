# Validation Report

Date: 2026-07-24

## Phase 04 deterministic validation executed

| Command | Result |
|---|---|
| `python -m pytest -o addopts=''` | PASS: 84 tests |
| `python -m pytest tests/schemas` | PASS: 10 tests |
| `python -m pytest tests/policy tests/unit/test_policy_gateway.py` | PASS: 14 tests |
| `python -m pytest tests/unit` | PASS: 21 tests |
| `python -m pytest tests/integration` | PASS: 13 tests |
| `python -m pytest tests/architecture` | PASS: 34 tests |
| Phase 04 Runner subset | PASS: 11 tests |
| `python -m compileall -q src scripts tests` | PASS |
| source line-length check (`src`, `tests`, `scripts`) | PASS: no lines over 100 characters |
| `git diff --check` | PASS |
| lightweight secret-pattern scan | PASS: only the deliberate `AKIA` test literal was observed |
| `make optional-tools` | Inventory completed; unavailable tools listed below |

## Phase 04 completion evidence

- Eighteen JSON Schemas conform to JSON Schema Draft 2020-12 and have synthetic examples.
- Runner job APIs accept registered IDs only and have no command, shell, path, URL, IP, hostname, endpoint, mount, package, or plugin field.
- The local registry maps repository/profile IDs to reviewed local paths and digest-pinned image references.
- Runtime creation uses rootless preflight, `--pull=never`, `--network=none`, private PID, IPC, UTS, and cgroup namespaces, ignored image volumes, read-only root, non-root UID/GID, all capabilities dropped, no-new-privileges, no host aliases, and no inherited proxy variables.
- One size-limited `noexec,nosuid,nodev` tmpfs is the only writable in-container workspace.
- Repository and job mounts are read-only; no audit database, Docker socket, Kubernetes token, cloud metadata, or evidence-store mount is present.
- CPU, memory, PID, open-file, single-file, wall-time, workspace, evidence, and source-file limits are represented by bounded contracts and runtime arguments.
- The fixed workload reads regular files, performs AST-based static analysis, runs built-in predefined tests, and emits bounded JSON evidence without executing repository code.
- Scope mismatch is rejected before runtime invocation.
- The fixed workload rejects an oversized source file, and the failed job leaves no active runtime or workspace.
- An injected audit failure prevents runtime creation.
- The independent Kill Switch monitor terminates a blocked job without model participation.
- Normal and terminated jobs remove the runtime staging workspace and active runtime entry.
- Evidence remains outside the Runner with an SHA-256 digest and destruction attestation.
- The offline image definition has no package-manager, network-download, or `RUN` step; build scripts require a preloaded base image and use `--pull-never --network=none`.

## Not executed in this environment

The following local quality or runtime tools were unavailable:

- Podman and Podman Desktop;
- Ruff;
- mypy;
- OPA;
- OpenTofu/Terraform;
- markdownlint;
- pip-audit;
- CycloneDX tooling;
- Trivy;
- Syft;
- Grype;
- Cosign;
- Gitleaks.

Therefore the real rootless-container smoke test, cgroup enforcement observation, no-default-route observation inside Podman, Ruff formatting/lint, mypy, dependency vulnerability scanning, SBOM generation, signature verification, and image scanning are not reported as passed. The repository provides `scripts/complete_phase4_local.ps1` and `scripts/live_runner_smoke.py` for the operator-laptop gate.

## Executed but not passed

`python -m pip check` reported a pre-existing shared-environment conflict:

```text
moviepy 2.2.1 requires pillow<12.0,>=9.2.0, but pillow 12.2.0 is installed.
```

The project declares no runtime dependency and the fixed Runner workload uses only the Python standard library. This shared-environment conflict is not caused by the repository, but dependency consistency is not reported as passed.

## Phase status

Phase 04 implementation, deterministic tests, documentation, offline image definition, and local completion scripts are complete. Formal Phase 04 completion remains conditional on the operator laptop successfully running Ruff, mypy, the complete pytest suite, rootless Podman preflight, and the live isolated Runner smoke test using a reviewed digest-pinned local image.
