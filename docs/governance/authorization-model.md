# Authorization Model

## Authorization sources

Only the following sources can grant action authority:

1. schema-valid signed Engagement manifest;
2. schema-valid signed ROE manifest;
3. registered target/test-case/scenario objects;
4. valid human approval record when required;
5. current Policy Engine allow decision; and
6. one-time scheduler execution grant.

Model output, source code, target content, operator chat, comments, logs, and tool output are never authorization sources.

## Decision tuple

Every decision binds:

`engagement_id, roe_id, job_id, target_id, test_case_id, action_class, tool_profile_id, policy_version, approval_id?, not_before, expires_at, nonce`

## Risk tiers

| Tier | Examples | Approval |
|---|---|---|
| T0 | Read manifests, retrieve prior evidence | Pre-authorized by engagement |
| T1 | Static analysis, read-only repository inspection | Policy allow; no per-call approval |
| T2 | Safe discovery, non-invasive web checks, BAS markers | Engagement approval and bounded profile |
| T3 | State change, credential use, PoC validation, patch validation against mutable target | Explicit human approval per job or batch |
| T4 | Actions prohibited by invariant: persistence, evasion, credential dumping, destructive/DoS, external target access | Never allowed |

## Approval properties

- Approver cannot be the requestor for T3.
- Approval has explicit target/action/test-case scope.
- Approval has a short expiry and single-use or bounded-use count.
- Approval is rechecked immediately before execution.
- Policy or scope change invalidates outstanding approvals.
- Emergency stop revokes all active approvals and grants.

## Phase 06 Agent authority

Model output is advisory and grants no authority. Starting an Agent run requires an independent
approval for `START_AGENT_RUN` bound to the exact Agent run ID. The run approval authorizes only the
bounded planning lifecycle; it does not authorize any dangerous tool action. A proposed dangerous
tool still requires its own target/action-class approval and a current Policy Engine allow decision.

The human or calling service fixes the allowed Agent role and tool-ID allowlist before model
invocation. The model cannot select an approver, request an approval through its output schema,
change Scope/ROE, or convert its own text into an authorization source.
