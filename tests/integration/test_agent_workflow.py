from __future__ import annotations

from cyber_eval.agent import AgentRole, AgentRunState, AgentTurnDisposition
from cyber_eval.domain import ToolId
from tests.harness.agent import (
    APPROVAL_ID,
    EVIDENCE_ID,
    approved_agent_app,
    finding,
    output_document,
    run_request,
    static_tool_proposal,
)
from tests.harness.control_plane import ENGAGEMENT_ID, OPERATOR_ID


def test_agent_tool_selection_flows_only_through_policy_and_tool_gateway() -> None:
    first = output_document(
        disposition=AgentTurnDisposition.PROPOSE_TOOLS,
        tool_proposals=[static_tool_proposal()],
    )
    final = output_document(findings=[finding()])
    app, agent, model = approved_agent_app([first, final])
    result = agent.run(OPERATOR_ID, APPROVAL_ID, run_request())
    assert result.state is AgentRunState.COMPLETED
    assert result.model_invocations == 2
    assert result.tool_invocations == 1
    assert app.policy.evaluation_count == 1
    assert app.tool_gateway.invocation_count == 1
    assert model.inputs[1].tool_receipts[0].allowed is True
    assert result.final_turn is not None
    assert result.final_turn.findings[0].evidence_object_ids == (EVIDENCE_ID,)
    assert result.scope_violation_rate == 0.0
    app.close(ENGAGEMENT_ID)


def test_same_denied_tool_request_cannot_repeat_without_bound() -> None:
    proposal = static_tool_proposal(
        tool_id=ToolId.VALIDATE_PATCH,
        action_class="patch_validation",
    )
    repeated = output_document(
        role=AgentRole.SELECT_APPROVED_TOOLS,
        disposition=AgentTurnDisposition.PROPOSE_TOOLS,
        tool_proposals=[proposal],
    )
    app, agent, _ = approved_agent_app([repeated, repeated])
    result = agent.run(
        OPERATOR_ID,
        APPROVAL_ID,
        run_request(
            role=AgentRole.SELECT_APPROVED_TOOLS,
            allowed_tools=(ToolId.VALIDATE_PATCH,),
            max_repeated_failures=2,
        ),
    )
    assert result.state is AgentRunState.BLOCKED
    assert result.tool_invocations == 2
    assert "repeated" in (result.terminal_reason or "")
    assert app.policy.evaluation_count == 2
    app.close(ENGAGEMENT_ID)


def test_agent_run_state_changes_are_bound_to_consumed_approval_and_audit() -> None:
    app, agent, _ = approved_agent_app([output_document()])
    result = agent.run(OPERATOR_ID, APPROVAL_ID, run_request())
    assert result.state is AgentRunState.COMPLETED
    approval = app.approvals.get(ENGAGEMENT_ID, OPERATOR_ID, APPROVAL_ID)
    assert approval.state.value == "consumed"
    events = app.audit.list_events(ENGAGEMENT_ID, OPERATOR_ID)
    start = [event for event in events if event.operation == "agent.run.start"]
    finish = [event for event in events if event.operation == "agent.run.finish"]
    assert len(start) == 1 and start[0].approval_id == APPROVAL_ID
    assert len(finish) == 1 and finish[0].approval_id == APPROVAL_ID
    app.close(ENGAGEMENT_ID)
