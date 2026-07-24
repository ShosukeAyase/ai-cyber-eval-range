from pathlib import Path
import json

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

ROOT = Path(__file__).resolve().parents[2]


def load_schema(name: str):
    return json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text())


def load_yaml(name: str):
    return yaml.safe_load((ROOT / "examples" / name).read_text())


def schema_names() -> set[str]:
    paths = (ROOT / "schemas").glob("*.schema.json")
    return {path.name.removesuffix(".schema.json") for path in paths}


def test_schemas_are_valid_draft_2020_12():
    for path in (ROOT / "schemas").glob("*.schema.json"):
        schema = json.loads(path.read_text())
        Draft202012Validator.check_schema(schema)


def test_every_schema_has_a_valid_synthetic_example():
    missing = []
    for name in sorted(schema_names()):
        example = ROOT / "examples" / f"{name}.yaml"
        if not example.exists():
            missing.append(name)
            continue
        Draft202012Validator(
            load_schema(name),
            format_checker=FormatChecker(),
        ).validate(load_yaml(example.name))
    assert not missing, missing


def test_closed_objects_at_root():
    for path in (ROOT / "schemas").glob("*.schema.json"):
        schema = json.loads(path.read_text())
        assert schema["additionalProperties"] is False, path


def test_approval_states_match_typed_contract():
    schema = load_schema("approval")
    states = set(schema["properties"]["state"]["enum"])
    assert states == {"requested", "approved", "denied", "expired", "revoked", "consumed"}


def test_roe_requires_approval_for_dangerous_actions():
    roe = load_yaml("roe.yaml")
    for action in ["state_change", "credentialed_test", "poc_validation", "patch_validation"]:
        assert roe["approval_requirements"][action] is True


def test_scenario_requires_destruction():
    scenario = load_yaml("scenario.yaml")
    assert all(scenario["destruction"].values())


def test_tool_request_rejects_raw_network_or_command_fields():
    instance = load_yaml("tool-request.yaml")
    instance["raw_url"] = "https://example.invalid"
    with pytest.raises(ValidationError):
        Draft202012Validator(load_schema("tool-request")).validate(instance)
