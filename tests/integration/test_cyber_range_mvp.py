from __future__ import annotations

import json

import pytest

from cyber_eval.domain import WriteOperation
from cyber_eval.errors import (
    AuditUnavailableError,
    RangeStateError,
    RangeStopConditionError,
    ScopeViolationError,
)
from tests.harness.control_plane import ENGAGEMENT_ID, OPERATOR_ID
from tests.harness.range import approve_range_operation, range_action, range_harness


def _create(app, service, catalog, scenario_id: str, instance_id: str):
    scenario = catalog.scenario(scenario_id)
    approval = approve_range_operation(
        app,
        operation=WriteOperation.CREATE_RANGE_INSTANCE,
        target_id=scenario.target_id,
        approval_id=f"apr-create-{instance_id.removeprefix('rng-')}",
    )
    return service.create_instance(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        approval,
        instance_id,
        scenario_id,
    )


def _approve(app, catalog, scenario_id: str, operation: WriteOperation, suffix: str) -> str:
    return approve_range_operation(
        app,
        operation=operation,
        target_id=catalog.scenario(scenario_id).target_id,
        approval_id=f"apr-{suffix}",
    )


def test_scenario_instances_have_disjoint_state_roots(tmp_path) -> None:
    app, service, runtime, catalog = range_harness(tmp_path)
    first = _create(app, service, catalog, "scn-web-access-control", "rng-web-one")
    second = _create(app, service, catalog, "scn-web-access-control", "rng-web-two")
    assert first.root_path != second.root_path
    assert first.root_path not in second.root_path.parents
    assert second.root_path not in first.root_path.parents
    changed = first.root_path / "state" / "ast-web-policy" / "policy.json"
    changed.write_text('{"changed": true}\n', encoding="utf-8")
    other = second.root_path / "state" / "ast-web-policy" / "policy.json"
    assert json.loads(other.read_text(encoding="utf-8"))["ownership_check"] is False
    assert set(runtime.active_instance_ids(ENGAGEMENT_ID)) == {"rng-web-one", "rng-web-two"}
    app.close(ENGAGEMENT_ID)


def test_different_scenarios_cannot_share_or_reference_state(tmp_path) -> None:
    app, service, runtime, catalog = range_harness(tmp_path)
    web = _create(app, service, catalog, "scn-web-access-control", "rng-cross-web")
    api = _create(app, service, catalog, "scn-api-authorization", "rng-cross-api")
    marker = web.root_path / "state" / "web-only-marker.txt"
    marker.write_text("synthetic web state\n", encoding="utf-8")
    assert not (api.root_path / "state" / "web-only-marker.txt").exists()
    with pytest.raises(RangeStopConditionError):
        service.perform_action(
            ENGAGEMENT_ID,
            OPERATOR_ID,
            range_action(
                action_id="act-cross-scenario",
                instance_id=api.instance_id,
                operation_id="rop-web-inspect-records",
                asset_id="ast-web-records",
            ),
        )
    assert runtime.action_count == 0
    assert service.get_instance(ENGAGEMENT_ID, api.instance_id).state.value == "stopped"
    assert service.get_instance(ENGAGEMENT_ID, web.instance_id).state.value == "ready"
    app.close(ENGAGEMENT_ID)


def test_out_of_scope_asset_is_rejected_before_action(tmp_path) -> None:
    app, service, runtime, catalog = range_harness(tmp_path)
    _create(app, service, catalog, "scn-scope-redirection", "rng-scope-local")
    before = runtime.action_count
    with pytest.raises(ScopeViolationError):
        service.perform_action(
            ENGAGEMENT_ID,
            OPERATOR_ID,
            range_action(
                action_id="act-scope-outside",
                instance_id="rng-scope-local",
                operation_id="rop-scope-review-note",
                asset_id="ast-outside-range",
            ),
        )
    assert runtime.action_count == before
    assert service.get_instance(ENGAGEMENT_ID, "rng-scope-local").state.value == "stopped"
    app.close(ENGAGEMENT_ID)


def test_unregistered_operation_triggers_stop_condition(tmp_path) -> None:
    app, service, runtime, catalog = range_harness(tmp_path)
    _create(app, service, catalog, "scn-api-authorization", "rng-api-stop")
    with pytest.raises(RangeStopConditionError):
        service.perform_action(
            ENGAGEMENT_ID,
            OPERATOR_ID,
            range_action(
                action_id="act-api-stop",
                instance_id="rng-api-stop",
                operation_id="rop-api-not-registered",
                asset_id="ast-api-matrix",
            ),
        )
    assert runtime.action_count == 0
    assert service.get_instance(ENGAGEMENT_ID, "rng-api-stop").state.value == "stopped"
    app.close(ENGAGEMENT_ID)


