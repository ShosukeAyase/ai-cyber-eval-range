# Phase 04 Isolated Runner MVP Plan

Status: completed

## Purpose

Implement a disposable local Runner that accepts only approved object-ID-based jobs. The verified profile uses rootless Podman, a preloaded digest-pinned image, no network, a read-only root filesystem, and a disposable host-staged workspace mounted only at `/workspace`.

## Completed controls

- Rootless Podman preflight.
- `--pull=never` and `--network=none`.
- Private PID, IPC, UTS, and cgroup namespaces.
- Read-only root, non-root UID/GID, all capabilities dropped, and no-new-privileges.
- CPU, memory, PID, open-file, file-size, wall-time, workspace, and evidence limits.
- Synthetic repository and job definition mounted read-only.
- Host-staged `/workspace` mounted `rw,noexec,nosuid,nodev` and removed after completion.
- Evidence retained outside the Runner; audit store never mounted.
- Independent Kill Switch and unconditional destruction.

## Live completion record

- Completed at: `2026-07-26T00:03:03.895362+00:00`.
- Runner image: `sha256:c811c3181bc063a443f2b0182f503fb2a95b28efd05ae81c86c95c5da15d3fc6`.
- Rootless Podman preflight: PASS.
- Ruff format/lint, mypy, complete pytest suite, and live isolated Runner smoke: PASS.
- Phase 04 is complete for the approved single-laptop local profile only.

## Residual decisions deferred

- Signed OCI distribution and offline acquisition governance.
- Production microVM backend and hardware separation.
- Independent WORM evidence storage.
- Remote scheduler, workload identity, and production Credential Broker.
