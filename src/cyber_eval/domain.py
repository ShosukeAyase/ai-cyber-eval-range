"""Immutable domain contracts for the local Control Plane MVP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ActionClass(StrEnum):
    READ_ONLY_ANALYSIS = "read_only_analysis"
    SAFE_DISCOVERY = "safe_discovery"
    SAFE_TEST = "safe_test"
    STATE_CHANGE = "state_change"
    CREDENTIALED_TEST = "credentialed_test"
    POC_VALIDATION = "poc_validation"
    PATCH_VALIDATION = "patch_validation"
    RANGE_RESET = "range_reset"
    ENGAGEMENT_TERMINATION = "engagement_termination"


class ToolId(StrEnum):
    RUN_STATIC_ANALYSIS = "run_static_analysis"
    RUN_SAFE_NETWORK_DISCOVERY = "run_safe_network_discovery"
    RUN_WEB_TEST = "run_web_test"
    REQUEST_POC_VALIDATION = "request_poc_validation"
    COLLECT_EVIDENCE = "collect_evidence"
    PROPOSE_PATCH = "propose_patch"
    VALIDATE_PATCH = "validate_patch"
    RESET_RANGE = "reset_range"
    TERMINATE_ENGAGEMENT = "terminate_engagement"


class ObjectReferenceName(StrEnum):
    REPOSITORY_ID = "repository_id"
    PROFILE_ID = "profile_id"
    TEST_CASE_ID = "test_case_id"
    POC_ID = "poc_id"
    EVIDENCE_ID = "evidence_id"
    FINDING_ID = "finding_id"
    PATCH_ID = "patch_id"
    TEST_SUITE_ID = "test_suite_id"
    SCENARIO_ID = "scenario_id"


class DecisionReason(StrEnum):
    ALLOW = "allow"
    POLICY_UNAVAILABLE = "policy_unavailable"
    POLICY_EVALUATION_ERROR = "policy_evaluation_error"
    MANIFEST_INVALID = "manifest_invalid"
    ENGAGEMENT_NOT_ACTIVE = "engagement_not_active"
    ROE_INVALID = "roe_invalid"
    ROE_EXPIRED = "roe_expired"
    POLICY_VERSION_STALE = "policy_version_stale"
    TARGET_OUT_OF_SCOPE = "target_out_of_scope"
    TEST_CASE_NOT_ALLOWED = "test_case_not_allowed"
    LIMIT_EXCEEDED = "limit_exceeded"
    DESTINATION_MISMATCH = "destination_mismatch"
    EMERGENCY_STOP_ACTIVE = "emergency_stop_active"
    APPROVAL_REQUIRED = "approval_required"
    APPROVAL_INVALID = "approval_invalid"
    APPROVAL_NOT_INDEPENDENT = "approval_not_independent"
    APPROVAL_EXPIRED = "approval_expired"
    APPROVAL_SCOPE_MISMATCH = "approval_scope_mismatch"
    ACTION_CLASS_MISMATCH = "action_class_mismatch"


class ApprovalState(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    REVOKED = "revoked"
    CONSUMED = "consumed"


class EngagementState(StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    APPROVED = "approved"
    ACTIVE = "active"
    STOPPING = "stopping"
    CLOSED = "closed"
    TERMINATED = "terminated"


class JobState(StrEnum):
    REQUESTED = "requested"
    POLICY_PENDING = "policy_pending"
    APPROVAL_PENDING = "approval_pending"
    AUTHORIZED = "authorized"
    PROVISIONING = "provisioning"
    READY = "ready"
    RUNNING = "running"
    COLLECTING = "collecting"
    DESTROYING = "destroying"
    COMPLETED = "completed"
    DENIED = "denied"
    EXPIRED = "expired"
    QUARANTINED = "quarantined"
    TERMINATED = "terminated"
    FAILED = "failed"


class RunnerState(StrEnum):
    ABSENT = "absent"
    CREATING = "creating"
    ATTESTED = "attested"
    NETWORKED = "networked"
    ACTIVE = "active"
    ISOLATED = "isolated"
    DESTROYED = "destroyed"


class WriteOperation(StrEnum):
    CREATE_ENGAGEMENT = "create_engagement"
    REGISTER_SCOPE_ROE = "register_scope_roe"
    ACTIVATE_ENGAGEMENT = "activate_engagement"
    CLOSE_ENGAGEMENT = "close_engagement"
    REQUEST_APPROVAL = "request_approval"
    DECIDE_APPROVAL = "decide_approval"
    MOCK_TOOL_WRITE = "mock_tool_write"
    ISSUE_CREDENTIAL_REFERENCE = "issue_credential_reference"
    REVOKE_CREDENTIAL_REFERENCE = "revoke_credential_reference"
    ACTIVATE_EMERGENCY_STOP = "activate_emergency_stop"
    CLEAR_EMERGENCY_STOP = "clear_emergency_stop"
    START_RUNNER_JOB = "start_runner_job"
    TERMINATE_RUNNER_JOB = "terminate_runner_job"
    CREATE_RANGE_INSTANCE = "create_range_instance"
    RESET_RANGE_INSTANCE = "reset_range_instance"
    DESTROY_RANGE_INSTANCE = "destroy_range_instance"
    START_AGENT_RUN = "start_agent_run"


class ResourceScope(StrEnum):
    ENGAGEMENT = "engagement"
    RESOURCE = "resource"


class AuditOutcome(StrEnum):
    ALLOWED = "allowed"
    DENIED = "denied"
    COMPLETED = "completed"


class ModelPurpose(StrEnum):
    ANALYZE_EVIDENCE = "analyze_evidence"
    PROPOSE_TEST_PLAN = "propose_test_plan"
    PROPOSE_REMEDIATION = "propose_remediation"
    SUMMARIZE_FINDINGS = "summarize_findings"


class MockToolStatus(StrEnum):
    ACCEPTED_NO_EXECUTION = "accepted_no_execution"
    DENIED = "denied"


class CredentialReferenceState(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class CredentialPurpose(StrEnum):
    SYNTHETIC_TARGET_AUTH = "synthetic_target_auth"
    MOCK_PATCH_VALIDATION = "mock_patch_validation"


@dataclass(frozen=True, slots=True)
class ObjectReference:
    name: ObjectReferenceName
    object_id: str


@dataclass(frozen=True, slots=True)
class ToolRequest:
    request_id: str
    engagement_id: str
    target_id: str
    test_case_id: str
    action_class: ActionClass
    tool_id: ToolId
    arguments: tuple[ObjectReference, ...] = ()


@dataclass(frozen=True, slots=True)
class ApprovalEvidence:
    approval_id: str
    valid: bool
    independent: bool
    unexpired: bool
    target_id: str
    action_class: ActionClass


@dataclass(frozen=True, slots=True)
class AuthorizationFacts:
    manifest_valid: bool
    roe_valid: bool
    policy_version_current: bool
    test_case_allowed: bool
    within_limits: bool
    destination_matches: bool
    emergency_stop_active: bool = False


@dataclass(frozen=True, slots=True)
class PolicyContext:
    facts: AuthorizationFacts
    target_in_scope: bool
    approval: ApprovalEvidence | None = None


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reason: DecisionReason
    policy_version: str


@dataclass(frozen=True, slots=True)
class EngagementRecord:
    engagement_id: str
    owner_actor_id: str
    state: EngagementState
    created_at: datetime
    valid_until: datetime


@dataclass(frozen=True, slots=True)
class RoeRecord:
    engagement_id: str
    target_ids: frozenset[str]
    test_case_ids: frozenset[str]
    valid_from: datetime
    valid_until: datetime


@dataclass(frozen=True, slots=True)
class ApprovalGrant:
    approval_id: str
    engagement_id: str
    requested_by: str
    approved_by: str | None
    state: ApprovalState
    allowed_operations: frozenset[WriteOperation]
    resource_scope: ResourceScope
    resource_id: str
    requested_at: datetime
    expires_at: datetime
    max_uses: int
    uses: int
    action_class: ActionClass | None = None


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    engagement_id: str
    actor_id: str
    operation: str
    outcome: AuditOutcome
    occurred_at: datetime
    approval_id: str | None = None
    details: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class ModelRequest:
    request_id: str
    purpose: ModelPurpose
    prompt_template_id: str
    context_object_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ModelResponse:
    request_id: str
    engagement_id: str
    model_profile: str
    output_text: str


@dataclass(frozen=True, slots=True)
class MockToolResult:
    request_id: str
    engagement_id: str
    status: MockToolStatus
    decision: PolicyDecision
    synthetic_result_id: str | None = None


@dataclass(frozen=True, slots=True)
class CredentialReference:
    reference_id: str
    engagement_id: str
    target_id: str
    purpose: CredentialPurpose
    issued_at: datetime
    expires_at: datetime
    state: CredentialReferenceState


@dataclass(frozen=True, slots=True)
class EmergencyStopRecord:
    engagement_id: str
    active: bool
    reason: str
    activated_by: str | None
    activated_at: datetime | None
    cleared_at: datetime | None


@dataclass(frozen=True, slots=True)
class LocalDevBootstrap:
    engagement_id: str
    operator_id: str
    approver_id: str
    operator_admin_approval_id: str
    approver_admin_approval_id: str
