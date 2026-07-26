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


class RunnerError(ControlPlaneError):
    """Base class for isolated Runner failures."""


class RunnerRuntimeUnavailableError(RunnerError):
    """Raised when the approved local runtime is unavailable or not rootless."""


class RunnerTerminatedError(RunnerError):
    """Raised when Emergency Stop terminates an active Runner job."""


class RunnerEvidenceError(RunnerError):
    """Raised when Runner evidence is absent, malformed, or exceeds limits."""


class ResourceLimitError(RunnerError):
    """Raised when a Runner request exceeds the approved resource profile."""


class CyberRangeError(ControlPlaneError):
    """Base class for synthetic Cyber Range failures."""


class ScenarioCatalogError(CyberRangeError):
    """Raised when a scenario package or answer key is invalid."""


class RangeStateError(CyberRangeError):
    """Raised when a range lifecycle operation violates state."""


class RangeStopConditionError(CyberRangeError):
    """Raised when a scenario stop condition is triggered."""


class RangeScoringError(CyberRangeError):
    """Raised when observations cannot be scored safely."""
