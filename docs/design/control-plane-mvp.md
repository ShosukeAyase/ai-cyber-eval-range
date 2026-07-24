# Local Control Plane MVP

## Status and purpose

Phase 03 implements a local-development-only Control Plane MVP. It runs in one Python process on one laptop and uses the Python standard-library SQLite driver. It does not require a cloud account, paid product, external model provider, container runtime, virtual machine, runner, or cyber range.

The MVP proves authorization and fail-closed behavior. It is not a production control plane and must not be connected to real targets.

## Local topology

```text
Local Python process
├── Engagement Service
├── Scope/ROE Service
├── Approval Service
├── Local Policy Engine Adapter
├── Deterministic Model Gateway Mock
├── Tool Gateway Mock
├── Credential Broker Mock
├── Emergency Stop Service
└── SQLite database
    ├── engagements
    ├── scope_roe
    ├── approvals
    ├── emergency_stops
    ├── credential_references
    └── audit_events
```

The execution plane and cyber range are absent. The local SQLite audit table is an MVP observability substitute, not a production WORM evidence store.

## Services

### Engagement Service

Creates, activates, reads, and closes engagement records. Activation requires a current Scope/ROE record. The activation operation applies the approved engagement-state transitions but does not schedule or execute work.

### Scope/ROE Service

Stores only registered `target_id` and `test_case_id` values. It rejects invalid identifier shapes and evaluates validity windows using an injected clock. It has no URL, IP address, hostname, repository path, or network endpoint resolver.

### Approval Service

Creates and decides approval grants. It rejects approval when the deciding actor is the requestor. Grants bind:

- `engagement_id`;
- one or more enumerated write operations;
- engagement or exact-resource scope;
- an optional action class;
- expiry, maximum uses, and current uses; and
- distinct requestor and approver identities.

The local composition root seeds two reciprocal administrative grants for distinct operator and approver identities. This is the explicit local-development bootstrap trust root. It is not a production substitute for an identity provider or signed approval record.

### Local Policy Engine Adapter

Builds deterministic policy facts from local engagement, Scope/ROE, approval, and Emergency Stop state. It delegates the final ordered checks to the fail-closed policy contract from Phase 02.

The adapter denies:

- unavailable policy service;
- mismatched or invalid engagement context;
- inactive or expired engagement;
- missing or expired ROE;
- out-of-scope target;
- disallowed test case;
- missing, expired, non-independent, exhausted, or mismatched approval; and
- active Emergency Stop.

No external OPA process or policy-distribution channel is used in this phase.

### Model Gateway abstraction

`ModelGateway` is a typed protocol. `DeterministicModelGatewayMock` accepts:

- `engagement_id` as a method argument;
- a request ID;
- an enumerated purpose;
- a registered prompt-template ID; and
- registered context-object IDs.

It accepts no raw provider endpoint, URL, IP address, hostname, command, model credential, or arbitrary tool definition. The mock returns deterministic text and performs no network operation.

### Tool Gateway mock

The Tool Gateway evaluates a structured `ToolRequest` and returns either a deny result or `accepted_no_execution`. It has no adapter registry capable of shell, scanner, exploit, patch, network, or target execution.

Write-class mock requests require a specific independently approved grant. Grant consumption and the audit event share one SQLite transaction.

### Credential Broker mock

The mock creates only opaque metadata references. A reference contains an identifier, engagement, target, purpose, validity interval, and state. There is no field or storage path for a credential value, password, provider token, key, or certificate.

Issuance requires current target scope and a specific `credentialed_test` approval. The result cannot authenticate to anything.

### Emergency Stop

The Emergency Stop service depends only on:

- the local store;
- Approval Service;
- audit generation; and
- the clock.

It does not import or receive a model, Tool Gateway, runner, scheduler, hypervisor, container runtime, or target connection. Policy evaluation reads the stop state and denies subsequent mock tool requests.

## Transactional audit rule

For every state-changing service method:

1. validate the typed request and approval record;
2. begin an SQLite `BEGIN IMMEDIATE` transaction;
3. insert the audit event;
4. consume the approval when applicable;
5. apply the state mutation; and
6. commit.

An audit-insert failure, approval-consumption failure, state error, or database error rolls back the entire transaction. The operation does not change state.

Read-only Model and Tool mock results are returned only after their audit event is committed. Injected audit failure therefore prevents the mock invocation count from changing and prevents a result from being returned.

## Public API rules

All public service operations require an explicit `engagement_id`. Constructors and passive properties are not domain operations.

No public operation accepts:

- arbitrary commands or shell fragments;
- URLs, IP addresses, hostnames, or provider endpoints;
- cloud resource names;
- real credential material; or
- exploit or proof-of-concept payloads.

## Local use

Install the pinned development dependencies and run validation:

```sh
python -m pip install -e ".[dev]"
make validate
```

Run the synthetic no-network demonstration:

```sh
PYTHONPATH=src python -m cyber_eval.demo
```

The demonstration creates only in-memory SQLite records and prints a synthetic summary.

## Limitations

- SQLite and the local OS account do not provide independent administration or WORM guarantees.
- The reciprocal bootstrap grants are suitable only for deterministic local development.
- The MVP is single-process and does not provide high availability or distributed locking.
- The policy adapter is not production OPA.
- The model, tool, and credential components are mocks.
- No external infrastructure, execution plane, range, or real target is present.
