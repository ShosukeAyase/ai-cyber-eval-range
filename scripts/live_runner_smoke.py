"""Run the Phase 04 fixed workload in a real rootless Podman container."""

from __future__ import annotations

import argparse
import json
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cyber_eval.clock import FixedClock
from cyber_eval.control_plane import ControlPlaneMvp
from cyber_eval.domain import ResourceScope, WriteOperation
from cyber_eval.runner.contracts import (
    RunnerJobRequest,
    RunnerLimits,
    RunnerOperation,
    RunnerProfile,
)
from cyber_eval.runner.coordinator import RunnerCoordinator
from cyber_eval.runner.podman import PodmanRunnerRuntime
from cyber_eval.runner.registry import LocalRunnerRegistry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-ref", required=True)
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    now = datetime.now(UTC)
    engagement_id = "eng-phase4-smoke"
    operator_id = "operator-local"
    approver_id = "approver-local"
    target_id = "tgt-phase4-repo"
    test_case_id = "tc-phase4-static"
    with tempfile.TemporaryDirectory(prefix="cyber-eval-phase4-") as directory:
        temporary = Path(directory)
        app = ControlPlaneMvp.local_dev(
            engagement_id=engagement_id,
            operator_id=operator_id,
            approver_id=approver_id,
            bootstrap_expires_at=now + timedelta(hours=2),
            clock=FixedClock(now),
        )
        admin = app.bootstrap.operator_admin_approval_id
        app.engagements.create(engagement_id, operator_id, admin, now + timedelta(hours=1))
        app.scope_roe.register(
            engagement_id,
            operator_id,
            admin,
            frozenset({target_id}),
            frozenset({test_case_id}),
            now - timedelta(minutes=1),
            now + timedelta(hours=1),
        )
        app.engagements.activate(engagement_id, operator_id, admin)
        approval_id = "apr-phase4-start"
        app.approvals.request(
            engagement_id,
            operator_id,
            admin,
            approval_id,
            frozenset({WriteOperation.START_RUNNER_JOB}),
            ResourceScope.RESOURCE,
            target_id,
            now + timedelta(hours=1),
        )
        app.approvals.approve(
            engagement_id,
            approver_id,
            app.bootstrap.approver_admin_approval_id,
            approval_id,
        )
        registry = LocalRunnerRegistry()
        registry.register_repository(
            "repo-phase4-synthetic",
            target_id,
            root / "examples/synthetic-runner-repo",
        )
        registry.register_profile(
            RunnerProfile(
                profile_id="prof-phase4-offline",
                test_case_id=test_case_id,
                image_ref=arguments.image_ref,
                operations=tuple(RunnerOperation),
                limits=RunnerLimits(),
            )
        )
        runtime = PodmanRunnerRuntime(temporary / "runtime")
        coordinator = RunnerCoordinator(
            store=app.store,
            approvals=app.approvals,
            policy=app.policy,
            emergency_stop=app.emergency_stop,
            registry=registry,
            runtime=runtime,
            evidence_root=temporary / "evidence",
            clock=app.clock,
        )
        record = coordinator.run(
            engagement_id,
            operator_id,
            approval_id,
            RunnerJobRequest(
                job_id="job-phase4-smoke",
                engagement_id=engagement_id,
                target_id=target_id,
                repository_id="repo-phase4-synthetic",
                profile_id="prof-phase4-offline",
                test_case_id=test_case_id,
            ),
        )
        evidence_path = (
            temporary / "evidence" / engagement_id / record.request.job_id / "evidence.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        if not all(evidence["isolation"].values()):
            raise SystemExit(f"isolation self-check failed: {evidence['isolation']}")
        print(
            json.dumps(
                {"state": record.state.value, "isolation": evidence["isolation"]},
                sort_keys=True,
            )
        )
        app.close(engagement_id)


if __name__ == "__main__":
    main()
