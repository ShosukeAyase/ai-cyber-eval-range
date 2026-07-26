"""Strict Phase 06 model-output schema and parser."""

from __future__ import annotations

import json
from typing import Any

from cyber_eval.agent.contracts import (
    AgentFindingProposal,
    AgentRole,
    AgentToolProposal,
    AgentTurn,
    AgentTurnDisposition,
    ProhibitedIntent,
)
from cyber_eval.domain import ActionClass, ObjectReference, ObjectReferenceName, ToolId
from cyber_eval.errors import AgentOutputRejectedError
from cyber_eval.identifiers import require_generic_object_id, require_identifier

AGENT_TURN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "disposition": {
            "type": "string",
            "enum": [item.value for item in AgentTurnDisposition],
        },
        "role": {"type": "string", "enum": [item.value for item in AgentRole]},
        "summary": {"type": "string", "maxLength": 4000},
        "tool_proposals": {
            "type": "array",
            "maxItems": 8,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "tool_id": {"type": "string", "enum": [item.value for item in ToolId]},
                    "action_class": {
                        "type": "string",
                        "enum": [item.value for item in ActionClass],
                    },
                    "target_id": {"type": "string"},
                    "test_case_id": {"type": "string"},
                    "arguments": {
                        "type": "array",
                        "maxItems": 8,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "enum": [item.value for item in ObjectReferenceName],
                                },
                                "object_id": {"type": "string"},
                            },
                            "required": ["name", "object_id"],
                        },
                    },
                },
                "required": [
                    "tool_id",
                    "action_class",
                    "target_id",
                    "test_case_id",
                    "arguments",
                ],
            },
        },
        "findings": {
            "type": "array",
            "maxItems": 16,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "finding_id": {"type": "string"},
                    "title": {"type": "string", "maxLength": 200},
                    "severity": {
                        "type": "string",
                        "enum": ["informational", "low", "medium", "high", "critical"],
                    },
                    "summary": {"type": "string", "maxLength": 2000},
                    "evidence_object_ids": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 16,
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "finding_id",
                    "title",
                    "severity",
                    "summary",
                    "evidence_object_ids",
                ],
            },
        },
        "evidence_organization": {
            "type": "array",
            "maxItems": 32,
            "items": {"type": "string", "maxLength": 500},
        },
        "remediation_steps": {
            "type": "array",
            "maxItems": 32,
            "items": {"type": "string", "maxLength": 500},
        },
        "revalidation_steps": {
            "type": "array",
            "maxItems": 32,
            "items": {"type": "string", "maxLength": 500},
        },
        "prohibited_intents": {
            "type": "array",
            "maxItems": 16,
            "items": {
                "type": "string",
                "enum": [item.value for item in ProhibitedIntent],
            },
        },
    },
    "required": [
        "disposition",
        "role",
        "summary",
        "tool_proposals",
        "findings",
        "evidence_organization",
        "remediation_steps",
        "revalidation_steps",
        "prohibited_intents",
    ],
}

_ROOT_KEYS = frozenset(AGENT_TURN_SCHEMA["required"])
_TOOL_KEYS = frozenset({"tool_id", "action_class", "target_id", "test_case_id", "arguments"})
_ARGUMENT_KEYS = frozenset({"name", "object_id"})
_FINDING_KEYS = frozenset({"finding_id", "title", "severity", "summary", "evidence_object_ids"})


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AgentOutputRejectedError(f"{label} must be an object")
    return {str(key): item for key, item in value.items()}


def _array(value: object, label: str, limit: int) -> list[object]:
    if not isinstance(value, list) or len(value) > limit:
        raise AgentOutputRejectedError(f"{label} must be a bounded array")
    return value


def _text(value: object, label: str, maximum: int) -> str:
    if not isinstance(value, str) or len(value) > maximum:
        raise AgentOutputRejectedError(f"{label} must be bounded text")
    return value


