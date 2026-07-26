# Production Readiness Gaps

## Summary

The current system is a local MVP. Production readiness requires replacing simulated or
same-host controls with independently administered, identity-bound, cryptographically verifiable,
and recoverable services. The remediation order below is mandatory because later capabilities
must not be built on untrusted identity, policy, audit, or isolation foundations.

## Wave 0 - authorization boundary before any production target

1. **Production IAM and workload identity**
   - Integrate an enterprise IdP with phishing-resistant MFA.
   - Issue short-lived workload identities with explicit audience and engagement claims.
   - Reject caller-supplied identity strings as authority.
   - Enforce role and separation-of-duties policy at service boundaries.

2. **Legally effective authorization and ROE**
   - Digitally sign engagement, scope, target ownership, test window, prohibited actions, data
     handling, and emergency contacts.
   - Add jurisdiction and privacy review.
   - Require revocation and expiry propagation before execution.

3. **Independent Policy Engine**
   - Replace hardcoded facts with authoritative services.
   - Sign/version policy bundles and verify trust roots.
   - Test missing, stale, corrupt, rollback, timeout, and partition cases.
   - Record the exact policy version and inputs in immutable evidence.

4. **Production Tool Gateway**
   - Implement one narrow adapter per tool profile.
   - Resolve destinations only from registered target IDs.
   - Use workload identity and one-time credentials.
   - Sign receipts and bind them to request, policy, adapter, target, and evidence digest.

## Wave 1 - independent containment and evidence

5. **Execution isolation**
   - Use dedicated Linux/KVM hosts and VM/microVM isolation for active workloads.
   - Apply explicit seccomp, AppArmor/SELinux, immutable host images, restricted device exposure,
     and host filesystem quotas.
   - Conduct independent sandbox-escape and malicious-image testing.

6. **Network isolation**
   - Remove default routes from execution/range zones.
   - Enforce deny rules through a separately administered firewall.
   - Use controlled DNS and an explicit egress proxy for the model adapter only.
   - Deploy independent network sensors and terminate on policy/telemetry loss.

7. **Independent Kill Switch**
   - Separate identity, process, host/plane, and administration from the Control Plane.
   - Provide runtime termination and network isolation authority.
   - Test control-plane compromise, partition, monitoring loss, and stuck workload cases.

8. **Immutable audit/evidence**
   - Stream events to an append-only collector in a separate account/plane.
   - Add chained digests, HSM-backed signatures, trusted timestamps, and monotonic sequence.
   - Store in compliance-mode WORM retention with independent verification and export.

## Wave 2 - supply-chain and secret custody

9. **Software supply chain**
   - Pin GitHub Actions to verified full commit SHAs.
   - Hash-lock all dependencies and build backends through an internal mirror.
   - Generate SBOM and SLSA provenance.
   - Sign and verify source releases, Runner images, policy bundles, and scenario packages.
   - Add dependency, image, IaC, secret, and license scanning with remediation SLAs.

10. **Secret management**
    - Replace environment-variable provider keys with KMS/HSM-backed workload authentication.
    - Deliver target credentials directly to adapters, never to the model or general Control Plane.
    - Add rotation, revocation, canary credentials, output scanning, and incident procedures.

11. **Scenario and scoring integrity**
    - Move answer keys to a private grader in a separate trust domain.
    - Sign scenario bundles and ground-truth versions.
    - Require independent scenario safety review and secret/PII scanning.

## Wave 3 - resilience and operational governance

12. **High availability and disaster recovery**
    - Define RTO/RPO and failure domains.
    - Deploy redundant Control Plane, Policy, Approval, and Audit services.
    - Protect backups and conduct restore/rollback tests.
    - Detect cloned or rolled-back state stores.

13. **Resource and cost governance**
    - Add organization-level concurrency, rate, token, cost, storage, and evidence quotas.
    - Implement backpressure and budget circuit breakers.
    - Test database growth, disk exhaustion, provider throttling, and prolonged outage.

14. **Model governance and live evaluations**
    - Use immutable model snapshots where available.
    - Treat every model/configuration change as a controlled release.
    - Run private live-model prompt-injection, tool-selection, scope, evidence, and outage evals.
    - Define rollback thresholds and provider data-retention/regional-processing requirements.

15. **Destruction assurance**
    - Inventory runtime disks, overlays, caches, snapshots, backups, and evidence copies.
    - Use encryption and key destruction for cryptographic erasure.
    - Test crash cleanup and independently verify absence after destruction.

## Minimum production pilot entry criteria

A restricted pilot may begin only after all Wave 0 and Wave 1 items are independently verified,
all high supply-chain and secret-management findings are closed, and the legal authority approves
the exact pilot target set. The pilot must still exclude public vulnerable services, corporate or
production network routes, arbitrary commands, unrestricted scanners, and real secrets in model
context.
