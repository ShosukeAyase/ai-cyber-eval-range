from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]

def test_prohibited_actions_are_present():
    roe = yaml.safe_load((ROOT/"examples/roe.yaml").read_text())
    required = {"credential_dumping","persistence","evasion","log_deletion","data_exfiltration","denial_of_service","social_engineering","autonomous_merge","autonomous_deployment","autonomous_patch_application"}
    assert required <= set(roe["prohibited_actions"])

def test_no_public_routes_in_scenario():
    scn = yaml.safe_load((ROOT/"examples/scenario.yaml").read_text())
    net = scn["network"]
    assert net["internet_route"] is False
    assert net["corporate_route"] is False
    assert net["production_route"] is False
    assert net["metadata_access"] is False

def test_policy_default_deny():
    for name in ["tool_authorization.rego", "stop_conditions.rego", "data_handling.rego"]:
        text = (ROOT/"policies"/name).read_text()
        assert "default" in text

def test_tool_authorization_requires_destination_match():
    text = (ROOT/"policies/tool_authorization.rego").read_text()
    assert "input.destination_matches == true" in text
    assert "input.target_in_scope == true" in text
    assert "input.within_limits == true" in text
