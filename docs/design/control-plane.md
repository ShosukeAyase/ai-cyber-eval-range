# Control Plane Design

## Components

### Agent Orchestrator

Maintains engagement workflow state, asks the model for structured analysis/tool intent, and cannot authorize or directly execute tools.

### Scope and ROE Service

Validates schemas, signatures, semantic constraints, target registries, validity windows, and immutable versions. It exposes read-only engagement views to the model.

### Policy Engine

Evaluates structured facts and returns `allow`, `deny`, required approval, obligations, and reason codes. Policy bundles are signed and versioned.

### Human Approval Service

Creates, signs, expires, revokes, and consumes approval records. It enforces separation of duties.

### Credential Broker

Holds target credentials and issues short-lived, audience-bound credentials directly to adapters.

### Job Scheduler

Issues one-time execution grants only after policy and approval checks. It does not accept free-form commands.

### Emergency Stop Service

Independent path to stop scheduling, isolate runners, revoke credentials, and seal evidence.

### Model Gateway

Pins approved GPT-5.6 profiles, minimizes context, redacts secrets, validates structured output, applies rate/token budgets, and records model metadata.

## Availability posture

Authorization dependencies are fail-closed. Read-only retrieval of already sealed evidence may remain available during policy outages, but no new execution begins.
