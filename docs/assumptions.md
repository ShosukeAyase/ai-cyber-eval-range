# Assumptions

This document records design-time assumptions made where the task brief, AGENTS.md, or prior documentation did not fully specify a decision, per the working method in the task brief (§12) and AGENTS.md's development workflow. Assumptions here are **not authorization** — they are provisional design defaults, subject to override by an approved ADR, the active execution plan, or explicit human decision, per AGENTS.md's precedence order.

Each entry states: the ambiguity, the assumption made, the rationale, and the condition under which it should be revisited.

---

## A1 — Model identity is a configuration value, not a hard-coded dependency

**Ambiguity**: The Japanese task brief names "GPT-5.6" as the model powering the cyber-evaluation agent's analysis/planning/evidence functions.

**Assumption**: The design treats the model as pluggable behind a **Model Gateway** abstraction (control-plane component). No document, schema, or interface hard-codes a specific model vendor, version, or API shape beyond a configuration field (e.g., `model_id: string`).

**Rationale**: AGENTS.md's security invariants (least privilege, compartmentalization, no direct model access to secrets) apply regardless of which model is behind the gateway. Coupling the architecture to one model vendor would violate the spirit of "context minimization to the model" (task brief §9, ADR topic) and create unnecessary vendor lock-in risk.

**Revisit if**: A specific model vendor's API constraints (context window, tool-calling schema, rate limits) turn out to require gateway-level special-casing.

---

## A2 — No pre-existing infrastructure, repository, or cloud account

**Ambiguity**: Neither AGENTS.md nor the task brief states whether this design assumes greenfield or brownfield conditions.

**Assumption**: Greenfield. No cloud account, Kubernetes cluster, CI/CD system, IAM tenant, or existing codebase is assumed to exist. All infrastructure in the design is described but not provisioned in the design phase.

**Rationale**: The repository, at the start of this work, contained only `AGENTS.md`. Nothing in the task brief indicates an existing target platform to integrate with.

**Revisit if**: A human decision-maker indicates this platform must integrate with an existing corporate IdP, cloud account, or CI system (see Open Decision O5 in the phase-01 plan).

---

## A3 — "Codex" refers to the coding agent performing this work, not a system component

**Ambiguity**: The Japanese task brief opens with "本タスクでは...Codexで設計する" (this task is designed using Codex).

**Assumption**: This refers to the AI coding agent used to perform the design work in this session/repository, not a named component of the target architecture. No design artifact should introduce a component literally named "Codex."

**Rationale**: Cross-referencing against task brief §4 (component list) and §7 (deliverables list), no such component is named there. The reference is best read as tooling-for-the-task, analogous to how this session uses Claude.

**Revisit if**: Future instructions explicitly name a "Codex" component with defined responsibilities.

---

## A4 — Default isolation technology for disposable Runners: microVM (Firecracker), pending ADR

**Ambiguity**: Task brief §9 requires an ADR comparing VM/microVM/container isolation and Firecracker/Kata/KVM choices, but does not pre-select an answer.

**Assumption**: For design-consistency purposes only (diagrams, network matrix, state machines), documents will refer to Runners as **microVM-isolated (Firecracker-class)** until the ADR is written and approved. This is a placeholder default, not a final decision.

**Rationale**: microVMs offer strong isolation with lower overhead than full VMs, and are a common choice for disposable, per-job execution environments. This keeps early diagrams concrete and reviewable rather than abstract.

