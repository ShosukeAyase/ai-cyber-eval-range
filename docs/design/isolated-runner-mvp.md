# Isolated Runner MVP

## Status and purpose

Phase 04 adds a disposable execution-plane MVP for synthetic repositories only. The Control Plane accepts registered object identifiers, performs Scope/ROE and independent-approval checks, writes an audit event, and then invokes a fixed Runner profile. It does not expose an arbitrary command, path, URL, IP, hostname, package, plugin, or image API.

## Free single-laptop profile

The real local adapter uses rootless Podman on the same laptop. Windows uses the Podman Desktop WSL2 machine. Execution requires a digest-pinned Runner image already present in local container storage. Runtime creation uses `--pull=never`; no registry or package source is contacted during a job.

The deterministic runtime under `tests/` exercises orchestration, workload, evidence, Kill Switch, and destruction behavior without claiming container isolation. The operator-laptop rootless Podman smoke test passed during Phase 04 completion.

## Fixed job lifecycle

1. Resolve `repository_id` and `profile_id` from the local registry.
2. Verify engagement, target, test case, active ROE, policy, Emergency Stop, and approval.
3. Commit the authorization audit event and job record before runtime creation.
4. Create a rootless container with a read-only root filesystem and no network.
5. Mount the synthetic repository and job manifest read-only.
6. Bind one disposable host-staged directory at `/workspace` with `rw,noexec,nosuid,nodev`.
7. Run only `python -P -m cyber_eval.runner.workload`.
8. Read files, perform AST-based static analysis, run built-in predefined tests, and write JSON evidence.
9. Read the bounded evidence from the disposable host-staged workspace after the workload exits.
10. Force-remove the container and host staging directory, then record destruction attestation.

## Isolation controls

The Podman plan explicitly sets:

- `--network=none`, private PID/IPC/UTS/cgroup namespaces, and ignored image volumes;
- `--read-only` and `--read-only-tmpfs=false`;
- a non-root UID/GID, rootless preflight verification, no host aliases, no inherited proxy variables, no image healthcheck, and no restart policy;
- `--cap-drop=ALL` and `--security-opt=no-new-privileges`;
- CPU, memory, process, open-file, single-file, wall-time, workspace, evidence, and source-file limits;
- read-only input and job mounts; and
- one disposable host-staged `/workspace` bind mount with `rw,noexec,nosuid,nodev`.

The plan never uses privileged mode, host network, host PID, Docker socket mounts, Kubernetes service-account tokens, cloud metadata routes, or an audit database mount.

## Fixed workload

The workload never imports or executes repository code. It:

- inventories regular files and rejects symbolic links;
- rejects files and repositories exceeding the profile limits;
- parses Python ASTs and records sensitive imports or dynamic-execution calls;
- runs built-in parse, symlink, and size-bound tests; and
- emits bounded JSON evidence with repository and job identifiers.

Repository-supplied tests, shell scripts, package managers, scanners, exploits, and plugins are not executed.

## Audit separation

The Runner receives no path, mount, token, or API for the SQLite audit store. Evidence is copied out by the host after workload completion. Only the Control Plane writes job, evidence, and destruction events.

## Kill Switch

`EmergencyStopService` remains independent of the model and Runner. `KillSwitchMonitor` observes the already-audited stop state and invokes the runtime termination primitive for every active job in the engagement. The run thread then performs unconditional cleanup and records a terminal state when audit storage remains available.

## Destruction semantics

“Nothing remains” means no active container, writable Runner workspace, job manifest, temporary evidence copy, or credential material remains. Immutable job/audit history and the collected evidence intentionally remain outside the Runner boundary.

## Limitations

- A laptop owner can still alter Podman, the host filesystem, and local audit/evidence.
- Rootless Podman and the live isolated Runner smoke test were verified on the operator laptop; production-grade host resistance remains out of scope.
- The digest-pinned image must be created and reviewed through a separate offline artifact process.
- This is not the production microVM, independent observability, or WORM profile.
