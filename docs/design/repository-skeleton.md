# Phase 02 Repository Skeleton

## Status and purpose

Phase 02 converts the approved design into a testable contract skeleton. It is deliberately incapable of performing a cyber evaluation. It contains schemas, immutable typed records, protocol interfaces, policy templates, state-transition validation, mocks, tests, and CI only.

## Directory structure

```text
src/cyber_eval/           Pure Python contracts and fail-closed stubs
schemas/                  Draft 2020-12 JSON Schemas
examples/                 Synthetic validating examples, one per schema
policies/                 Review-only Rego templates
 tests/unit/               Pure policy/gateway/state tests
 tests/schemas/            Schema and example validation
 tests/policy/             Static Rego contract checks
 tests/architecture/       Repository invariants and prohibited-capability checks
.github/workflows/         Validation-only CI
```

## Runtime prohibition

`NonExecutableToolGateway.authorize` may return an allow or deny decision over synthetic records. `NonExecutableToolGateway.dispatch` always raises `ExecutionDisabledError`. There are no execution adapters, shell wrappers, network clients, cloud SDKs, infrastructure definitions, exploit modules, credential stores, or secret-handling types.

An allow decision in this phase means only that the supplied synthetic contract satisfies the local policy stub. It cannot cause a side effect.

## API contracts

- `ScopeRegistry`: answers whether a target-object ID belongs to an engagement.
- `ApprovalRepository`: returns pre-registered approval evidence for dangerous action classes.
- `PolicyEngine`: evaluates a structured `ToolRequest` and `PolicyContext` without side effects.
- `ToolGateway`: authorizes structured requests; dispatch remains disabled.

The model-facing request uses registered object identifiers only. It has no command, URL, hostname, IP address, repository location, cloud-resource name, or free-form transport field.

## Policy behavior

The local `FailClosedPolicyEngine` denies when any mandatory input is false, unavailable, mismatched, expired, or absent. Dangerous action classes require valid, independent, unexpired, target-bound, action-bound approval evidence. The Tool Gateway converts Policy Engine exceptions into an explicit `policy_evaluation_error` deny decision.

The Rego files remain templates. Phase 02 neither starts OPA nor treats the Python stub as a production policy decision point.

## State behavior

Approval, engagement, job, and runner transitions are explicit allowlists. Missing edges are rejected. Terminal states have no recovery edge. In particular, an isolated runner cannot return to active and a denied job cannot become authorized.

## Trust-boundary effect

- Control plane: contracts only; no service process.
- Execution plane: represented only by a permanently disabled dispatch boundary.
- Cyber range: absent.
- Observability plane: represented by existing schemas only.

No new trust path is introduced.
