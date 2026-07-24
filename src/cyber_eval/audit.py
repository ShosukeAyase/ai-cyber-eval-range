"""Audit-event construction and read access for the local MVP."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime

from cyber_eval.domain import AuditEvent, AuditOutcome
from cyber_eval.identifiers import new_identifier, require_identifier
from cyber_eval.interfaces import Clock
from cyber_eval.store import LocalControlPlaneStore


def make_audit_event(
    *,
    engagement_id: str,
    actor_id: str,
    operation: str,
    outcome: AuditOutcome,
    clock: Clock,
    approval_id: str | None = None,
    details: Mapping[str, str] | None = None,
) -> AuditEvent:
    require_identifier(engagement_id, "eng")
    return AuditEvent(
        event_id=new_identifier("evt"),
        engagement_id=engagement_id,
        actor_id=actor_id,
        operation=operation,
        outcome=outcome,
        occurred_at=clock.now(),
        approval_id=approval_id,
        details=tuple(sorted((details or {}).items())),
    )


class AuditService:
    def __init__(self, *, store: LocalControlPlaneStore, clock: Clock) -> None:
        self._store = store
        self._clock = clock

    def list_events(self, engagement_id: str, actor_id: str) -> tuple[AuditEvent, ...]:
        rows = self._store.fetch_all(
            """
            SELECT event_id, engagement_id, actor_id, operation, outcome,
                   approval_id, occurred_at, details
            FROM audit_events
            WHERE engagement_id = ?
            ORDER BY occurred_at, event_id
            """,
            (engagement_id,),
        )
        events = tuple(
            AuditEvent(
                event_id=str(row["event_id"]),
                engagement_id=str(row["engagement_id"]),
                actor_id=str(row["actor_id"]),
                operation=str(row["operation"]),
                outcome=AuditOutcome(str(row["outcome"])),
                approval_id=(str(row["approval_id"]) if row["approval_id"] is not None else None),
                occurred_at=datetime.fromisoformat(str(row["occurred_at"])),
                details=tuple(
                    sorted(
                        (str(key), str(value))
                        for key, value in json.loads(str(row["details"])).items()
                    )
                ),
            )
            for row in rows
        )
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="audit.list_events",
            outcome=AuditOutcome.COMPLETED,
            clock=self._clock,
            details={"event_count": str(len(events))},
        )
        self._store.append_audit(engagement_id, event)
        return events
