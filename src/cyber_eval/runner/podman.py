"""Rootless Podman adapter with a fixed, non-arbitrary execution contract."""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Event, RLock
from typing import Protocol

from cyber_eval.errors import (
    RunnerEvidenceError,
    RunnerRuntimeUnavailableError,
    RunnerTerminatedError,
)
from cyber_eval.runner.contracts import (
    RunnerDestructionAttestation,
    RunnerExecutionResult,
    RunnerExecutionSpec,
)
from cyber_eval.runner.runtime import RunnerRuntime, execution_job_document


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class CommandExecutor(Protocol):
    def run(self, arguments: Sequence[str], *, timeout_seconds: int) -> CommandResult:
        """Run one fixed argv vector without a shell."""


class SubprocessCommandExecutor:
    """The only approved subprocess boundary; it never accepts a command string."""

    def run(self, arguments: Sequence[str], *, timeout_seconds: int) -> CommandResult:
        completed = subprocess.run(
            list(arguments),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
        )
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


class PodmanCommandBuilder:
    """Build immutable Podman commands from validated Runner contracts."""

    def __init__(self, executable: str = "podman") -> None:
        self.executable = executable

    def info(self) -> tuple[str, ...]:
        return (self.executable, "info", "--format={{.Host.Security.Rootless}}")

    def image_exists(self, image_ref: str) -> tuple[str, ...]:
        return (self.executable, "image", "exists", image_ref)

    def create(
        self,
        spec: RunnerExecutionSpec,
        *,
        container_name: str,
        job_path: Path,
    ) -> tuple[str, ...]:
        limits = spec.profile.limits
        source = str(spec.repository.source_path)
        job_file = str(job_path)
        return (
            self.executable,
            "create",
            "--name",
            container_name,
            "--pull=never",
            "--network=none",
            "--pid=private",
            "--ipc=none",
            "--uts=private",
            "--cgroupns=private",
            "--no-hosts",
            "--no-hostname",
            "--http-proxy=false",
            "--image-volume=ignore",
            "--no-healthcheck",
            "--restart=no",
            "--log-driver=none",
            "--read-only",
            "--read-only-tmpfs=false",
            "--userns=keep-id",
            "--user=65532:65532",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            f"--cpus={limits.cpus}",
            f"--memory={limits.memory_mib}m",
            f"--pids-limit={limits.pids}",
            f"--ulimit=fsize={limits.max_file_bytes}:{limits.max_file_bytes}",
            f"--ulimit=nofile={limits.open_files}:{limits.open_files}",
            "--stop-timeout=1",
            (f"--tmpfs=/workspace:rw,noexec,nosuid,nodev,size={limits.workspace_bytes},mode=1777"),
            f"--mount=type=bind,src={source},dst=/input,ro=true",
            f"--mount=type=bind,src={job_file},dst=/job.json,ro=true",
            "--workdir=/workspace",
            "--env=HOME=/workspace/home",
            "--env=TMPDIR=/workspace/tmp",
            "--env=XDG_CACHE_HOME=/workspace/cache",
            "--env=PYTHONDONTWRITEBYTECODE=1",
            spec.profile.image_ref,
            "python",
            "-P",
            "-m",
            "cyber_eval.runner.workload",
            "--job",
            "/job.json",
            "--input",
            "/input",
            "--workspace",
            "/workspace",
        )

    def start(self, container_name: str) -> tuple[str, ...]:
        return (self.executable, "start", "--attach", container_name)

    def copy_evidence(self, container_name: str, destination: Path) -> tuple[str, ...]:
        return (
            self.executable,
            "cp",
            f"{container_name}:/workspace/evidence.json",
            str(destination),
        )

    def kill(self, container_name: str) -> tuple[str, ...]:
        return (self.executable, "kill", "--signal=KILL", container_name)

    def remove(self, container_name: str) -> tuple[str, ...]:
        return (self.executable, "rm", "--force", "--time=0", container_name)


@dataclass(slots=True)
class _PodmanActiveJob:
    engagement_id: str
    container_name: str
    workspace: Path
    terminated: Event


