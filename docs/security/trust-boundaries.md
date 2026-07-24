# Trust Boundaries

Status: draft — foundational document. Referenced by `ARCHITECTURE.md`, `docs/security/threat-model.md`, `docs/security/network-matrix.md`, and all plane-specific design documents.

This document defines the four trust planes required by AGENTS.md and the task brief, the boundaries between them, and the rules that must hold at each boundary. It does not describe implementation; it describes the invariants that any implementation must satisfy.

## 1. The four planes

Per AGENTS.md ("Separation of duties," "Compartmentalization") and the task brief (絶対条件 #1–2), the system is divided into four trust planes. **No plane shares IAM identities, credentials, networks, or execution hosts with another plane.**

### 1.1 Control Plane

**Responsibility**: Decides what is allowed. Never executes against a target.

Components (task brief §4): Agent Orchestrator, Scope and ROE Service, Policy Engine, Human Approval Service, Credential Broker, Job Scheduler, Emergency Stop Service, Model Gateway.

**Holds**: Scope/ROE manifests (signed), policy rules, approval records, credential issuance logic (not the credentials' long-term secrets — see Credential Broker design in `docs/security/credential-model.md`), job state.

**Does not hold**: Direct network access to the cyber range; direct filesystem access to Runners; long-lived target credentials.

### 1.2 Execution Plane

**Responsibility**: Carries out authorized actions against range targets, under continuous mediation.

Components (task brief §4): disposable Runners, Tool Gateway, Command Allowlist, Resource Quotas, Egress Firewall, Artifact Collector, Runner Lifecycle Manager.

**Holds**: Ephemeral, target-scoped, short-lived credentials issued per-job by the Credential Broker; a running job's working state until evidence collection.

**Does not hold**: Scope/ROE manifest authority (it consumes decisions, it does not make them); the model's full conversational context beyond what a specific tool call requires; any credential outside the current job's authorized scope; access to the monitoring plane's audit store (write path only, one-directional — see §3.4).

### 1.3 Cyber Range

**Responsibility**: Hosts disposable, synthetic target systems (Web/API, Linux, Windows domain, container/Kubernetes, cloud IAM/storage simulations) and their supporting dummy services (DNS, PKI, IdP, package mirror).

**Holds**: Synthetic data, dummy credentials, scenario state.

**Does not hold**: Any route to the general internet, corporate networks, or production systems (see §2.3). No real personal or confidential data (AGENTS.md invariant).

### 1.4 Monitoring Plane

**Responsibility**: Independently observes and records everything happening in the other three planes. Cannot be modified by them.

Components (task brief §4): centralized logging, packet capture, process tree monitoring, file diffing, OpenTelemetry, metrics, SIEM, tamper detection, scoring engine, evidence storage.

**Holds**: Append-only audit records, evidence artifacts, scoring data.

**Does not hold**: Any write-back capability into the control, execution, or range planes. It is a sink, not a source, of control signals — with one narrow exception: the Emergency Stop Service (control plane) may consume monitoring-plane signals (e.g., a stop-condition detector) to *trigger* termination, but the monitoring plane itself never directly halts or reconfigures another plane; it only reports.

## 2. Boundary rules

### 2.1 Control Plane ↔ Execution Plane

- All execution-plane actions originate from an explicit, validated instruction from the control plane (Job Scheduler dispatches a job only after Policy Engine + Scope/ROE Service approval).
- The execution plane never accepts an unmediated instruction from the model directly; every tool call passes through the Tool Gateway, which itself calls back into the Policy Engine before allowing any range-facing action (task brief §5).
- Credentials cross this boundary only as short-lived, single-job-scoped tokens issued by the Credential Broker at job dispatch time — never as long-lived secrets, never placed in the model's context (AGENTS.md: "No direct model access to secrets").
- The execution plane cannot request scope changes, expiration extensions, or new targets from the control plane; it can only report job status and request already-authorized next steps within the existing job's approved envelope.

### 2.2 Execution Plane ↔ Cyber Range

- All execution-plane→range traffic passes through the Egress Firewall and is checked against the Command Allowlist and per-job Resource Quotas.
- Default-deny: an execution-plane Runner has no route to any range asset it was not explicitly authorized for in the current job.
- Runners have no reachability to cloud metadata endpoints, the Docker socket, or Kubernetes management APIs unless a specific scenario's design explicitly and narrowly requires it, and even then, that reachability is itself a range-internal path, never a shortcut to the host or to production (AGENTS.md invariants).

### 2.3 Cyber Range ↔ Outside World

- **No route exists from the cyber range to the general internet.** (AGENTS.md, task brief 絶対条件 #3)
- **No route exists from the cyber range to corporate or production networks.**
- Any service the range needs that would normally reach the internet (DNS resolution, package installation, PKI/certificate issuance, identity provider behavior) is provided by a **dummy, range-internal equivalent** (task brief §4: "ダミーDNS、PKI、IdP、パッケージミラー").
- This boundary is enforced at the network layer (firewall/segmentation), not merely by policy or convention — per AGENTS.md, "Prompt-based instructions are not a security boundary."

### 2.4 Any Plane ↔ Monitoring Plane

- Telemetry, logs, packet captures, and process/file diff data flow **one-way, outward**, from the control/execution/range planes into the monitoring plane.
- No plane other than the monitoring plane's own administrative process can delete or modify an audit record once written (AGENTS.md: "No route from... the execution plane to delete audit records"; task brief: "実行側から監査ログを削除または変更できない").
- The monitoring plane is architecturally isolated (its own account/IAM, per the ADR topic "監視プレーンの別アカウント化") so that a compromise of the control or execution plane cannot retroactively erase evidence of that compromise.

### 2.5 Model ↔ Everything

- The model (via the Model Gateway, control plane) never receives raw IP addresses, hostnames, URLs, or shell command strings to execute unconditionally.
- The model's only means of requesting action is a small set of typed, target-ID-based functions (task brief §5: `get_engagement()`, `run_static_analysis(repository_id, profile_id)`, etc.), each of which is independently validated by the Policy Engine and Tool Gateway against: engagement ID correspondence, scope membership, action permission, expiration, rate/concurrency limits, required human approval, prohibited terms/options, and expected network destination.
- The model cannot alter the Scope/ROE manifest, approve its own actions, extend expiration, or add targets (AGENTS.md: "The model cannot add targets, extend expiration dates, broaden actions, alter limits, or approve its own actions").
- Untrusted content the model processes (target source code, README files, code comments, issues/PRs, logs, web content, API responses, documents, test fixtures, scenario content, tool output) is treated strictly as **data**, never as instructions, regardless of its phrasing (AGENTS.md "Untrusted content"; this is the basis for `docs/security/prompt-injection-model.md`).

## 3. Cross-cutting invariants applied at every boundary

These restate AGENTS.md's security invariants as boundary-level checks, so that each interface in `docs/design/api-boundaries.md` can be tested against a concrete rule:

1. **Default deny** — every boundary crossing requires an explicit allow; absence of a rule means deny.
2. **Complete mediation** — every single tool call, not just the first in a session, is checked (no caching of "already authorized" across calls without re-validation against current scope/expiration/rate state).
3. **Fail closed** — any ambiguity, error, or missing policy decision at a boundary results in the action being blocked, not permitted.
4. **No shared secrets across boundaries** — a credential valid in one plane is never simultaneously valid or reused in another.
5. **Attributability** — every boundary crossing is logged with enough context to answer: which engagement, scenario, target, tool, model version, policy decision, and approval decision authorized it.

## 4. Open items for this document

- Exact IAM account/tenant boundaries (AWS accounts, GCP projects, or on-prem equivalents) are deferred to `docs/security/iam-model.md` and the relevant ADRs (local-first vs. cloud, monitoring plane account separation).
- Precise network zone diagram (Mermaid) is deferred to `docs/security/data-flow-diagrams.md` and `docs/security/network-matrix.md`, which will instantiate the rules in §2 as concrete allow/deny tables.
- The narrow exception process for scenario-internal Kubernetes/Docker/cloud-metadata reachability (§2.2) needs a concrete allowlist mechanism, to be specified in `docs/design/execution-plane.md`.
