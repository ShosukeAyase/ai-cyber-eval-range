# API Boundaries

## Rules

- Closed request/response schemas with `additionalProperties: false`.
- Object IDs only for targets, repositories, scenarios, test cases, profiles, findings, and evidence.
- No arbitrary commands, URLs, IP addresses, hostnames, repository paths, or cloud resource strings from the model.
- Every public service operation receives `engagement_id` as an explicit typed argument; the model cannot choose or alter authenticated session context.
- Idempotency keys for state changes.
- Explicit error codes; no silent fallback.

## Example tool contract

```json
{
  "operation": "run_web_test",
  "target_id": "tgt-web-001",
  "test_case_id": "tc-authz-001"
}
```

The Tool Gateway resolves `tgt-web-001` to a signed scenario endpoint and `tc-authz-001` to an approved adapter profile.

## Validation pipeline

1. Parse strict JSON.
2. Authenticate caller and bind job context.
3. Validate schema and object existence.
4. Verify engagement/ROE version and time window.
5. Verify action class, limits, and target mapping.
6. Detect forbidden fields/tokens/options.
7. Verify or request approval.
8. Ask Policy Engine.
9. Derive expected network destinations.
10. Execute adapter under quotas and record evidence.

## Representative errors

- `INVALID_SCHEMA`
- `UNKNOWN_OBJECT_ID`
- `OUT_OF_SCOPE`
- `ROE_EXPIRED`
- `APPROVAL_REQUIRED`
- `APPROVAL_EXPIRED`
- `POLICY_UNAVAILABLE`
- `FORBIDDEN_OPTION`
- `DESTINATION_MISMATCH`
- `QUOTA_EXCEEDED`
- `EMERGENCY_STOP_ACTIVE`
## Phase 02 skeleton mapping

The non-executable interfaces are defined under `src/cyber_eval/`:

- `ToolRequest`, `AuthorizationFacts`, `PolicyContext`, and `PolicyDecision` are immutable typed records.
- `ScopeRegistry`, `ApprovalRepository`, `PolicyEngine`, and `ToolGateway` are protocols.
- `NonExecutableToolGateway` performs authorization only; `dispatch` always raises `ExecutionDisabledError`.
- `FailClosedPolicyEngine` is a local deterministic stub used only for negative contract tests.

No Phase 02 interface accepts an arbitrary command, URL, hostname, IP address, repository location, cloud resource, transport option, or credential value.


## Phase 03 local API mapping

- `ModelRequest` accepts purpose, prompt-template ID, and context-object IDs only.
- `ToolRequest` continues to use target, test-case, tool, and object IDs only.
- All state-changing service methods require an approval ID.
- The Tool Gateway returns `accepted_no_execution` rather than dispatching an adapter.
- The Credential Broker returns an opaque metadata reference and stores no credential value.
- SQLite is an internal local persistence detail and is not exposed as an arbitrary query API.

## Phase 04 Runner boundary

`RunnerJobRequest` accepts only `job_id`, `engagement_id`, `target_id`, `repository_id`,
`profile_id`, and `test_case_id`. Paths and image references are resolved from a locally configured
registry. The workload command is fixed by `PodmanCommandBuilder`; no caller supplies argv, shell,
URL, IP, hostname, mount, environment variable, package, or plugin values.
