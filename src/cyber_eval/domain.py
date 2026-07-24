"""Immutable domain contracts with no infrastructure or execution behavior."""

from __future__ import annotations

from dataclasses import dataclass
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
    ROE_INVALID = "roe_invalid"
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
