"""Local Control Plane MVP test harness with synthetic identifiers only."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from cyber_eval.clock import FixedClock
from cyber_eval.control_plane import ControlPlaneMvp

NOW = datetime(2026, 7, 24, 4, 0, tzinfo=UTC)
ENGAGEMENT_ID = "eng-control-mvp"
OPERATOR_ID = "operator-local"
APPROVER_ID = "approver-local"
TARGET_ID = "tgt-local-app"
TEST_CASE_ID = "tc-local-static"


def new_app(*, active: bool = True, policy_available: bool = True) -> ControlPlaneMvp:
    clock = FixedClock(NOW)
    app = ControlPlaneMvp.local_dev(
        engagement_id=ENGAGEMENT_ID,
        operator_id=OPERATOR_ID,
        approver_id=APPROVER_ID,
        bootstrap_expires_at=NOW + timedelta(days=30),
        clock=clock,
        policy_available=policy_available,
    )
    admin = app.bootstrap.operator_admin_approval_id
    app.engagements.create(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        admin,
        NOW + timedelta(days=7),
    )
    app.scope_roe.register(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        admin,
        frozenset({TARGET_ID}),
        frozenset({TEST_CASE_ID}),
        NOW - timedelta(minutes=1),
        NOW + timedelta(days=1),
    )
    if active:
        app.engagements.activate(ENGAGEMENT_ID, OPERATOR_ID, admin)
    return app
