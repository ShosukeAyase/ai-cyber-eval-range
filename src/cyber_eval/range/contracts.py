"""Typed contracts for the non-networked synthetic Cyber Range MVP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path


class ScenarioKind(StrEnum):
    WEB_ACCESS_CONTROL = "web_access_control"
    API_AUTHORIZATION = "api_authorization"
    DEPENDENCY_ADVISORY = "dependency_advisory"
    IAC_MISCONFIGURATION = "iac_misconfiguration"
    KUBERNETES_RBAC = "kubernetes_rbac"
    INDIRECT_PROMPT_INJECTION = "indirect_prompt_injection"
    SCOPE_REDIRECTION = "scope_redirection"


class RangeOperation(StrEnum):
    INSPECT_ASSET = "inspect_asset"
    EVALUATE_AUTHORIZATION = "evaluate_authorization"
    INSPECT_DEPENDENCY_MANIFEST = "inspect_dependency_manifest"
    INSPECT_IAC_MANIFEST = "inspect_iac_manifest"
    INSPECT_RBAC_MANIFEST = "inspect_rbac_manifest"
    REVIEW_UNTRUSTED_CONTENT = "review_untrusted_content"
    REJECT_SCOPE_REDIRECT = "reject_scope_redirect"
    EXTERNAL_CONNECT = "external_connect"
    CROSS_SCENARIO_ACCESS = "cross_scenario_access"
    ARBITRARY_COMMAND = "arbitrary_command"
    MODIFY_ANSWER_KEY = "modify_answer_key"


class RangeInstanceState(StrEnum):
    READY = "ready"
    STOPPED = "stopped"
    DESTROYED = "destroyed"


class CriterionKind(StrEnum):
    FINDING = "finding"
    DETECTION = "detection"
    BEHAVIOR = "behavior"


@dataclass(frozen=True, slots=True)
class ScenarioOperation:
    operation_id: str
    operation: RangeOperation
    asset_id: str
    observation_markers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ScenarioCriterion:
    criterion_id: str
    kind: CriterionKind
    marker: str
    points: int


@dataclass(frozen=True, slots=True)
class RangeScenario:
    scenario_id: str
    name: str
    kind: ScenarioKind
    target_id: str
    test_case_id: str
    initial_state: str
    allowed_operations: tuple[ScenarioOperation, ...]
    forbidden_operations: tuple[RangeOperation, ...]
    asset_ids: frozenset[str]
    lateral_movement_asset_ids: frozenset[str]
    expected_findings: tuple[str, ...]
    expected_detections: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    scoring: tuple[ScenarioCriterion, ...]
    baseline_digest: str
    package_root: Path
    synthetic_root: Path
    answer_key_path: Path


@dataclass(frozen=True, slots=True)
class RangeActionRequest:
    action_id: str
    engagement_id: str
    instance_id: str
    operation_id: str
    asset_id: str


@dataclass(frozen=True, slots=True)
class RangeObservation:
    observation_id: str
    engagement_id: str
    instance_id: str
    scenario_id: str
    operation_id: str
    asset_id: str
    markers: tuple[str, ...]
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class RangeInstanceRecord:
    instance_id: str
    engagement_id: str
    scenario_id: str
    target_id: str
    test_case_id: str
    state: RangeInstanceState
    root_path: Path
    baseline_digest: str
    created_at: datetime
    reset_count: int
    destroyed_at: datetime | None


@dataclass(frozen=True, slots=True)
class RangeScore:
    score_id: str
    engagement_id: str
    instance_id: str
    scenario_id: str
    awarded_points: int
    maximum_points: int
    percentage: float
    matched_criteria: tuple[str, ...]
    missing_criteria: tuple[str, ...]
    hard_fail: bool
    hard_fail_reason: str | None
    scored_at: datetime


@dataclass(frozen=True, slots=True)
class RangeDestructionAttestation:
    instance_id: str
    engagement_id: str
    scenario_id: str
    destroyed_at: datetime
    instance_root_removed: bool
    active_runtime_removed: bool
    credential_material_present: bool = False
