# Execution Plan — Phase 01: Design

Status: ACTIVE
Phase: Design only (no implementation, no deployment, no execution against real or synthetic infrastructure)
Owner: AI evaluation agent (Codex/Claude), under human review
Precedence reference: AGENTS.md → "Sources of truth" / "Security invariants"

---

## 1. Purpose

Design, in a single repository, two coupled systems:

**A. Cyber-evaluation system** — an LLM-assisted (GPT-5.6, per task brief) analysis/planning/evidence-review agent whose scope, authorization, and execution permissions are enforced by deterministic mechanisms external to the model itself (Policy Engine, Tool Gateway, Scope/ROE manifests, Human Approval Service, Credential Broker).

**B. Isolated cyber range** — a disposable, non-production exercise environment (Web/API, Linux, Windows domain, container/Kubernetes, cloud IAM/storage simulations) with no route to corporate networks or the general internet, fully destructible after each engagement, and capable of scoring both the target system and the AI agent's own behavior.

This phase produces design artifacts only: architecture documents, schemas, diagrams, ADRs, and design-verification tests. No implementation, deployment, exploit code, or execution against any target — synthetic or real — occurs in this phase.

## 2. Scope of this plan

In scope:
- Repository skeleton and documentation structure listed in AGENTS.md §7 (task brief §7)
- Trust boundary, threat model, network matrix, and authorization model documentation
- JSON Schemas for engagement, ROE, scenario, finding, evidence, approval, score
- Mermaid diagrams listed in task brief §8
- ADRs listed in task brief §9
- Machine-checkable tests validating schema conformance and doc/architecture consistency (not runtime behavior)

Out of scope for this phase (deferred to implementation phases):
- Any working Runner, Tool Gateway, Policy Engine, or Credential Broker code
- Any real or synthetic network scanning, exploitation, or payload execution
- CI/CD pipeline execution
- Any connection to real external systems (explicitly prohibited at all phases, not just this one)

## 3. Precedence and conflict handling

Per AGENTS.md:
1. Security invariants (AGENTS.md)
2. Approved ADRs
3. Architecture documentation
4. Active execution plan (this file)
5. Implementation code
6. Comments and examples

Conflicts encountered during design are recorded in §7 (Open Decisions) below, not resolved silently. Ambiguities that do not block progress are resolved with a documented, reasonable assumption in `docs/assumptions.md`, per the task brief's working method (§12).

## 4. Work items

Tracked in dependency order. Status values: `not-started`, `in-progress`, `blocked`, `done`.

| # | Item | Depends on | Status |
|---|------|-----------|--------|
| 1 | This execution plan | — | done |
| 2 | Repo survey / baseline summary | — | done (see §8) |
| 3 | `docs/assumptions.md` | 1 | not-started |
| 4 | `README.md` | 1 | not-started |
| 5 | `docs/security/trust-boundaries.md` | 4 | not-started |
| 6 | `ARCHITECTURE.md` | 5 | not-started |
| 7 | `docs/security/threat-model.md` | 6 | not-started |
| 8 | `docs/security/security-principles.md` | 6 | not-started |
| 9 | `docs/security/network-matrix.md` | 5,6 | not-started |
| 10 | `docs/security/iam-model.md` | 5,6 | not-started |
| 11 | `docs/security/credential-model.md` | 6,10 | not-started |
| 12 | `docs/security/prompt-injection-model.md` | 7 | not-started |
| 13 | `docs/security/abuse-cases.md` | 7 | not-started |
| 14 | `docs/security/risk-register.md` | 7,9,10,11 | not-started |
| 15 | `docs/security/data-flow-diagrams.md` (Mermaid) | 5,6 | not-started |
| 16 | `docs/governance/authorization-model.md` | 6 | not-started |
| 17 | `docs/governance/rules-of-engagement.md` | 16 | not-started |
| 18 | `docs/governance/data-handling.md` | 6 | not-started |
| 19 | `docs/governance/evidence-retention.md` | 6 | not-started |
| 20 | `docs/governance/incident-response.md` | 7,14 | not-started |
| 21 | `docs/design/control-plane.md` | 6 | not-started |
| 22 | `docs/design/execution-plane.md` | 6,21 | not-started |
| 23 | `docs/design/cyber-range.md` | 6 | not-started |
| 24 | `docs/design/observability.md` | 6 | not-started |
| 25 | `docs/design/scoring.md` | 23 | not-started |
| 26 | `docs/design/reset-and-destruction.md` | 23 | not-started |
| 27 | `docs/design/api-boundaries.md` | 21,22 | not-started |
| 28 | `docs/design/state-machines.md` (approval, job, credential lifecycle) | 16,21 | not-started |
| 29 | `schemas/engagement.schema.json` | 16 | not-started |
| 30 | `schemas/roe.schema.json` | 17 | not-started |
| 31 | `schemas/scenario.schema.json` | 23 | not-started |
| 32 | `schemas/finding.schema.json` | 25 | not-started |
| 33 | `schemas/evidence.schema.json` | 19 | not-started |
| 34 | `schemas/approval.schema.json` | 28 | not-started |
| 35 | `schemas/score.schema.json` | 25 | not-started |
| 36 | `examples/engagement.yaml`, `roe.yaml`, `scenario.yaml` | 29–31 | not-started |
| 37 | Mermaid diagrams (context, trust-boundary DFD, network zones, job sequence, approval FSM, emergency stop, runner lifecycle, credential lifecycle, find→verify→patch→reverify loop, audit log one-way flow) | 5,6,21–28 | not-started |
| 38 | ADRs (`docs/adr/`) — isolation tech, policy engine, IaC tool, K8s-as-control-plane risk, local-vs-cloud, monitoring account separation, package mirror, secrets mgmt, message queue, WORM evidence store, logs/metrics/traces stack, context minimization, human-in-the-loop boundary | 6 | not-started |
| 39 | `tests/schemas/` — JSON Schema validation tests against examples | 29–36 | not-started |
| 40 | `tests/architecture/` — dependency/layering checks (e.g., no execution-plane import of control-plane secrets) | 6,21,22 | not-started |
| 41 | `tests/policy/` — policy rule test stubs (allow/deny cases, fail-closed cases) | 16,21 | not-started |
| 42 | Traceability matrix (requirement → design element → test) | all above | not-started |
| 43 | Design review checklist | all above | not-started |
| 44 | `docs/exec-plans/active/` → next-phase implementation plan (dependency-ordered) | all above | not-started |
| 45 | `Makefile` (design-phase targets: lint, schema-validate, diagram-render-check, doc-link-check) | 39–41 | not-started |

