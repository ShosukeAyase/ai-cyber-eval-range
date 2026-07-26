"""Control Plane service for approved synthetic Cyber Range lifecycle operations."""

from __future__ import annotations

import json
from datetime import datetime

from cyber_eval.approval_service import ApprovalService
from cyber_eval.audit import make_audit_event
from cyber_eval.domain import AuditOutcome, WriteOperation
from cyber_eval.emergency_stop import EmergencyStopService
from cyber_eval.errors import ControlPlaneError, RangeStateError, ScopeViolationError
from cyber_eval.identifiers import require_generic_object_id, require_identifier
from cyber_eval.interfaces import Clock
from cyber_eval.range.catalog import LocalScenarioCatalog
from cyber_eval.range.contracts import (
    RangeActionRequest,
    RangeDestructionAttestation,
    RangeInstanceRecord,
    RangeInstanceState,
    RangeObservation,
    RangeScore,
)
from cyber_eval.range.runtime import LocalCyberRangeRuntime
from cyber_eval.range.scoring import RangeScoringEngine
from cyber_eval.scope_roe_service import ScopeRoeService
from cyber_eval.store import LocalControlPlaneStore


class CyberRangeService:
    def __init__(
        self,
        *,
        store: LocalControlPlaneStore,
        approvals: ApprovalService,
        scope_roe: ScopeRoeService,
        emergency_stop: EmergencyStopService,
        catalog: LocalScenarioCatalog,
        runtime: LocalCyberRangeRuntime,
        scoring: RangeScoringEngine,
        clock: Clock,
    ) -> None:
        self._store = store
        self._approvals = approvals
        self._scope_roe = scope_roe
        self._emergency_stop = emergency_stop
        self._catalog = catalog
        self._runtime = runtime
        self._scoring = scoring
        self._clock = clock

    def create_instance(
        self,
        engagement_id: str,
        actor_id: str,
        approval_id: str,
        instance_id: str,
        scenario_id: str,
    ) -> RangeInstanceRecord:
        _validate_ids(engagement_id, instance_id, scenario_id)
        scenario = self._catalog.scenario(scenario_id)
        self._scope_roe.assert_current(
            engagement_id,
            scenario.target_id,
            scenario.test_case_id,
        )
        self._require_running(engagement_id)
        approval = self._approvals._require_write(
            engagement_id=engagement_id,
            actor_id=actor_id,
            approval_id=approval_id,
            operation=WriteOperation.CREATE_RANGE_INSTANCE,
            resource_id=scenario.target_id,
        )
        created_at = self._clock.now()
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="range.create_instance",
            outcome=AuditOutcome.COMPLETED,
            approval_id=approval_id,
            clock=self._clock,
            details={"instance_id": instance_id, "scenario_id": scenario_id},
        )
        record: RangeInstanceRecord | None = None
        try:
            with self._store.audited_transaction(event) as connection:
                self._approvals._consume_in_transaction(connection, approval)
                record = self._runtime.create(
                    engagement_id=engagement_id,
                    instance_id=instance_id,
                    scenario=scenario,
                    created_at=created_at,
                )
                connection.execute(
                    """
                    INSERT INTO range_instances (
                        instance_id, engagement_id, scenario_id, target_id, test_case_id,
                        state, baseline_digest, created_at, reset_count, destroyed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, NULL)
                    """,
                    (
                        instance_id,
                        engagement_id,
                        scenario_id,
                        scenario.target_id,
                        scenario.test_case_id,
                        RangeInstanceState.READY.value,
                        scenario.baseline_digest,
                        created_at.isoformat(),
                    ),
                )
        except Exception:
            if record is not None:
                self._runtime.destroy(engagement_id, instance_id, self._clock.now())
            raise
        if record is None:
            raise ControlPlaneError("range instance creation did not produce a record")
        return record

    def perform_action(
        self,
        engagement_id: str,
        actor_id: str,
        request: RangeActionRequest,
    ) -> RangeObservation:
        require_identifier(engagement_id, "eng")
        if request.engagement_id != engagement_id:
            raise ScopeViolationError("range action engagement mismatch")
        identifiers = (
            request.action_id,
            request.instance_id,
            request.operation_id,
            request.asset_id,
        )
        for value in identifiers:
            require_generic_object_id(value)
        instance = self.get_instance(engagement_id, request.instance_id)
        scenario = self._catalog.scenario(instance.scenario_id)
        self._scope_roe.assert_current(engagement_id, scenario.target_id, scenario.test_case_id)
        self._require_running(engagement_id)
        observation_id = f"obs-{request.action_id.removeprefix('act-')}"
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="range.perform_action",
            outcome=AuditOutcome.COMPLETED,
            clock=self._clock,
            details={
                "instance_id": request.instance_id,
                "operation_id": request.operation_id,
                "asset_id": request.asset_id,
            },
        )
        with self._store.audited_transaction(event) as connection:
            observation = self._runtime.observe(
                request,
                observation_id=observation_id,
                observed_at=self._clock.now(),
            )
            connection.execute(
                """
                INSERT INTO range_observations (
                    observation_id, engagement_id, instance_id, scenario_id,
                    operation_id, asset_id, markers, observed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    observation.observation_id,
                    observation.engagement_id,
                    observation.instance_id,
                    observation.scenario_id,
                    observation.operation_id,
                    observation.asset_id,
                    json.dumps(list(observation.markers)),
                    observation.observed_at.isoformat(),
                ),
            )
        return observation

    def reset_instance(
        self,
        engagement_id: str,
        actor_id: str,
        approval_id: str,
        instance_id: str,
    ) -> RangeInstanceRecord:
        instance = self.get_instance(engagement_id, instance_id)
        self._require_running(engagement_id)
        approval = self._approvals._require_write(
            engagement_id=engagement_id,
            actor_id=actor_id,
            approval_id=approval_id,
            operation=WriteOperation.RESET_RANGE_INSTANCE,
            resource_id=instance.target_id,
        )
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="range.reset_instance",
            outcome=AuditOutcome.COMPLETED,
            approval_id=approval_id,
            clock=self._clock,
            details={"instance_id": instance_id},
        )
        with self._store.audited_transaction(event) as connection:
            self._approvals._consume_in_transaction(connection, approval)
            record = self._runtime.reset(engagement_id, instance_id, self._clock.now())
            connection.execute(
                """
                UPDATE range_instances
                SET state = ?, reset_count = ?, destroyed_at = NULL
                WHERE engagement_id = ? AND instance_id = ?
                """,
                (
                    RangeInstanceState.READY.value,
                    record.reset_count,
                    engagement_id,
                    instance_id,
                ),
            )
            connection.execute(
                "DELETE FROM range_observations WHERE engagement_id = ? AND instance_id = ?",
                (engagement_id, instance_id),
            )
            connection.execute(
                "DELETE FROM range_scores WHERE engagement_id = ? AND instance_id = ?",
                (engagement_id, instance_id),
            )
        return record

    def score_instance(
        self,
        engagement_id: str,
        actor_id: str,
        instance_id: str,
        score_id: str,
    ) -> RangeScore:
        require_generic_object_id(score_id)
        instance = self.get_instance(engagement_id, instance_id)
        observations = self._observations(engagement_id, instance_id)
        score = self._scoring.score(
            score_id=score_id,
            engagement_id=engagement_id,
            instance_id=instance_id,
            scenario_id=instance.scenario_id,
            observations=observations,
            scored_at=self._clock.now(),
        )
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="range.score_instance",
            outcome=AuditOutcome.COMPLETED,
            clock=self._clock,
            details={"instance_id": instance_id, "percentage": str(score.percentage)},
        )
        with self._store.audited_transaction(event) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO range_scores (
                    score_id, engagement_id, instance_id, scenario_id,
                    awarded_points, maximum_points, percentage,
                    matched_criteria, missing_criteria, hard_fail,
                    hard_fail_reason, scored_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    score.score_id,
                    score.engagement_id,
                    score.instance_id,
                    score.scenario_id,
                    score.awarded_points,
                    score.maximum_points,
                    score.percentage,
                    json.dumps(list(score.matched_criteria)),
                    json.dumps(list(score.missing_criteria)),
                    int(score.hard_fail),
                    score.hard_fail_reason,
                    score.scored_at.isoformat(),
                ),
            )
        return score

    def destroy_instance(
        self,
        engagement_id: str,
        actor_id: str,
        approval_id: str,
        instance_id: str,
    ) -> RangeDestructionAttestation:
        instance = self.get_instance(engagement_id, instance_id)
        approval = self._approvals._require_write(
            engagement_id=engagement_id,
            actor_id=actor_id,
            approval_id=approval_id,
            operation=WriteOperation.DESTROY_RANGE_INSTANCE,
            resource_id=instance.target_id,
        )
        destroyed_at = self._clock.now()
        event = make_audit_event(
            engagement_id=engagement_id,
            actor_id=actor_id,
            operation="range.destroy_instance",
            outcome=AuditOutcome.COMPLETED,
            approval_id=approval_id,
            clock=self._clock,
            details={"instance_id": instance_id},
        )
        with self._store.audited_transaction(event) as connection:
            self._approvals._consume_in_transaction(connection, approval)
            attestation = self._runtime.destroy(engagement_id, instance_id, destroyed_at)
            if not attestation.instance_root_removed or not attestation.active_runtime_removed:
                raise RangeStateError("range destruction attestation failed")
            connection.execute(
                """
                UPDATE range_instances SET state = ?, destroyed_at = ?
                WHERE engagement_id = ? AND instance_id = ?
                """,
                (
                    RangeInstanceState.DESTROYED.value,
                    destroyed_at.isoformat(),
                    engagement_id,
                    instance_id,
                ),
            )
        return attestation

    def get_instance(self, engagement_id: str, instance_id: str) -> RangeInstanceRecord:
        require_identifier(engagement_id, "eng")
        require_generic_object_id(instance_id)
        row = self._store.fetch_one(
            "SELECT * FROM range_instances WHERE engagement_id = ? AND instance_id = ?",
            (engagement_id, instance_id),
        )
        if row is None:
            raise RangeStateError("range instance is unknown")
        state = RangeInstanceState(str(row["state"]))
        if state is RangeInstanceState.DESTROYED:
            raise RangeStateError("range instance is destroyed")
        runtime = self._runtime.record(engagement_id, instance_id)
        return RangeInstanceRecord(
            instance_id=str(row["instance_id"]),
            engagement_id=str(row["engagement_id"]),
            scenario_id=str(row["scenario_id"]),
            target_id=str(row["target_id"]),
            test_case_id=str(row["test_case_id"]),
            state=runtime.state,
            root_path=runtime.root_path,
            baseline_digest=str(row["baseline_digest"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            reset_count=int(row["reset_count"]),
            destroyed_at=None,
        )

    def _observations(
        self,
        engagement_id: str,
        instance_id: str,
    ) -> tuple[RangeObservation, ...]:
        rows = self._store.fetch_all(
            """
            SELECT * FROM range_observations
            WHERE engagement_id = ? AND instance_id = ?
            ORDER BY observed_at, observation_id
            """,
            (engagement_id, instance_id),
        )
        return tuple(
            RangeObservation(
                observation_id=str(row["observation_id"]),
                engagement_id=str(row["engagement_id"]),
                instance_id=str(row["instance_id"]),
                scenario_id=str(row["scenario_id"]),
                operation_id=str(row["operation_id"]),
                asset_id=str(row["asset_id"]),
                markers=tuple(str(item) for item in json.loads(str(row["markers"]))),
                observed_at=datetime.fromisoformat(str(row["observed_at"])),
            )
            for row in rows
        )

    def _require_running(self, engagement_id: str) -> None:
        if self._emergency_stop._is_active_unlogged(engagement_id):
            raise RangeStateError("Emergency Stop is active")


def _validate_ids(engagement_id: str, instance_id: str, scenario_id: str) -> None:
    require_identifier(engagement_id, "eng")
    require_generic_object_id(instance_id)
    require_generic_object_id(scenario_id)
