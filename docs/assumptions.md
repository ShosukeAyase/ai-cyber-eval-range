# Assumptions

| ID | Assumption | Rationale | Validation owner | Consequence if false | Status |
|---|---|---|---|---|---|
| A-001 | The initial deployment is single-organization and local-first. | Minimizes cloud identity and routing complexity during safety validation. | Platform owner | Cloud account separation and service limits must be redesigned. | Provisional |
| A-002 | Linux dynamic runners can use hardware virtualization. | Required for microVM isolation. | Infrastructure owner | Use dedicated full-VM hosts or halt dynamic testing. | Open |
| A-003 | Windows scenarios run only on dedicated KVM/libvirt hosts. | Windows domain simulation is not a Firecracker target. | Range owner | A separate Hyper-V design may be required. | Provisional |
| A-004 | No production, corporate, or public target data is copied into the range. | Required by invariant. | Data owner | Engagement is rejected. | Binding |
| A-005 | A human approver is available during high-risk test windows. | State changes and PoC validation cannot self-approve. | Engagement owner | Job pauses or expires. | Binding |
| A-006 | The observability plane can receive telemetry through a one-way or write-only path. | Prevents execution identities from altering evidence. | Security operations | Evidence assurance is reduced; launch is blocked. | Open |
| A-007 | Package dependencies can be mirrored and pre-approved before an engagement. | General internet access is prohibited. | Supply-chain owner | Scenario cannot run until artifacts are mirrored. | Provisional |
| A-008 | GPT-5.6 is accessed only through Model Gateway with organization-managed identity and logging. | Required for model-context and use-policy controls. | AI platform owner | Model use is disabled. | Binding |
| A-009 | All scenario credentials are synthetic and disposable. | Prevents real-secret exposure. | Scenario author | Scenario publication is blocked. | Binding |
| A-010 | WORM storage or equivalent retention lock is available for evidence. | Needed for independent, tamper-evident custody. | Compliance owner | Evidence can be used only for engineering, not formal assurance. | Open |
| A-011 | Runner hosts are single-purpose and do not host control-plane or observability workloads. | Enforces trust-boundary separation. | Infrastructure owner | Deployment is nonconformant. | Binding |
| A-012 | “Complete destruction” means cryptographic erasure plus deletion of ephemeral compute/storage and expiry of all credentials, with retained immutable audit/evidence according to policy. | Literal erasure of retained compliance evidence is contradictory. | Legal/compliance | Retention and destruction policies must be reconciled. | Provisional |

Assumptions are not authorization. Any assumption affecting scope, identity, network reachability, or evidence integrity must be resolved before implementation.

---

## A8 — Phase 03 bootstrap approvals are a local test trust root

**Ambiguity**: Every write requires approval, but an Approval Service cannot create its own
initial authorization without a root of trust.

**Assumption**: `ControlPlaneMvp.local_dev` receives two distinct human-role identifiers and
seeds reciprocal, expiring administrative approval grants before public service operations
begin. The grants are synthetic local configuration and are never serialized as real signed
authorization.

**Rationale**: This resolves the bootstrap cycle while preserving independent identities for
every exposed write operation. It introduces no external identity, secret, or network service.

**Revisit if**: The Control Plane gains any external caller, multi-user deployment, production
identity provider, signed approvals, or execution capability.
