"""Protocol-only API boundaries for Phase 02."""

from __future__ import annotations

from typing import Never, Protocol

from cyber_eval.domain import (
    ActionClass,
    ApprovalEvidence,
    AuthorizationFacts,
    PolicyContext,
    PolicyDecision,
    ToolRequest,
)


class ScopeRegistry(Protocol):
    def contains(self, engagement_id: str, target_id: str) -> bool:
        """Return whether a registered target belongs to an engagement."""


class ApprovalRepository(Protocol):
    def find(
        self,
        engagement_id: str,
        target_id: str,
        action_class: ActionClass,
    ) -> ApprovalEvidence | None:
        """Return pre-registered approval evidence or no record."""


class PolicyEngine(Protocol):
    @property
    def version(self) -> str:
        """Return the immutable policy bundle identifier."""

    def evaluate(self, request: ToolRequest, context: PolicyContext) -> PolicyDecision:
        """Return an allow or deny decision without side effects."""


class ToolGateway(Protocol):
    def authorize(self, request: ToolRequest, facts: AuthorizationFacts) -> PolicyDecision:
        """Authorize a structured object-ID request."""

    def dispatch(self, request: ToolRequest) -> Never:
        """Remain disabled throughout Phase 02."""
