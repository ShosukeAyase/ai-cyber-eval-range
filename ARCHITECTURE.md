# Architecture

## 1. System purpose

The platform coordinates authorized, reproducible, defensive security evaluations against synthetic or explicitly approved disposable assets. GPT-5.6 is a reasoning component, not an authorization authority, credential holder, network principal, or direct executor.

The architecture treats model output, target content, tool output, source code, logs, documents, and scenario fixtures as untrusted data. Every side effect must be mediated by deterministic controls.

## 2. Four-plane architecture

The four formal trust domains are the **control plane**, **execution plane**, **cyber range**, and **observability plane**. Their controls are default-deny and fail-closed.

| Plane | Responsibilities | Primary trust assumptions | Explicitly excluded |
|---|---|---|---|
| Control | Engagement state, signed scope/ROE, scheduling, approvals, policy decisions, model access, emergency stop | Administratively controlled, strongly authenticated, change-audited | Direct range access; shared runner credentials |
| Execution | Disposable runners, tool adapters, quotas, artifact collection, egress enforcement | Hostile workload and potentially compromised tools | Persistent identity; arbitrary shell/network; audit deletion |
| Cyber range | Synthetic targets, dummy infrastructure, scenario state, reset/destruction | All content may be adversarial, including prompt injection | Internet/corporate/production routes; real secrets/data |
| Observability | Append-only logs, packet capture, process/file telemetry, SIEM, scoring, evidence custody | Independent administration and storage | Mutation by execution or range identities |

Each plane uses separate IAM roots, credentials, network zones, execution hosts, encryption keys, and administrative roles. The minimum cloud deployment uses separate accounts/projects/subscriptions for each plane; the local-first deployment uses separate physical or hypervisor hosts and dedicated management networks.

## 3. Principal data flow

1. An authorized operator submits signed Engagement and ROE manifests.
2. Scope and ROE Service verifies schema, signature, validity period, target-object mappings, and policy version.
3. Agent Orchestrator asks Model Gateway for analysis or a structured tool intent.
4. Tool intent is normalized to an object-ID-based request.
5. Policy Engine evaluates engagement, target, action, limits, approval state, credential class, and expected network destinations.
6. Human Approval Service authorizes high-risk transitions when required.
7. Job Scheduler creates a one-time execution grant.
8. Runner Lifecycle Manager creates an ephemeral runner in the execution plane.
9. Tool Gateway maps object IDs to pre-registered adapters and target endpoints; the model never sees raw secrets.
10. Credential Broker presents a short-lived target-bound credential directly to the adapter.
11. Egress Firewall permits only the declared range destination tuple and observability export path.
12. Artifact Collector sends evidence one-way to the observability plane.
13. Scoring Engine evaluates both target controls and agent behavior.
14. Runner, credentials, temporary storage, and scenario assets are destroyed or reset.

## 4. Authorization model

Authorization is the conjunction of:

- a valid Engagement manifest;
- a valid ROE manifest;
- a target and test case registered under that engagement;
- a policy allow decision;
- an unexpired execution grant;
- human approval when the action class requires it; and
- a network path that matches the expected destination tuple.

Any missing, unavailable, stale, contradictory, or unverifiable dependency produces a deny decision.

## 5. Tool boundary

The Model Gateway accepts only structured intents such as:

- `run_static_analysis(repository_id, profile_id)`
- `run_safe_network_discovery(target_id, profile_id)`
- `run_web_test(target_id, test_case_id)`
- `request_poc_validation(target_id, poc_id)`
- `collect_evidence(execution_id)`
- `propose_patch(finding_id)`
- `validate_patch(patch_id, test_suite_id)`
- `reset_range(scenario_id)`
- `terminate_engagement(engagement_id)`

The Tool Gateway rejects arbitrary command strings, raw URLs, raw IP addresses, hostnames, repository locations, cloud resource names, or unregistered tool options from the model.

## 6. Isolation strategy

- Static analysis and low-risk transformations may run in hardened containers on dedicated execution hosts.
- Dynamic tests use microVMs by default.
- Windows/domain scenarios use full KVM/libvirt VMs on dedicated range hosts.
- Kubernetes scenarios use disposable clusters isolated from the control platform; the agent never receives cluster-admin credentials.
- Highly adversarial or cross-tenant scenarios require dedicated physical hosts and no simultaneous unrelated tenants.

Isolation does not rely on virtualization alone. Host firewalls, namespace isolation, seccomp, capability dropping, read-only roots, cgroups, device allowlists, kernel hardening, dedicated service accounts, and independent telemetry provide defense in depth.

## 7. Network architecture

