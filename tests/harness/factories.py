"""Synthetic test factories; no external systems or credentials."""

from cyber_eval.domain import (
    ActionClass,
    ApprovalEvidence,
    AuthorizationFacts,
    ToolId,
    ToolRequest,
)


def safe_facts(**overrides: bool) -> AuthorizationFacts:
    values = {
        "manifest_valid": True,
        "roe_valid": True,
        "policy_version_current": True,
        "test_case_allowed": True,
        "within_limits": True,
        "destination_matches": True,
        "emergency_stop_active": False,
    }
    values.update(overrides)
    return AuthorizationFacts(**values)


def static_request(
    *,
    target_id: str = "tgt-web-demo",
    action_class: ActionClass = ActionClass.READ_ONLY_ANALYSIS,
    tool_id: ToolId = ToolId.RUN_STATIC_ANALYSIS,
) -> ToolRequest:
    return ToolRequest(
        request_id="req-test-demo",
        engagement_id="eng-design-demo",
        target_id=target_id,
        test_case_id="tc-static-sast",
        action_class=action_class,
        tool_id=tool_id,
    )


def valid_approval(
    *,
    target_id: str = "tgt-web-demo",
    action_class: ActionClass = ActionClass.PATCH_VALIDATION,
) -> ApprovalEvidence:
    return ApprovalEvidence(
        approval_id="apr-design-demo",
        valid=True,
        independent=True,
        unexpired=True,
        target_id=target_id,
        action_class=action_class,
    )
