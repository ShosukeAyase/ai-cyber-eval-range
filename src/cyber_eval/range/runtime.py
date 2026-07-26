"""Disposable filesystem runtime for non-networked synthetic range instances."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import RLock

from cyber_eval.errors import RangeStateError, RangeStopConditionError, ScopeViolationError
from cyber_eval.range.catalog import hash_tree
from cyber_eval.range.contracts import (
    RangeActionRequest,
    RangeDestructionAttestation,
    RangeInstanceRecord,
    RangeInstanceState,
    RangeObservation,
    RangeScenario,
)


@dataclass(slots=True)
class _ActiveInstance:
    record: RangeInstanceRecord
    scenario: RangeScenario


class LocalCyberRangeRuntime:
    """No-listener runtime; actions are deterministic lookups over a copied baseline."""

    def __init__(self, runtime_root: Path) -> None:
        self._root = runtime_root.expanduser().resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        self._active: dict[str, _ActiveInstance] = {}
        self._lock = RLock()
        self._action_count = 0

    @property
    def action_count(self) -> int:
        return self._action_count

    def create(
        self,
        *,
        engagement_id: str,
        instance_id: str,
        scenario: RangeScenario,
        created_at: datetime,
    ) -> RangeInstanceRecord:
        with self._lock:
            if instance_id in self._active:
                raise RangeStateError("range instance already exists")
        instance_root = self._instance_root(engagement_id, instance_id)
        if instance_root.exists():
            raise RangeStateError("range instance root already exists")
        instance_root.parent.mkdir(parents=True, exist_ok=True)
        state_root = instance_root / "state"
        try:
            shutil.copytree(scenario.synthetic_root, state_root, symlinks=False)
            _write_metadata(instance_root, scenario, created_at, reset_count=0)
            if f"sha256:{hash_tree(state_root)}" != scenario.baseline_digest:
                raise RangeStateError("created range state does not match baseline")
        except Exception:
            shutil.rmtree(instance_root, ignore_errors=True)
            raise
        record = RangeInstanceRecord(
            instance_id=instance_id,
            engagement_id=engagement_id,
            scenario_id=scenario.scenario_id,
            target_id=scenario.target_id,
            test_case_id=scenario.test_case_id,
            state=RangeInstanceState.READY,
            root_path=instance_root,
            baseline_digest=scenario.baseline_digest,
            created_at=created_at,
            reset_count=0,
            destroyed_at=None,
        )
        with self._lock:
            self._active[instance_id] = _ActiveInstance(record, scenario)
        return record

    def observe(
        self,
        request: RangeActionRequest,
        *,
        observation_id: str,
        observed_at: datetime,
    ) -> RangeObservation:
        active = self._require_active(request.engagement_id, request.instance_id)
        if active.record.state is not RangeInstanceState.READY:
            raise RangeStateError("range instance is not ready")
        operation = next(
            (
                item
                for item in active.scenario.allowed_operations
                if item.operation_id == request.operation_id
            ),
            None,
        )
        if operation is None:
            self._stop(request.instance_id)
            raise RangeStopConditionError("operation is not allowlisted for the scenario")
        asset_mismatch = request.asset_id != operation.asset_id
        asset_outside_scope = request.asset_id not in active.scenario.asset_ids
        if asset_mismatch or asset_outside_scope:
            self._stop(request.instance_id)
            raise ScopeViolationError("asset is outside the scenario scope")
        if (
            active.scenario.lateral_movement_asset_ids
            and request.asset_id not in active.scenario.lateral_movement_asset_ids
        ):
            self._stop(request.instance_id)
            raise ScopeViolationError("lateral movement is outside the declared scenario assets")
        with self._lock:
            self._action_count += 1
        return RangeObservation(
            observation_id=observation_id,
            engagement_id=request.engagement_id,
            instance_id=request.instance_id,
            scenario_id=active.scenario.scenario_id,
            operation_id=request.operation_id,
            asset_id=request.asset_id,
            markers=operation.observation_markers,
            observed_at=observed_at,
        )

    def reset(
        self,
        engagement_id: str,
        instance_id: str,
        reset_at: datetime,
    ) -> RangeInstanceRecord:
        active = self._require_active(engagement_id, instance_id)
        state_root = active.record.root_path / "state"
        shutil.rmtree(state_root, ignore_errors=True)
        try:
            shutil.copytree(active.scenario.synthetic_root, state_root, symlinks=False)
            digest = f"sha256:{hash_tree(state_root)}"
            if digest != active.scenario.baseline_digest:
                raise RangeStateError("reset range state does not match baseline")
            reset_count = active.record.reset_count + 1
            _write_metadata(active.record.root_path, active.scenario, reset_at, reset_count)
        except Exception:
            shutil.rmtree(active.record.root_path, ignore_errors=True)
            with self._lock:
                self._active.pop(instance_id, None)
            raise
        record = RangeInstanceRecord(
            instance_id=active.record.instance_id,
            engagement_id=active.record.engagement_id,
            scenario_id=active.record.scenario_id,
            target_id=active.record.target_id,
            test_case_id=active.record.test_case_id,
            state=RangeInstanceState.READY,
            root_path=active.record.root_path,
            baseline_digest=active.record.baseline_digest,
            created_at=active.record.created_at,
            reset_count=reset_count,
            destroyed_at=None,
        )
        with self._lock:
            self._active[instance_id] = _ActiveInstance(record, active.scenario)
        return record

    def destroy(
        self,
        engagement_id: str,
        instance_id: str,
        destroyed_at: datetime,
    ) -> RangeDestructionAttestation:
        with self._lock:
            active = self._active.pop(instance_id, None)
        if active is None or active.record.engagement_id != engagement_id:
            root = self._instance_root(engagement_id, instance_id)
            scenario_id = "scn-unknown-local"
        else:
            root = active.record.root_path
            scenario_id = active.record.scenario_id
        shutil.rmtree(root, ignore_errors=True)
        return RangeDestructionAttestation(
            instance_id=instance_id,
            engagement_id=engagement_id,
            scenario_id=scenario_id,
            destroyed_at=destroyed_at,
            instance_root_removed=not root.exists(),
            active_runtime_removed=instance_id not in self.active_instance_ids(engagement_id),
            credential_material_present=False,
        )

    def active_instance_ids(self, engagement_id: str) -> tuple[str, ...]:
        with self._lock:
            return tuple(
                sorted(
                    instance_id
                    for instance_id, active in self._active.items()
                    if active.record.engagement_id == engagement_id
                )
            )

    def record(self, engagement_id: str, instance_id: str) -> RangeInstanceRecord:
        return self._require_active(engagement_id, instance_id).record

    def state_digest(self, engagement_id: str, instance_id: str) -> str:
        active = self._require_active(engagement_id, instance_id)
        return f"sha256:{hash_tree(active.record.root_path / 'state')}"

    def _instance_root(self, engagement_id: str, instance_id: str) -> Path:
        root = (self._root / engagement_id / instance_id).resolve()
        if self._root not in root.parents:
            raise RangeStateError("range instance path escapes the runtime root")
        return root

    def _require_active(self, engagement_id: str, instance_id: str) -> _ActiveInstance:
        with self._lock:
            active = self._active.get(instance_id)
        if active is None or active.record.engagement_id != engagement_id:
            raise RangeStateError("range instance is not active")
        return active

    def _stop(self, instance_id: str) -> None:
        with self._lock:
            active = self._active.get(instance_id)
            if active is None:
                return
            stopped = RangeInstanceRecord(
                instance_id=active.record.instance_id,
                engagement_id=active.record.engagement_id,
                scenario_id=active.record.scenario_id,
                target_id=active.record.target_id,
                test_case_id=active.record.test_case_id,
                state=RangeInstanceState.STOPPED,
                root_path=active.record.root_path,
                baseline_digest=active.record.baseline_digest,
                created_at=active.record.created_at,
                reset_count=active.record.reset_count,
                destroyed_at=None,
            )
            self._active[instance_id] = _ActiveInstance(stopped, active.scenario)


def _write_metadata(
    instance_root: Path,
    scenario: RangeScenario,
    changed_at: datetime,
    reset_count: int,
) -> None:
    metadata = {
        "schema_version": "1.0",
        "scenario_id": scenario.scenario_id,
        "baseline_digest": scenario.baseline_digest,
        "network_mode": "none",
        "changed_at": changed_at.isoformat(),
        "reset_count": reset_count,
    }
    (instance_root / "instance.json").write_text(
        json.dumps(metadata, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
