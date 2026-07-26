# Production Identity Design

## Decision summary

The production-facing identity boundary uses separate contracts for human and workload principals:

- Human users authenticate through an enterprise OIDC provider and phishing-resistant MFA.
- Services authenticate through SPIFFE/SPIRE-compatible short-lived SVIDs and mutually authenticated channels.
- The Control, Execution, Range, Evidence, and Management planes use separate trust domains.
- Authorization receives a canonical context containing verified identity, engagement, action, environment, device posture, and optional time-bounded elevation.

The current implementation is a deterministic, no-network fake. It proves validation semantics but is not a production IdP, JWT library, certificate verifier, Workload API client, or PAM integration.

## Human identity flow

1. An ingress adapter receives an OIDC token from a configured enterprise IdP.
2. The verifier pins the expected issuer and audience and rejects unsigned or unsupported algorithms.
3. Signature, `iss`, `aud`, `sub`, `jti`, `nonce`, `iat`, `nbf`, and `exp` are validated.
4. Authentication strength must represent phishing-resistant MFA; break-glass uses a separate strength and audit path.
5. Roles, trust domain, engagement attributes, and device posture are normalized into `VerifiedPrincipal`.
6. Replay and revocation checks run before the principal is returned.
7. Caller-supplied actor or role fields are ignored as authority and rejected when they conflict with verified identity.

## Workload identity flow

1. A workload obtains a short-lived SVID from the local Workload API.
2. The receiving service validates the SPIFFE ID against the correct trust bundle.
3. The SPIFFE trust domain, intended audience, expected workload identity, validity interval, and revocation state are checked.
4. The resulting principal is bound to one workload identity and one trust domain.
5. Cross-domain calls require an explicitly configured federation relationship; the deterministic fake denies them by default.

## Authorization context

The policy input must contain:

- verified principal identifier and kind;
- verified trust domain and credential identifier;
- verified human roles, if any;
- engagement binding;
- requested action and environment;
- device posture;
- optional JIT elevation grant.

An elevation grant is valid only when it is unrevoked, current, principal-bound, engagement-bound, ticket-bound, and approved by two distinct principals other than the elevated principal.

## Separation of duties

Requester and approver must be separate verified human identities. A dual-role user cannot approve their own request. Workload identities cannot satisfy human approval roles.

## Failure behavior

The following conditions deny state changes:

- IdP or Workload API unavailable;
- missing, malformed, unsigned, expired, future, wrong-issuer, or wrong-audience token;
- replayed nonce;
- revoked user, session, SVID, or elevation grant;
- workload credential used by another workload;
- trust-domain crossing without federation;
- role, engagement, environment, or device-posture mismatch;
- audit dependency unavailable in the future production adapter.

## Migration boundary

Existing Phase 03 services still accept `actor_id` internally for local compatibility. Production adapters must authenticate first and pass only `VerifiedPrincipal.principal_id` into legacy internals during migration. No public production endpoint may expose a caller-controlled `actor_id` authorization path.

## Standards basis

The design follows OpenID Connect Core identity-token validation concepts, JWT registered claim validation, SPIFFE trust-domain/SVID semantics, and NIST phishing-resistant authenticator guidance. The repository does not claim formal conformance until live adapters and conformance tests exist.
