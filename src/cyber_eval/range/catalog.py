"""Validated local catalog for immutable synthetic Cyber Range scenarios."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, cast

from cyber_eval.errors import ScenarioCatalogError, ScopeViolationError
from cyber_eval.identifiers import require_generic_object_id, require_identifier
from cyber_eval.range.contracts import (
    CriterionKind,
    RangeOperation,
    RangeScenario,
    ScenarioCriterion,
    ScenarioKind,
    ScenarioOperation,
)

_MARKER = re.compile(r"^RANGE-MARKER-[A-Z0-9-]{3,96}$")
_DIGEST = re.compile(r"^sha256:[a-f0-9]{64}$")
_REQUIRED_SCENARIOS = frozenset(
    {
        "scn-web-access-control",
        "scn-api-authorization",
        "scn-dependency-advisory",
        "scn-iac-misconfiguration",
        "scn-kubernetes-rbac",
        "scn-indirect-prompt-injection",
        "scn-scope-redirection",
    }
)


class LocalScenarioCatalog:
    """Load reviewed scenario packages; public callers receive IDs, never paths."""

    def __init__(self, catalog_root: Path) -> None:
        self._root = catalog_root.expanduser().resolve(strict=True)
        if not self._root.is_dir():
            raise ScenarioCatalogError("scenario catalog root must be a directory")
        self._scenarios = self._load_all()

    def scenario(self, scenario_id: str) -> RangeScenario:
        require_generic_object_id(scenario_id)
        try:
            return self._scenarios[scenario_id]
        except KeyError as exc:
            raise ScopeViolationError("scenario identifier is not registered") from exc

    def scenario_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._scenarios))

    def answer_key(self, scenario_id: str) -> frozenset[str]:
        scenario = self.scenario(scenario_id)
        document = _load_json(scenario.answer_key_path)
        markers = document.get("required_markers")
        if not isinstance(markers, list) or not markers:
            raise ScenarioCatalogError("answer key must contain required markers")
        result = frozenset(_required_marker(item) for item in markers)
        declared = frozenset(item.marker for item in scenario.scoring)
        if result != declared:
            raise ScenarioCatalogError("answer key and scoring criteria do not match")
        return result

    def _load_all(self) -> dict[str, RangeScenario]:
        scenarios: dict[str, RangeScenario] = {}
        for package_root in sorted(path for path in self._root.iterdir() if path.is_dir()):
            manifest_path = package_root / "scenario.json"
            if not manifest_path.is_file():
                raise ScenarioCatalogError(f"missing scenario manifest: {package_root.name}")
            scenario = self._parse(package_root, _load_json(manifest_path))
            if scenario.scenario_id in scenarios:
                raise ScenarioCatalogError("duplicate scenario identifier")
            scenarios[scenario.scenario_id] = scenario
        if frozenset(scenarios) != _REQUIRED_SCENARIOS:
            raise ScenarioCatalogError("catalog must contain the seven approved Phase 05 scenarios")
        return scenarios

    def _parse(self, package_root: Path, raw: dict[str, Any]) -> RangeScenario:
        expected_keys = {
            "schema_version",
            "scenario_id",
            "name",
            "kind",
            "target_id",
            "test_case_id",
            "initial_state",
            "allowed_operations",
            "forbidden_operations",
            "synthetic_data",
            "expected_findings",
            "expected_detections",
            "stop_conditions",
            "scoring",
            "reset",
            "destruction",
            "network",
            "lateral_movement",
        }
        if set(raw) != expected_keys or raw.get("schema_version") != "1.0":
            raise ScenarioCatalogError("scenario manifest keys or version are invalid")
        scenario_id = _required_text(raw, "scenario_id")
        require_generic_object_id(scenario_id)
        if package_root.name != scenario_id:
            raise ScenarioCatalogError("scenario directory must match scenario_id")
        target_id = _required_text(raw, "target_id")
        test_case_id = _required_text(raw, "test_case_id")
        require_identifier(target_id, "tgt")
        require_identifier(test_case_id, "tc")
        synthetic = _required_object(raw, "synthetic_data")
        if synthetic != {
            "root": "synthetic",
            "contains_real_data": False,
            "contains_credentials": False,
            "marker_prefix": "RANGE-MARKER-",
        }:
            raise ScenarioCatalogError("scenario synthetic-data declaration is invalid")
        network = _required_object(raw, "network")
        if network.get("mode") != "none" or network.get("external_access") is not False:
            raise ScenarioCatalogError("Phase 05 scenarios must have no network")
        synthetic_root = (package_root / "synthetic").resolve(strict=True)
        if not synthetic_root.is_dir() or package_root not in synthetic_root.parents:
            raise ScenarioCatalogError("synthetic root escapes the scenario package")
        answer_key = (package_root / "answer-key.json").resolve(strict=True)
        if package_root not in answer_key.parents:
            raise ScenarioCatalogError("answer key escapes the scenario package")
        baseline_digest = _required_text(_required_object(raw, "reset"), "baseline_digest")
        if not _DIGEST.fullmatch(baseline_digest):
            raise ScenarioCatalogError("baseline digest is invalid")
        if f"sha256:{hash_tree(synthetic_root)}" != baseline_digest:
            raise ScenarioCatalogError("synthetic baseline digest mismatch")
        operations = tuple(
            _parse_operation(item) for item in _required_list(raw, "allowed_operations")
        )
        if not operations:
            raise ScenarioCatalogError("scenario must allow at least one predefined operation")
        if len({item.operation_id for item in operations}) != len(operations):
            raise ScenarioCatalogError("operation identifiers must be unique")
        asset_ids = frozenset(item.asset_id for item in operations)
        lateral = _required_object(raw, "lateral_movement")
        lateral_assets = frozenset(cast(list[str], lateral.get("allowed_asset_ids", [])))
        if not lateral_assets <= asset_ids:
            raise ScenarioCatalogError("lateral movement assets must be declared scenario assets")
        forbidden = tuple(
            RangeOperation(item) for item in _required_list(raw, "forbidden_operations")
        )
        scoring = tuple(_parse_criterion(item) for item in _required_list(raw, "scoring"))
        if not scoring or sum(item.points for item in scoring) != 100:
            raise ScenarioCatalogError("scenario scoring must total 100 points")
        destruction = _required_object(raw, "destruction")
        required_destruction = (
            "remove_instance_state",
            "remove_network_state",
            "remove_temporary_storage",
            "attestation_required",
        )
        if not all(destruction.get(key) is True for key in required_destruction):
            raise ScenarioCatalogError("scenario destruction requirements are incomplete")
        return RangeScenario(
            scenario_id=scenario_id,
            name=_required_text(raw, "name"),
            kind=ScenarioKind(_required_text(raw, "kind")),
            target_id=target_id,
            test_case_id=test_case_id,
            initial_state=_required_text(raw, "initial_state"),
            allowed_operations=operations,
            forbidden_operations=forbidden,
            asset_ids=asset_ids,
            lateral_movement_asset_ids=lateral_assets,
            expected_findings=tuple(
                _required_marker(item) for item in _required_list(raw, "expected_findings")
            ),
            expected_detections=tuple(
                _required_marker(item) for item in _required_list(raw, "expected_detections")
            ),
            stop_conditions=tuple(str(item) for item in _required_list(raw, "stop_conditions")),
            scoring=scoring,
            baseline_digest=baseline_digest,
            package_root=package_root,
            synthetic_root=synthetic_root,
            answer_key_path=answer_key,
        )


def hash_tree(root: Path) -> str:
    digest = hashlib.sha256()
    count = 0
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink():
            raise ScenarioCatalogError("scenario packages cannot contain symbolic links")
        if not path.is_file():
            continue
        count += 1
        if count > 1000:
            raise ScenarioCatalogError("scenario package contains too many files")
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        data = path.read_bytes()
        if len(data) > 2 * 1024 * 1024:
            raise ScenarioCatalogError("scenario file exceeds the approved size")
        digest.update(data)
    if count == 0:
        raise ScenarioCatalogError("scenario synthetic data cannot be empty")
    return digest.hexdigest()


def _parse_operation(raw: object) -> ScenarioOperation:
    item = _object(raw)
    operation_id = _required_text(item, "operation_id")
    asset_id = _required_text(item, "asset_id")
    require_generic_object_id(operation_id)
    require_generic_object_id(asset_id)
    markers = tuple(_required_marker(value) for value in _required_list(item, "markers"))
    return ScenarioOperation(
        operation_id=operation_id,
        operation=RangeOperation(_required_text(item, "operation")),
        asset_id=asset_id,
        observation_markers=markers,
    )


def _parse_criterion(raw: object) -> ScenarioCriterion:
    item = _object(raw)
    criterion_id = _required_text(item, "criterion_id")
    require_generic_object_id(criterion_id)
    points = item.get("points")
    if not isinstance(points, int) or not 1 <= points <= 100:
        raise ScenarioCatalogError("criterion points are invalid")
    return ScenarioCriterion(
        criterion_id=criterion_id,
        kind=CriterionKind(_required_text(item, "kind")),
        marker=_required_marker(item.get("marker")),
        points=points,
    )


def _required_marker(value: object) -> str:
    if not isinstance(value, str) or not _MARKER.fullmatch(value):
        raise ScenarioCatalogError("safe marker is invalid")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScenarioCatalogError(f"invalid JSON document: {path.name}") from exc
    return _object(document)


def _required_text(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ScenarioCatalogError(f"{key} must be non-empty text")
    return value


def _required_object(raw: dict[str, Any], key: str) -> dict[str, Any]:
    return _object(raw.get(key))


def _required_list(raw: dict[str, Any], key: str) -> list[Any]:
    value = raw.get(key)
    if not isinstance(value, list):
        raise ScenarioCatalogError(f"{key} must be a list")
    return value


def _object(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ScenarioCatalogError("expected an object with string keys")
    return cast(dict[str, Any], value)
