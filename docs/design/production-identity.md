# Production Identity Design

## Decision summary

The production-facing identity boundary uses separate contracts for human and workload principals:

- Human users authenticate through an enterprise OIDC provider and phishing-resistant MFA.
- Services authenticate through SPIFFE/SPIRE-compatible short-lived SVIDs and mutually authenticated channels.
- One SPIFFE trust domain may use separately selected identity paths for the Control, Execution, Range, Evidence, and Management zones; federation is required before accepting another trust root.
- Authorization receives a canonical context containing verified identity, engagement, action, environment, device posture, and optional time-bounded elevation.
- Every declared `WriteOperation` is bound to exactly one verified principal class by `ProductionIdentityGateway`.

The implementation contains deterministic fakes and a live OIDC introspection adapter. The SPIRE bootstrap and evidence contract are present, but the repository does not claim the live gates passed until externally executed evidence is validated.

## Human identity flow

1. An ingress adapter receives a token from a configured enterprise OIDC provider.
2. `UrlLibOidcIntrospectionTransport` sends it to a pinned HTTPS introspection endpoint using a client secret supplied at runtime.
3. The adapter rejects endpoint outages, inactive tokens, malformed responses, wrong issuer or audience, invalid temporal claims, unsupported roles or trust domains, and non-phishing-resistant authentication.
4. `sub`, `jti`, nonce, engagement attributes, roles, trust zone, authentication strength, and device posture are normalized into `VerifiedPrincipal`.
5. The token and client secret are never logged or persisted by the evidence collector; only SHA-256 token fingerprints are recorded.
6. Caller-supplied actor or role fields remain nonauthoritative.

The introspection client is a confidential management-plane workload. Its secret must come from a secret manager or process environment and must be independently revocable.

## Workload identity flow

1. A workload obtains a short-lived X.509-SVID from the local SPIFFE Workload API.
2. Both peers establish mTLS using SVIDs and the current trust bundle.
3. The receiving application validates the peer SPIFFE ID, not merely certificate-chain validity.
4. Namespace and pod-label selectors bind workloads to logical Control, Execution, Range, Evidence, or Management zones.
5. Cross-zone state changes are allowed only when the receiving operation inventory explicitly permits the caller zone.
6. SVID rotation, registration revocation, and Workload API outages must be observed against new state-changing connections.

## Complete mediation inventory

`ProductionIdentityGateway` contains an immutable binding for every `WriteOperation`. Human bindings declare required roles. Workload bindings declare allowed trust zones. Approval decisions additionally require a separately verified requester.

`scripts/generate_phase8_api_coverage.py` compares this binding set with the `WriteOperation` enumeration, confirms the public gateway signature has no `actor_id`, and emits JSON and CSV evidence. This proves declared operation inventory coverage. Deployment review must still prove that every production-facing adapter actually routes through the gateway; legacy Phase 03 services remain local-demo internals only.

## Evidence model

Three content-valid evidence packages are required:

- `oidc-staging-evidence.json`: enterprise staging profile and all required OIDC cases pass;
- `spire-mtls-staging-evidence.json`: isolated SPIRE/mTLS cases pass and five logical zones are covered;
- `coverage-report.json`: 100% declared state-changing operation mediation, zero missing operations, and zero production-boundary `actor_id` parameters.

The OIDC package requires valid authentication, nonce replay rejection, signing-key rotation, wrong-audience rejection, expiry, revocation, and IdP outage fail-closed evidence. The SPIRE package requires server/agent readiness, SVID issuance, successful mTLS, unauthorized peer rejection, rotation, revocation, and Workload API outage evidence.

The completion script invokes `validate_phase8_live_evidence.py`; empty directories or marker-free logs fail closed.

## Separation of duties

Requester and approver must be separate verified human identities. A dual-role user cannot approve their own request. Workload identities cannot satisfy human approval roles. Privileged elevation remains ticket-bound, time-bound, and independently approved.

## Failure behavior

The following conditions deny state changes:

- IdP, introspection endpoint, Workload API, trust bundle, replay cache, revocation service, or required audit dependency unavailable;
- inactive, missing, malformed, expired, future, wrong-issuer, or wrong-audience token;
- replayed nonce;
- revoked user, session, SVID, registration, or elevation grant;
- workload credential used by another workload;
- unauthorized peer SPIFFE ID or trust-zone crossing;
- role, engagement, environment, or device-posture mismatch;
- incomplete or invalid live evidence.

## Migration boundary

Existing Phase 03 services still accept `actor_id` internally for local compatibility. Production adapters must authenticate and authorize through `ProductionIdentityGateway`, then pass only `VerifiedPrincipal.principal_id` into legacy internals during migration. No public production endpoint may expose a caller-controlled `actor_id` authorization path.

## Standards basis

The design follows OpenID Connect identity concepts, OAuth 2.0 token introspection, JWT registered claim validation, SPIFFE trust-domain/SVID semantics, and phishing-resistant authenticator guidance. Formal conformance is not claimed until live staging and independent review complete.