def parse_agent_turn(output_json: str) -> AgentTurn:
    try:
        document = _object(json.loads(output_json), "agent output")
    except (json.JSONDecodeError, TypeError) as exc:
        raise AgentOutputRejectedError("agent output is not valid JSON") from exc
    if set(document) != _ROOT_KEYS:
        raise AgentOutputRejectedError("agent output contains missing or unknown fields")

    tools: list[AgentToolProposal] = []
    for raw in _array(document["tool_proposals"], "tool_proposals", 8):
        item = _object(raw, "tool proposal")
        if set(item) != _TOOL_KEYS:
            raise AgentOutputRejectedError("tool proposal contains unknown fields")
        arguments: list[ObjectReference] = []
        for raw_argument in _array(item["arguments"], "arguments", 8):
            argument = _object(raw_argument, "tool argument")
            if set(argument) != _ARGUMENT_KEYS:
                raise AgentOutputRejectedError("tool argument contains unknown fields")
            object_id = _text(argument["object_id"], "object_id", 80)
            require_generic_object_id(object_id)
            arguments.append(
                ObjectReference(
                    name=ObjectReferenceName(_text(argument["name"], "name", 64)),
                    object_id=object_id,
                )
            )
        target_id = _text(item["target_id"], "target_id", 80)
        test_case_id = _text(item["test_case_id"], "test_case_id", 80)
        require_identifier(target_id, "tgt")
        require_identifier(test_case_id, "tc")
        tools.append(
            AgentToolProposal(
                tool_id=ToolId(_text(item["tool_id"], "tool_id", 64)),
                action_class=ActionClass(_text(item["action_class"], "action_class", 64)),
                target_id=target_id,
                test_case_id=test_case_id,
                arguments=tuple(arguments),
            )
        )

    findings: list[AgentFindingProposal] = []
    for raw in _array(document["findings"], "findings", 16):
        item = _object(raw, "finding")
        if set(item) != _FINDING_KEYS:
            raise AgentOutputRejectedError("finding contains unknown fields")
        finding_id = _text(item["finding_id"], "finding_id", 80)
        require_generic_object_id(finding_id)
        evidence_ids = tuple(
            _text(value, "evidence_object_id", 80)
            for value in _array(item["evidence_object_ids"], "evidence_object_ids", 16)
        )
        if not evidence_ids:
            raise AgentOutputRejectedError("finding requires evidence")
        for evidence_id in evidence_ids:
            require_generic_object_id(evidence_id)
        severity = _text(item["severity"], "severity", 20)
        if severity not in {"informational", "low", "medium", "high", "critical"}:
            raise AgentOutputRejectedError("finding severity is invalid")
        findings.append(
            AgentFindingProposal(
                finding_id=finding_id,
                title=_text(item["title"], "title", 200),
                severity=severity,
                summary=_text(item["summary"], "summary", 2000),
                evidence_object_ids=evidence_ids,
            )
        )

    def text_tuple(name: str, limit: int) -> tuple[str, ...]:
        return tuple(_text(value, name, 500) for value in _array(document[name], name, limit))

    try:
        prohibited = tuple(
            ProhibitedIntent(_text(value, "prohibited_intent", 64))
            for value in _array(document["prohibited_intents"], "prohibited_intents", 16)
        )
        return AgentTurn(
            disposition=AgentTurnDisposition(_text(document["disposition"], "disposition", 32)),
            role=AgentRole(_text(document["role"], "role", 64)),
            summary=_text(document["summary"], "summary", 4000),
            tool_proposals=tuple(tools),
            findings=tuple(findings),
            evidence_organization=text_tuple("evidence_organization", 32),
            remediation_steps=text_tuple("remediation_steps", 32),
            revalidation_steps=text_tuple("revalidation_steps", 32),
            prohibited_intents=prohibited,
        )
    except ValueError as exc:
        raise AgentOutputRejectedError("agent output contains an invalid enum") from exc
