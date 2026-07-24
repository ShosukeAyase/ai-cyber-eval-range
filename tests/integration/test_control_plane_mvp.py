from __future__ import annotations

from datetime import timedelta

import pytest

from cyber_eval.domain import (
    ActionClass,
    ApprovalState,
    CredentialPurpose,
    DecisionReason,
    MockToolStatus,
    ModelPurpose,
    ModelRequest,
    ResourceScope,
    ToolId,
    ToolRequest,
    WriteOperation,
)
from cyber_eval.errors import AuditUnavailableError, SelfApprovalError
from tests.harness.control_plane import (
    APPROVER_ID,
    ENGAGEMENT_ID,
    NOW,
    OPERATOR_ID,
    TARGET_ID,
    TEST_CASE_ID,
    new_app,
)


def tool_request(
    *,
    request_id: str = "req-control-read",
    target_id: str = TARGET_ID,
    action_class: ActionClass = ActionClass.READ_ONLY_ANALYSIS,
    tool_id: ToolId = ToolId.RUN_STATIC_ANALYSIS,
) -> ToolRequest:
    return ToolRequest(
        request_id=request_id,
        engagement_id=ENGAGEMENT_ID,
        target_id=target_id,
        test_case_id=TEST_CASE_ID,
        action_class=action_class,
        tool_id=tool_id,
    )


def test_scope_deviation_is_denied() -> None:
    app = new_app()
    result = app.tool_gateway.invoke(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        tool_request(target_id="tgt-outside-scope"),
    )
    assert result.status is MockToolStatus.DENIED
    assert result.decision.reason is DecisionReason.TARGET_OUT_OF_SCOPE
    app.close(ENGAGEMENT_ID)


def test_expired_roe_is_denied() -> None:
    app = new_app()
    app.clock.advance(timedelta(days=2))
    result = app.tool_gateway.invoke(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        tool_request(request_id="req-expired-roe"),
    )
    assert result.status is MockToolStatus.DENIED
    assert result.decision.reason is DecisionReason.ROE_EXPIRED
    app.close(ENGAGEMENT_ID)


def test_self_approval_is_rejected() -> None:
    app = new_app()
    approval_id = "apr-self-denied"
    app.approvals.request(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        app.bootstrap.operator_admin_approval_id,
        approval_id,
        frozenset({WriteOperation.MOCK_TOOL_WRITE}),
        ResourceScope.RESOURCE,
        TARGET_ID,
        NOW + timedelta(hours=1),
        ActionClass.RANGE_RESET,
    )
    with pytest.raises(SelfApprovalError):
        app.approvals.approve(
            ENGAGEMENT_ID,
            OPERATOR_ID,
            app.bootstrap.operator_admin_approval_id,
            approval_id,
        )
    pending = app.approvals.get(ENGAGEMENT_ID, APPROVER_ID, approval_id)
    assert pending.state is ApprovalState.REQUESTED
    app.close(ENGAGEMENT_ID)


def test_audit_failure_rolls_back_state_change() -> None:
    from cyber_eval.clock import FixedClock
    from cyber_eval.control_plane import ControlPlaneMvp

    clock = FixedClock(NOW)
    app = ControlPlaneMvp.local_dev(
        engagement_id=ENGAGEMENT_ID,
        operator_id=OPERATOR_ID,
        approver_id=APPROVER_ID,
        bootstrap_expires_at=NOW + timedelta(days=30),
        clock=clock,
    )
    app.store.fail_audit_writes = True
    with pytest.raises(AuditUnavailableError):
        app.engagements.create(
            ENGAGEMENT_ID,
            OPERATOR_ID,
            app.bootstrap.operator_admin_approval_id,
            NOW + timedelta(days=7),
        )
    assert app.engagements._load(ENGAGEMENT_ID) is None
    app.store.fail_audit_writes = False
    admin = app.approvals.get(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        app.bootstrap.operator_admin_approval_id,
    )
    assert admin.uses == 0
    app.close(ENGAGEMENT_ID)


