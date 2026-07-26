# Phase 06 Agent Integration Plan

Status: completed

## Purpose

Integrate a GPT model as an untrusted proposal component behind the existing Control Plane,
approval, Scope/ROE, Policy Engine, Tool Gateway, audit, credential-reference, Emergency Stop,
Runner, and synthetic Cyber Range boundaries.

## Approved model roles

- Propose an evaluation plan.
- Select from explicitly approved tool IDs.
- Analyze authenticated results.
- Organize evidence.
- Propose remediation.
- Propose a revalidation plan.

## Explicit exclusions

- Scope decision or change.
- Self-approval.
- Credential management or secret access.
- Arbitrary command or payload execution.
- Network destination selection or general Internet tools.
- Kill Switch control.
- Audit-log mutation.
- Automatic patch merge.

## Work items

- [x] Add strict Agent run, context, turn, finding, proposal, and receipt contracts.
- [x] Add registered context resolution with secret-reference redaction.
- [x] Add a fixed-endpoint OpenAI Responses adapter using strict structured output.
- [x] Disable provider tools and parallel tool calls.
- [x] Add independently approved Agent run lifecycle persistence and audit.
- [x] Route every accepted tool proposal through the existing Tool Gateway and Policy Engine.
- [x] Add evidence authentication and unsupported-finding rejection.
- [x] Add bounded turns and repeated-failure loop protection.
- [x] Add model-stop and Emergency Stop fail-closed handling.
- [x] Add the required adversarial tests.
- [x] Update schemas, examples, architecture tests, CI, and documentation.
- [x] Execute operator-laptop Ruff, mypy, full pytest, compilation, and Git gates.

## Completion criteria

- Dangerous model output cannot become an operation.
- Control Plane termination is safe when the model stops.
- Every tool invocation passes through the Policy Engine and Tool Gateway.
- Agent run state changes are bound to an independent approval.
- Secret-reference content is absent from model input.
- Executed Scope violation rate is zero.
- All required adversarial, schema, unit, integration, architecture, and regression tests pass.

## Deferred decisions

- Production KMS or HSM custody for provider authentication.
- Independent remote Agent execution service.
- Provider-side Zero Data Retention contract validation.
- Signed prompt templates and external immutable evidence storage.
- Automated live-model evals in a private CI environment.

## Operator-laptop completion record

- Completed at: `2026-07-26T02:15:29.953565+00:00`.
- Ruff format and lint: PASS.
- mypy strict type check: PASS.
- Complete pytest suite: PASS.
- Python compilation: PASS.
- Git whitespace validation: PASS.
- Live provider request: not required for deterministic completion; explicit operator gate.
- Phase 06 is complete for the proposal-only Agent integration profile.
