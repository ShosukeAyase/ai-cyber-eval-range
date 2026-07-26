"""Typed contracts for the Phase 06 untrusted model integration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from cyber_eval.domain import ActionClass, ObjectReference, ToolId


class AgentRole(StrEnum):
    PROPOSE_EVALUATION_PLAN = "propose_evaluation_plan"
    SELECT_APPROVED_TOOLS = "select_approved_tools"
    ANALYZE_RESULTS = "analyze_results"
    ORGANIZE_EVIDENCE = "organize_evidence"
    PROPOSE_REMEDIATION = "propose_remediation"
    PROPOSE_REVALIDATION = "propose_revalidation"


class AgentRunState(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    TERMINATED = "terminated"


class AgentTurnDisposition(StrEnum):
    PROPOSE_TOOLS = "propose_tools"
    FINAL = "final"


class ContextTrust(StrEnum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"
    SECRET_REFERENCE = "secret_reference"


class ProhibitedIntent(StrEnum):
    DECIDE_SCOPE = "decide_scope"
    CHANGE_SCOPE = "change_scope"
    SELF_APPROVE = "self_approve"
    MANAGE_CREDENTIALS = "manage_credentials"
    EXECUTE_ARBITRARY_COMMAND = "execute_arbitrary_command"
    CHOOSE_NETWORK_DESTINATION = "choose_network_destination"
    CONTROL_KILL_SWITCH = "control_kill_switch"
    MODIFY_AUDIT_LOG = "modify_audit_log"
    AUTO_MERGE_PATCH = "auto_merge_patch"
    ACCESS_GENERAL_INTERNET = "access_general_internet"
    USE_FORBIDDEN_TOOL = "use_forbidden_tool"
    FORGE_TOOL_RESPONSE = "forge_tool_response"


@dataclass(frozen=True, slots=True)
class AgentContextObject:
    object_id: str
    trust: ContextTrust
    content: str


@dataclass(frozen=True, slots=True)
class AgentToolProposal:
    tool_id: ToolId
    action_class: ActionClass
    target_id: str
    test_case_id: str
    arguments: tuple[ObjectReference, ...] = ()


@dataclass(frozen=True, slots=True)
class AgentFindingProposal:
    finding_id: str
    title: str
    severity: str
    summary: str
    evidence_object_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AgentTurn:
    disposition: AgentTurnDisposition
    role: AgentRole
    summary: str
    tool_proposals: tuple[AgentToolProposal, ...]
    findings: tuple[AgentFindingProposal, ...]
    evidence_organization: tuple[str, ...]
    remediation_steps: tuple[str, ...]
    revalidation_steps: tuple[str, ...]
    prohibited_intents: tuple[ProhibitedIntent, ...]


@dataclass(frozen=True, slots=True)
class AgentRunRequest:
    run_id: str
    engagement_id: str
    role: AgentRole
    context_object_ids: tuple[str, ...]
    allowed_tool_ids: tuple[ToolId, ...]
    max_steps: int = 4
    max_repeated_failures: int = 2


@dataclass(frozen=True, slots=True)
class ToolGatewayReceipt:
    receipt_id: str
    request_id: str
    tool_id: ToolId
    target_id: str
    test_case_id: str
    allowed: bool
    decision_reason: str
    evidence_object_id: str | None
    attestation: str


@dataclass(frozen=True, slots=True)
class AgentModelInput:
    run_id: str
    turn_number: int
    role: AgentRole
    scope_target_ids: tuple[str, ...]
    scope_test_case_ids: tuple[str, ...]
    allowed_tool_ids: tuple[ToolId, ...]
    contexts: tuple[AgentContextObject, ...]
    redacted_object_ids: tuple[str, ...]
    tool_receipts: tuple[ToolGatewayReceipt, ...]
    failure_summaries: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AgentModelOutput:
    provider_response_id: str
    model_profile: str
    output_json: str


@dataclass(frozen=True, slots=True)
class AgentRunResult:
    run_id: str
    engagement_id: str
    state: AgentRunState
    steps: int
    model_invocations: int
    tool_invocations: int
    blocked_proposals: int
    executed_scope_violations: int
    terminal_reason: str | None
    final_turn: AgentTurn | None

    @property
    def scope_violation_rate(self) -> float:
        if self.tool_invocations == 0:
            return 0.0
        return self.executed_scope_violations / self.tool_invocations
