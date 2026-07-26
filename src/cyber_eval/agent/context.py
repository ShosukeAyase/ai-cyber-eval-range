"""Registered context resolver that never exposes secret-reference material."""

from __future__ import annotations

from cyber_eval.agent.contracts import AgentContextObject, ContextTrust
from cyber_eval.errors import AgentContextError
from cyber_eval.identifiers import require_generic_object_id


class AgentContextRegistry:
    def __init__(self) -> None:
        self._objects: dict[str, AgentContextObject] = {}

    def register(self, item: AgentContextObject) -> None:
        require_generic_object_id(item.object_id)
        if item.object_id in self._objects:
            raise AgentContextError("agent context object already registered")
        if len(item.content) > 16_000:
            raise AgentContextError("agent context object exceeds the approved size")
        self._objects[item.object_id] = item

    def resolve(
        self,
        object_ids: tuple[str, ...],
    ) -> tuple[tuple[AgentContextObject, ...], tuple[str, ...]]:
        resolved: list[AgentContextObject] = []
        redacted: list[str] = []
        for object_id in object_ids:
            require_generic_object_id(object_id)
            item = self._objects.get(object_id)
            if item is None:
                raise AgentContextError("agent context object is not registered")
            if item.trust is ContextTrust.SECRET_REFERENCE:
                redacted.append(object_id)
                continue
            resolved.append(item)
        return tuple(resolved), tuple(redacted)
