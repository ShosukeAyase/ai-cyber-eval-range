# Phase 08 Identity Operations Runbook

## Deterministic validation

Run:

```powershell
python -m ruff format --check .
python -m ruff check .
python -m mypy src
python -m compileall -q src scripts tests
python -m pytest
python scripts/verify_phase5_catalog.py
python scripts/generate_phase8_api_coverage.py --output-dir artifacts/phase-08/api-coverage
```

The deterministic suite and static coverage report are prerequisites, not substitutes for live staging evidence.

## Live OIDC evidence

Configure the enterprise staging provider and required claim mappings described in `staging/oidc/README.md`. Keep the introspection secret and all tokens in process environment variables only. Run:

```powershell
python scripts/collect_phase8_oidc_evidence.py --output-dir artifacts/phase-08/oidc
```

The collector must produce `oidc-staging-evidence.json` with valid authentication, nonce replay rejection, signing-key rotation, wrong-audience rejection, expiry, revocation, and outage cases passing, plus `gate_eligible: true`. A local Keycloak development profile is not enterprise-gate eligible.

## SPIRE and mTLS evidence

Install the isolated staging foundation:

```powershell
pwsh -File scripts/setup_phase8_spire_staging.ps1
```

Execute the workload tests described in `staging/spire/README.md`. The raw logs must prove server and agent readiness, workload SVID issuance, successful mTLS, rejection of a valid but unauthorized peer SPIFFE ID, SVID rotation, revocation, and Workload API outage fail-closed behavior. Assemble them with:

```powershell
python scripts/collect_phase8_spire_evidence.py `
  --input-dir artifacts/phase-08/spire/raw `
  --output-dir artifacts/phase-08/spire `
  --cluster phase8-spire `
  --trust-domain phase8.internal `
  --profile isolated-staging
```

The collector hashes raw logs but never copies private keys.

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

- Revoke the human subject, session/token identifier, SVID registration, or elevation grant as applicable.
- Terminate affected sessions and connections.
- Demonstrate that a new state-changing operation is rejected.
- Record the action in the independently administered Evidence Plane.

## Break-glass

- Require phishing-resistant break-glass MFA.
- Require a declared incident or ticket.
- Emit a dedicated identity event and alert security operator and auditor roles.
- Review all resulting actions after the incident.

## Completion

Run:

```powershell
pwsh -File scripts/complete_phase8.ps1 `
  -OidcEvidencePath artifacts/phase-08/oidc `
  -SpireEvidencePath artifacts/phase-08/spire `
  -ApiCoverageEvidencePath artifacts/phase-08/api-coverage
```

The script validates evidence content. Directory existence alone is insufficient. Independent review is still mandatory before moving the plan to `completed/`.

## Rollback

Rollback means disabling the live adapter or staging integration and returning to production NO-GO. It must never restore caller-controlled actor identifiers as a production authentication mechanism. The isolated synthetic profile may continue for development.
