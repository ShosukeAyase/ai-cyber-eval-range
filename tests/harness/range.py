"""Phase 05 synthetic Cyber Range test harness."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from cyber_eval.control_plane import ControlPlaneMvp
from cyber_eval.domain import ResourceScope, WriteOperation
from cyber_eval.range.catalog import LocalScenarioCatalog
from cyber_eval.range.contracts import RangeActionRequest
from cyber_eval.range.runtime import LocalCyberRangeRuntime
from cyber_eval.range.scoring import RangeScoringEngine
from cyber_eval.range.service import CyberRangeService
from tests.harness.control_plane import APPROVER_ID, ENGAGEMENT_ID, NOW, OPERATOR_ID

ROOT = Path(__file__).resolve().parents[2]
CATALOG_ROOT = ROOT / "range-scenarios"


def range_harness(tmp_path: Path):
    catalog = LocalScenarioCatalog(CATALOG_ROOT)
    app = ControlPlaneMvp.local_dev(
        engagement_id=ENGAGEMENT_ID,
        operator_id=OPERATOR_ID,
        approver_id=APPROVER_ID,
        bootstrap_expires_at=NOW + timedelta(days=30),
        clock=_fixed_clock(),
    )
    admin = app.bootstrap.operator_admin_approval_id
    app.engagements.create(ENGAGEMENT_ID, OPERATOR_ID, admin, NOW + timedelta(days=7))
    scenarios = tuple(catalog.scenario(item) for item in catalog.scenario_ids())
    app.scope_roe.register(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        admin,
        frozenset(item.target_id for item in scenarios),
        frozenset(item.test_case_id for item in scenarios),
        NOW - timedelta(minutes=1),
        NOW + timedelta(days=1),
    )
    app.engagements.activate(ENGAGEMENT_ID, OPERATOR_ID, admin)
    runtime = LocalCyberRangeRuntime(tmp_path / "range-runtime")
    scoring = RangeScoringEngine(catalog=catalog)
    service = CyberRangeService(
        store=app.store,
        approvals=app.approvals,
        scope_roe=app.scope_roe,
        emergency_stop=app.emergency_stop,
        catalog=catalog,
        runtime=runtime,
        scoring=scoring,
        clock=app.clock,
    )
    return app, service, runtime, catalog


def approve_range_operation(
    app: ControlPlaneMvp,
    *,
    operation: WriteOperation,
    target_id: str,
    approval_id: str,
) -> str:
    app.approvals.request(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        app.bootstrap.operator_admin_approval_id,
        approval_id,
        frozenset({operation}),
        ResourceScope.RESOURCE,
        target_id,
        NOW + timedelta(hours=1),
    )
    app.approvals.approve(
        ENGAGEMENT_ID,
        APPROVER_ID,
        app.bootstrap.approver_admin_approval_id,
        approval_id,
    )
    return approval_id


def range_action(
    *,
    action_id: str,
    instance_id: str,
    operation_id: str,
    asset_id: str,
) -> RangeActionRequest:
    return RangeActionRequest(
        action_id=action_id,
        engagement_id=ENGAGEMENT_ID,
        instance_id=instance_id,
        operation_id=operation_id,
        asset_id=asset_id,
    )


def _fixed_clock():
    from cyber_eval.clock import FixedClock

    return FixedClock(NOW)
