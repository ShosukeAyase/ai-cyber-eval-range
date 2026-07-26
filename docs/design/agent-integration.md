# Phase 06 Agent integration

## Security position

The GPT model is an untrusted proposal component. It has no authority to decide or change Scope,
approve actions, manage credentials, execute commands, select network destinations, control the
Kill Switch, mutate audit records, or merge patches. The model receives no executable provider
tools. It returns one strict JSON document describing proposals.

The Control Plane reconstructs every `ToolRequest` from typed object identifiers. It validates the
approved Agent role, the human-supplied tool allowlist, current Scope/ROE, target and test-case IDs,
and the fixed tool/action-class mapping before calling the Tool Gateway. The Tool Gateway remains
the only tool invocation path and evaluates every call through the Policy Engine.

## OpenAI boundary

The optional production adapter uses the Responses API at the single fixed endpoint
`https://api.openai.com/v1/responses`. The request sets `store=false`, disables parallel tool calls,
sets `tool_choice=none`, and supplies a strict JSON Schema under `text.format`. The explicit model ID `gpt-5.6-sol` is used by default, with medium reasoning and a bounded
output budget. Provider authentication is added only by the HTTP transport and is never serialized into model input, context, audit details, or persisted Agent output.

The Control Plane may allow egress only to the fixed OpenAI API endpoint. A model request for the
general Internet, a different destination, a built-in provider tool, or arbitrary function call has
no representation in the Agent contracts.

## Context trust

Context objects must be pre-registered. Trusted and untrusted objects are explicitly labeled.
Untrusted content is data, never an instruction. Objects classified as secret references are omitted
from model input and only their redacted object IDs are recorded.

## Execution lifecycle

1. An independent approver authorizes `START_AGENT_RUN` for one Agent run ID.
2. The Control Plane verifies the engagement, current Scope/ROE, and Emergency Stop state.
3. The approval is consumed atomically with the `agent_runs` start record and audit event.
4. The model returns a strict `AgentTurn` proposal.
5. The Control Plane rejects prohibited intents, unknown fields, role changes, non-approved tools,
   out-of-scope targets, out-of-ROE test cases, and tool/action-class mismatches.
6. Valid proposals are converted to `ToolRequest` objects and sent to the Tool Gateway.
7. Only Control Plane-generated tool receipts are returned to the model on the next turn.
8. Findings must reference registered context evidence or evidence IDs created from accepted Tool
   Gateway receipts.
9. The loop stops after a bounded number of turns or repeated identical failures.
10. Model timeout, refusal, malformed output, Emergency Stop, or any exception produces a terminal
    fail-closed Agent state and audit record.

## Explicitly prohibited model roles

- Scope decision or modification;
- self-approval or approval selection;
- credential acquisition, storage, or revocation;
- arbitrary command or payload construction;
- network destination selection;
- Kill Switch activation or clearing;
- audit deletion, modification, or suppression;
- automatic patch merge;
- unsupported vulnerability claims;
- forged Tool Gateway receipts.

## Residual limitations

The local profile does not perform a live OpenAI call during automated tests. Operator-laptop live
validation requires a separately provisioned provider credential and explicit egress policy. The
SQLite store and local process remain subject to local-administrator compromise. Provider response
quality remains non-deterministic, so explicit model IDs, strict schemas, adversarial tests, and runtime
policy enforcement are all required.
