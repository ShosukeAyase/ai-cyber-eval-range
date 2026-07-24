"""Independent approval service for local Control Plane writes."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from cyber_eval.audit import make_audit_event
from cyber_eval.domain import (
    ActionClass,
    ApprovalEvidence,
    ApprovalGrant,
    ApprovalState,
    AuditOutcome,
    ResourceScope,
    WriteOperation,
)
from cyber_eval.errors import (
    ApprovalInvalidError,
    ApprovalRequiredError,
    DuplicateRecordError,
    SelfApprovalError,
)
from cyber_eval.identifiers import require_identifier
from cyber_eval.interfaces import Clock
from cyber_eval.store import LocalControlPlaneStore


class ApprovalService:
    def __init__(self, *, store: LocalControlPlaneStore, clock: Clock) -> None:
        self._store = store
        self._clock = clock

    def request(
        self,
        engagement_id: str,
        actor_id: str,
        admin_approval_id: str,
        approval_id: str,
        allowed_operations: frozenset[WriteOperation],
        resource_scope: ResourceScope,
        resource_id: str,
        expires_at: datetime,
        action_class: ActionClass | None = None,
        max_uses: int = 1,
    ) -> ApprovalGrant:
        require_identifier(engagement_id, "eng")
        require_identifier(approval_id, "apr")
        if not allowed_operations:
            raise ApprovalInvalidError("approval must authorize at least one operation")
        if expires_at <= self._clock.now():
            raise ApprovalInvalidError("approval request expiry must be in the future")
        if max_uses < 1:
            raise ApprovalInvalidError("approval max_uses must be positive")

        admin = self._require_write(
            engagement_id=engagement_id,
            actor_id=actor_id,
            approval_id=admin_approval_id,
            operation=WriteOperation.REQUEST_APPROVAL,
            resource_id=engagement_id,
        )
        requested_at = self._clock.now()
        grant = ApprovalGrant(
            approval_id=approval_id,
            engagement_id=engagement_id,
            requested_by=actor_id,
            approved_by=None,
            state=ApprovalState.REQUESTED,
            allowed_operations=allowed_operations,
            resource_scope=resource_scope,
            resource_id=resource_id,
            requested_at=requested_at,
            expires_at=expires_at,
            max_uses=max_uses,
            uses=0,
            action_class=action_class,
        )
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="approval.request",
            outcome=AuditOutcome.COMPLETED,
            approval_id=admin_approval_id,
            clock=self._clock,
            details={"requested_approval_id": approval_id},
        )
        try:
            with self._store.audited_transaction(event) as connection:
                self._consume_in_transaction(connection, admin)
                self._insert_in_transaction(connection, grant)
        except sqlite3.IntegrityError as exc:
            raise DuplicateRecordError(f"approval already exists: {approval_id}") from exc
        return grant

    def approve(
        self,
        engagement_id: str,
        actor_id: str,
        admin_approval_id: str,
        approval_id: str,
    ) -> ApprovalGrant:
        grant = self._load(engagement_id, approval_id)
        if grant is None:
            self._audit_denial(
                engagement_id,
                actor_id,
                "approval.approve",
                admin_approval_id,
                "approval_not_found",
            )
            raise ApprovalRequiredError("approval request not found")
        if grant.requested_by == actor_id:
            self._audit_denial(
                engagement_id,
                actor_id,
                "approval.approve",
                admin_approval_id,
                "self_approval",
            )
            raise SelfApprovalError("requestor cannot approve their own request")
        if grant.state is not ApprovalState.REQUESTED:
            raise ApprovalInvalidError("approval request is not pending")
        if grant.expires_at <= self._clock.now():
            raise ApprovalInvalidError("approval request has expired")

        admin = self._require_write(
            engagement_id=engagement_id,
            actor_id=actor_id,
            approval_id=admin_approval_id,
            operation=WriteOperation.DECIDE_APPROVAL,
            resource_id=approval_id,
        )
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="approval.approve",
            outcome=AuditOutcome.COMPLETED,
            approval_id=admin_approval_id,
            clock=self._clock,
            details={"approved_approval_id": approval_id},
        )
        with self._store.audited_transaction(event) as connection:
            self._consume_in_transaction(connection, admin)
            connection.execute(
                """
                UPDATE approvals
                SET state = ?, approved_by = ?
                WHERE engagement_id = ? AND approval_id = ? AND state = ?
                """,
                (
                    ApprovalState.APPROVED.value,
                    actor_id,
                    engagement_id,
                    approval_id,
                    ApprovalState.REQUESTED.value,
                ),
            )
        approved = self._load(engagement_id, approval_id)
        if approved is None:
            raise ApprovalInvalidError("approved record could not be read")
        return approved

    def get(self, engagement_id: str, actor_id: str, approval_id: str) -> ApprovalGrant:
        grant = self._load(engagement_id, approval_id)
        if grant is None:
            raise ApprovalRequiredError("approval record not found")
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="approval.get",
            outcome=AuditOutcome.COMPLETED,
            clock=self._clock,
            details={"approval_id": approval_id},
        )
        self._store.append_audit(engagement_id, event)
        return grant

    def _require_write(
        self,
        *,
        engagement_id: str,
        actor_id: str,
        approval_id: str,
        operation: WriteOperation,
        resource_id: str,
        action_class: ActionClass | None = None,
    ) -> ApprovalGrant:
        grant = self._load(engagement_id, approval_id)
        if grant is None:
            raise ApprovalRequiredError("approval record is required")
        now = self._clock.now()
        checks = (
            grant.state is ApprovalState.APPROVED,
            grant.requested_by == actor_id,
            grant.approved_by is not None,
            grant.approved_by != actor_id,
            grant.expires_at > now,
            grant.uses < grant.max_uses,
            operation in grant.allowed_operations,
            grant.engagement_id == engagement_id,
        )
        if not all(checks):
            raise ApprovalInvalidError("approval is invalid, expired, exhausted, or mismatched")
        if grant.resource_scope is ResourceScope.ENGAGEMENT:
            if grant.resource_id != engagement_id:
                raise ApprovalInvalidError("engagement-scoped approval mismatch")
        elif grant.resource_id != resource_id:
            raise ApprovalInvalidError("resource-scoped approval mismatch")
        if action_class is not None and grant.action_class is not action_class:
            raise ApprovalInvalidError("approval action class mismatch")
        return grant

    def _find_policy_approval(
        self,
        engagement_id: str,
        actor_id: str,
        target_id: str,
        action_class: ActionClass,
    ) -> tuple[ApprovalGrant | None, ApprovalEvidence | None]:
        rows = self._store.fetch_all(
            """
            SELECT * FROM approvals
            WHERE engagement_id = ? AND requested_by = ? AND state = ?
            ORDER BY requested_at DESC
            """,
            (engagement_id, actor_id, ApprovalState.APPROVED.value),
        )
        for row in rows:
            grant = self._row_to_grant(row)
            if WriteOperation.MOCK_TOOL_WRITE not in grant.allowed_operations:
                continue
            if grant.resource_scope is not ResourceScope.RESOURCE:
                continue
            if grant.resource_id != target_id or grant.action_class is not action_class:
                continue
            evidence = ApprovalEvidence(
                approval_id=grant.approval_id,
                valid=grant.state is ApprovalState.APPROVED and grant.uses < grant.max_uses,
                independent=grant.approved_by is not None and grant.approved_by != actor_id,
                unexpired=grant.expires_at > self._clock.now(),
                target_id=grant.resource_id,
                action_class=action_class,
            )
            return grant, evidence
        return None, None

    def _consume_in_transaction(
        self,
        connection: sqlite3.Connection,
        grant: ApprovalGrant,
    ) -> None:
        next_uses = grant.uses + 1
        next_state = (
            ApprovalState.CONSUMED.value
            if next_uses >= grant.max_uses
            else ApprovalState.APPROVED.value
        )
        cursor = connection.execute(
            """
            UPDATE approvals
            SET uses = ?, state = ?
            WHERE approval_id = ? AND engagement_id = ? AND uses = ? AND state = ?
            """,
            (
                next_uses,
                next_state,
                grant.approval_id,
                grant.engagement_id,
                grant.uses,
                ApprovalState.APPROVED.value,
            ),
        )
        if cursor.rowcount != 1:
            raise ApprovalInvalidError("approval could not be consumed atomically")

    def _load(self, engagement_id: str, approval_id: str) -> ApprovalGrant | None:
        row = self._store.fetch_one(
            "SELECT * FROM approvals WHERE engagement_id = ? AND approval_id = ?",
            (engagement_id, approval_id),
        )
        return self._row_to_grant(row) if row is not None else None

    def _insert_in_transaction(
        self,
        connection: sqlite3.Connection,
        grant: ApprovalGrant,
    ) -> None:
        connection.execute(
            """
            INSERT INTO approvals (
                approval_id, engagement_id, requested_by, approved_by, state,
                allowed_operations, resource_scope, resource_id, requested_at,
                expires_at, max_uses, uses, action_class
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                grant.approval_id,
                grant.engagement_id,
                grant.requested_by,
                grant.approved_by,
                grant.state.value,
                json.dumps(sorted(item.value for item in grant.allowed_operations)),
                grant.resource_scope.value,
                grant.resource_id,
                grant.requested_at.isoformat(),
                grant.expires_at.isoformat(),
                grant.max_uses,
                grant.uses,
                grant.action_class.value if grant.action_class else None,
            ),
        )

    def _row_to_grant(self, row: sqlite3.Row) -> ApprovalGrant:
        action_value = row["action_class"]
        return ApprovalGrant(
            approval_id=str(row["approval_id"]),
            engagement_id=str(row["engagement_id"]),
            requested_by=str(row["requested_by"]),
            approved_by=(str(row["approved_by"]) if row["approved_by"] is not None else None),
            state=ApprovalState(str(row["state"])),
            allowed_operations=frozenset(
                WriteOperation(item) for item in json.loads(str(row["allowed_operations"]))
            ),
            resource_scope=ResourceScope(str(row["resource_scope"])),
            resource_id=str(row["resource_id"]),
            requested_at=datetime.fromisoformat(str(row["requested_at"])),
            expires_at=datetime.fromisoformat(str(row["expires_at"])),
            max_uses=int(row["max_uses"]),
            uses=int(row["uses"]),
            action_class=ActionClass(str(action_value)) if action_value is not None else None,
        )

    def _audit_denial(
        self,
        engagement_id: str,
        actor_id: str,
        operation: str,
        approval_id: str | None,
        reason: str,
    ) -> None:
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation=operation,
            outcome=AuditOutcome.DENIED,
            approval_id=approval_id,
            clock=self._clock,
            details={"reason": reason},
        )
        self._store.append_audit(engagement_id, event)