def test_audit_failure_prevents_model_mock_invocation() -> None:
    app = new_app()
    app.store.fail_audit_writes = True
    with pytest.raises(AuditUnavailableError):
        app.model_gateway.generate(
            ENGAGEMENT_ID,
            OPERATOR_ID,
            ModelRequest(
                request_id="req-model-audit-fail",
                purpose=ModelPurpose.ANALYZE_EVIDENCE,
                prompt_template_id="tmpl-audit-test",
                context_object_ids=("evd-local-evidence",),
            ),
        )
    assert app.model_gateway.invocation_count == 0
    app.store.fail_audit_writes = False
    app.close(ENGAGEMENT_ID)


def test_emergency_stop_is_independent_and_blocks_policy() -> None:
    app = new_app()
    stop = app.emergency_stop.activate(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        app.bootstrap.operator_admin_approval_id,
        "operator kill switch",
    )
    assert stop.active is True
    result = app.tool_gateway.invoke(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        tool_request(request_id="req-after-stop"),
    )
    assert result.decision.reason is DecisionReason.EMERGENCY_STOP_ACTIVE
    assert app.emergency_stop.is_active(ENGAGEMENT_ID, APPROVER_ID) is True
    app.close(ENGAGEMENT_ID)


def test_policy_unavailability_fails_closed() -> None:
    app = new_app(policy_available=False)
    result = app.tool_gateway.invoke(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        tool_request(request_id="req-policy-down"),
    )
    assert result.decision.reason is DecisionReason.POLICY_UNAVAILABLE
    app.close(ENGAGEMENT_ID)


def test_control_plane_mvp_integration_flow() -> None:
    app = new_app()
    model = app.model_gateway.generate(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        ModelRequest(
            request_id="req-model-integration",
            purpose=ModelPurpose.PROPOSE_TEST_PLAN,
            prompt_template_id="tmpl-local-plan",
            context_object_ids=("repo-local-source",),
        ),
    )
    assert model.model_profile == "deterministic-local-mock"

    read_result = app.tool_gateway.invoke(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        tool_request(request_id="req-read-integration"),
    )
    assert read_result.status is MockToolStatus.ACCEPTED_NO_EXECUTION

    tool_approval_id = "apr-range-reset"
    app.approvals.request(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        app.bootstrap.operator_admin_approval_id,
        tool_approval_id,
        frozenset({WriteOperation.MOCK_TOOL_WRITE}),
        ResourceScope.RESOURCE,
        TARGET_ID,
        NOW + timedelta(hours=1),
        ActionClass.RANGE_RESET,
    )
    app.approvals.approve(
        ENGAGEMENT_ID,
        APPROVER_ID,
        app.bootstrap.approver_admin_approval_id,
        tool_approval_id,
    )
    write_result = app.tool_gateway.invoke(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        tool_request(
            request_id="req-reset-mock",
            action_class=ActionClass.RANGE_RESET,
            tool_id=ToolId.RESET_RANGE,
        ),
    )
    assert write_result.status is MockToolStatus.ACCEPTED_NO_EXECUTION
    assert app.approvals.get(
        ENGAGEMENT_ID,
        APPROVER_ID,
        tool_approval_id,
    ).state is ApprovalState.CONSUMED

    credential_approval_id = "apr-credential-reference"
    app.approvals.request(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        app.bootstrap.operator_admin_approval_id,
        credential_approval_id,
        frozenset({WriteOperation.ISSUE_CREDENTIAL_REFERENCE}),
        ResourceScope.RESOURCE,
        TARGET_ID,
        NOW + timedelta(hours=1),
        ActionClass.CREDENTIALED_TEST,
    )
    app.approvals.approve(
        ENGAGEMENT_ID,
        APPROVER_ID,
        app.bootstrap.approver_admin_approval_id,
        credential_approval_id,
    )
    reference = app.credential_broker.issue_reference(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        credential_approval_id,
        TARGET_ID,
        CredentialPurpose.SYNTHETIC_TARGET_AUTH,
        900,
    )
    assert reference.target_id == TARGET_ID
    assert not hasattr(reference, "value")

    events = app.audit.list_events(ENGAGEMENT_ID, APPROVER_ID)
    operations = {event.operation for event in events}
    assert {
        "engagement.create",
        "scope_roe.register",
        "engagement.activate",
        "model_gateway.generate_mock",
        "tool_gateway.invoke_mock",
        "credential_broker.issue_mock_reference",
    } <= operations
    app.close(ENGAGEMENT_ID)
