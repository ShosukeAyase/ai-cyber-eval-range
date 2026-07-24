import pytest

from cyber_eval.domain import ActionClass, DecisionReason, PolicyDecision, ToolId
from cyber_eval.errors import ExecutionDisabledError
from cyber_eval.gateway import NonExecutableToolGateway
from cyber_eval.policy import FailClosedPolicyEngine
from cyber_eval.stubs import StaticApprovalRepository, StaticScopeRegistry
from tests.harness.factories import safe_facts, static_request, valid_approval


def gateway(*, in_scope: bool = True, approvals=None, engine=None):
    entries = frozenset({("eng-design-demo", "tgt-web-demo")}) if in_scope else frozenset()
    return NonExecutableToolGateway(
        scope_registry=StaticScopeRegistry(entries),
        approval_repository=StaticApprovalRepository(approvals or {}),
        policy_engine=engine or FailClosedPolicyEngine(),
    )


def test_read_only_in_scope_request_is_allowed():
    decision = gateway().authorize(static_request(), safe_facts())
    assert decision.allowed is True
    assert decision.reason is DecisionReason.ALLOW


def test_out_of_scope_target_is_rejected():
    decision = gateway(in_scope=False).authorize(static_request(), safe_facts())
    assert decision.allowed is False
    assert decision.reason is DecisionReason.TARGET_OUT_OF_SCOPE


def test_unapproved_dangerous_action_is_rejected():
    request = static_request(
        action_class=ActionClass.PATCH_VALIDATION,
        tool_id=ToolId.VALIDATE_PATCH,
    )
    decision = gateway().authorize(request, safe_facts())
    assert decision.allowed is False
    assert decision.reason is DecisionReason.APPROVAL_REQUIRED


def test_independently_approved_dangerous_action_is_allowed():
    request = static_request(
        action_class=ActionClass.PATCH_VALIDATION,
        tool_id=ToolId.VALIDATE_PATCH,
    )
    approval = valid_approval()
    approvals = {("eng-design-demo", "tgt-web-demo", ActionClass.PATCH_VALIDATION): approval}
    decision = gateway(approvals=approvals).authorize(request, safe_facts())
    assert decision.allowed is True


def test_policy_engine_unavailable_fails_closed():
    engine = FailClosedPolicyEngine(available=False)
    decision = gateway(engine=engine).authorize(static_request(), safe_facts())
    assert decision.allowed is False
    assert decision.reason is DecisionReason.POLICY_UNAVAILABLE


def test_policy_engine_exception_fails_closed():
    class RaisingEngine:
        version = "policy-raising-stub"

        def evaluate(self, request, context):
            del request, context
            raise RuntimeError("synthetic policy failure")

    decision = gateway(engine=RaisingEngine()).authorize(static_request(), safe_facts())
    assert decision == PolicyDecision(
        allowed=False,
        reason=DecisionReason.POLICY_EVALUATION_ERROR,
        policy_version="policy-raising-stub",
    )


def test_action_class_mismatch_is_rejected():
    request = static_request(
        action_class=ActionClass.SAFE_TEST,
        tool_id=ToolId.RUN_STATIC_ANALYSIS,
    )
    decision = gateway().authorize(request, safe_facts())
    assert decision.allowed is False
    assert decision.reason is DecisionReason.ACTION_CLASS_MISMATCH


def test_dispatch_is_permanently_disabled_in_phase_02():
    with pytest.raises(ExecutionDisabledError):
        gateway().dispatch(static_request())
