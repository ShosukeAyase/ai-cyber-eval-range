"""Emergency Stop service independent of model and runner components."""

from __future__ import annotations

from datetime import datetime

from cyber_eval.approval_service import ApprovalService
from cyber_eval.audit import make_audit_event
from cyber_eval.domain import AuditOutcome, EmergencyStopRecord, WriteOperation
from cyber_eval.interfaces import Clock
from cyber_eval.store import LocalControlPlaneStore


class EmergencyStopService:
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

    def activate(
        self,
        engagement_id: str,
        actor_id: str,
        approval_id: str,
        reason: str,
    ) -> EmergencyStopRecord:
        if not reason.strip():
            raise ValueError("Emergency Stop reason is required")
        approval = self._approvals._require_write(
            engagement_id=engagement_id,
            actor_id=actor_id,
            approval_id=approval_id,
            operation=WriteOperation.ACTIVATE_EMERGENCY_STOP,
            resource_id=engagement_id,
        )
        activated_at = self._clock.now()
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="emergency_stop.activate",
            outcome=AuditOutcome.COMPLETED,
            approval_id=approval_id,
            clock=self._clock,
            details={"reason": reason},
        )
        with self._store.audited_transaction(event) as connection:
            self._approvals._consume_in_transaction(connection, approval)
            connection.execute(
                """
                INSERT INTO emergency_stops (
                    engagement_id, active, reason, activated_by, activated_at, cleared_at
                ) VALUES (?, 1, ?, ?, ?, NULL)
                ON CONFLICT(engagement_id) DO UPDATE SET
                    active = 1,
                    reason = excluded.reason,
                    activated_by = excluded.activated_by,
                    activated_at = excluded.activated_at,
                    cleared_at = NULL
                """,
                (engagement_id, reason, actor_id, activated_at.isoformat()),
            )
        return self._load(engagement_id)

    def clear(
        self,
        engagement_id: str,
        actor_id: str,
        approval_id: str,
    ) -> EmergencyStopRecord:
        approval = self._approvals._require_write(
            engagement_id=engagement_id,
            actor_id=actor_id,
            approval_id=approval_id,
            operation=WriteOperation.CLEAR_EMERGENCY_STOP,
            resource_id=engagement_id,
        )
        cleared_at = self._clock.now()
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="emergency_stop.clear",
            outcome=AuditOutcome.COMPLETED,
            approval_id=approval_id,
            clock=self._clock,
        )
        with self._store.audited_transaction(event) as connection:
            self._approvals._consume_in_transaction(connection, approval)
            connection.execute(
                """
                INSERT INTO emergency_stops (
                    engagement_id, active, reason, activated_by, activated_at, cleared_at
                ) VALUES (?, 0, '', NULL, NULL, ?)
                ON CONFLICT(engagement_id) DO UPDATE SET
                    active = 0,
                    cleared_at = excluded.cleared_at
                """,
                (engagement_id, cleared_at.isoformat()),
            )
        return self._load(engagement_id)

    def is_active(self, engagement_id: str, actor_id: str) -> bool:
        active = self._is_active_unlogged(engagement_id)
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="emergency_stop.is_active",
            outcome=AuditOutcome.COMPLETED,
            clock=self._clock,
            details={"active": str(active).lower()},
        )
        self._store.append_audit(engagement_id, event)
        return active

    def _is_active_unlogged(self, engagement_id: str) -> bool:
        row = self._store.fetch_one(
            "SELECT active FROM emergency_stops WHERE engagement_id = ?",
            (engagement_id,),
        )
        return bool(row["active"]) if row is not None else False

    def _load(self, engagement_id: str) -> EmergencyStopRecord:
        row = self._store.fetch_one(
            "SELECT * FROM emergency_stops WHERE engagement_id = ?",
            (engagement_id,),
        )
        if row is None:
            return EmergencyStopRecord(
                engagement_id=engagement_id,
                active=False,
                reason="",
                activated_by=None,
                activated_at=None,
                cleared_at=None,
            )
        return EmergencyStopRecord(
            engagement_id=engagement_id,
            active=bool(row["active"]),
            reason=str(row["reason"]),
            activated_by=(str(row["activated_by"]) if row["activated_by"] is not None else None),
            activated_at=self._optional_datetime(row["activated_at"]),
            cleared_at=self._optional_datetime(row["cleared_at"]),
        )

    @staticmethod
    def _optional_datetime(value: object) -> datetime | None:
        return datetime.fromisoformat(str(value)) if value is not None else None
