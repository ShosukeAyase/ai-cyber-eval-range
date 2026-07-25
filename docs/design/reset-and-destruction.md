# Reset and Destruction

## Required order

1. Stop new tool calls and isolate runner networking.
2. Revoke target, broker, model, and job credentials.
3. Flush and seal telemetry/evidence.
4. Stop runner and scenario workloads.
5. Destroy ephemeral compute instances and runtime namespaces.
6. Delete writable disks, snapshots, caches, and temporary object prefixes.
7. Destroy per-engagement encryption keys for cryptographic erasure.
8. Remove network rules, DNS records, identities, and leases.
9. Verify absence through inventory and reachability checks.
10. Emit a signed destruction attestation.

## Idempotency

Every deletion operation accepts an object ID and desired terminal state. Repeated calls return the same terminal result and do not resurrect resources.

## Reset versus destroy

- **Reset** restores a scenario to a signed baseline for another authorized run after all prior credentials and mutable state are removed.
- **Destroy** removes the scenario allocation and its cryptographic keys entirely.

## Verification

The lifecycle manager compares pre- and post-destruction inventories, confirms credential revocation, checks no routes/listeners remain, and records retained evidence exceptions.

## Phase 04 local Runner destruction

The local runtime removes the container with force, deletes the host staging directory, confirms
that no active runtime entry remains, and records a destruction attestation. The Runner has no real
credential material. Collected evidence and audit history remain outside the Runner by design;
all writable execution state, job manifests, and temporary evidence copies are destroyed.
