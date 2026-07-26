# Threat Model

## Method

The design uses assets, trust boundaries, abuse cases, STRIDE-style threat categories, and explicit safety invariants. Risk treatment is tracked in `risk-register.md`.

## Assets

- Signed Engagement and ROE manifests.
- Policy bundles and approval records.
- Model prompts, outputs, and safety metadata.
- Credentials and one-time execution grants.
- Runner hosts, base images, and tool adapters.
- Synthetic targets and scenario definitions.
- Audit logs, evidence, scores, and destruction attestations.
- Source repositories and patch artifacts under evaluation.

## Threat actors

| Actor | Objective | Key controls |
|---|---|---|
| External attacker | Compromise control services, inject jobs, steal evidence | Strong IAM, network isolation, signed manifests, rate limits, independent monitoring |
| Malicious scenario content | Induce the model to escape scope or disclose secrets | Untrusted-content labeling, context isolation, capability APIs, deterministic policy |
| Compromised or misaligned model | Broaden scope, invoke dangerous tools, repeat failures, conceal actions | No authorization authority, object-ID APIs, quotas, approval gates, behavior scoring |
| Malicious insider | Approve unauthorized work, alter policy, suppress evidence | Separation of duties, dual control, immutable logs, break-glass review |
| Compromised runner/tool | Escape sandbox, access host sockets/metadata, tamper with evidence | microVM/VM isolation, host firewall, no sockets, write-only telemetry, disposable hosts |
| Supply-chain attacker | Insert malicious dependency, image, scanner, or policy bundle | Pinning, signatures, SBOM, mirror quarantine, reproducible builds, admission controls |
| Observability-plane attacker | Alter evidence or scoring | Separate administration, WORM retention, signatures, independent integrity checks |

## Primary threats by boundary

### Model boundary

- Direct and indirect prompt injection.
- Tool-call argument smuggling.
- Context poisoning from logs or source code.
- Hallucinated target identifiers or approvals.
- Excessive agency and repeated unsafe planning.

### Control-to-execution boundary

- Forged or replayed execution grants.
- Policy decision bypass.
- Scheduler race conditions after approval expiry.
- Confused deputy behavior in Tool Gateway.
- Credential substitution.

### Execution-to-range boundary

- Scope-out network access.
- Unexpected listeners or lateral movement.
- Credential discovery and reuse.
- Exploit effects beyond the disposable target.
- Resource exhaustion or denial of service.

### Execution-to-observability boundary

- Log suppression, truncation, or spoofing.
- Evidence exfiltration through telemetry.
- Scoring manipulation.
- Clock manipulation.

## Required controls

- Signed manifests and nonce-bound execution grants.
- Policy decision at scheduling and immediately before tool execution.
- Destination tuples resolved from target IDs, not model input.
- One-time credentials delivered directly to adapters.
- Read-only runner base, bounded scratch storage, and strict quotas.
- Independent network sensor and host telemetry.
- Emergency stop on monitoring loss.
- Negative tests for every authorization rule.

## Residual risk

A sufficiently privileged compromise of the hypervisor or CPU may cross isolation boundaries. High-risk workloads therefore require dedicated physical hosts, patched firmware, restricted scheduling, and no unrelated tenants. This remains a human-governed acceptance decision.

## Phase 03 local MVP threat considerations

The single-laptop profile introduces local-development threats that do not exist in the intended
production separation model:

- a laptop administrator can read or alter the SQLite database and audit rows;
- a copied database can be rolled back without an independent monotonic authority;
- reciprocal bootstrap approvals can be misused if exported beyond the local profile;
- one process failure affects all local Control Plane services; and
- deterministic mocks can create false confidence if mistaken for production integrations.

Controls in Phase 03 are naming, closed typed APIs, no network/runtime imports, transactional
audit tests, approval expiry/use limits, and explicit local-only documentation. These controls
do not convert local SQLite into WORM evidence or a production trust boundary.

## Phase 04 local Runner threats

The local rootless-container profile introduces container escape, runtime replacement, host-path
confusion, resource-limit bypass, evidence spoofing, and incomplete destruction risks. Controls
include a digest-only local image reference, `--pull=never`, no network, private PID namespace,
non-root execution, all capabilities dropped, no-new-privileges, read-only root, read-only inputs,
one disposable host-staged workspace bind-mounted with `rw,noexec,nosuid,nodev`, fixed argv, evidence identity/hash validation, and forced removal.

These controls do not protect against a malicious laptop administrator or a compromised Podman
machine. Production execution still requires microVM or VM isolation and independent evidence.

## Phase 05 local range threats

- **Scenario-state bleed:** mitigated by unique instance roots and asset-ID allowlists.
- **Answer-key exposure to the range:** mitigated by keeping answer keys outside copied synthetic state.
- **Malicious exercise content:** treated as data; prompt and scope redirection produce refusal markers.
- **External communication attempt:** impossible through the Phase 05 API and blocked as a stop condition.
- **Non-deterministic reset:** detected by baseline SHA-256 verification after every create and reset.
- **Incomplete destruction:** fails the destruction attestation when the root or active runtime remains.
