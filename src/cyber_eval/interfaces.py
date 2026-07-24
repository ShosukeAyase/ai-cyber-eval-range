"""Typed API boundaries for the local Control Plane MVP."""

from __future__ import annotations

from datetime import datetime
from typing import Never, Protocol

from cyber_eval.domain import (
    ActionClass,
    ApprovalEvidence,
    AuditEvent,
    AuthorizationFacts,
    ModelRequest,
    ModelResponse,
    PolicyContext,
    PolicyDecision,
    ToolRequest,
)


class Clock(Protocol):
    def now(self) -> datetime:
        """Return a timezone-aware current time."""


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
        """Remain disabled for the non-executable Phase 02 compatibility boundary."""


class AuditWriter(Protocol):
    def append(self, engagement_id: str, event: AuditEvent) -> None:
        """Append an audit event or raise without partial state change."""


class ModelGateway(Protocol):
    def generate(
        self,
        engagement_id: str,
        actor_id: str,
        request: ModelRequest,
    ) -> ModelResponse:
        """Return a model response without exposing an external provider contract."""
