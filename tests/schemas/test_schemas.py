from pathlib import Path
import json
import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
PAIRS = [
    ("engagement", "engagement.yaml"),
    ("roe", "roe.yaml"),
    ("scenario", "scenario.yaml"),
]

def load_schema(name):
    return json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text())

def load_yaml(name):
    return yaml.safe_load((ROOT / "examples" / name).read_text())

def test_schemas_are_valid_draft_2020_12():
    for path in (ROOT / "schemas").glob("*.schema.json"):
        schema = json.loads(path.read_text())
        Draft202012Validator.check_schema(schema)

def test_examples_validate():
    for schema_name, example_name in PAIRS:
        schema = load_schema(schema_name)
        instance = load_yaml(example_name)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(instance)

def test_closed_objects_at_root():
    for path in (ROOT / "schemas").glob("*.schema.json"):
        schema = json.loads(path.read_text())
        assert schema["additionalProperties"] is False, path

def test_approval_states():
    schema = load_schema("approval")
    states = set(schema["properties"]["state"]["enum"])
    assert states == {"requested", "approved", "denied", "expired", "revoked", "consumed"}

def test_roe_requires_approval_for_dangerous_actions():
    roe = load_yaml("roe.yaml")
    for action in ["state_change", "credentialed_test", "poc_validation", "patch_validation"]:
        assert roe["approval_requirements"][action] is True

def test_scenario_requires_destruction():
    scn = load_yaml("scenario.yaml")
    assert all(scn["destruction"].values())
