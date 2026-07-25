"""Phase 04 synthetic Runner harness."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from cyber_eval.domain import ResourceScope, WriteOperation
from cyber_eval.runner.contracts import (
    RunnerJobRequest,
    RunnerLimits,
    RunnerOperation,
    RunnerProfile,
)
from cyber_eval.runner.coordinator import RunnerCoordinator
from cyber_eval.runner.registry import LocalRunnerRegistry
from cyber_eval.runner.runtime import DeterministicRunnerRuntime
from tests.harness.control_plane import (
    APPROVER_ID,
    ENGAGEMENT_ID,
    NOW,
    OPERATOR_ID,
    TARGET_ID,
    TEST_CASE_ID,
    new_app,
)

IMAGE_REF = "localhost/cyber-eval-runner@sha256:" + "a" * 64
REPOSITORY_ID = "repo-local-synthetic"
PROFILE_ID = "prof-static-offline"


def runner_harness(
    tmp_path: Path,
    *,
    blocked_job_ids: frozenset[str] | None = None,
    limits: RunnerLimits | None = None,
):
    app = new_app()
    source = tmp_path / "synthetic-repository"
    source.mkdir()
    (source / "app.py").write_text("def add(a: int, b: int) -> int:\n    return a + b\n")
    (source / "README.md").write_text("synthetic repository\n")
    registry = LocalRunnerRegistry()
    registry.register_repository(REPOSITORY_ID, TARGET_ID, source)
    registry.register_profile(
        RunnerProfile(
            profile_id=PROFILE_ID,
            test_case_id=TEST_CASE_ID,
            image_ref=IMAGE_REF,
            operations=tuple(RunnerOperation),
            limits=limits or RunnerLimits(),
        )
    )
    runtime = DeterministicRunnerRuntime(
        tmp_path / "runtime",
        blocked_job_ids=blocked_job_ids or frozenset(),
    )
    coordinator = RunnerCoordinator(
        store=app.store,
        approvals=app.approvals,
        policy=app.policy,
        emergency_stop=app.emergency_stop,
        registry=registry,
        runtime=runtime,
        evidence_root=tmp_path / "evidence",
        clock=app.clock,
    )
    return app, coordinator, runtime, tmp_path / "evidence"


def approve_runner_start(app, approval_id: str = "apr-runner-start") -> str:
    app.approvals.request(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        app.bootstrap.operator_admin_approval_id,
        approval_id,
        frozenset({WriteOperation.START_RUNNER_JOB}),
        ResourceScope.RESOURCE,
        TARGET_ID,
        NOW + timedelta(hours=1),
    )
    app.approvals.approve(
        ENGAGEMENT_ID,
        APPROVER_ID,
        app.bootstrap.approver_admin_approval_id,
        approval_id,
    )
    return approval_id


def runner_request(job_id: str = "job-local-static") -> RunnerJobRequest:
    return RunnerJobRequest(
        job_id=job_id,
        engagement_id=ENGAGEMENT_ID,
        target_id=TARGET_ID,
        repository_id=REPOSITORY_ID,
        profile_id=PROFILE_ID,
        test_case_id=TEST_CASE_ID,
    )