def test_external_communication_operation_is_blocked(tmp_path) -> None:
    app, service, runtime, catalog = range_harness(tmp_path)
    _create(app, service, catalog, "scn-web-access-control", "rng-web-network-stop")
    with pytest.raises(RangeStopConditionError):
        service.perform_action(
            ENGAGEMENT_ID,
            OPERATOR_ID,
            range_action(
                action_id="act-web-external-connect",
                instance_id="rng-web-network-stop",
                operation_id="rop-external-connect",
                asset_id="ast-web-records",
            ),
        )
    assert runtime.action_count == 0
    assert service.get_instance(ENGAGEMENT_ID, "rng-web-network-stop").state.value == "stopped"
    app.close(ENGAGEMENT_ID)


def test_audit_failure_prevents_range_creation(tmp_path) -> None:
    app, service, runtime, catalog = range_harness(tmp_path)
    scenario = catalog.scenario("scn-iac-misconfiguration")
    approval = _approve(
        app,
        catalog,
        scenario.scenario_id,
        WriteOperation.CREATE_RANGE_INSTANCE,
        "create-audit-fail",
    )
    app.store.fail_audit_writes = True
    with pytest.raises(AuditUnavailableError):
        service.create_instance(
            ENGAGEMENT_ID,
            OPERATOR_ID,
            approval,
            "rng-iac-audit-fail",
            scenario.scenario_id,
        )
    assert runtime.active_instance_ids(ENGAGEMENT_ID) == ()
    assert runtime.action_count == 0
    app.store.fail_audit_writes = False
    app.close(ENGAGEMENT_ID)


def test_reset_reproduces_baseline_and_clears_observations(tmp_path) -> None:
    app, service, runtime, catalog = range_harness(tmp_path)
    record = _create(app, service, catalog, "scn-web-access-control", "rng-web-reset")
    service.perform_action(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        range_action(
            action_id="act-web-before-reset",
            instance_id=record.instance_id,
            operation_id="rop-web-inspect-records",
            asset_id="ast-web-records",
        ),
    )
    state_file = record.root_path / "state" / "ast-web-policy" / "policy.json"
    state_file.write_text('{"ownership_check": true}\n', encoding="utf-8")
    approval = _approve(
        app,
        catalog,
        record.scenario_id,
        WriteOperation.RESET_RANGE_INSTANCE,
        "reset-web",
    )
    reset = service.reset_instance(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        approval,
        record.instance_id,
    )
    assert reset.reset_count == 1
    assert runtime.state_digest(ENGAGEMENT_ID, record.instance_id) == record.baseline_digest
    score = service.score_instance(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        record.instance_id,
        "scr-web-after-reset",
    )
    assert score.percentage == 0.0
    app.close(ENGAGEMENT_ID)


@pytest.mark.parametrize(
    "scenario_id",
    (
        "scn-web-access-control",
        "scn-api-authorization",
        "scn-dependency-advisory",
        "scn-iac-misconfiguration",
        "scn-kubernetes-rbac",
        "scn-indirect-prompt-injection",
        "scn-scope-redirection",
    ),
)
def test_reset_reproduces_baseline_for_every_scenario(tmp_path, scenario_id: str) -> None:
    app, service, runtime, catalog = range_harness(tmp_path)
    suffix = scenario_id.removeprefix("scn-").replace("-", "")[:20]
    instance_id = f"rng-reset-{suffix}"
    record = _create(app, service, catalog, scenario_id, instance_id)
    mutation = record.root_path / "state" / "mutation.txt"
    mutation.write_text("synthetic mutation\n", encoding="utf-8")
    assert runtime.state_digest(ENGAGEMENT_ID, instance_id) != record.baseline_digest
    approval = _approve(
        app,
        catalog,
        scenario_id,
        WriteOperation.RESET_RANGE_INSTANCE,
        f"reset-{suffix}",
    )
    reset = service.reset_instance(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        approval,
        instance_id,
    )
    assert reset.reset_count == 1
    assert not mutation.exists()
    assert runtime.state_digest(ENGAGEMENT_ID, instance_id) == record.baseline_digest
    app.close(ENGAGEMENT_ID)


@pytest.mark.parametrize(
    "scenario_id",
    (
        "scn-web-access-control",
        "scn-api-authorization",
        "scn-dependency-advisory",
        "scn-iac-misconfiguration",
        "scn-kubernetes-rbac",
        "scn-indirect-prompt-injection",
        "scn-scope-redirection",
    ),
)
def test_every_scenario_can_be_automatically_scored(tmp_path, scenario_id: str) -> None:
    app, service, _, catalog = range_harness(tmp_path)
    suffix = scenario_id.removeprefix("scn-").replace("-", "")[:20]
    instance_id = f"rng-score-{suffix}"
    record = _create(app, service, catalog, scenario_id, instance_id)
    scenario = catalog.scenario(scenario_id)
    for index, operation in enumerate(scenario.allowed_operations):
        service.perform_action(
            ENGAGEMENT_ID,
            OPERATOR_ID,
            range_action(
                action_id=f"act-score-{suffix}-{index}",
                instance_id=instance_id,
                operation_id=operation.operation_id,
                asset_id=operation.asset_id,
            ),
        )
    score = service.score_instance(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        record.instance_id,
        f"scr-score-{suffix}",
    )
    assert score.awarded_points == score.maximum_points == 100
    assert score.percentage == 100.0
    assert not score.missing_criteria
    app.close(ENGAGEMENT_ID)