## 5. Assumptions made so far

Recorded in full in `docs/assumptions.md` (to be created at item 3). Summary of assumptions already implied by adopting the task brief verbatim:

- "GPT-5.6" in the task brief refers to the model used by the cyber-evaluation agent in the target design; this repository's design is model-agnostic behind the Model Gateway abstraction, so no design artifact hard-codes a specific model vendor or version beyond a configuration value.
- No existing repository, CI system, or cloud account is assumed to exist yet; all infrastructure described is designed but not provisioned in this phase.
- "Codex" in the task brief refers to the coding agent used to perform this design work, not a system component to be built.
- Where the task brief (Japanese) and AGENTS.md (English) overlap, they are treated as consistent statements of the same requirements; AGENTS.md's precedence list governs conflict resolution as stated in §3 above.

## 6. Progress

- [x] Reviewed uploaded `AGENTS.md` and Japanese task brief for consistency (no conflicts found; task brief is more granular, AGENTS.md is the durable governance layer).
- [x] Confirmed no pre-existing repository content — starting from a clean slate.
- [x] Created this execution plan.
- [ ] All other items in §4 pending.

## 7. Open decisions requiring human input

These are decisions this agent will not resolve unilaterally, per AGENTS.md ("The model cannot add targets, extend expiration dates, broaden actions, alter limits, or approve its own actions") and the general principle that scope and authorization are human/policy-owned:

1. **Isolation technology default**: microVM (Firecracker/Kata) vs. container vs. full VM for disposable Runners — a real ADR is required (task brief §9), but the *default* choice that ships in examples/config needs a human owner to accept the operational cost tradeoff.
2. **Policy Engine choice**: OPA/Rego vs. an alternative — affects schema design for `schemas/*.schema.json` and policy test structure (item 41). Recommend proceeding with OPA as a working default for design purposes, subject to ADR and human confirmation.
3. **Cloud vs. local-first deployment target**: affects network-matrix and IAM-model concreteness. Will default to "local-first, cloud-portable" in design docs unless directed otherwise.
4. **Evidence retention duration and WORM backend choice**: legal/compliance-driven; this agent will propose a default (e.g., 90-day minimum) in `docs/governance/evidence-retention.md` but retention policy is ultimately an organizational/compliance decision.
5. **Human Approval Service authentication/authorization backend**: e.g., tied to an existing corporate IdP vs. standalone — needs a real target environment decision, not assumable in the abstract.

## 8. Repository baseline summary (as of this plan's creation)

- Repository did not previously exist in this workspace.
- Only file present at start: `AGENTS.md` (uploaded, matches the version reproduced in this session).
- A companion Japanese-language task brief was supplied in the same turn; treated as an elaboration of AGENTS.md, not a superseding document — AGENTS.md's own precedence rules apply if the two ever conflict.
- No ADRs, schemas, diagrams, or code exist yet.

## 9. Risks (design-phase level; full detail deferred to `docs/security/risk-register.md`, item 14)

- **R1 — Scope creep in examples**: Illustrative `examples/*.yaml` or diagrams could be mistaken for authorization to act; mitigate by marking all examples non-functional/synthetic and never wiring them to live credentials.
- **R2 — Under-specification of fail-closed behavior**: If state-machine designs (item 28) don't enumerate every failure transition, later implementation could default to fail-open. Mitigate with explicit negative-path documentation in state machines and policy tests.
- **R3 — Model-influenced scope drift across phases**: Nothing in this repository's design should allow a model (this agent or the target GPT-5.6-based agent) to expand its own authority between phases. Mitigate by keeping Scope/ROE manifest schemas signed and external to model context.
- **R4 — Documentation/implementation divergence in later phases**: Deferred risk; flagged here so the next execution plan inherits it explicitly.

## 10. Validation performed for this plan

- Manual consistency check between AGENTS.md and the Japanese task brief: no contradictions found; task brief is a more detailed elaboration of the same invariants.
- No automated tests exist yet (schemas, architecture tests, etc. are all pending — see §4 items 39–41). This is explicitly reported per AGENTS.md ("do not claim a test passed unless it was executed").

## 11. Next steps (immediate)

1. Create `docs/assumptions.md`.
2. Create `README.md`.
3. Draft `docs/security/trust-boundaries.md` and `ARCHITECTURE.md` as the foundational pair (items 5–6), since nearly everything else in §4 depends on them.
