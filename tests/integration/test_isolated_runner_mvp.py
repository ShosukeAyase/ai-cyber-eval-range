from __future__ import annotations

import json
import threading
import time
from dataclasses import replace

import pytest

from cyber_eval.domain import JobState
from cyber_eval.errors import (
    AuditUnavailableError,
    ResourceLimitError,
    RunnerTerminatedError,
    ScopeViolationError,
)
from cyber_eval.runner.contracts import RunnerLimits
from cyber_eval.runner.kill_switch import KillSwitchMonitor
from tests.harness.control_plane import ENGAGEMENT_ID, OPERATOR_ID
from tests.harness.runner import approve_runner_start, runner_harness, runner_request


def test_runner_collects_evidence_and_destroys_all_ephemeral_state(tmp_path) -> None:
    app, coordinator, runtime, evidence_root = runner_harness(tmp_path)
    approval_id = approve_runner_start(app)
    record = coordinator.run(ENGAGEMENT_ID, OPERATOR_ID, approval_id, runner_request())
    assert record.state is JobState.COMPLETED
    assert runtime.active_job_ids(ENGAGEMENT_ID) == ()
    assert not (tmp_path / "runtime" / "job-local-static").exists()
    evidence_path = evidence_root / ENGAGEMENT_ID / "job-local-static" / "evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["repository_id"] == "repo-local-synthetic"
    assert {item["test_id"] for item in evidence["tests"]} == {
        "defined-python-parse",
        "defined-no-symlinks",
        "defined-size-bounds",
    }
    assert record.evidence_id == "evd-local-static"
    app.close(ENGAGEMENT_ID)


def test_scope_outside_target_is_rejected_before_runtime(tmp_path) -> None:
    app, coordinator, runtime, _ = runner_harness(tmp_path)
    approval_id = approve_runner_start(app)
    request = replace(runner_request(), target_id="tgt-outside-scope")
    with pytest.raises(ScopeViolationError):
        coordinator.run(ENGAGEMENT_ID, OPERATOR_ID, approval_id, request)
    assert runtime.invocation_count == 0
    app.close(ENGAGEMENT_ID)


def test_audit_failure_prevents_runtime_creation(tmp_path) -> None:
    app, coordinator, runtime, _ = runner_harness(tmp_path)
    approval_id = approve_runner_start(app)
    app.store.fail_audit_writes = True
    with pytest.raises(AuditUnavailableError):
        coordinator.run(ENGAGEMENT_ID, OPERATOR_ID, approval_id, runner_request())
    assert runtime.invocation_count == 0
    app.store.fail_audit_writes = False
    app.close(ENGAGEMENT_ID)


def test_source_file_limit_is_enforced_and_workspace_is_destroyed(tmp_path) -> None:
    app, coordinator, runtime, _ = runner_harness(
        tmp_path,
        limits=RunnerLimits(max_file_bytes=1024),
    )
    source = tmp_path / "synthetic-repository"
    (source / "oversized.bin").write_bytes(b"x" * 1025)
    approval_id = approve_runner_start(app)
    with pytest.raises(ResourceLimitError):
        coordinator.run(ENGAGEMENT_ID, OPERATOR_ID, approval_id, runner_request())
    assert runtime.active_job_ids(ENGAGEMENT_ID) == ()
    assert not (tmp_path / "runtime" / "job-local-static").exists()
    record = coordinator.get_job(ENGAGEMENT_ID, OPERATOR_ID, "job-local-static")
    assert record.state is JobState.FAILED
    app.close(ENGAGEMENT_ID)


def test_kill_switch_terminates_blocked_runner_and_cleanup_completes(tmp_path) -> None:
    job_id = "job-kill-switch"
    app, coordinator, runtime, _ = runner_harness(
        tmp_path,
        blocked_job_ids=frozenset({job_id}),
    )
    approval_id = approve_runner_start(app)
    failures: list[Exception] = []

    def target() -> None:
        try:
            coordinator.run(
                ENGAGEMENT_ID,
                OPERATOR_ID,
                approval_id,
                runner_request(job_id),
            )
        except Exception as exc:
            failures.append(exc)

    thread = threading.Thread(target=target)
    thread.start()
    for _ in range(200):
        if runtime.active_job_ids(ENGAGEMENT_ID):
            break
        time.sleep(0.01)
    app.emergency_stop.activate(
        ENGAGEMENT_ID,
        OPERATOR_ID,
        app.bootstrap.operator_admin_approval_id,
        "phase-04-test-stop",
    )
    monitor = KillSwitchMonitor(emergency_stop=app.emergency_stop, runtime=runtime)
    assert monitor.enforce(ENGAGEMENT_ID) == (job_id,)
    thread.join(timeout=5)
    assert failures and isinstance(failures[0], RunnerTerminatedError)
    assert runtime.active_job_ids(ENGAGEMENT_ID) == ()
    assert not (tmp_path / "runtime" / job_id).exists()
    record = coordinator.get_job(ENGAGEMENT_ID, OPERATOR_ID, job_id)
    assert record.state is JobState.TERMINATED
    app.close(ENGAGEMENT_ID)
