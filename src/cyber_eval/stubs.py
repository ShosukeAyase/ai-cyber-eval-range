"""In-memory stubs containing synthetic identifiers only."""

from __future__ import annotations

from dataclasses import dataclass, field

from cyber_eval.domain import ActionClass, ApprovalEvidence


@dataclass(frozen=True, slots=True)
class StaticScopeRegistry:
    entries: frozenset[tuple[str, str]] = field(default_factory=frozenset)

    def contains(self, engagement_id: str, target_id: str) -> bool:
        return (engagement_id, target_id) in self.entries


@dataclass(frozen=True, slots=True)
class StaticApprovalRepository:
    records: dict[tuple[str, str, ActionClass], ApprovalEvidence] = field(default_factory=dict)

    def find(
        self,
        engagement_id: str,
        target_id: str,
        action_class: ActionClass,
    ) -> ApprovalEvidence | None:
        return self.records.get((engagement_id, target_id, action_class))
