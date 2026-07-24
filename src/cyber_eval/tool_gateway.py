"""Authorization-only Tool Gateway mock with no execution adapter."""

from __future__ import annotations

from cyber_eval.approval_service import ApprovalService
from cyber_eval.audit import make_audit_event
from cyber_eval.domain import (
    AuditOutcome,
    MockToolResult,
    MockToolStatus,
    ToolRequest,
)
from cyber_eval.interfaces import Clock
from cyber_eval.policy import DANGEROUS_ACTIONS
from cyber_eval.policy_adapter import LocalPolicyEngineAdapter
from cyber_eval.store import LocalControlPlaneStore


class ToolGatewayMock:
    def __init__(
        self,
        *,
        store: LocalControlPlaneStore,
        policy: LocalPolicyEngineAdapter,
        approvals: ApprovalService,
        clock: Clock,
    ) -> None:
        self._store = store
        self._policy = policy
        self._approvals = approvals
        self._clock = clock
        self._invocation_count = 0

    @property
    def invocation_count(self) -> int:
        return self._invocation_count

    def invoke(
        self,
        engagement_id: str,
        actor_id: str,
        request: ToolRequest,
    ) -> MockToolResult:
        decision = self._policy._evaluate_unlogged(engagement_id, actor_id, request)
        outcome = AuditOutcome.ALLOWED if decision.allowed else AuditOutcome.DENIED
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="tool_gateway.invoke_mock",
            outcome=outcome,
            clock=self._clock,
            details={"reason": decision.reason.value, "request_id": request.request_id},
        )
        if decision.allowed and request.action_class in DANGEROUS_ACTIONS:
            grant, _ = self._approvals._find_policy_approval(
                engagement_id,
                actor_id,
                request.target_id,
                request.action_class,
            )
            if grant is None:
                raise RuntimeError("policy allowed a write without an approval grant")
            with self._store.audited_transaction(event) as connection:
                self._approvals._consume_in_transaction(connection, grant)
        else:
            self._store.append_audit(engagement_id, event)
        self._invocation_count += 1
        if decision.allowed:
            return MockToolResult(
                request_id=request.request_id,
                engagement_id=engagement_id,
                status=MockToolStatus.ACCEPTED_NO_EXECUTION,
                decision=decision,
                synthetic_result_id=f"mock-result-{request.request_id}",
            )
        return MockToolResult(
            request_id=request.request_id,
            engagement_id=engagement_id,
            status=MockToolStatus.DENIED,
            decision=decision,
        )
