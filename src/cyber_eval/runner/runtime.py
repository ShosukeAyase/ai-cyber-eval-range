"""Runner runtime protocol and deterministic no-container test runtime."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Event, RLock
from typing import Protocol

from cyber_eval.errors import RunnerEvidenceError, RunnerTerminatedError
from cyber_eval.runner.contracts import (
    RunnerDestructionAttestation,
    RunnerExecutionResult,
    RunnerExecutionSpec,
)
from cyber_eval.runner.workload import execute_fixed_workload


class RunnerRuntime(Protocol):
    @property
    def invocation_count(self) -> int:
        """Return how many jobs crossed the runtime boundary."""

    def execute(self, spec: RunnerExecutionSpec) -> RunnerExecutionResult:
        """Execute one fixed workload and return evidence bytes."""

    def terminate(self, engagement_id: str, job_id: str) -> None:
        """Terminate one active runtime without depending on the model."""

    def destroy(self, spec: RunnerExecutionSpec) -> RunnerDestructionAttestation:
        """Remove runtime and writable workspace state."""

    def active_job_ids(self, engagement_id: str) -> tuple[str, ...]:
        """Return active jobs for Kill Switch enforcement."""


@dataclass(slots=True)
class _FakeActiveJob:
    engagement_id: str
    runtime_id: str
    workspace: Path
    cancelled: Event
    released: Event


class DeterministicRunnerRuntime:
    """Test runtime that exercises the fixed workload without claiming OS isolation."""

    def __init__(
        self,
        runtime_root: Path,
        *,
        blocked_job_ids: frozenset[str] | None = None,
    ) -> None:
        self._root = runtime_root.expanduser().resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        self._blocked_job_ids = blocked_job_ids or frozenset()
        self._active: dict[str, _FakeActiveJob] = {}
        self._lock = RLock()
        self._invocation_count = 0

    @property
    def invocation_count(self) -> int:
        return self._invocation_count

    def execute(self, spec: RunnerExecutionSpec) -> RunnerExecutionResult:
        job_id = spec.request.job_id
        workspace = self._root / job_id
        if workspace.exists():
            raise RunnerEvidenceError("runner workspace already exists")
        workspace.mkdir(mode=0o700)
        active = _FakeActiveJob(
            engagement_id=spec.request.engagement_id,
            runtime_id=f"fake-{job_id}",
            workspace=workspace,
            cancelled=Event(),
            released=Event(),
        )
        with self._lock:
            self._active[job_id] = active
            self._invocation_count += 1
        if job_id in self._blocked_job_ids:
            while not active.cancelled.is_set() and not active.released.wait(0.01):
                continue
        if active.cancelled.is_set():
            raise RunnerTerminatedError("runner terminated by Emergency Stop")

        job = execution_job_document(spec)
        (workspace / "job.json").write_text(json.dumps(job, sort_keys=True), encoding="utf-8")
        execute_fixed_workload(
            job=job,
            input_root=spec.repository.source_path,
            workspace_root=workspace,
        )
        evidence_path = workspace / "evidence.json"
        if not evidence_path.is_file():
            raise RunnerEvidenceError("fixed workload produced no evidence")
        evidence = evidence_path.read_bytes()
        if len(evidence) > spec.profile.limits.evidence_bytes:
            raise RunnerEvidenceError("runtime evidence exceeds the approved limit")
        return RunnerExecutionResult(active.runtime_id, evidence, 0)

    def terminate(self, engagement_id: str, job_id: str) -> None:
        with self._lock:
            active = self._active.get(job_id)
        if active is not None and active.engagement_id == engagement_id:
            active.cancelled.set()

    def release(self, job_id: str) -> None:
        """Allow a deliberately blocked test job to continue."""
        with self._lock:
            active = self._active.get(job_id)
        if active is not None:
            active.released.set()

    def destroy(self, spec: RunnerExecutionSpec) -> RunnerDestructionAttestation:
        job_id = spec.request.job_id
        with self._lock:
            active = self._active.pop(job_id, None)
        runtime_id = active.runtime_id if active is not None else f"fake-{job_id}"
        workspace = active.workspace if active is not None else self._root / job_id
        shutil.rmtree(workspace, ignore_errors=True)
        return RunnerDestructionAttestation(
            job_id=job_id,
            runtime_id=runtime_id,
            destroyed_at=datetime.now(UTC),
            workspace_removed=not workspace.exists(),
            runtime_removed=True,
            credential_material_present=False,
        )

    def active_job_ids(self, engagement_id: str) -> tuple[str, ...]:
        with self._lock:
            return tuple(
                sorted(
                    job_id
                    for job_id, active in self._active.items()
                    if active.engagement_id == engagement_id
                )
            )


def execution_job_document(spec: RunnerExecutionSpec) -> dict[str, object]:
    limits = spec.profile.limits
    return {
        "schema_version": "1.0",
        "job_id": spec.request.job_id,
        "engagement_id": spec.request.engagement_id,
        "target_id": spec.request.target_id,
        "repository_id": spec.request.repository_id,
        "profile_id": spec.request.profile_id,
        "test_case_id": spec.request.test_case_id,
        "expected_repository_sha256": spec.repository.content_sha256,
        "operations": [item.value for item in spec.profile.operations],
        "limits": {
            "cpus": limits.cpus,
            "memory_mib": limits.memory_mib,
            "timeout_seconds": limits.timeout_seconds,
            "pids": limits.pids,
            "open_files": limits.open_files,
            "max_file_bytes": limits.max_file_bytes,
            "workspace_bytes": limits.workspace_bytes,
            "evidence_bytes": limits.evidence_bytes,
            "max_source_files": limits.max_source_files,
        },
    }
