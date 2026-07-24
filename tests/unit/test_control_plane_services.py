from __future__ import annotations

import inspect
from datetime import timedelta

import pytest

from cyber_eval.domain import (
    ActionClass,
    DecisionReason,
    ResourceScope,
    ToolId,
    ToolRequest,
    WriteOperation,
)
from cyber_eval.emergency_stop import EmergencyStopService
from cyber_eval.errors import ApprovalRequiredError, InvalidIdentifierError
from tests.harness.control_plane import (
    ENGAGEMENT_ID,
    NOW,
    OPERATOR_ID,
    TARGET_ID,
    TEST_CASE_ID,
    new_app,
)


def test_write_tool_without_approval_is_denied() -> None:
    app = new_app()
    result = app.tool_gateway.invoke(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        ToolRequest(
            request_id="req-unapproved-reset",
            engagement_id=ENGAGEMENT_ID,
            target_id=TARGET_ID,
            test_case_id=TEST_CASE_ID,
            action_class=ActionClass.RANGE_RESET,
            tool_id=ToolId.RESET_RANGE,
        ),
    )
    assert result.decision.reason is DecisionReason.APPROVAL_REQUIRED
    app.close(ENGAGEMENT_ID)


def test_approval_request_requires_admin_approval() -> None:
    app = new_app()
    with pytest.raises(ApprovalRequiredError):
        app.approvals.request(
            ENGAGEMENT_ID,
            OPERATOR_ID,
            "apr-missing-admin",
            "apr-new-write",
            frozenset({WriteOperation.MOCK_TOOL_WRITE}),
            ResourceScope.RESOURCE,
            TARGET_ID,
            NOW + timedelta(hours=1),
            ActionClass.RANGE_RESET,
        )
    app.close(ENGAGEMENT_ID)


def test_model_request_rejects_non_object_context() -> None:
    from cyber_eval.domain import ModelPurpose, ModelRequest

    app = new_app()
    with pytest.raises(InvalidIdentifierError):
        app.model_gateway.generate(
            ENGAGEMENT_ID,
            OPERATOR_ID,
            ModelRequest(
                request_id="req-invalid-context",
                purpose=ModelPurpose.ANALYZE_EVIDENCE,
                prompt_template_id="tmpl-safe-analysis",
                context_object_ids=("https://invalid.example",),
            ),
        )
    app.close(ENGAGEMENT_ID)


def test_emergency_stop_constructor_has_no_model_or_runner_dependency() -> None:
    parameters = inspect.signature(EmergencyStopService.__init__).parameters
    names = set(parameters)
    assert "model" not in names
    assert "model_gateway" not in names
    assert "runner" not in names
    assert "tool_gateway" not in names
