"""Local deterministic Policy Engine adapter with fail-closed behavior."""

from __future__ import annotations

from cyber_eval.approval_service import ApprovalService
from cyber_eval.audit import make_audit_event
from cyber_eval.domain import (
    AuditOutcome,
    AuthorizationFacts,
    DecisionReason,
    EngagementState,
    PolicyContext,
    PolicyDecision,
    ToolRequest,
)
from cyber_eval.emergency_stop import EmergencyStopService
from cyber_eval.engagement_service import EngagementService
from cyber_eval.interfaces import Clock
from cyber_eval.policy import FailClosedPolicyEngine
from cyber_eval.scope_roe_service import ScopeRoeService
from cyber_eval.store import LocalControlPlaneStore


class LocalPolicyEngineAdapter:
    def __init__(
        self,
        *,
        store: LocalControlPlaneStore,
        engagements: EngagementService,
        scope_roe: ScopeRoeService,
        approvals: ApprovalService,
        emergency_stop: EmergencyStopService,
        clock: Clock,
        available: bool = True,
    ) -> None:
        self._store = store
        self._engagements = engagements
        self._scope_roe = scope_roe
        self._approvals = approvals
        self._emergency_stop = emergency_stop
        self._clock = clock
        self._engine = FailClosedPolicyEngine(
            available=available,
            version="policy-local-mvp-0.3",
        )
        self._available = available

    @property
    def version(self) -> str:
        return self._engine.version

    def evaluate(
        self,
        engagement_id: str,
        actor_id: str,
        request: ToolRequest,
    ) -> PolicyDecision:
        decision = self._evaluate_unlogged(engagement_id, actor_id, request)
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="policy.evaluate",
            outcome=(AuditOutcome.ALLOWED if decision.allowed else AuditOutcome.DENIED),
            clock=self._clock,
            details={"reason": decision.reason.value, "request_id": request.request_id},
        )
        self._store.append_audit(engagement_id, event)
        return decision

    def _evaluate_unlogged(
        self,
        engagement_id: str,
        actor_id: str,
        request: ToolRequest,
    ) -> PolicyDecision:
        if not self._available:
            return PolicyDecision(False, DecisionReason.POLICY_UNAVAILABLE, self.version)
        if request.engagement_id != engagement_id:
            return PolicyDecision(False, DecisionReason.MANIFEST_INVALID, self.version)
        engagement = self._engagements._load(engagement_id)
        if engagement is None or engagement.valid_until <= self._clock.now():
            return PolicyDecision(False, DecisionReason.MANIFEST_INVALID, self.version)
        if engagement.state is not EngagementState.ACTIVE:
            return PolicyDecision(False, DecisionReason.ENGAGEMENT_NOT_ACTIVE, self.version)
        roe = self._scope_roe._load(engagement_id)
        if roe is None:
            return PolicyDecision(False, DecisionReason.ROE_INVALID, self.version)
        now = self._clock.now()
        if not (roe.valid_from <= now < roe.valid_until):
            return PolicyDecision(False, DecisionReason.ROE_EXPIRED, self.version)

        _, approval = self._approvals._find_policy_approval(
            engagement_id,
            actor_id,
            request.target_id,
            request.action_class,
        )
        facts = AuthorizationFacts(
            manifest_valid=True,
            roe_valid=True,
            policy_version_current=True,
            test_case_allowed=request.test_case_id in roe.test_case_ids,
            within_limits=True,
            destination_matches=True,
            emergency_stop_active=self._emergency_stop._is_active_unlogged(engagement_id),
        )
        context = PolicyContext(
            facts=facts,
            target_in_scope=request.target_id in roe.target_ids,
            approval=approval,
        )
        try:
            return self._engine.evaluate(request, context)
        except Exception:
            return PolicyDecision(False, DecisionReason.POLICY_EVALUATION_ERROR, self.version)
