"""SQLite-backed local state and transactional audit persistence."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import cast

from cyber_eval.domain import ApprovalGrant, AuditEvent
from cyber_eval.errors import AuditUnavailableError


class LocalControlPlaneStore:
    """Single-process SQLite store for the free local-development profile."""

    def __init__(self, database: str | Path = ":memory:") -> None:
        database_name = str(database)
        if database_name != ":memory:":
            Path(database_name).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(
            database_name,
            check_same_thread=False,
            isolation_level=None,
        )
        self._connection.row_factory = sqlite3.Row
        self._lock = RLock()
        self._fail_audit_writes = False
        self._connection.execute("PRAGMA foreign_keys = ON")
        if database_name != ":memory:":
            self._connection.execute("PRAGMA journal_mode = WAL")
        self._migrate()

    @property
    def fail_audit_writes(self) -> bool:
        return self._fail_audit_writes

    @fail_audit_writes.setter
    def fail_audit_writes(self, enabled: bool) -> None:
        self._fail_audit_writes = enabled

    @contextmanager
    def audited_transaction(self, event: AuditEvent) -> Iterator[sqlite3.Connection]:
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                self._insert_audit(self._connection, event)
                yield self._connection
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise

    def append_audit(self, engagement_id: str, event: AuditEvent) -> None:
        if engagement_id != event.engagement_id:
            raise ValueError("audit engagement mismatch")
        with self.audited_transaction(event):
            pass

    def fetch_one(
        self,
        query: str,
        parameters: Sequence[object] = (),
    ) -> sqlite3.Row | None:
        with self._lock:
            row = self._connection.execute(query, tuple(parameters)).fetchone()
            return cast(sqlite3.Row | None, row)

    def fetch_all(
        self,
        query: str,
        parameters: Sequence[object] = (),
    ) -> tuple[sqlite3.Row, ...]:
        with self._lock:
            rows = self._connection.execute(query, tuple(parameters)).fetchall()
            return cast(tuple[sqlite3.Row, ...], tuple(rows))

    def seed_approval(self, grant: ApprovalGrant) -> None:
        """Seed the explicit local bootstrap trust root before service operations begin."""
        with self._lock:
            self._connection.execute(
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

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def _insert_audit(self, connection: sqlite3.Connection, event: AuditEvent) -> None:
        if self._fail_audit_writes:
            raise AuditUnavailableError("injected local audit write failure")
        connection.execute(
            """
            INSERT INTO audit_events (
                event_id, engagement_id, actor_id, operation, outcome,
                approval_id, occurred_at, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.engagement_id,
                event.actor_id,
                event.operation,
                event.outcome.value,
                event.approval_id,
                event.occurred_at.isoformat(),
                json.dumps(dict(event.details), sort_keys=True),
            ),
        )

    def _migrate(self) -> None:
        statements = (
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                engagement_id TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                operation TEXT NOT NULL,
                outcome TEXT NOT NULL,
                approval_id TEXT,
                occurred_at TEXT NOT NULL,
                details TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS engagements (
                engagement_id TEXT PRIMARY KEY,
                owner_actor_id TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                valid_until TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scope_roe (
                engagement_id TEXT PRIMARY KEY,
                target_ids TEXT NOT NULL,
                test_case_ids TEXT NOT NULL,
                valid_from TEXT NOT NULL,
                valid_until TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS approvals (
                approval_id TEXT PRIMARY KEY,
                engagement_id TEXT NOT NULL,
                requested_by TEXT NOT NULL,
                approved_by TEXT,
                state TEXT NOT NULL,
                allowed_operations TEXT NOT NULL,
                resource_scope TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                requested_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                max_uses INTEGER NOT NULL,
                uses INTEGER NOT NULL,
                action_class TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS emergency_stops (
                engagement_id TEXT PRIMARY KEY,
                active INTEGER NOT NULL,
                reason TEXT NOT NULL,
                activated_by TEXT,
                activated_at TEXT,
                cleared_at TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS credential_references (
                reference_id TEXT PRIMARY KEY,
                engagement_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                purpose TEXT NOT NULL,
                issued_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                state TEXT NOT NULL
            )
            """,
        )
        with self._lock:
            for statement in statements:
                self._connection.execute(statement)
