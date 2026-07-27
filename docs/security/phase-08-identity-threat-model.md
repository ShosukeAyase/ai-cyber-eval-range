# Phase 08 Identity Threat Model

## Assets

- Human principal identity and authentication strength.
- Workload SPIFFE ID and SVID private key custody.
- Trust bundles and authoritative OIDC token status.
- OIDC introspection client identity and secret.
- Role, engagement, device-posture, and elevation attributes.
- Replay and revocation state.
- Identity audit and live-gate evidence.

## Trust boundaries

- Browser/client to management ingress.
- Management identity adapter to the configured enterprise IdP introspection endpoint.
- Identity transport adapter to transport-neutral identity core.
- Workload to local SPIFFE Workload API.
- Service-to-service mTLS boundary.
- Logical Control, Execution, Range, Evidence, and Management workload zones.
- Local SPIFFE trust domain to any federated trust root.
- Identity boundary to Policy Decision Point.
- Identity boundary to independently administered Evidence Plane.

## Abuse cases and controls

| Abuse case | Control | Test/evidence |
|---|---|---|
| Inactive, revoked, or fabricated bearer token | Authoritative introspection and exact `active=true` requirement | revoked-token and inactive-token tests |
| Wrong issuer or audience | Exact issuer/audience pinning | wrong issuer/audience tests |
| Expired or future token | `iat`, `nbf`, `exp` validation | temporal negative tests |
| Token replay | Single-use nonce cache | replay test and live evidence case |
| Signing-key rotation breaks authentication | Fresh post-rotation token must introspect and normalize successfully | signing-key-rotation live evidence |
| Introspection endpoint substitution | HTTPS or loopback-only transport and configured endpoint | endpoint-validation test |
| Introspection client secret leaks | Runtime-only environment/secret manager input; evidence stores fingerprints only | architecture review and evidence inspection |
| Request-body actor spoofing | Verified principal is authoritative | actor spoofing integration test |
| Role escalation | Closed role enum and ABAC role check | missing-role test |
| Self approval | Identity-level requester/approver separation | self-approval test |
| Workload A uses workload B credential | Expected SPIFFE ID and workload selector binding | workload binding test |
| Valid but unauthorized workload calls a service | Application-level peer SPIFFE-ID authorization | foreign-identity live mTLS test |
| Trust-root crossing | Federation absent by default | foreign trust-root negative test |
| Revoked workload continues | Registration revocation and rejection of a new connection | revoked-SVID live test |
| Stale SVID remains indefinitely | Workload API stream and observed certificate rotation | SVID-rotation live test |
| IdP/Workload API outage | Fail closed for new state changes | outage tests |
| Fake evidence directory passes completion | Content validator requires profiles, cases, status, and no-key/no-secret declarations | completion-gate architecture test |
| Static operation list is mistaken for deployed routing proof | Coverage report sets `deployment_review_required=true` | independent deployment review |
| Break-glass use hidden | Dedicated high-priority event | break-glass audit test |

## Residual risks

- Enterprise OIDC staging has not yet been executed against the selected organizational IdP.
- The live adapter uses authoritative introspection; provider configuration must ensure token signature, key rotation, session revocation, and phishing-resistant authentication before reporting `active=true` and mapped claims.
- The local Keycloak profile runs in development mode and is deliberately not gate eligible.
- The SPIRE Helm bootstrap and identity selectors have not yet been exercised on the user's isolated staging cluster.
- Application-level mTLS peer SPIFFE-ID authorization, rotation, revocation, and outage evidence remain externally executed requirements.
- The static coverage report proves the declared `WriteOperation` inventory, not the routing of an independently deployed API gateway.
- Replay and revocation stores in the deterministic profile are in-memory and not highly available.
- Independent identity audit storage is not connected.

These remain High until content-valid live staging evidence, deployed adapter review, Evidence Plane tests, and independent completion review exist.
