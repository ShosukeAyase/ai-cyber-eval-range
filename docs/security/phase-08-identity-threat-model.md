# Phase 08 Identity Threat Model

## Assets

- Human principal identity and authentication strength.
- Workload SPIFFE ID and SVID private key custody.
- Trust bundles and OIDC verification keys.
- Role, engagement, device-posture, and elevation attributes.
- Replay and revocation state.
- Identity audit evidence.

## Trust boundaries

- Browser/client to management ingress.
- Management ingress to enterprise IdP.
- Workload to local SPIFFE Workload API.
- Service-to-service mTLS boundary.
- Each plane's separate SPIFFE trust domain.
- Identity boundary to Policy Decision Point.
- Identity boundary to independently administered Evidence Plane.

## Abuse cases and controls

| Abuse case | Control | Test/evidence |
|---|---|---|
| Unsigned or algorithm-confused token | Fixed algorithm allowlist and signature verification | unsigned/tampered token tests |
| Wrong issuer or audience | Exact issuer/audience pinning | wrong issuer/audience tests |
| Expired or future token | `iat`, `nbf`, `exp` validation | temporal negative tests |
| Token replay | Single-use nonce cache | replay test |
| Request-body actor spoofing | Verified principal is authoritative | actor spoofing integration test |
| Role escalation | Closed role enum and ABAC role check | missing-role test |
| Self approval | Identity-level requester/approver separation | self-approval test |
| Workload A uses workload B credential | Expected SPIFFE ID binding | workload binding test |
| Trust-domain crossing | Explicit expected trust domain; federation absent by default | crossing test |
| Revoked user/workload continues | Principal and credential revocation checks | revocation tests |
| IdP/Workload API outage | Fail closed | outage tests |
| Break-glass use hidden | Dedicated high-priority event | break-glass audit test |
| Excessively long SVID | Maximum one-hour deterministic profile | SVID lifetime validation |

## Residual risks

- The synthetic HMAC token is not a production JWT/OIDC implementation.
- X.509 certificate path, SAN, key-usage, trust-bundle rotation, and federation validation are not implemented.
- Replay and revocation stores are in-memory and not highly available.
- Existing public service methods have not all migrated from actor identifiers.
- Independent identity audit storage is not connected.

These remain High until live staging and API migration evidence exist.
