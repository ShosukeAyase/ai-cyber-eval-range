"""Pure, local, fail-closed policy stub; not a production Policy Engine."""

from __future__ import annotations

from cyber_eval.domain import (
    ActionClass,
    DecisionReason,
    PolicyContext,
    PolicyDecision,
    ToolId,
    ToolRequest,
)

DANGEROUS_ACTIONS = frozenset(
    {
        ActionClass.STATE_CHANGE,
        ActionClass.CREDENTIALED_TEST,
        ActionClass.POC_VALIDATION,
        ActionClass.PATCH_VALIDATION,
        ActionClass.RANGE_RESET,
        ActionClass.ENGAGEMENT_TERMINATION,
    }
)

TOOL_ACTION_CLASS = {
    ToolId.RUN_STATIC_ANALYSIS: ActionClass.READ_ONLY_ANALYSIS,
    ToolId.RUN_SAFE_NETWORK_DISCOVERY: ActionClass.SAFE_DISCOVERY,
    ToolId.RUN_WEB_TEST: ActionClass.SAFE_TEST,
    ToolId.REQUEST_POC_VALIDATION: ActionClass.POC_VALIDATION,
    ToolId.COLLECT_EVIDENCE: ActionClass.READ_ONLY_ANALYSIS,
    ToolId.PROPOSE_PATCH: ActionClass.READ_ONLY_ANALYSIS,
    ToolId.VALIDATE_PATCH: ActionClass.PATCH_VALIDATION,
    ToolId.RESET_RANGE: ActionClass.RANGE_RESET,
    ToolId.TERMINATE_ENGAGEMENT: ActionClass.ENGAGEMENT_TERMINATION,
}


class FailClosedPolicyEngine:
    """Deterministic contract stub with no I/O, credentials, or execution hooks."""

    def __init__(self, *, available: bool = True, version: str = "policy-skeleton-0.2") -> None:
        self._available = available
        self._version = version

    @property
    def version(self) -> str:
        return self._version

    def evaluate(self, request: ToolRequest, context: PolicyContext) -> PolicyDecision:
        if not self._available:
            return self._deny(DecisionReason.POLICY_UNAVAILABLE)
        if TOOL_ACTION_CLASS.get(request.tool_id) is not request.action_class:
            return self._deny(DecisionReason.ACTION_CLASS_MISMATCH)

        facts = context.facts
        ordered_checks = (
            (facts.manifest_valid, DecisionReason.MANIFEST_INVALID),
            (facts.roe_valid, DecisionReason.ROE_INVALID),
            (facts.policy_version_current, DecisionReason.POLICY_VERSION_STALE),
            (context.target_in_scope, DecisionReason.TARGET_OUT_OF_SCOPE),
            (facts.test_case_allowed, DecisionReason.TEST_CASE_NOT_ALLOWED),
            (facts.within_limits, DecisionReason.LIMIT_EXCEEDED),
            (facts.destination_matches, DecisionReason.DESTINATION_MISMATCH),
            (not facts.emergency_stop_active, DecisionReason.EMERGENCY_STOP_ACTIVE),
        )
        for condition, reason in ordered_checks:
            if not condition:
                return self._deny(reason)

        if request.action_class in DANGEROUS_ACTIONS:
            approval = context.approval
            if approval is None:
                return self._deny(DecisionReason.APPROVAL_REQUIRED)
            if not approval.valid:
                return self._deny(DecisionReason.APPROVAL_INVALID)
            if not approval.independent:
                return self._deny(DecisionReason.APPROVAL_NOT_INDEPENDENT)
            if not approval.unexpired:
                return self._deny(DecisionReason.APPROVAL_EXPIRED)
            if (
                approval.target_id != request.target_id
                or approval.action_class is not request.action_class
            ):
                return self._deny(DecisionReason.APPROVAL_SCOPE_MISMATCH)

        return PolicyDecision(True, DecisionReason.ALLOW, self.version)

    def _deny(self, reason: DecisionReason) -> PolicyDecision:
        return PolicyDecision(False, reason, self.version)
