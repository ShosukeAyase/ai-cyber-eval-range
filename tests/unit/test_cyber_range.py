from __future__ import annotations

from dataclasses import fields

import pytest

from cyber_eval.errors import RangeScoringError
from cyber_eval.range.catalog import LocalScenarioCatalog
from cyber_eval.range.contracts import RangeActionRequest, RangeObservation
from cyber_eval.range.scoring import RangeScoringEngine
from tests.harness.control_plane import ENGAGEMENT_ID, NOW
from tests.harness.range import CATALOG_ROOT


def test_catalog_loads_exactly_seven_complete_scenarios() -> None:
    catalog = LocalScenarioCatalog(CATALOG_ROOT)
    assert len(catalog.scenario_ids()) == 7
    for scenario_id in catalog.scenario_ids():
        scenario = catalog.scenario(scenario_id)
        assert scenario.allowed_operations
        assert scenario.forbidden_operations
        assert scenario.expected_findings
        assert scenario.expected_detections
        assert scenario.stop_conditions
        assert sum(item.points for item in scenario.scoring) == 100
        assert catalog.answer_key(scenario_id) == frozenset(
            item.marker for item in scenario.scoring
        )


def test_range_action_contract_has_no_destination_or_command_fields() -> None:
    names = {field.name for field in fields(RangeActionRequest)}
    assert names.isdisjoint(
        {"url", "ip", "hostname", "endpoint", "command", "shell", "path", "port"}
    )


def test_scoring_rejects_markers_outside_host_answer_key() -> None:
    catalog = LocalScenarioCatalog(CATALOG_ROOT)
    scoring = RangeScoringEngine(catalog=catalog)
    observation = RangeObservation(
        observation_id="obs-invalid-marker",
        engagement_id=ENGAGEMENT_ID,
        instance_id="rng-web-local",
        scenario_id="scn-web-access-control",
        operation_id="rop-web-inspect-records",
        asset_id="ast-web-records",
        markers=("RANGE-MARKER-NOT-IN-ANSWER-KEY",),
        observed_at=NOW,
    )
    with pytest.raises(RangeScoringError):
        scoring.score(
            score_id="scr-invalid-marker",
            engagement_id=ENGAGEMENT_ID,
            instance_id="rng-web-local",
            scenario_id="scn-web-access-control",
            observations=(observation,),
            scored_at=NOW,
        )
