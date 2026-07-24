"""Non-executable Tool Gateway skeleton."""

from __future__ import annotations

from typing import Never

from cyber_eval.domain import (
    AuthorizationFacts,
    DecisionReason,
    PolicyContext,
    PolicyDecision,
    ToolRequest,
)
from cyber_eval.errors import ExecutionDisabledError
from cyber_eval.interfaces import ApprovalRepository, PolicyEngine, ScopeRegistry
from cyber_eval.policy import DANGEROUS_ACTIONS


class NonExecutableToolGateway:
    """Performs authorization only; dispatch is prohibited in Phase 02."""

    def __init__(
        self,
        *,
        scope_registry: ScopeRegistry,
        approval_repository: ApprovalRepository,
        policy_engine: PolicyEngine,
    ) -> None:
        self._scope_registry = scope_registry
        self._approval_repository = approval_repository
        self._policy_engine = policy_engine

    def authorize(self, request: ToolRequest, facts: AuthorizationFacts) -> PolicyDecision:
        target_in_scope = self._scope_registry.contains(
            request.engagement_id,
            request.target_id,
        )
        approval = None
        if request.action_class in DANGEROUS_ACTIONS:
            approval = self._approval_repository.find(
                request.engagement_id,
                request.target_id,
                request.action_class,
            )
        context = PolicyContext(
            facts=facts,
            target_in_scope=target_in_scope,
            approval=approval,
        )
        try:
            return self._policy_engine.evaluate(request, context)
        except Exception:
            return PolicyDecision(
                allowed=False,
                reason=DecisionReason.POLICY_EVALUATION_ERROR,
                policy_version=self._policy_engine.version,
            )

    def dispatch(self, request: ToolRequest) -> Never:
        del request
        raise ExecutionDisabledError("Phase 02 has no execution adapters or dispatch path")
