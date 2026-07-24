# Credential Model

## Design rule

The model never receives a credential in its context, environment, files, logs, or tool result. The runner should not receive a reusable credential either.

## Credential flow

1. Policy Engine authorizes a specific action and target.
2. Tool Gateway authenticates with a job-specific workload identity.
3. Credential Broker verifies engagement, target, adapter, action, approval, and expiry.
4. Broker issues or retrieves a short-lived credential with a narrow audience and capability.
5. Credential is delivered over a protected channel directly to the tool adapter.
6. Adapter uses it in memory and redacts all outputs.
7. Credential is revoked on completion, timeout, stop event, or policy change.

## Credential classes

- Anonymous/synthetic test identity.
- Read-only repository token.
- Scenario-local user credential.
- Scenario-local privileged credential requiring explicit approval.
- Cloud-simulator token with no real cloud validity.
- Kubernetes scenario service account scoped to a namespace and verb/resource allowlist.

## Prohibitions

- No production or corporate credentials.
- No long-lived static secrets in images or repositories.
- No credentials in environment variables for general-purpose processes.
- No credential disclosure in evidence; store a reference and issuance metadata instead.
- No credential reuse across engagements, targets, or runners.
