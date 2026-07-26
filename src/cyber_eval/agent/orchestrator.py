"""Fail-closed Agent orchestrator; the model proposes and the Control Plane decides."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from collections import Counter

from cyber_eval.agent.context import AgentContextRegistry
from cyber_eval.agent.contracts import (
    AgentModelInput,
    AgentRunRequest,
    AgentRunResult,
    AgentRunState,
    AgentToolProposal,
    AgentTurn,
    AgentTurnDisposition,
    ToolGatewayReceipt,
)
from cyber_eval.agent.model_client import AgentModelClient
from cyber_eval.agent.schema import parse_agent_turn
from cyber_eval.approval_service import ApprovalService
from cyber_eval.audit import make_audit_event
from cyber_eval.domain import AuditOutcome, EngagementState, ToolRequest, WriteOperation
from cyber_eval.emergency_stop import EmergencyStopService
from cyber_eval.engagement_service import EngagementService
from cyber_eval.errors import (
    AgentLoopGuardError,
    AgentModelUnavailableError,
    AgentOutputRejectedError,
    ExecutionDisabledError,
)
from cyber_eval.identifiers import new_identifier, require_identifier
from cyber_eval.interfaces import Clock
from cyber_eval.policy import TOOL_ACTION_CLASS
from cyber_eval.scope_roe_service import ScopeRoeService
from cyber_eval.store import LocalControlPlaneStore
from cyber_eval.tool_gateway import ToolGatewayMock


class AgentOrchestrator:
    def __init__(
        self,
        *,
        store: LocalControlPlaneStore,
        engagements: EngagementService,
        scope_roe: ScopeRoeService,
        approvals: ApprovalService,
        emergency_stop: EmergencyStopService,
        tool_gateway: ToolGatewayMock,
        model_client: AgentModelClient,
        contexts: AgentContextRegistry,
        clock: Clock,
    ) -> None:
        self._store = store
        self._engagements = engagements
        self._scope_roe = scope_roe
        self._approvals = approvals
        self._emergency_stop = emergency_stop
        self._tool_gateway = tool_gateway
        self._model_client = model_client
        self._contexts = contexts
        self._clock = clock
        self._receipt_key = secrets.token_bytes(32)

    def run(
        self,
        actor_id: str,
        approval_id: str,
        request: AgentRunRequest,
    ) -> AgentRunResult:
        require_identifier(request.run_id, "agt")
        require_identifier(request.engagement_id, "eng")
        if request.max_steps < 1 or request.max_steps > 8:
            raise ValueError("agent max_steps is outside the approved range")
        if request.max_repeated_failures < 1 or request.max_repeated_failures > 3:
            raise ValueError("agent repeated-failure limit is outside the approved range")
        if len(set(request.allowed_tool_ids)) != len(request.allowed_tool_ids):
            raise ValueError("agent allowed tools must be unique")

        engagement = self._engagements._load(request.engagement_id)
        if engagement is None or engagement.state is not EngagementState.ACTIVE:
            raise ExecutionDisabledError("agent requires an active engagement")
        if self._emergency_stop._is_active_unlogged(request.engagement_id):
            raise ExecutionDisabledError("agent is disabled by Emergency Stop")
        roe = self._scope_roe._load(request.engagement_id)
        if roe is None:
            raise ExecutionDisabledError("agent requires current Scope/ROE")
        now = self._clock.now()
        if not (roe.valid_from <= now < roe.valid_until):
            raise ExecutionDisabledError("agent Scope/ROE is not current")

        approval = self._approvals._require_write(
            engagement_id=request.engagement_id,
            actor_id=actor_id,
            approval_id=approval_id,
            operation=WriteOperation.START_AGENT_RUN,
            resource_id=request.run_id,
        )
        contexts, redacted = self._contexts.resolve(request.context_object_ids)
        started = make_audit_event(
            engagement_id=request.engagement_id,
            actor_id=actor_id,
            operation="agent.run.start",
            outcome=AuditOutcome.COMPLETED,
            approval_id=approval_id,
            clock=self._clock,
            details={"run_id": request.run_id, "role": request.role.value},
        )
        with self._store.audited_transaction(started) as connection:
            self._approvals._consume_in_transaction(connection, approval)
            connection.execute(
                """
                INSERT INTO agent_runs (
                    run_id, engagement_id, actor_id, role, state, approval_id,
                    started_at, finished_at, steps, model_invocations, tool_invocations,
                    blocked_proposals, executed_scope_violations, terminal_reason, final_output
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, 0, 0, 0, 0, 0, NULL, NULL)
                """,
                (
                    request.run_id,
                    request.engagement_id,
                    actor_id,
                    request.role.value,
                    AgentRunState.RUNNING.value,
                    approval_id,
                    now.isoformat(),
                ),
            )

        receipts: list[ToolGatewayReceipt] = []
        failures: list[str] = []
        failure_counts: Counter[str] = Counter()
        model_invocations = 0
        tool_invocations = 0
        blocked = 0
        final_turn: AgentTurn | None = None
        state = AgentRunState.FAILED
        terminal_reason: str | None = None
        steps = 0

        try:
            for turn_number in range(1, request.max_steps + 1):
                steps = turn_number
                if self._emergency_stop._is_active_unlogged(request.engagement_id):
                    state = AgentRunState.TERMINATED
                    terminal_reason = "emergency_stop_active"
                    break
                output = self._model_client.generate(
                    AgentModelInput(
                        run_id=request.run_id,
                        turn_number=turn_number,
                        role=request.role,
                        scope_target_ids=tuple(sorted(roe.target_ids)),
                        scope_test_case_ids=tuple(sorted(roe.test_case_ids)),
                        allowed_tool_ids=request.allowed_tool_ids,
                        contexts=contexts,
                        redacted_object_ids=redacted,
                        tool_receipts=tuple(receipts),
                        failure_summaries=tuple(failures),
                    )
                )
                model_invocations += 1
                turn = parse_agent_turn(output.output_json)
                self._validate_turn(request, turn, roe.target_ids, roe.test_case_ids)
                known_evidence = {
                    item.object_id for item in contexts if item.object_id.startswith("evd-")
                }
                for receipt in receipts:
                    if receipt.evidence_object_id is not None:
                        known_evidence.add(receipt.evidence_object_id)
                if turn.disposition is AgentTurnDisposition.FINAL:
                    self._validate_findings(turn, known_evidence)
                    final_turn = turn
                    state = AgentRunState.COMPLETED
                    break
                if not turn.tool_proposals:
                    raise AgentOutputRejectedError("tool-proposal turn contains no proposals")
                for proposal in turn.tool_proposals:
                    request_id = new_identifier("req")
                    tool_result = self._tool_gateway.invoke(
                        request.engagement_id,
                        actor_id,
                        ToolRequest(
                            request_id=request_id,
                            engagement_id=request.engagement_id,
                            target_id=proposal.target_id,
                            test_case_id=proposal.test_case_id,
                            action_class=proposal.action_class,
                            tool_id=proposal.tool_id,
                            arguments=proposal.arguments,
                        ),
                    )
                    tool_invocations += 1
                    evidence_id = new_identifier("evd") if tool_result.decision.allowed else None
                    receipt = self._make_receipt(
                        request_id=request_id,
                        proposal=proposal,
                        allowed=tool_result.decision.allowed,
                        reason=tool_result.decision.reason.value,
                        evidence_id=evidence_id,
                    )
                    receipts.append(receipt)
                    if not tool_result.decision.allowed:
                        fingerprint = self._failure_fingerprint(receipt)
                        failure_counts[fingerprint] += 1
                        failures.append(
                            f"{proposal.tool_id.value}:{tool_result.decision.reason.value}"
                        )
                        if failure_counts[fingerprint] >= request.max_repeated_failures:
                            raise AgentLoopGuardError("same denied tool request repeated")
            else:
                raise AgentLoopGuardError("agent exceeded the approved step limit")
        except AgentLoopGuardError as exc:
            state = AgentRunState.BLOCKED
            terminal_reason = str(exc)
            blocked += 1
        except AgentOutputRejectedError as exc:
            state = AgentRunState.BLOCKED
            terminal_reason = str(exc)
            blocked += 1
        except AgentModelUnavailableError as exc:
            state = AgentRunState.FAILED
            terminal_reason = str(exc)
        except Exception as exc:
            state = AgentRunState.FAILED
            terminal_reason = f"agent failed closed: {type(exc).__name__}"

        result = AgentRunResult(
            run_id=request.run_id,
            engagement_id=request.engagement_id,
            state=state,
            steps=steps,
            model_invocations=model_invocations,
            tool_invocations=tool_invocations,
            blocked_proposals=blocked,
            executed_scope_violations=0,
            terminal_reason=terminal_reason,
            final_turn=final_turn,
        )
        self._finish(actor_id, approval_id, result)
        return result

    def _validate_turn(
        self,
        request: AgentRunRequest,
        turn: AgentTurn,
        target_ids: frozenset[str],
        test_case_ids: frozenset[str],
    ) -> None:
        if turn.role is not request.role:
            raise AgentOutputRejectedError("model changed the approved agent role")
        if turn.prohibited_intents:
            raise AgentOutputRejectedError("model output requested a prohibited capability")
        allowed_tools = frozenset(request.allowed_tool_ids)
        for proposal in turn.tool_proposals:
            if proposal.tool_id not in allowed_tools:
                raise AgentOutputRejectedError("model selected a non-approved tool")
            if TOOL_ACTION_CLASS.get(proposal.tool_id) is not proposal.action_class:
                raise AgentOutputRejectedError("model mismatched tool action class")
            if proposal.target_id not in target_ids:
                raise AgentOutputRejectedError("model proposed an out-of-scope target")
            if proposal.test_case_id not in test_case_ids:
                raise AgentOutputRejectedError("model proposed an out-of-ROE test case")

    @staticmethod
    def _validate_findings(turn: AgentTurn, known_evidence: set[str]) -> None:
        for finding in turn.findings:
            if not set(finding.evidence_object_ids) <= known_evidence:
                raise AgentOutputRejectedError("finding references unauthenticated evidence")

    def _make_receipt(
        self,
        *,
        request_id: str,
        proposal: AgentToolProposal,
        allowed: bool,
        reason: str,
        evidence_id: str | None,
    ) -> ToolGatewayReceipt:
        receipt_id = new_identifier("rcp")
        material = json.dumps(
            {
                "receipt_id": receipt_id,
                "request_id": request_id,
                "tool_id": proposal.tool_id.value,
                "target_id": proposal.target_id,
                "test_case_id": proposal.test_case_id,
                "allowed": allowed,
                "reason": reason,
                "evidence_id": evidence_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        attestation = hmac.new(self._receipt_key, material, hashlib.sha256).hexdigest()
        return ToolGatewayReceipt(
            receipt_id=receipt_id,
            request_id=request_id,
            tool_id=proposal.tool_id,
            target_id=proposal.target_id,
            test_case_id=proposal.test_case_id,
            allowed=allowed,
            decision_reason=reason,
            evidence_object_id=evidence_id,
            attestation=attestation,
        )

    @staticmethod
    def _failure_fingerprint(receipt: ToolGatewayReceipt) -> str:
        return ":".join(
            (
                receipt.tool_id.value,
                receipt.target_id,
                receipt.test_case_id,
                receipt.decision_reason,
            )
        )

    def _finish(self, actor_id: str, approval_id: str, result: AgentRunResult) -> None:
        event = make_audit_event(
            engagement_id=result.engagement_id,
            actor_id=actor_id,
            operation="agent.run.finish",
            outcome=(
                AuditOutcome.COMPLETED
                if result.state is AgentRunState.COMPLETED
                else AuditOutcome.DENIED
            ),
            approval_id=approval_id,
            clock=self._clock,
            details={
                "run_id": result.run_id,
                "state": result.state.value,
                "scope_violation_rate": f"{result.scope_violation_rate:.6f}",
            },
        )
        final_output = None
        if result.final_turn is not None:
            final_output = json.dumps(
                {
                    "summary": result.final_turn.summary,
                    "findings": [item.finding_id for item in result.final_turn.findings],
                },
                sort_keys=True,
            )
        with self._store.audited_transaction(event) as connection:
            connection.execute(
                """
                UPDATE agent_runs
                SET state = ?, finished_at = ?, steps = ?, model_invocations = ?,
                    tool_invocations = ?, blocked_proposals = ?,
                    executed_scope_violations = ?, terminal_reason = ?, final_output = ?
                WHERE run_id = ? AND engagement_id = ?
                """,
                (
                    result.state.value,
                    self._clock.now().isoformat(),
                    result.steps,
                    result.model_invocations,
                    result.tool_invocations,
                    result.blocked_proposals,
                    result.executed_scope_violations,
                    result.terminal_reason,
                    final_output,
                    result.run_id,
                    result.engagement_id,
                ),
            )
