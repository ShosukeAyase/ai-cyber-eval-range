# Phase 08 Identity Operations Runbook

## Normal validation

1. Run formatting, lint, type checking, compilation, schema validation, architecture tests, unit tests, integration tests, and the full regression suite.
2. Confirm no secret or private-key material exists in source, fixtures, logs, or CI configuration.
3. Confirm the active Phase 08 plan has not been moved to completed.

## IdP outage

- Deny all new state-changing human operations.
- Preserve existing audit evidence.
- Do not fall back to caller-supplied actor identifiers, cached allow decisions, or local static users.
- Permit only separately governed emergency procedures with break-glass MFA and high-priority auditing.

## Workload API or trust-bundle outage

- Deny new service-to-service state changes.
- Stop scheduling new jobs.
- Isolate affected workloads if identity freshness cannot be established.
- Do not fall back to network location or static bearer tokens.

## Revocation

- Revoke the human subject, session/token identifier, SVID serial, or elevation grant as applicable.
- Invalidate authorization caches by revocation epoch in the future production implementation.
- Terminate affected sessions and record the action in the Evidence Plane.

## Break-glass

- Require phishing-resistant break-glass MFA.
- Require a declared incident or ticket.
- Emit a dedicated identity event and alert the security operator and auditor roles.
- Review all resulting actions after the incident.

## Rollback

Rollback means disabling the new production adapter and returning to production NO-GO. It must never restore caller-controlled actor identifiers as a production authentication mechanism. The local demo may continue only in its isolated, synthetic profile.

## Phase completion

Run `scripts/complete_phase8.ps1`. The script must refuse completion unless explicit live-gate evidence paths are supplied and exist. Moving the plan to `completed/` requires an independent review.
