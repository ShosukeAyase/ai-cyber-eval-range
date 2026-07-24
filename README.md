# AI Cyber Evaluation Platform & Range (Design Phase)

Status: **Design phase — no implementation, no deployment, no execution against real or synthetic infrastructure.**

This repository designs an authorized, isolated cyber-evaluation platform and cyber range consisting of:

- **A cyber-evaluation system** — an LLM-assisted agent for analysis, planning, evidence review, and patch proposals, whose scope and authorization are enforced by deterministic mechanisms external to the model (Policy Engine, Tool Gateway, signed Scope/ROE manifests, Human Approval Service, Credential Broker).
- **An isolated cyber range** — a disposable exercise environment (Web/API, Linux, Windows domain, container/Kubernetes, cloud IAM/storage simulations) with no route to corporate networks or the general internet, fully destructible after each engagement.

## Start here

- [`AGENTS.md`](./AGENTS.md) — governing security invariants, scope enforcement rules, and required development workflow. This is the top-level source of truth; read it before making any change.
- [`docs/exec-plans/active/phase-01-design.md`](./docs/exec-plans/active/phase-01-design.md) — current phase's execution plan, work items, assumptions, open decisions, and risks.

## Repository status

This repository is in its earliest bootstrap state. Most of the documentation, schemas, diagrams, and ADRs described in the active execution plan have not yet been created. See the plan's work-item table for what exists and what's pending.

## Prohibited in this repository (see AGENTS.md for full list)

- Connecting to public/real external targets
- Executing exploit code outside a synthetic, isolated range
- Any autonomous merge, deployment, or production modification
- Storing secrets or real credentials in this repository