**Revisit if**: The ADR (task brief §9, item in phase-01 plan #38) concludes differently, or a human operator specifies a required runtime (e.g., an existing Kubernetes-based fleet mandating gVisor or Kata instead).

**Flagged in**: phase-01 plan, Open Decision O1.

---

## A5 — Default Policy Engine: OPA (Open Policy Agent), pending ADR

**Ambiguity**: Task brief §9 requires an ADR on Policy Engine choice ("OPAまたは同等").

**Assumption**: Design documents, schema shapes, and policy test stubs will assume **OPA/Rego** as the working default.

**Rationale**: OPA is a widely adopted, well-documented policy-as-code engine with a mature decision API (`POST /v1/data/...`) that maps cleanly onto the "Policy Engine authorizes every tool call" requirement (task brief §5). Using a concrete default makes the Tool Gateway's request/response contracts easier to specify precisely.

**Revisit if**: The ADR selects a different engine, or organizational standards mandate an alternative (e.g., Cedar, OpenFGA).

**Flagged in**: phase-01 plan, Open Decision O2.

---

## A6 — Deployment topology default: local-first, cloud-portable

**Ambiguity**: Task brief §9 requires comparing local-first vs. cloud configurations, without a stated default.

**Assumption**: Design documents describe the control plane, execution plane, cyber range, and monitoring plane as deployable on a **single local host or small on-prem cluster by default**, with cloud deployment treated as a portable alternative (not the primary target) for this phase.

**Rationale**: A local-first default keeps the design's "no route to production or general internet" invariant easiest to enforce and verify (fewer implicit cloud-network paths to reason about), and matches an evaluation/lab use case rather than a multi-tenant SaaS use case.

**Revisit if**: A human operator specifies this must run in a specific cloud environment (AWS/GCP/Azure) from the outset, e.g., for organizational infrastructure reasons.

**Flagged in**: phase-01 plan, Open Decision O3.

---

## A7 — Evidence retention default: minimum 90 days, WORM-backed

**Ambiguity**: Task brief requires an evidence-retention design (`docs/governance/evidence-retention.md`) and a WORM storage ADR, without specifying duration or legal/compliance constraints.

**Assumption**: Design documents will propose a **minimum 90-day retention period** for evidence and audit records, stored in a WORM (write-once-read-many) backend, as a starting default subject to organizational/compliance override.

**Rationale**: 90 days is a common baseline for security evidence retention in absence of a specific regulatory driver, long enough to support post-engagement review and dispute resolution, short enough to bound storage cost during design.

**Revisit if**: A specific compliance regime (e.g., contractual audit requirements) mandates a longer or shorter period.

**Flagged in**: phase-01 plan, Open Decision O4.

---

## A8 — Human Approval Service identity backend: standalone for this phase

**Ambiguity**: Task brief requires a Human Approval Service and approval state machine, without specifying its authentication backend.

**Assumption**: The design treats the Human Approval Service as having its **own standalone identity/authorization mechanism** for this phase (e.g., a dedicated approver role list), rather than assuming integration with any specific existing corporate IdP.

**Rationale**: No existing IdP is assumed to exist (see A2). A standalone mechanism keeps the design testable in isolation; integration points for an external IdP can be added as an extension point in `docs/design/control-plane.md` without blocking this phase.

**Revisit if**: A human operator specifies a required IdP (e.g., Okta, Entra ID) for approval identity.

**Flagged in**: phase-01 plan, Open Decision O5.

---

## A9 — AGENTS.md and the Japanese task brief are treated as non-conflicting

**Ambiguity**: Two governing documents were supplied (AGENTS.md in English, a task brief in Japanese) without an explicit statement of which supersedes the other beyond AGENTS.md's own precedence list.

**Assumption**: The two are treated as consistent elaborations of the same requirements — AGENTS.md as the durable, higher-precedence governance layer; the task brief as a more granular one-time work order. Where the task brief adds detail not in AGENTS.md (e.g., the specific component list in §4, the deliverables list in §7), that detail is adopted. Where a genuine conflict is found, AGENTS.md's invariants win per its own stated precedence.

**Rationale**: A line-by-line comparison at plan-creation time found no contradictions — only differences in granularity and language.

**Revisit if**: A future addition to either document introduces an actual conflict; if so, it will be recorded in the active execution plan's "unresolved conflicts" section rather than resolved silently, per AGENTS.md's instruction.
