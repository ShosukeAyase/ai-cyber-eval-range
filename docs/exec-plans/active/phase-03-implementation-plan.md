# Phase 03 Controlled Implementation Plan (Not Started)

This plan is dependency ordered. Runtime implementation must not begin until the human decisions at the end are approved.

1. Approve security baseline, risk acceptances, and ADRs.
2. Select physical/cloud topology and create separate identity/network administrative domains.
3. Implement schemas, signature verification, immutable registries, and semantic validation.
4. Implement Policy Engine bundles and negative tests.
5. Implement approval service and one-time execution grants.
6. Implement Credential Broker integration and redaction tests.
7. Implement Tool Gateway with one low-risk static-analysis adapter only.
8. Implement independent observability and WORM evidence path.
9. Implement runner lifecycle with microVM attestation, quotas, and egress deny.
10. Implement minimal Web/API synthetic scenario and destruction attestation.
11. Run architecture, policy, isolation, prompt-injection, and emergency-stop tests.
12. Add patch proposal and revalidation workflow without auto-merge.
13. Add Linux, Windows, Kubernetes, and cloud-simulator scenarios sequentially.
14. Conduct independent security review before any broader use.

## Required human decisions

- Local physical topology or cloud account model.
- Firecracker/Kata/KVM profiles and dedicated-host thresholds.
- Kubernetes use for platform control components.
- IAM provider, workload identity, and credential broker.
- Evidence retention/WORM product and legal retention periods.
- Package mirror and trusted build/signing roots.
- Message queue and observability stack.
- OpenAI model profile, organization controls, and trusted-access requirements.
- Approval roles, staffing, and escalation SLA.
