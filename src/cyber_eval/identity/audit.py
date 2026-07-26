"""Deterministic identity audit sink for local and CI validation."""

from __future__ import annotations

from threading import Lock

from cyber_eval.identity.contracts import IdentityAuditEvent


class InMemoryIdentityAuditSink:
    """Append-only deterministic sink; production must use independent evidence storage."""

    def __init__(self) -> None:
        self._events: list[IdentityAuditEvent] = []
        self._lock = Lock()

    def append(self, event: IdentityAuditEvent) -> None:
        with self._lock:
            self._events.append(event)

    def events(self) -> tuple[IdentityAuditEvent, ...]:
        with self._lock:
            return tuple(self._events)