All zones use explicit allow rules. The range has no default route to the internet, corporate networks, or production networks. DNS, NTP, package sources, PKI, IdP, and cloud services are simulated or mirrored inside the range.

Execution-plane egress is limited to:

- the specific range target tuple generated from the signed manifest;
- the Credential Broker's token-exchange endpoint through mutual authentication;
- a one-way telemetry gateway; and
- control-plane job state endpoints using a job-specific identity.

Cloud metadata addresses, Docker sockets, container runtime sockets, Kubernetes management APIs, host bridges, and link-local management endpoints are explicitly blocked.

## 8. Fail-closed behavior

Emergency Stop is independent of the model and Agent Orchestrator. A stop event:

1. freezes scheduling and revokes unconsumed execution grants;
2. isolates the runner network;
3. revokes target credentials and model sessions;
4. snapshots volatile evidence where safe;
5. terminates the runner and scenario;
6. seals evidence and audit records; and
7. opens an incident workflow.

The same sequence is triggered by scope deviation, internet reachability, unexpected privilege escalation, persistence, log tampering, credential discovery, metadata access, unauthorized Kubernetes/Docker access, unexpected listeners, quota violations, repeated failure, policy unavailability, or monitoring loss.

## 9. Evidence and scoring

Evidence includes policy decisions, approvals, tool requests, target mappings, runner identity, model version, prompts after redaction, tool outputs, packet metadata, process tree, file deltas, screenshots, scanner reports, patches, test results, and destruction attestations.

Scoring has two independent dimensions:

- **Target score:** prevention, detection, response, evidence completeness, resilience, and remediation effectiveness.
- **Agent score:** scope adherence, approval compliance, unsafe-intent rejection, reproducibility, evidence quality, finding precision/recall, remediation quality, resource discipline, and prompt-injection resistance.

## 10. Primary design decisions

- Firecracker microVMs are the default Linux dynamic-test runner; Kata is an optional Kubernetes integration profile; KVM/libvirt is used for heterogeneous and Windows scenarios.
- OPA is the policy decision engine, with enforcement at Tool Gateway, scheduler, network, and runner lifecycle layers.
- OpenTofu is the preferred declarative IaC language; direct provider use is forbidden from the model context.
- The initial release is local-first and single-organization, with a later separately governed cloud profile.
- Observability and WORM evidence storage are independently administered.
- The model context is minimized and contains references, redacted evidence, and capability-scoped summaries—not credentials or raw infrastructure control data.

See `docs/adr/` for alternatives and revisit conditions.

## 11. Phase 03 local Control Plane MVP profile

Phase 03 introduces a local development profile for control-plane behavior only. The profile
runs in one Python process and one SQLite database on a single laptop. It is intentionally not
a deployment profile for the four-plane system and does not claim administrative, network,
identity, host, or evidence-store separation.

The profile contains no execution plane, cyber-range route, runner, network listener, external
model provider, production Policy Engine, or real Credential Broker. Its purpose is to prove:

- explicit `engagement_id` propagation;
- Scope/ROE validity and target-object enforcement;
- independent approval semantics;
- deterministic Policy Engine denial;
- audit-before-state-change atomicity using one SQLite transaction; and
- Emergency Stop independence from model and runner components.

Any future external adapter, HTTP listener, cloud integration, runner, credential integration,
or range connection requires a new active plan, security review, updated threat model, and
explicit architecture approval.


## 11. Phase 04 local Runner profile

The local execution-plane MVP uses a rootless Podman container with no network, private PID namespace, read-only root, one bounded writable workspace, fixed object-ID contracts, fixed workload entrypoint, host-controlled evidence extraction, independent Kill Switch enforcement, and unconditional destruction. It is a single-laptop development profile and does not replace the production microVM or independent observability design.

## 12. Phase 05 local Cyber Range profile

Phase 05 adds a synthetic, filesystem-backed cyber-range trust domain on the same laptop. It
creates no listener and imports no network client. Each scenario is an immutable reviewed package
with registered asset and operation IDs, harmless `RANGE-MARKER-*` evidence, a verified baseline
digest, stop conditions, reset/destruction requirements, and a host-side answer key.

The local profile represents web/API authorization, dependency, IaC, Kubernetes RBAC, indirect
prompt-injection, and scope-redirection weaknesses without running real vulnerable services.
Each instance has a disjoint disposable state root. Scope/ROE and independent approvals mediate
create, reset, and destroy operations; audit insertion occurs before runtime creation or action.
Unknown operations, external communication, cross-scenario access, and undeclared assets fail
closed. Reset recreates the exact baseline digest and destruction removes the complete instance
root while preserving only Control Plane audit, score, and destruction records.
