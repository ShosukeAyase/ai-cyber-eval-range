"""Scope and Rules of Engagement service using object identifiers only."""

from __future__ import annotations

import json
from datetime import datetime

from cyber_eval.approval_service import ApprovalService
from cyber_eval.audit import make_audit_event
from cyber_eval.domain import AuditOutcome, RoeRecord, WriteOperation
from cyber_eval.errors import (
    EngagementNotFoundError,
    RoeExpiredError,
    ScopeViolationError,
)
from cyber_eval.identifiers import require_identifier
from cyber_eval.interfaces import Clock
from cyber_eval.store import LocalControlPlaneStore


class ScopeRoeService:
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

    def register(
        self,
        engagement_id: str,
        actor_id: str,
        approval_id: str,
        target_ids: frozenset[str],
        test_case_ids: frozenset[str],
        valid_from: datetime,
        valid_until: datetime,
    ) -> RoeRecord:
        require_identifier(engagement_id, "eng")
        for target_id in target_ids:
            require_identifier(target_id, "tgt")
        for test_case_id in test_case_ids:
            require_identifier(test_case_id, "tc")
        if not target_ids or not test_case_ids:
            raise ValueError("Scope/ROE requires targets and test cases")
        if valid_from >= valid_until:
            raise ValueError("ROE valid_from must precede valid_until")
        if (
            self._store.fetch_one(
                "SELECT engagement_id FROM engagements WHERE engagement_id = ?",
                (engagement_id,),
            )
            is None
        ):
            raise EngagementNotFoundError(engagement_id)

        approval = self._approvals._require_write(
            engagement_id=engagement_id,
            actor_id=actor_id,
            approval_id=approval_id,
            operation=WriteOperation.REGISTER_SCOPE_ROE,
            resource_id=engagement_id,
        )
        record = RoeRecord(
            engagement_id=engagement_id,
            target_ids=target_ids,
            test_case_ids=test_case_ids,
            valid_from=valid_from,
            valid_until=valid_until,
        )
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="scope_roe.register",
            outcome=AuditOutcome.COMPLETED,
            approval_id=approval_id,
            clock=self._clock,
            details={
                "target_count": str(len(target_ids)),
                "test_case_count": str(len(test_case_ids)),
            },
        )
        with self._store.audited_transaction(event) as connection:
            self._approvals._consume_in_transaction(connection, approval)
            connection.execute(
                """
                INSERT INTO scope_roe (
                    engagement_id, target_ids, test_case_ids, valid_from, valid_until
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(engagement_id) DO UPDATE SET
                    target_ids = excluded.target_ids,
                    test_case_ids = excluded.test_case_ids,
                    valid_from = excluded.valid_from,
                    valid_until = excluded.valid_until
                """,
                (
                    engagement_id,
                    json.dumps(sorted(target_ids)),
                    json.dumps(sorted(test_case_ids)),
                    valid_from.isoformat(),
                    valid_until.isoformat(),
                ),
            )
        return record

    def get(self, engagement_id: str, actor_id: str) -> RoeRecord:
        record = self._load(engagement_id)
        if record is None:
            raise ScopeViolationError("Scope/ROE record not found")
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="scope_roe.get",
            outcome=AuditOutcome.COMPLETED,
            clock=self._clock,
        )
        self._store.append_audit(engagement_id, event)
        return record

    def assert_current(
        self,
        engagement_id: str,
        target_id: str,
        test_case_id: str,
        now: datetime | None = None,
    ) -> RoeRecord:
        record = self._load(engagement_id)
        if record is None:
            raise ScopeViolationError("Scope/ROE record not found")
        current = now or self._clock.now()
        if not (record.valid_from <= current < record.valid_until):
            raise RoeExpiredError("ROE is outside its validity window")
        if target_id not in record.target_ids:
            raise ScopeViolationError("target is outside the engagement scope")
        if test_case_id not in record.test_case_ids:
            raise ScopeViolationError("test case is outside the engagement ROE")
        return record

    def assert_target_current(
        self,
        engagement_id: str,
        target_id: str,
        now: datetime | None = None,
    ) -> RoeRecord:
        record = self._load(engagement_id)
        if record is None:
            raise ScopeViolationError("Scope/ROE record not found")
        current = now or self._clock.now()
        if not (record.valid_from <= current < record.valid_until):
            raise RoeExpiredError("ROE is outside its validity window")
        if target_id not in record.target_ids:
            raise ScopeViolationError("target is outside the engagement scope")
        return record

    def contains(self, engagement_id: str, target_id: str) -> bool:
        record = self._load(engagement_id)
        return record is not None and target_id in record.target_ids

    def _load(self, engagement_id: str) -> RoeRecord | None:
        row = self._store.fetch_one(
            "SELECT * FROM scope_roe WHERE engagement_id = ?",
            (engagement_id,),
        )
        if row is None:
            return None
        return RoeRecord(
            engagement_id=str(row["engagement_id"]),
            target_ids=frozenset(str(item) for item in json.loads(str(row["target_ids"]))),
            test_case_ids=frozenset(str(item) for item in json.loads(str(row["test_case_ids"]))),
            valid_from=datetime.fromisoformat(str(row["valid_from"])),
            valid_until=datetime.fromisoformat(str(row["valid_until"])),
        )
