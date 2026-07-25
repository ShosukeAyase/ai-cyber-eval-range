"""Typed contracts for the single-laptop isolated Runner MVP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from cyber_eval.domain import JobState


class RunnerOperation(StrEnum):
    READ_REPOSITORY = "read_repository"
    STATIC_ANALYSIS = "static_analysis"
    RUN_DEFINED_TESTS = "run_defined_tests"
    COLLECT_EVIDENCE = "collect_evidence"


@dataclass(frozen=True, slots=True)
class RunnerLimits:
    cpus: float = 1.0
    memory_mib: int = 256
    timeout_seconds: int = 60
    pids: int = 64
    open_files: int = 128
    max_file_bytes: int = 2 * 1024 * 1024
    workspace_bytes: int = 32 * 1024 * 1024
    evidence_bytes: int = 4 * 1024 * 1024
    max_source_files: int = 1000

    def __post_init__(self) -> None:
        bounded = (
            0.1 <= self.cpus <= 2.0,
            64 <= self.memory_mib <= 1024,
            1 <= self.timeout_seconds <= 600,
            8 <= self.pids <= 128,
            32 <= self.open_files <= 256,
            1024 <= self.max_file_bytes <= 16 * 1024 * 1024,
            1024 * 1024 <= self.workspace_bytes <= 128 * 1024 * 1024,
            1024 <= self.evidence_bytes <= 16 * 1024 * 1024,
            1 <= self.max_source_files <= 5000,
        )
        if not all(bounded):
            raise ValueError("runner limits exceed the approved local profile")
        if self.evidence_bytes > self.workspace_bytes:
            raise ValueError("evidence limit cannot exceed workspace capacity")


@dataclass(frozen=True, slots=True)
class RegisteredRepository:
    repository_id: str
    target_id: str
    source_path: Path
    content_sha256: str


@dataclass(frozen=True, slots=True)
class RunnerProfile:
    profile_id: str
    test_case_id: str
    image_ref: str
    operations: tuple[RunnerOperation, ...]
    limits: RunnerLimits


@dataclass(frozen=True, slots=True)
class RunnerJobRequest:
    job_id: str
    engagement_id: str
    target_id: str
    repository_id: str
    profile_id: str
    test_case_id: str


@dataclass(frozen=True, slots=True)
class RunnerExecutionSpec:
    request: RunnerJobRequest
    repository: RegisteredRepository
    profile: RunnerProfile


@dataclass(frozen=True, slots=True)
class RunnerExecutionResult:
    runtime_id: str
    evidence_bytes: bytes
    exit_code: int


@dataclass(frozen=True, slots=True)
class RunnerDestructionAttestation:
    job_id: str
    runtime_id: str
    destroyed_at: datetime
    workspace_removed: bool
    runtime_removed: bool
    credential_material_present: bool = False


@dataclass(frozen=True, slots=True)
class RunnerEvidenceRecord:
    evidence_id: str
    job_id: str
    engagement_id: str
    relative_path: str
    sha256: str
    size_bytes: int
    created_at: datetime
    destruction_attested: bool


@dataclass(frozen=True, slots=True)
class RunnerJobRecord:
    request: RunnerJobRequest
    state: JobState
    approval_id: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    destroyed_at: datetime | None
    evidence_id: str | None
    runtime_id: str | None
    terminal_reason: str | None
