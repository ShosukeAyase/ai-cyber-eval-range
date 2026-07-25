# Execution Plane Design

## Ephemeral runner

A runner is created for one job, uses a read-only signed image, has bounded scratch storage, and is destroyed after evidence transfer. Dynamic runners use microVMs by default.

## Tool Gateway

The gateway is the policy enforcement point and adapter registry. It:

- validates closed-schema requests;
- maps object IDs to endpoints and tool profiles;
- re-evaluates policy;
- checks approval and expiry;
- obtains credentials from the broker;
- starts a pre-approved adapter;
- records input/output hashes and decision IDs;
- enforces result redaction and size limits.

## Command allowlist

Adapters expose semantic operations, not command strings. Tool-specific options are enumerated and validated. Unknown flags, shell metacharacters, file redirections, raw sockets, and dynamic plugin loading are prohibited unless explicitly implemented in a reviewed adapter.

## Quotas

- CPU, memory, process, file descriptor, disk, and network bytes.
- Wall-clock time, model tokens, tool calls, retries, and concurrent jobs.
- Per-target request rate and response-size limits.

## Egress firewall

Rules are generated from signed target objects and installed before the runner starts. DNS answers are pinned to scenario allocations. Policy synchronization loss stops the runner.

## Artifact collector

Collects only declared paths and structured outputs. It performs redaction, hashing, signing, and one-way upload. It cannot read the evidence store after upload.

## Lifecycle manager

States: requested, authorized, provisioning, ready, running, quarantined, collecting, destroying, destroyed, failed. State transitions are idempotent and audited.


## Phase 04 local MVP

See [Isolated Runner MVP](isolated-runner-mvp.md). The local adapter is rootless, uses `--network=none`, a read-only root filesystem, one bounded `/workspace`, a digest-pinned preloaded image, and a fixed Python workload. No arbitrary command or repository-supplied test is executed.
