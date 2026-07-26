# Documentation Index

## Start here

1. [Architecture](../ARCHITECTURE.md)
2. [Security principles](security/security-principles.md)
3. [Threat model](security/threat-model.md)
4. [Trust boundaries](security/trust-boundaries.md)
5. [Network matrix](security/network-matrix.md)
6. [Authorization model](governance/authorization-model.md)
7. [API boundaries](design/api-boundaries.md)
8. [Phase 02 repository skeleton](design/repository-skeleton.md)
9. [Local Control Plane MVP](design/control-plane-mvp.md)
10. [Isolated Runner MVP](design/isolated-runner-mvp.md)
11. [Cyber Range MVP](design/cyber-range-mvp.md)
12. [Agent integration](design/agent-integration.md)
13. [State machines](design/state-machines.md)
14. [Reset and destruction](design/reset-and-destruction.md)
15. [Risk register](security/risk-register.md)
16. [Independent assurance report](assurance/assurance-report.md)
17. [Production go/no-go checklist](assurance/go-no-go-checklist.md)

## Execution plans

- [Completed Phase 01 design](exec-plans/completed/phase-01-design.md)
- [Completed Phase 02 repository skeleton](exec-plans/completed/phase-02-repository-skeleton.md)
- [Completed Phase 03 Control Plane MVP](exec-plans/completed/phase-03-control-plane-mvp.md)
- [Completed Phase 04 Runner MVP](exec-plans/completed/phase-04-isolated-runner-mvp.md)
- [Completed Phase 05 Cyber Range MVP](exec-plans/completed/phase-05-cyber-range-mvp.md)
- [Completed Phase 06 Agent integration](exec-plans/completed/phase-06-agent-integration.md)
- [Completed Phase 07 assurance review](exec-plans/completed/phase-07-assurance-review.md)
- [Active plans](exec-plans/active/README.md)

## Cross-cutting documents

- [Assumptions](assumptions.md)
- [References](references.md)
- [Project source review](source-review.md)
- [Traceability](traceability.md)
- [Design review checklist](design-review-checklist.md)
- [Validation report](validation-report.md)
- [CISSP mapping](education/cissp-mapping.md)

## Design status

Phase 01 is the approved design baseline. Phase 02 is the non-executable contract skeleton. Phase 03 implements the local Control Plane MVP; Phase 04 adds the approved rootless isolated Runner; Phase 05 adds a non-networked synthetic Cyber Range. Phase 06 adds a proposal-only GPT Agent behind the existing approval, Scope/ROE, Tool Gateway, Policy Engine, audit, and Emergency Stop boundaries. Phase 07 independently reviewed the complete system and issued a production NO-GO because unresolved high risks remain. Real vulnerable services, real credentials, external targets, cloud resources, and production deployment remain prohibited.
