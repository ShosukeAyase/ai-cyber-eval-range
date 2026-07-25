"""Independent Emergency Stop monitor for active Runner jobs."""

from __future__ import annotations

from cyber_eval.emergency_stop import EmergencyStopService
from cyber_eval.runner.runtime import RunnerRuntime


class KillSwitchMonitor:
    """Enforce an already-audited stop state without model participation."""

    def __init__(self, *, emergency_stop: EmergencyStopService, runtime: RunnerRuntime) -> None:
        self._emergency_stop = emergency_stop
        self._runtime = runtime

    def enforce(self, engagement_id: str) -> tuple[str, ...]:
        if not self._emergency_stop._is_active_unlogged(engagement_id):
            return ()
        active = self._runtime.active_job_ids(engagement_id)
        for job_id in active:
            self._runtime.terminate(engagement_id, job_id)
        return active
