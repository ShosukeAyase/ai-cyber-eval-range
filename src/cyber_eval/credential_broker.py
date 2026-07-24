"""Opaque-reference-only Credential Broker mock."""

from __future__ import annotations

from datetime import datetime, timedelta

from cyber_eval.approval_service import ApprovalService
from cyber_eval.audit import make_audit_event
from cyber_eval.domain import (
    ActionClass,
    AuditOutcome,
    CredentialPurpose,
    CredentialReference,
    CredentialReferenceState,
    WriteOperation,
)
from cyber_eval.identifiers import new_identifier, require_identifier
from cyber_eval.interfaces import Clock
from cyber_eval.scope_roe_service import ScopeRoeService
from cyber_eval.store import LocalControlPlaneStore


class CredentialBrokerMock:
    """Stores metadata references only; no credential value exists in this component."""

    def __init__(
        self,
        *,
        store: LocalControlPlaneStore,
        approvals: ApprovalService,
        scope_roe: ScopeRoeService,
        clock: Clock,
    ) -> None:
        self._store = store
        self._approvals = approvals
        self._scope_roe = scope_roe
        self._clock = clock

    def issue_reference(
        self,
        engagement_id: str,
        actor_id: str,
        approval_id: str,
        target_id: str,
        purpose: CredentialPurpose,
        ttl_seconds: int,
    ) -> CredentialReference:
        require_identifier(target_id, "tgt")
        if ttl_seconds < 1 or ttl_seconds > 3600:
            raise ValueError("mock reference TTL must be between 1 and 3600 seconds")
        self._scope_roe.assert_target_current(engagement_id, target_id)
        approval = self._approvals._require_write(
            engagement_id=engagement_id,
            actor_id=actor_id,
            approval_id=approval_id,
            operation=WriteOperation.ISSUE_CREDENTIAL_REFERENCE,
            resource_id=target_id,
            action_class=ActionClass.CREDENTIALED_TEST,
        )
        issued_at = self._clock.now()
        record = CredentialReference(
            reference_id=new_identifier("cref"),
            engagement_id=engagement_id,
            target_id=target_id,
            purpose=purpose,
            issued_at=issued_at,
            expires_at=issued_at + timedelta(seconds=ttl_seconds),
            state=CredentialReferenceState.ACTIVE,
        )
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="credential_broker.issue_mock_reference",
            outcome=AuditOutcome.COMPLETED,
            approval_id=approval_id,
            clock=self._clock,
            details={"reference_id": record.reference_id, "target_id": target_id},
        )
        with self._store.audited_transaction(event) as connection:
            self._approvals._consume_in_transaction(connection, approval)
            connection.execute(
                """
                INSERT INTO credential_references (
                    reference_id, engagement_id, target_id, purpose,
                    issued_at, expires_at, state
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.reference_id,
                    record.engagement_id,
                    record.target_id,
                    record.purpose.value,
                    record.issued_at.isoformat(),
                    record.expires_at.isoformat(),
                    record.state.value,
                ),
            )
        return record

    def revoke_reference(
        self,
        engagement_id: str,
        actor_id: str,
        approval_id: str,
        reference_id: str,
    ) -> CredentialReference:
        record = self._load(engagement_id, reference_id)
        if record is None:
            raise ValueError("mock credential reference not found")
        approval = self._approvals._require_write(
            engagement_id=engagement_id,
            actor_id=actor_id,
            approval_id=approval_id,
            operation=WriteOperation.REVOKE_CREDENTIAL_REFERENCE,
            resource_id=reference_id,
        )
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="credential_broker.revoke_mock_reference",
            outcome=AuditOutcome.COMPLETED,
            approval_id=approval_id,
            clock=self._clock,
            details={"reference_id": reference_id},
        )
        with self._store.audited_transaction(event) as connection:
            self._approvals._consume_in_transaction(connection, approval)
            connection.execute(
                """
                UPDATE credential_references
                SET state = ?
                WHERE engagement_id = ? AND reference_id = ?
                """,
                (CredentialReferenceState.REVOKED.value, engagement_id, reference_id),
            )
        revoked = self._load(engagement_id, reference_id)
        if revoked is None:
            raise ValueError("mock credential reference could not be read")
        return revoked

    def get_reference(
        self,
        engagement_id: str,
        actor_id: str,
        reference_id: str,
    ) -> CredentialReference:
        record = self._load(engagement_id, reference_id)
        if record is None:
            raise ValueError("mock credential reference not found")
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="credential_broker.get_mock_reference",
            outcome=AuditOutcome.COMPLETED,
            clock=self._clock,
            details={"reference_id": reference_id},
        )
        self._store.append_audit(engagement_id, event)
        return record

    def _load(self, engagement_id: str, reference_id: str) -> CredentialReference | None:
        row = self._store.fetch_one(
            """
            SELECT * FROM credential_references
            WHERE engagement_id = ? AND reference_id = ?
            """,
            (engagement_id, reference_id),
        )
        if row is None:
            return None
        return CredentialReference(
            reference_id=str(row["reference_id"]),
            engagement_id=str(row["engagement_id"]),
            target_id=str(row["target_id"]),
            purpose=CredentialPurpose(str(row["purpose"])),
            issued_at=datetime.fromisoformat(str(row["issued_at"])),
            expires_at=datetime.fromisoformat(str(row["expires_at"])),
            state=CredentialReferenceState(str(row["state"])),
        )
