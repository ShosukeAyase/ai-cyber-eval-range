"""Fail-closed identity errors for Phase 08."""


class IdentityError(RuntimeError):
    """Base class for identity verification and authorization failures."""


class IdentityProviderUnavailableError(IdentityError):
    """Raised when the human identity provider cannot be verified."""


class WorkloadIdentityUnavailableError(IdentityError):
    """Raised when the workload identity service cannot be verified."""


class InvalidIdentityTokenError(IdentityError):
    """Raised when an identity token is malformed or fails cryptographic checks."""


class IdentityClaimError(IdentityError):
    """Raised when required claims are absent, stale, or contradictory."""


class IdentityReplayError(IdentityError):
    """Raised when a nonce or credential is replayed."""


class IdentityRevokedError(IdentityError):
    """Raised when the principal or credential has been revoked."""


class IdentityAuthorizationError(IdentityError):
    """Raised when a verified principal lacks the required authority."""


class SeparationOfDutiesError(IdentityAuthorizationError):
    """Raised when requester and approver identities are not independent."""


class ActorSpoofingError(IdentityAuthorizationError):
    """Raised when caller-supplied actor data conflicts with verified identity."""