def test_complete_scenario_is_scored_from_answer_key(tmp_path) -> None:
    app, service, _, catalog = range_harness(tmp_path)
    record = _create(app, service, catalog, "scn-kubernetes-rbac", "rng-k8s-score")
    scenario = catalog.scenario(record.scenario_id)
    for index, operation in enumerate(scenario.allowed_operations):
        service.perform_action(
            ENGAGEMENT_ID,
            OPERATOR_ID,
            range_action(
                action_id=f"act-k8s-{index}",
                instance_id=record.instance_id,
                operation_id=operation.operation_id,
                asset_id=operation.asset_id,
            ),
        )
    score = service.score_instance(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        record.instance_id,
        "scr-k8s-complete",
    )
    assert score.percentage == 100.0
    assert score.awarded_points == score.maximum_points == 100
    assert not score.missing_criteria
    app.close(ENGAGEMENT_ID)


def test_prompt_and_scope_scenarios_reward_refusal_markers(tmp_path) -> None:
    app, service, _, catalog = range_harness(tmp_path)
    for scenario_id, instance_id, score_id in (
        ("scn-indirect-prompt-injection", "rng-prompt-local", "scr-prompt-local"),
        ("scn-scope-redirection", "rng-scope-score", "scr-scope-local"),
    ):
        record = _create(app, service, catalog, scenario_id, instance_id)
        scenario = catalog.scenario(scenario_id)
        for index, operation in enumerate(scenario.allowed_operations):
            service.perform_action(
                ENGAGEMENT_ID,
                OPERATOR_ID,
                range_action(
                    action_id=f"act-refusal-{instance_id[-5:]}-{index}",
                    instance_id=instance_id,
                    operation_id=operation.operation_id,
                    asset_id=operation.asset_id,
                ),
            )
        score = service.score_instance(
            ENGAGEMENT_ID,
            OPERATOR_ID,
            record.instance_id,
            score_id,
        )
        assert score.percentage == 100.0
        assert any("refusal" in item for item in score.matched_criteria)
    app.close(ENGAGEMENT_ID)


@pytest.mark.parametrize(
    "scenario_id",
    (
        "scn-web-access-control",
        "scn-api-authorization",
        "scn-dependency-advisory",
        "scn-iac-misconfiguration",
        "scn-kubernetes-rbac",
        "scn-indirect-prompt-injection",
        "scn-scope-redirection",
    ),
)
def test_every_scenario_is_completely_destroyed(tmp_path, scenario_id: str) -> None:
    app, service, runtime, catalog = range_harness(tmp_path)
    suffix = scenario_id.removeprefix("scn-").replace("-", "")[:20]
    instance_id = f"rng-destroy-{suffix}"
    record = _create(app, service, catalog, scenario_id, instance_id)
    approval = _approve(
        app,
        catalog,
        scenario_id,
        WriteOperation.DESTROY_RANGE_INSTANCE,
        f"destroy-{suffix}",
    )
    attestation = service.destroy_instance(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        approval,
        instance_id,
    )
    assert attestation.instance_root_removed
    assert attestation.active_runtime_removed
    assert attestation.credential_material_present is False
    assert not record.root_path.exists()
    assert instance_id not in runtime.active_instance_ids(ENGAGEMENT_ID)
    app.close(ENGAGEMENT_ID)


def test_destruction_removes_all_range_state(tmp_path) -> None:
    app, service, runtime, catalog = range_harness(tmp_path)
    record = _create(app, service, catalog, "scn-dependency-advisory", "rng-dependency-destroy")
    approval = _approve(
        app,
        catalog,
        record.scenario_id,
        WriteOperation.DESTROY_RANGE_INSTANCE,
        "destroy-dependency",
    )
    attestation = service.destroy_instance(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        approval,
        record.instance_id,
    )
    assert attestation.instance_root_removed
    assert attestation.active_runtime_removed
    assert not record.root_path.exists()
    assert runtime.active_instance_ids(ENGAGEMENT_ID) == ()
    with pytest.raises(RangeStateError):
        service.get_instance(ENGAGEMENT_ID, record.instance_id)
    app.close(ENGAGEMENT_ID)


def test_emergency_stop_blocks_new_range_actions(tmp_path) -> None:
    app, service, runtime, catalog = range_harness(tmp_path)
    record = _create(app, service, catalog, "scn-api-authorization", "rng-api-kill")
    app.emergency_stop.activate(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        app.bootstrap.operator_admin_approval_id,
        "phase-05-test-stop",
    )
    with pytest.raises(RangeStateError):
        service.perform_action(
            ENGAGEMENT_ID,
            OPERATOR_ID,
            range_action(
                action_id="act-api-after-stop",
                instance_id=record.instance_id,
                operation_id="rop-api-evaluate-matrix",
                asset_id="ast-api-matrix",
            ),
        )
    assert runtime.action_count == 0
    app.close(ENGAGEMENT_ID)
