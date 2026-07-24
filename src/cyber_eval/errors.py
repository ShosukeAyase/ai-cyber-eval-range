"""Errors used to make prohibited behavior explicit and testable."""


class ExecutionDisabledError(RuntimeError):
    """Raised whenever a caller attempts to dispatch an executable action."""


class InvalidTransitionError(ValueError):
    """Raised when a state-machine edge is not explicitly allowlisted."""
