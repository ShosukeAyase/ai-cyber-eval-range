"""Control Plane coordinator for approved disposable Runner jobs."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from cyber_eval.approval_service import ApprovalService
from cyber_eval.audit import make_audit_event
from cyber_eval.domain import (
    ActionClass,
    AuditOutcome,
    DecisionReason,
    JobState,
    ToolId,
    ToolRequest,
    WriteOperation,
)
from cyber_eval.emergency_stop import EmergencyStopService
from cyber_eval.errors import (
    ControlPlaneError,
    RoeExpiredError,
    RunnerEvidenceError,
    RunnerTerminatedError,
    ScopeViolationError,
)
from cyber_eval.identifiers import require_generic_object_id, require_identifier
from cyber_eval.interfaces import Clock
from cyber_eval.policy_adapter import LocalPolicyEngineAdapter
from cyber_eval.runner.contracts import (
    RunnerEvidenceRecord,
    RunnerExecutionSpec,
    RunnerJobRecord,
    RunnerJobRequest,
)
from cyber_eval.runner.registry import LocalRunnerRegistry
from cyber_eval.runner.runtime import RunnerRuntime
from cyber_eval.store import LocalControlPlaneStore


class RunnerCoordinator:
    """Authorize, execute, collect, and destroy one fixed Runner workload."""

    def __init__(
        self,
        *,
        store: LocalControlPlaneStore,
        approvals: ApprovalService,
        policy: LocalPolicyEngineAdapter,
        emergency_stop: EmergencyStopService,
        registry: LocalRunnerRegistry,
        runtime: RunnerRuntime,
        evidence_root: Path,
        clock: Clock,
    ) -> None:
        self._store = store
        self._approvals = approvals
        self._policy = policy
        self._emergency_stop = emergency_stop
        self._registry = registry
        self._runtime = runtime
        self._evidence_root = evidence_root.expanduser().resolve()
        self._evidence_root.mkdir(parents=True, exist_ok=True)
        self._clock = clock

    @property
    def runtime(self) -> RunnerRuntime:
        return self._runtime

    def run(
        self,
        engagement_id: str,
        actor_id: str,
        approval_id: str,
        request: RunnerJobRequest,
    ) -> RunnerJobRecord:
        spec = self._authorize(engagement_id, actor_id, approval_id, request)
        self._record_started(engagement_id, actor_id, request.job_id)
        terminal_reason: str | None = None
        evidence: RunnerEvidenceRecord | None = None
        try:
            result = self._runtime.execute(spec)
            evidence = self._persist_evidence(
                engagement_id, actor_id, request, result.evidence_bytes
            )
        except RunnerTerminatedError:
            terminal_reason = "emergency_stop"
            raise
        except Exception as exc:
            terminal_reason = type(exc).__name__
            raise
        finally:
            attestation = self._runtime.destroy(spec)
            terminal_state = (
                JobState.COMPLETED
                if evidence is not None
                and attestation.workspace_removed
                and attestation.runtime_removed
                and not attestation.credential_material_present
                else JobState.TERMINATED
                if terminal_reason == "emergency_stop"
                else JobState.FAILED
            )
            self._record_destroyed(
                engagement_id=engagement_id,
                actor_id=actor_id,
                job_id=request.job_id,
                runtime_id=attestation.runtime_id,
                state=terminal_state,
                evidence_id=evidence.evidence_id if evidence else None,
                terminal_reason=terminal_reason,
                destroyed_at=attestation.destroyed_at.isoformat(),
            )
        record = self._load_job(engagement_id, request.job_id)
        if record is None:
            raise ControlPlaneError("completed runner job record is unavailable")
        return record

    def get_job(self, engagement_id: str, actor_id: str, job_id: str) -> RunnerJobRecord:
        require_identifier(engagement_id, "eng")
        require_identifier(job_id, "job")
        record = self._load_job(engagement_id, job_id)
        if record is None:
            raise ControlPlaneError("runner job not found")
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="runner.get_job",
            outcome=AuditOutcome.COMPLETED,
            clock=self._clock,
            details={"job_id": job_id, "state": record.state.value},
        )
        self._store.append_audit(engagement_id, event)
        return record

    def _authorize(
        self,
        engagement_id: str,
        actor_id: str,
        approval_id: str,
        request: RunnerJobRequest,
    ) -> RunnerExecutionSpec:
        require_identifier(engagement_id, "eng")
        require_identifier(request.job_id, "job")
        require_identifier(request.target_id, "tgt")
        require_generic_object_id(request.repository_id)
        require_generic_object_id(request.profile_id)
        require_identifier(request.test_case_id, "tc")
        if request.engagement_id != engagement_id:
            self._audit_denial(engagement_id, actor_id, request.job_id, "engagement_mismatch")
            raise ScopeViolationError("runner request engagement mismatch")
        repository = self._registry.repository(request.repository_id)
        profile = self._registry.profile(request.profile_id)
        if repository.target_id != request.target_id:
            self._audit_denial(
                engagement_id, actor_id, request.job_id, "repository_target_mismatch"
            )
            raise ScopeViolationError("repository is not registered for the requested target")
        if profile.test_case_id != request.test_case_id:
            self._audit_denial(engagement_id, actor_id, request.job_id, "profile_test_mismatch")
            raise ScopeViolationError("runner profile is not registered for the requested test")
        policy_request = ToolRequest(
            request_id=f"req-{request.job_id[4:]}",
            engagement_id=engagement_id,
            target_id=request.target_id,
            test_case_id=request.test_case_id,
            action_class=ActionClass.READ_ONLY_ANALYSIS,
            tool_id=ToolId.RUN_STATIC_ANALYSIS,
        )
        decision = self._policy._evaluate_unlogged(engagement_id, actor_id, policy_request)
        if not decision.allowed:
            self._audit_denial(engagement_id, actor_id, request.job_id, decision.reason.value)
            if decision.reason is DecisionReason.ROE_EXPIRED:
                raise RoeExpiredError("runner request has an expired ROE")
            raise ScopeViolationError(f"runner request denied: {decision.reason.value}")
        approval = self._approvals._require_write(
            engagement_id=engagement_id,
            actor_id=actor_id,
            approval_id=approval_id,
            operation=WriteOperation.START_RUNNER_JOB,
            resource_id=request.target_id,
        )
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="runner.authorize",
            outcome=AuditOutcome.ALLOWED,
            approval_id=approval_id,
            clock=self._clock,
            details={"job_id": request.job_id, "repository_id": request.repository_id},
        )
        try:
            with self._store.audited_transaction(event) as connection:
                self._approvals._consume_in_transaction(connection, approval)
                connection.execute(
                    """
                    INSERT INTO runner_jobs (
                        job_id, engagement_id, target_id, repository_id, profile_id,
                        test_case_id, state, approval_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        request.job_id,
                        engagement_id,
                        request.target_id,
                        request.repository_id,
                        request.profile_id,
                        request.test_case_id,
                        JobState.AUTHORIZED.value,
                        approval_id,
                        self._clock.now().isoformat(),
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise ControlPlaneError("runner job already exists") from exc
        return RunnerExecutionSpec(request, repository, profile)

    def _record_started(self, engagement_id: str, actor_id: str, job_id: str) -> None:
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="runner.start",
            outcome=AuditOutcome.COMPLETED,
            clock=self._clock,
            details={"job_id": job_id},
        )
        with self._store.audited_transaction(event) as connection:
            cursor = connection.execute(
                """
                UPDATE runner_jobs SET state = ?, started_at = ?
                WHERE engagement_id = ? AND job_id = ? AND state = ?
                """,
                (
                    JobState.RUNNING.value,
                    self._clock.now().isoformat(),
                    engagement_id,
                    job_id,
                    JobState.AUTHORIZED.value,
                ),
            )
            if cursor.rowcount != 1:
                raise ControlPlaneError("runner job could not transition to running")

    def _persist_evidence(
        self,
        engagement_id: str,
        actor_id: str,
        request: RunnerJobRequest,
        evidence_bytes: bytes,
    ) -> RunnerEvidenceRecord:
        document = json.loads(evidence_bytes)
        required_matches = (
            document.get("job_id") == request.job_id,
            document.get("engagement_id") == engagement_id,
            document.get("target_id") == request.target_id,
            document.get("repository_id") == request.repository_id,
            document.get("profile_id") == request.profile_id,
        )
        if not all(required_matches):
            raise RunnerEvidenceError("runner evidence does not match the authorized job")
        digest = hashlib.sha256(evidence_bytes).hexdigest()
        evidence_id = f"evd-{request.job_id[4:]}"
        relative = Path(engagement_id) / request.job_id / "evidence.json"
        destination = self._evidence_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".tmp")
        temporary.write_bytes(evidence_bytes)
        temporary.replace(destination)
        record = RunnerEvidenceRecord(
            evidence_id=evidence_id,
            job_id=request.job_id,
            engagement_id=engagement_id,
            relative_path=relative.as_posix(),
            sha256=digest,
            size_bytes=len(evidence_bytes),
            created_at=self._clock.now(),
            destruction_attested=False,
        )
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="runner.collect_evidence",
            outcome=AuditOutcome.COMPLETED,
            clock=self._clock,
            details={"job_id": request.job_id, "evidence_sha256": digest},
        )
        try:
            with self._store.audited_transaction(event) as connection:
                connection.execute(
                    """
                    INSERT INTO runner_evidence (
                        evidence_id, job_id, engagement_id, relative_path, sha256,
                        size_bytes, created_at, destruction_attested
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                    """,
                    (
                        record.evidence_id,
                        record.job_id,
                        record.engagement_id,
                        record.relative_path,
                        record.sha256,
                        record.size_bytes,
                        record.created_at.isoformat(),
                    ),
                )
                connection.execute(
                    """
                    UPDATE runner_jobs SET state = ?, evidence_id = ?, finished_at = ?
                    WHERE engagement_id = ? AND job_id = ?
                    """,
                    (
                        JobState.COLLECTING.value,
                        evidence_id,
                        self._clock.now().isoformat(),
                        engagement_id,
                        request.job_id,
                    ),
                )
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return record

    def _record_destroyed(
        self,
        *,
        engagement_id: str,
        actor_id: str,
        job_id: str,
        runtime_id: str,
        state: JobState,
        evidence_id: str | None,
        terminal_reason: str | None,
        destroyed_at: str,
    ) -> None:
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="runner.destroy",
            outcome=(
                AuditOutcome.COMPLETED if state is JobState.COMPLETED else AuditOutcome.DENIED
            ),
            clock=self._clock,
            details={"job_id": job_id, "state": state.value},
        )
        with self._store.audited_transaction(event) as connection:
            connection.execute(
                """
                UPDATE runner_jobs
                SET state = ?, runtime_id = ?, destroyed_at = ?, terminal_reason = ?
                WHERE engagement_id = ? AND job_id = ?
                """,
                (state.value, runtime_id, destroyed_at, terminal_reason, engagement_id, job_id),
            )
            if evidence_id is not None and state is JobState.COMPLETED:
                connection.execute(
                    """
                    UPDATE runner_evidence SET destruction_attested = 1
                    WHERE engagement_id = ? AND evidence_id = ?
                    """,
                    (engagement_id, evidence_id),
                )

    def _audit_denial(
        self,
        engagement_id: str,
        actor_id: str,
        job_id: str,
        reason: str,
    ) -> None:
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="runner.authorize",
            outcome=AuditOutcome.DENIED,
            clock=self._clock,
            details={"job_id": job_id, "reason": reason},
        )
        self._store.append_audit(engagement_id, event)

    def _load_job(self, engagement_id: str, job_id: str) -> RunnerJobRecord | None:
        row = self._store.fetch_one(
            "SELECT * FROM runner_jobs WHERE engagement_id = ? AND job_id = ?",
            (engagement_id, job_id),
        )
        if row is None:
            return None
        request = RunnerJobRequest(
            job_id=str(row["job_id"]),
            engagement_id=str(row["engagement_id"]),
            target_id=str(row["target_id"]),
            repository_id=str(row["repository_id"]),
            profile_id=str(row["profile_id"]),
            test_case_id=str(row["test_case_id"]),
        )
        return RunnerJobRecord(
            request=request,
            state=JobState(str(row["state"])),
            approval_id=str(row["approval_id"]),
            created_at=self._parse_required(row["created_at"]),
            started_at=self._parse_optional(row["started_at"]),
            finished_at=self._parse_optional(row["finished_at"]),
            destroyed_at=self._parse_optional(row["destroyed_at"]),
            evidence_id=str(row["evidence_id"]) if row["evidence_id"] else None,
            runtime_id=str(row["runtime_id"]) if row["runtime_id"] else None,
            terminal_reason=str(row["terminal_reason"]) if row["terminal_reason"] else None,
        )

    @staticmethod
    def _parse_required(value: object) -> datetime:
        return datetime.fromisoformat(str(value))

    @staticmethod
    def _parse_optional(value: object) -> datetime | None:
        return datetime.fromisoformat(str(value)) if value is not None else None
