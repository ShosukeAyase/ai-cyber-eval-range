"""Explicit failure types for fail-closed Control Plane behavior."""


class ControlPlaneError(RuntimeError):
    """Base class for deterministic Control Plane failures."""


class ExecutionDisabledError(ControlPlaneError):
    """Raised whenever a caller attempts executable behavior."""


class InvalidTransitionError(ValueError):
    """Raised when a state-machine edge is not explicitly allowlisted."""


class AuditUnavailableError(ControlPlaneError):
    """Raised when an audit event cannot be committed."""


class ApprovalRequiredError(ControlPlaneError):
    """Raised when a state-changing operation lacks a valid approval."""


class ApprovalInvalidError(ControlPlaneError):
    """Raised when an approval is invalid, expired, exhausted, or mismatched."""


class SelfApprovalError(ControlPlaneError):
    """Raised when a requestor attempts to approve their own request."""


class EngagementNotFoundError(ControlPlaneError):
    """Raised when an engagement identifier is unknown."""


class DuplicateRecordError(ControlPlaneError):
    """Raised when a unique local record already exists."""


class RoeExpiredError(ControlPlaneError):
    """Raised when a Rules of Engagement record is outside its validity window."""


class ScopeViolationError(ControlPlaneError):
    """Raised when a registered target or test case is outside scope."""


class InvalidIdentifierError(ControlPlaneError):
    """Raised when a caller supplies an unregistered identifier shape."""
