"""Composition root for the single-laptop Control Plane MVP."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from cyber_eval.agent.context import AgentContextRegistry
from cyber_eval.agent.model_client import AgentModelClient
from cyber_eval.agent.orchestrator import AgentOrchestrator
from cyber_eval.approval_service import ApprovalService
from cyber_eval.audit import AuditService
from cyber_eval.clock import SystemClock
from cyber_eval.credential_broker import CredentialBrokerMock
from cyber_eval.domain import (
    ApprovalGrant,
    ApprovalState,
    LocalDevBootstrap,
    ResourceScope,
    WriteOperation,
)
from cyber_eval.emergency_stop import EmergencyStopService
from cyber_eval.engagement_service import EngagementService
from cyber_eval.identifiers import new_identifier, require_identifier
from cyber_eval.interfaces import Clock
from cyber_eval.model_gateway import DeterministicModelGatewayMock
from cyber_eval.policy_adapter import LocalPolicyEngineAdapter
from cyber_eval.scope_roe_service import ScopeRoeService
from cyber_eval.store import LocalControlPlaneStore
from cyber_eval.tool_gateway import ToolGatewayMock

_OPERATOR_ADMIN_OPERATIONS = frozenset(
    {
        WriteOperation.CREATE_ENGAGEMENT,
        WriteOperation.REGISTER_SCOPE_ROE,
        WriteOperation.ACTIVATE_ENGAGEMENT,
        WriteOperation.CLOSE_ENGAGEMENT,
        WriteOperation.REQUEST_APPROVAL,
        WriteOperation.ACTIVATE_EMERGENCY_STOP,
        WriteOperation.CLEAR_EMERGENCY_STOP,
    }
)
_APPROVER_ADMIN_OPERATIONS = frozenset(
    {
        WriteOperation.DECIDE_APPROVAL,
        WriteOperation.ACTIVATE_EMERGENCY_STOP,
        WriteOperation.CLEAR_EMERGENCY_STOP,
    }
)


class ControlPlaneMvp:
    """Local service graph; external model egress is optional and explicitly attached."""

    def __init__(
        self,
        *,
        store: LocalControlPlaneStore,
        clock: Clock,
        bootstrap: LocalDevBootstrap,
        policy_available: bool,
    ) -> None:
        self.store = store
        self.clock = clock
        self.bootstrap = bootstrap
        self.approvals = ApprovalService(store=store, clock=clock)
        self.engagements = EngagementService(
            store=store,
            approvals=self.approvals,
            clock=clock,
        )
        self.scope_roe = ScopeRoeService(
            store=store,
            approvals=self.approvals,
            clock=clock,
        )
        self.emergency_stop = EmergencyStopService(
            store=store,
            approvals=self.approvals,
            clock=clock,
        )
        self.policy = LocalPolicyEngineAdapter(
            store=store,
            engagements=self.engagements,
            scope_roe=self.scope_roe,
            approvals=self.approvals,
            emergency_stop=self.emergency_stop,
            clock=clock,
            available=policy_available,
        )
        self.model_gateway = DeterministicModelGatewayMock(
            store=store,
            engagements=self.engagements,
            clock=clock,
        )
        self.tool_gateway = ToolGatewayMock(
            store=store,
            policy=self.policy,
            approvals=self.approvals,
            clock=clock,
        )
        self.credential_broker = CredentialBrokerMock(
            store=store,
            approvals=self.approvals,
            scope_roe=self.scope_roe,
            clock=clock,
        )
        self.audit = AuditService(store=store, clock=clock)
        self.agent_contexts = AgentContextRegistry()
        self.agent: AgentOrchestrator | None = None

    def configure_agent(self, model_client: AgentModelClient) -> AgentOrchestrator:
        """Attach one proposal-only model client to the existing Control Plane boundaries."""
        self.agent = AgentOrchestrator(
            store=self.store,
            engagements=self.engagements,
            scope_roe=self.scope_roe,
            approvals=self.approvals,
            emergency_stop=self.emergency_stop,
            tool_gateway=self.tool_gateway,
            model_client=model_client,
            contexts=self.agent_contexts,
            clock=self.clock,
        )
        return self.agent

    @classmethod
    def local_dev(
        cls,
        engagement_id: str,
        operator_id: str,
        approver_id: str,
        bootstrap_expires_at: datetime,
        database: str | Path = ":memory:",
        clock: Clock | None = None,
        policy_available: bool = True,
    ) -> ControlPlaneMvp:
        require_identifier(engagement_id, "eng")
        if operator_id == approver_id:
            raise ValueError("local operator and approver identities must be distinct")
        selected_clock = clock or SystemClock()
        if bootstrap_expires_at.tzinfo is None:
            raise ValueError("bootstrap expiry must be timezone-aware")
        if bootstrap_expires_at <= selected_clock.now():
            raise ValueError("bootstrap expiry must be in the future")

        store = LocalControlPlaneStore(database)
        operator_approval_id = new_identifier("apr")
        approver_approval_id = new_identifier("apr")
        requested_at = selected_clock.now()
        store.seed_approval(
            ApprovalGrant(
                approval_id=operator_approval_id,
                engagement_id=engagement_id,
                requested_by=operator_id,
                approved_by=approver_id,
                state=ApprovalState.APPROVED,
                allowed_operations=_OPERATOR_ADMIN_OPERATIONS,
                resource_scope=ResourceScope.ENGAGEMENT,
                resource_id=engagement_id,
                requested_at=requested_at,
                expires_at=bootstrap_expires_at,
                max_uses=1000,
                uses=0,
            )
        )
        store.seed_approval(
            ApprovalGrant(
                approval_id=approver_approval_id,
                engagement_id=engagement_id,
                requested_by=approver_id,
                approved_by=operator_id,
                state=ApprovalState.APPROVED,
                allowed_operations=_APPROVER_ADMIN_OPERATIONS,
                resource_scope=ResourceScope.ENGAGEMENT,
                resource_id=engagement_id,
                requested_at=requested_at,
                expires_at=bootstrap_expires_at,
                max_uses=1000,
                uses=0,
            )
        )
        bootstrap = LocalDevBootstrap(
            engagement_id=engagement_id,
            operator_id=operator_id,
            approver_id=approver_id,
            operator_admin_approval_id=operator_approval_id,
            approver_admin_approval_id=approver_approval_id,
        )
        return cls(
            store=store,
            clock=selected_clock,
            bootstrap=bootstrap,
            policy_available=policy_available,
        )

    def close(self, engagement_id: str) -> None:
        if engagement_id != self.bootstrap.engagement_id:
            raise ValueError("engagement mismatch for local store close")
        self.store.close()


def default_bootstrap_expiry() -> datetime:
    return datetime(2099, 1, 1, tzinfo=UTC)
