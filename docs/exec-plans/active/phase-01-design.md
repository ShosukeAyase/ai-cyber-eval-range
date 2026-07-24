# Phase 01 Design Plan

## Purpose

Produce a reviewable, testable architecture baseline for the authorized AI cyber-evaluation platform and isolated cyber range. Stop before implementation or deployment.

## Work items

- [x] Establish repository invariants from `AGENTS.md`.
- [x] Define four planes and trust boundaries.
- [x] Define network matrix and mandatory deny paths.
- [x] Define authorization, ROE, approvals, IAM, and credentials.
- [x] Define model/tool API boundary and prompt-injection controls.
- [x] Define range scenario families and destruction lifecycle.
- [x] Define independent observability, evidence custody, and scoring.
- [x] Create JSON Schemas and synthetic examples.
- [x] Create required ADRs.
- [x] Create architecture/policy/schema consistency tests.
- [x] Create traceability matrix and design-review checklist.
- [x] Draft dependency-ordered Phase 02 plan.

## Premises

- Design only; no live targets, deployment, exploit execution, or external communications.
- Local-first is provisional.
- Model output is untrusted and has no authorization authority.
- High-risk actions require independent human approval.

## Decisions

- Firecracker default for Linux dynamic runners; KVM/libvirt for Windows/heterogeneous scenarios; Kata optional for Kubernetes-integrated workloads.
- OPA as PDP, with enforcement in multiple PEPs.
- OpenTofu preferred for IaC.
- Separate observability administration and WORM evidence.
- Object-ID-based tool interfaces and no arbitrary command API.

## Progress

Design artifacts, schemas, examples, diagrams, policies, ADRs, and tests created.

## Open issues

- Minimum physical topology for local-first separation.
- WORM implementation and retention authority.
- Credential broker technology and trust roots.
- Whether Kubernetes is permitted for the v1 control plane.
- Windows licensing/image maintenance.
- OpenAI organization/model access configuration and data-retention review.
- Hardware profile and microarchitectural-risk acceptance.

## Risks

See `docs/security/risk-register.md`, especially R-001, R-002, R-003, R-005, R-008, R-010, and R-018.

## Validation results

- `make validate`: passed; 21 tests passed.
- Schema validation: passed for all seven schemas and three examples.
- Architecture invariants: passed, including four planes, mandatory deny paths, required threat actors, stop conditions, ten Mermaid diagrams, and fourteen ADRs.
- Policy contract checks: passed for default deny, approval requirements, destination matching, prohibited actions, and no public routes.
- Documentation checks: passed for relative links and unresolved marker policy.
- `git diff --check`: passed.
- Python bytecode compilation: passed.
- Optional tools not installed and therefore not executed: OPA, OpenTofu/Terraform, markdownlint, Trivy, Syft, Grype, Cosign, and Gitleaks.
- IaC validation/security scanning, dependency scanning, SBOM generation for runtime dependencies, and image scanning are not applicable until implementation artifacts exist; they remain mandatory Phase 02 gates.
