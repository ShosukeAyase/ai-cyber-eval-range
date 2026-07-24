"""Engagement lifecycle service for the local Control Plane MVP."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from cyber_eval.approval_service import ApprovalService
from cyber_eval.audit import make_audit_event
from cyber_eval.domain import (
    AuditOutcome,
    EngagementRecord,
    EngagementState,
    WriteOperation,
)
from cyber_eval.errors import (
    DuplicateRecordError,
    EngagementNotFoundError,
    RoeExpiredError,
)
from cyber_eval.identifiers import require_identifier
from cyber_eval.interfaces import Clock
from cyber_eval.state_machine import ENGAGEMENT_MACHINE
from cyber_eval.store import LocalControlPlaneStore


class EngagementService:
    def __init__(
        self,
        *,
        store: LocalControlPlaneStore,
        approvals: ApprovalService,
        clock: Clock,
    ) -> None:
        self._store = store
        self._approvals = approvals
        self._clock = clock

    def create(
        self,
        engagement_id: str,
        actor_id: str,
        approval_id: str,
        valid_until: datetime,
    ) -> EngagementRecord:
        require_identifier(engagement_id, "eng")
        if valid_until <= self._clock.now():
            raise ValueError("engagement validity must end in the future")
        approval = self._approvals._require_write(
            engagement_id=engagement_id,
            actor_id=actor_id,
            approval_id=approval_id,
            operation=WriteOperation.CREATE_ENGAGEMENT,
            resource_id=engagement_id,
        )
        created_at = self._clock.now()
        record = EngagementRecord(
            engagement_id=engagement_id,
            owner_actor_id=actor_id,
            state=EngagementState.DRAFT,
            created_at=created_at,
            valid_until=valid_until,
        )
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="engagement.create",
            outcome=AuditOutcome.COMPLETED,
            approval_id=approval_id,
            clock=self._clock,
        )
        try:
            with self._store.audited_transaction(event) as connection:
                self._approvals._consume_in_transaction(connection, approval)
                connection.execute(
                    """
                    INSERT INTO engagements (
                        engagement_id, owner_actor_id, state, created_at, valid_until
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        record.engagement_id,
                        record.owner_actor_id,
                        record.state.value,
                        record.created_at.isoformat(),
                        record.valid_until.isoformat(),
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise DuplicateRecordError(f"engagement already exists: {engagement_id}") from exc
        return record

    def activate(
        self,
        engagement_id: str,
        actor_id: str,
        approval_id: str,
    ) -> EngagementRecord:
        record = self._load(engagement_id)
        if record is None:
            raise EngagementNotFoundError(engagement_id)
        if not self._roe_is_current(engagement_id, self._clock.now()):
            raise RoeExpiredError("a current Scope/ROE record is required")
        approval = self._approvals._require_write(
            engagement_id=engagement_id,
            actor_id=actor_id,
            approval_id=approval_id,
            operation=WriteOperation.ACTIVATE_ENGAGEMENT,
            resource_id=engagement_id,
        )
        paths = {
            EngagementState.DRAFT: (
                EngagementState.VALIDATED,
                EngagementState.APPROVED,
                EngagementState.ACTIVE,
            ),
            EngagementState.VALIDATED: (
                EngagementState.APPROVED,
                EngagementState.ACTIVE,
            ),
            EngagementState.APPROVED: (EngagementState.ACTIVE,),
            EngagementState.ACTIVE: (),
        }
        if record.state not in paths:
            ENGAGEMENT_MACHINE.transition(record.state, EngagementState.ACTIVE)
        target = record.state
        for next_state in paths[record.state]:
            target = ENGAGEMENT_MACHINE.transition(target, next_state)
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="engagement.activate",
            outcome=AuditOutcome.COMPLETED,
            approval_id=approval_id,
            clock=self._clock,
        )
        with self._store.audited_transaction(event) as connection:
            self._approvals._consume_in_transaction(connection, approval)
            connection.execute(
                "UPDATE engagements SET state = ? WHERE engagement_id = ?",
                (target.value, engagement_id),
            )
        activated = self._load(engagement_id)
        if activated is None:
            raise EngagementNotFoundError(engagement_id)
        return activated

    def close(
        self,
        engagement_id: str,
        actor_id: str,
        approval_id: str,
    ) -> EngagementRecord:
        record = self._load(engagement_id)
        if record is None:
            raise EngagementNotFoundError(engagement_id)
        approval = self._approvals._require_write(
            engagement_id=engagement_id,
            actor_id=actor_id,
            approval_id=approval_id,
            operation=WriteOperation.CLOSE_ENGAGEMENT,
            resource_id=engagement_id,
        )
        stopping = ENGAGEMENT_MACHINE.transition(record.state, EngagementState.STOPPING)
        closed = ENGAGEMENT_MACHINE.transition(stopping, EngagementState.CLOSED)
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="engagement.close",
            outcome=AuditOutcome.COMPLETED,
            approval_id=approval_id,
            clock=self._clock,
        )
        with self._store.audited_transaction(event) as connection:
            self._approvals._consume_in_transaction(connection, approval)
            connection.execute(
                "UPDATE engagements SET state = ? WHERE engagement_id = ?",
                (closed.value, engagement_id),
            )
        result = self._load(engagement_id)
        if result is None:
            raise EngagementNotFoundError(engagement_id)
        return result

    def get(self, engagement_id: str, actor_id: str) -> EngagementRecord:
        record = self._load(engagement_id)
        if record is None:
            raise EngagementNotFoundError(engagement_id)
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="engagement.get",
            outcome=AuditOutcome.COMPLETED,
            clock=self._clock,
        )
        self._store.append_audit(engagement_id, event)
        return record

    def _load(self, engagement_id: str) -> EngagementRecord | None:
        row = self._store.fetch_one(
            "SELECT * FROM engagements WHERE engagement_id = ?",
            (engagement_id,),
        )
        if row is None:
            return None
        return EngagementRecord(
            engagement_id=str(row["engagement_id"]),
            owner_actor_id=str(row["owner_actor_id"]),
            state=EngagementState(str(row["state"])),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            valid_until=datetime.fromisoformat(str(row["valid_until"])),
        )

    def _roe_is_current(self, engagement_id: str, now: datetime) -> bool:
        row = self._store.fetch_one(
            "SELECT valid_from, valid_until, target_ids FROM scope_roe WHERE engagement_id = ?",
            (engagement_id,),
        )
        if row is None:
            return False
        valid_from = datetime.fromisoformat(str(row["valid_from"]))
        valid_until = datetime.fromisoformat(str(row["valid_until"]))
        targets = json.loads(str(row["target_ids"]))
        return valid_from <= now < valid_until and bool(targets)
