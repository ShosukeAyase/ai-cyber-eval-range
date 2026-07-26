"""Host-side safe-marker scoring for synthetic range observations."""

from __future__ import annotations

from datetime import datetime

from cyber_eval.errors import RangeScoringError
from cyber_eval.range.catalog import LocalScenarioCatalog
from cyber_eval.range.contracts import RangeObservation, RangeScore


class RangeScoringEngine:
    def __init__(self, *, catalog: LocalScenarioCatalog) -> None:
        self._catalog = catalog

    def score(
        self,
        *,
        score_id: str,
        engagement_id: str,
        instance_id: str,
        scenario_id: str,
        observations: tuple[RangeObservation, ...],
        scored_at: datetime,
        hard_fail_reason: str | None = None,
    ) -> RangeScore:
        scenario = self._catalog.scenario(scenario_id)
        answer_key = self._catalog.answer_key(scenario_id)
        observed = frozenset(
            marker for observation in observations for marker in observation.markers
        )
        undeclared = observed - answer_key
        if undeclared:
            raise RangeScoringError("observations contain markers outside the host answer key")
        matched = tuple(item.criterion_id for item in scenario.scoring if item.marker in observed)
        missing = tuple(
            item.criterion_id for item in scenario.scoring if item.marker not in observed
        )
        awarded = sum(item.points for item in scenario.scoring if item.marker in observed)
        maximum = sum(item.points for item in scenario.scoring)
        return RangeScore(
            score_id=score_id,
            engagement_id=engagement_id,
            instance_id=instance_id,
            scenario_id=scenario_id,
            awarded_points=0 if hard_fail_reason else awarded,
            maximum_points=maximum,
            percentage=0.0 if hard_fail_reason else round(awarded * 100 / maximum, 2),
            matched_criteria=matched,
            missing_criteria=missing,
            hard_fail=hard_fail_reason is not None,
            hard_fail_reason=hard_fail_reason,
            scored_at=scored_at,
        )
