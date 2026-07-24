"""Safe local demonstration with synthetic identifiers and no external I/O."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from cyber_eval.clock import FixedClock
from cyber_eval.control_plane import ControlPlaneMvp
from cyber_eval.domain import (
    ActionClass,
    ModelPurpose,
    ModelRequest,
    ToolId,
    ToolRequest,
)


def main() -> None:
    now = datetime(2026, 7, 24, 4, 0, tzinfo=UTC)
    clock = FixedClock(now)
    engagement_id = "eng-local-demo"
    app = ControlPlaneMvp.local_dev(
        engagement_id=engagement_id,
        operator_id="operator-local",
        approver_id="approver-local",
        bootstrap_expires_at=now + timedelta(days=30),
        clock=clock,
    )
    admin = app.bootstrap.operator_admin_approval_id
    app.engagements.create(
        engagement_id,
        "operator-local",
        admin,
        now + timedelta(days=7),
    )
    app.scope_roe.register(
        engagement_id,
        "operator-local",
        admin,
        frozenset({"tgt-demo-app"}),
        frozenset({"tc-static-review"}),
        now - timedelta(minutes=1),
        now + timedelta(days=1),
    )
    app.engagements.activate(engagement_id, "operator-local", admin)
    model = app.model_gateway.generate(
        engagement_id,
        "operator-local",
        ModelRequest(
            request_id="req-model-demo",
            purpose=ModelPurpose.PROPOSE_TEST_PLAN,
            prompt_template_id="tmpl-safe-plan",
            context_object_ids=("repo-demo-source",),
        ),
    )
    tool = app.tool_gateway.invoke(
        engagement_id,
        "operator-local",
        ToolRequest(
            request_id="req-tool-demo",
            engagement_id=engagement_id,
            target_id="tgt-demo-app",
            test_case_id="tc-static-review",
            action_class=ActionClass.READ_ONLY_ANALYSIS,
            tool_id=ToolId.RUN_STATIC_ANALYSIS,
        ),
    )
    stop = app.emergency_stop.activate(
        engagement_id,
        "operator-local",
        admin,
        "local demonstration stop",
    )
    events = app.audit.list_events(engagement_id, "operator-local")
    print(
        json.dumps(
            {
                "engagement_id": engagement_id,
                "model_profile": model.model_profile,
                "tool_status": tool.status.value,
                "emergency_stop_active": stop.active,
                "audit_events_before_list_event": len(events),
            },
            indent=2,
            sort_keys=True,
        )
    )
    app.close(engagement_id)


if __name__ == "__main__":
    main()
