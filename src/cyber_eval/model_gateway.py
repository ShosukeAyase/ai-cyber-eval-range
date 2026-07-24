"""External-model abstraction and deterministic local mock."""

from __future__ import annotations

from cyber_eval.audit import make_audit_event
from cyber_eval.domain import AuditOutcome, EngagementState, ModelRequest, ModelResponse
from cyber_eval.engagement_service import EngagementService
from cyber_eval.errors import EngagementNotFoundError, ExecutionDisabledError
from cyber_eval.identifiers import require_generic_object_id, require_identifier
from cyber_eval.interfaces import Clock
from cyber_eval.store import LocalControlPlaneStore


class DeterministicModelGatewayMock:
    """Returns fixed local text and never contacts a model provider."""

    def __init__(
        self,
        *,
        store: LocalControlPlaneStore,
        engagements: EngagementService,
        clock: Clock,
    ) -> None:
        self._store = store
        self._engagements = engagements
        self._clock = clock
        self._invocation_count = 0

    @property
    def invocation_count(self) -> int:
        return self._invocation_count

    def generate(
        self,
        engagement_id: str,
        actor_id: str,
        request: ModelRequest,
    ) -> ModelResponse:
        require_identifier(engagement_id, "eng")
        require_identifier(request.request_id, "req")
        require_identifier(request.prompt_template_id, "tmpl")
        for object_id in request.context_object_ids:
            require_generic_object_id(object_id)
        engagement = self._engagements._load(engagement_id)
        if engagement is None:
            raise EngagementNotFoundError(engagement_id)
        if engagement.state is not EngagementState.ACTIVE:
            raise ExecutionDisabledError("model mock requires an active engagement")
        response = ModelResponse(
            request_id=request.request_id,
            engagement_id=engagement_id,
            model_profile="deterministic-local-mock",
            output_text=(
                f"mock:{request.purpose.value}:"
                f"{request.prompt_template_id}:contexts={len(request.context_object_ids)}"
            ),
        )
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="model_gateway.generate_mock",
            outcome=AuditOutcome.COMPLETED,
            clock=self._clock,
            details={"request_id": request.request_id, "purpose": request.purpose.value},
        )
        self._store.append_audit(engagement_id, event)
        self._invocation_count += 1
        return response