class PodmanRunnerRuntime(RunnerRuntime):
    """Disposable rootless-container runtime using only a preloaded image digest."""

    def __init__(
        self,
        runtime_root: Path,
        *,
        executor: CommandExecutor | None = None,
        builder: PodmanCommandBuilder | None = None,
    ) -> None:
        self._root = runtime_root.expanduser().resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        self._executor = executor or SubprocessCommandExecutor()
        self._builder = builder or PodmanCommandBuilder()
        self._active: dict[str, _PodmanActiveJob] = {}
        self._lock = RLock()
        self._invocation_count = 0

    @property
    def invocation_count(self) -> int:
        return self._invocation_count

    def execute(self, spec: RunnerExecutionSpec) -> RunnerExecutionResult:
        self._verify_runtime(spec.profile.image_ref)
        job_id = spec.request.job_id
        workspace = self._root / job_id
        if workspace.exists():
            raise RunnerEvidenceError("runner host workspace already exists")
        workspace.mkdir(mode=0o700)
        job_path = workspace / "job.json"
        job_path.write_text(
            json.dumps(execution_job_document(spec), sort_keys=True),
            encoding="utf-8",
        )
        container_name = f"ce-{job_id}"
        created = self._executor.run(
            self._builder.create(spec, container_name=container_name, job_path=job_path),
            timeout_seconds=30,
        )
        if created.returncode != 0:
            shutil.rmtree(workspace, ignore_errors=True)
            raise RunnerRuntimeUnavailableError(created.stderr.strip() or "podman create failed")
        with self._lock:
            self._active[job_id] = _PodmanActiveJob(
                spec.request.engagement_id,
                container_name,
                workspace,
                Event(),
            )
            self._invocation_count += 1
        try:
            started = self._executor.run(
                self._builder.start(container_name),
                timeout_seconds=spec.profile.limits.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            self.terminate(spec.request.engagement_id, job_id)
            raise RunnerTerminatedError("runner exceeded the wall-clock limit") from exc
        with self._lock:
            active = self._active.get(job_id)
        if started.returncode != 0 and active is not None and active.terminated.is_set():
            raise RunnerTerminatedError("runner terminated by Emergency Stop")
        if started.returncode != 0:
            raise RunnerEvidenceError(started.stderr.strip() or "fixed workload failed")
        evidence_path = workspace / "evidence.json"
        copied = self._executor.run(
            self._builder.copy_evidence(container_name, evidence_path),
            timeout_seconds=30,
        )
        if copied.returncode != 0 or not evidence_path.is_file():
            raise RunnerEvidenceError(copied.stderr.strip() or "evidence copy failed")
        evidence = evidence_path.read_bytes()
        if len(evidence) > spec.profile.limits.evidence_bytes:
            raise RunnerEvidenceError("evidence exceeds the approved byte limit")
        return RunnerExecutionResult(container_name, evidence, started.returncode)

    def terminate(self, engagement_id: str, job_id: str) -> None:
        with self._lock:
            active = self._active.get(job_id)
        if active is None or active.engagement_id != engagement_id:
            return
        active.terminated.set()
        self._executor.run(self._builder.kill(active.container_name), timeout_seconds=10)

    def destroy(self, spec: RunnerExecutionSpec) -> RunnerDestructionAttestation:
        job_id = spec.request.job_id
        with self._lock:
            active = self._active.pop(job_id, None)
        container_name = active.container_name if active else f"ce-{job_id}"
        workspace = active.workspace if active else self._root / job_id
        removed = self._executor.run(self._builder.remove(container_name), timeout_seconds=30)
        shutil.rmtree(workspace, ignore_errors=True)
        return RunnerDestructionAttestation(
            job_id=job_id,
            runtime_id=container_name,
            destroyed_at=datetime.now(UTC),
            workspace_removed=not workspace.exists(),
            runtime_removed=removed.returncode == 0,
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

    def _verify_runtime(self, image_ref: str) -> None:
        info = self._executor.run(self._builder.info(), timeout_seconds=30)
        if info.returncode != 0 or info.stdout.strip().lower() != "true":
            raise RunnerRuntimeUnavailableError("Podman runtime is unavailable or not rootless")
        exists = self._executor.run(self._builder.image_exists(image_ref), timeout_seconds=30)
        if exists.returncode != 0:
            raise RunnerRuntimeUnavailableError(
                "digest-pinned Runner image is not present in local storage"
            )
