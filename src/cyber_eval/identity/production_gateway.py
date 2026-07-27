"""Complete-mediation gateway for production-facing state-changing operations."""

from __future__ import annotations

from dataclasses import dataclass

from cyber_eval.domain import WriteOperation
from cyber_eval.identity.boundary import IdentityBoundary
from cyber_eval.identity.contracts import (
    AuthorizationContext,
    DevicePosture,
    EnvironmentClass,
    HumanRole,
    PamElevationGrant,
    TrustDomain,
    VerifiedPrincipal,
)
from cyber_eval.identity.errors import IdentityAuthorizationError


@dataclass(frozen=True, slots=True)
class StateChangeBinding:
    operation: WriteOperation
    action: str
    required_roles: frozenset[HumanRole] = frozenset()
    allowed_workload_domains: frozenset[TrustDomain] = frozenset()
    independent_approval_required: bool = False

    def __post_init__(self) -> None:
        if not self.action:
            raise ValueError("state-change action must not be empty")
        if bool(self.required_roles) == bool(self.allowed_workload_domains):
            raise ValueError("a state-change binding must select exactly one principal class")


_BINDINGS = (
    StateChangeBinding(
        WriteOperation.CREATE_ENGAGEMENT,
        "engagement.create",
        required_roles=frozenset({HumanRole.PLATFORM_ADMIN}),
    ),
    StateChangeBinding(
        WriteOperation.REGISTER_SCOPE_ROE,
        "scope_roe.register",
        required_roles=frozenset({HumanRole.REQUESTER}),
    ),
    StateChangeBinding(
        WriteOperation.ACTIVATE_ENGAGEMENT,
        "engagement.activate",
        required_roles=frozenset({HumanRole.REQUESTER}),
    ),
    StateChangeBinding(
        WriteOperation.CLOSE_ENGAGEMENT,
        "engagement.close",
        required_roles=frozenset({HumanRole.REQUESTER}),
    ),
    StateChangeBinding(
        WriteOperation.REQUEST_APPROVAL,
        "approval.request",
        required_roles=frozenset({HumanRole.REQUESTER}),
    ),
    StateChangeBinding(
        WriteOperation.DECIDE_APPROVAL,
        "approval.decide",
        required_roles=frozenset({HumanRole.APPROVER}),
        independent_approval_required=True,
    ),
    StateChangeBinding(
        WriteOperation.MOCK_TOOL_WRITE,
        "tool.write",
        allowed_workload_domains=frozenset({TrustDomain.CONTROL}),
    ),
    StateChangeBinding(
        WriteOperation.ISSUE_CREDENTIAL_REFERENCE,
        "credential_reference.issue",
        required_roles=frozenset({HumanRole.SECURITY_OPERATOR}),
    ),
    StateChangeBinding(
        WriteOperation.REVOKE_CREDENTIAL_REFERENCE,
        "credential_reference.revoke",
        required_roles=frozenset({HumanRole.SECURITY_OPERATOR}),
    ),
    StateChangeBinding(
        WriteOperation.ACTIVATE_EMERGENCY_STOP,
        "emergency_stop.activate",
        required_roles=frozenset({HumanRole.SECURITY_OPERATOR}),
    ),
    StateChangeBinding(
        WriteOperation.CLEAR_EMERGENCY_STOP,
        "emergency_stop.clear",
        required_roles=frozenset({HumanRole.SECURITY_OPERATOR}),
    ),
    StateChangeBinding(
        WriteOperation.START_RUNNER_JOB,
        "runner_job.start",
        allowed_workload_domains=frozenset({TrustDomain.EXECUTION}),
    ),
    StateChangeBinding(
        WriteOperation.TERMINATE_RUNNER_JOB,
        "runner_job.terminate",
        allowed_workload_domains=frozenset({TrustDomain.EXECUTION}),
    ),
    StateChangeBinding(
        WriteOperation.CREATE_RANGE_INSTANCE,
        "range_instance.create",
        allowed_workload_domains=frozenset({TrustDomain.RANGE}),
    ),
    StateChangeBinding(
        WriteOperation.RESET_RANGE_INSTANCE,
        "range_instance.reset",
        allowed_workload_domains=frozenset({TrustDomain.RANGE}),
    ),
    StateChangeBinding(
        WriteOperation.DESTROY_RANGE_INSTANCE,
        "range_instance.destroy",
        allowed_workload_domains=frozenset({TrustDomain.RANGE}),
    ),
    StateChangeBinding(
        WriteOperation.START_AGENT_RUN,
        "agent_run.start",
        allowed_workload_domains=frozenset({TrustDomain.CONTROL}),
    ),
)
_BINDING_MAP = {binding.operation: binding for binding in _BINDINGS}


class ProductionIdentityGateway:
    """The only production-facing entry point for authorizing state changes."""

    def __init__(self, boundary: IdentityBoundary) -> None:
        self._boundary = boundary
        if set(_BINDING_MAP) != set(WriteOperation):
            raise RuntimeError("production identity bindings do not cover all write operations")

    def authorize(
        self,
        *,
        operation: WriteOperation,
        principal: VerifiedPrincipal,
        engagement_id: str,
        environment: EnvironmentClass,
        device_posture: DevicePosture,
        elevation_grant: PamElevationGrant | None = None,
        requester: VerifiedPrincipal | None = None,
    ) -> VerifiedPrincipal:
        try:
            binding = _BINDING_MAP[operation]
        except KeyError as exc:
            raise IdentityAuthorizationError(
                "state-changing operation is not registered at the identity boundary"
            ) from exc
        context = AuthorizationContext(
            principal=principal,
            engagement_id=engagement_id,
            action=binding.action,
            environment=environment,
            device_posture=device_posture,
            elevation_grant=elevation_grant,
        )
        verified = self._boundary.authorize_state_change(
            context,
            required_roles=binding.required_roles,
            allowed_workload_domains=binding.allowed_workload_domains,
        )
        if binding.independent_approval_required:
            if requester is None:
                raise IdentityAuthorizationError(
                    "state-changing operation requires a verified requester"
                )
            self._boundary.require_independent_approval(
                requester=requester,
                approver=verified,
                engagement_id=engagement_id,
            )
        return verified


def production_state_change_bindings() -> tuple[StateChangeBinding, ...]:
    """Return the immutable production operation inventory."""

    return tuple(sorted(_BINDINGS, key=lambda binding: binding.operation.value))
