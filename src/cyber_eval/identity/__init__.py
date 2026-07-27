"""Phase 08 production IAM contracts, live adapters, and deterministic verifiers."""

from cyber_eval.identity.audit import InMemoryIdentityAuditSink
from cyber_eval.identity.boundary import IdentityBoundary
from cyber_eval.identity.contracts import (
    AuthenticationStrength,
    AuthorizationContext,
    DevicePosture,
    EnvironmentClass,
    HumanRole,
    HumanTokenClaims,
    IdentityAuditEvent,
    IdentityAuditOutcome,
    PamElevationGrant,
    PrincipalKind,
    SyntheticSvid,
    TrustDomain,
    VerifiedPrincipal,
)
from cyber_eval.identity.live_oidc import (
    LiveOidcIntrospectionVerifier,
    OidcClaimNames,
)
from cyber_eval.identity.production_gateway import (
    ProductionIdentityGateway,
    StateChangeBinding,
    production_state_change_bindings,
)
from cyber_eval.identity.synthetic import (
    DeterministicOidcVerifier,
    DeterministicSpiffeVerifier,
    InMemoryReplayCache,
    InMemoryRevocationRegistry,
    SyntheticOidcIssuer,
)

__all__ = [
    "AuthenticationStrength",
    "AuthorizationContext",
    "DeterministicOidcVerifier",
    "DeterministicSpiffeVerifier",
    "DevicePosture",
    "EnvironmentClass",
    "HumanRole",
    "HumanTokenClaims",
    "IdentityAuditEvent",
    "IdentityAuditOutcome",
    "IdentityBoundary",
    "InMemoryIdentityAuditSink",
    "InMemoryReplayCache",
    "InMemoryRevocationRegistry",
    "LiveOidcIntrospectionVerifier",
    "OidcClaimNames",
    "PamElevationGrant",
    "PrincipalKind",
    "ProductionIdentityGateway",
    "StateChangeBinding",
    "SyntheticOidcIssuer",
    "SyntheticSvid",
    "TrustDomain",
    "VerifiedPrincipal",
    "production_state_change_bindings",
]
