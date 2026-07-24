from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_prohibited_actions_are_present():
    roe = yaml.safe_load((ROOT / "examples/roe.yaml").read_text())
    required = {
        "credential_dumping",
        "persistence",
        "evasion",
        "log_deletion",
        "data_exfiltration",
        "denial_of_service",
        "social_engineering",
        "autonomous_merge",
        "autonomous_deployment",
        "autonomous_patch_application",
    }
    assert required <= set(roe["prohibited_actions"])


def test_no_public_routes_in_scenario():
    scenario = yaml.safe_load((ROOT / "examples/scenario.yaml").read_text())
    network = scenario["network"]
    assert network["internet_route"] is False
    assert network["corporate_route"] is False
    assert network["production_route"] is False
    assert network["metadata_access"] is False


def test_policy_files_are_default_deny():
    for name in [
        "tool_authorization.rego",
        "gateway_fail_closed.rego",
        "stop_conditions.rego",
        "data_handling.rego",
    ]:
        text = (ROOT / "policies" / name).read_text()
        assert "default" in text
        assert ":= false" in text


def test_tool_authorization_requires_scope_limits_destination_and_dependencies():
    text = (ROOT / "policies/tool_authorization.rego").read_text()
    for requirement in [
        "input.policy_data_available == true",
        "input.scope_service_available == true",
        "input.destination_matches == true",
        "input.target_in_scope == true",
        "input.within_limits == true",
        "input.approval_service_available == true",
    ]:
        assert requirement in text


def test_gateway_contract_denies_missing_policy_response():
    text = (ROOT / "policies/gateway_fail_closed.rego").read_text()
    assert "default dispatch_allowed := false" in text
    assert "input.policy_response_received == true" in text
    assert "input.policy_response.allowed == true" in text


def test_phase_03_policy_template_includes_all_write_classes():
    text = (ROOT / "policies/tool_authorization.rego").read_text()
    for action_class in [
        "state_change",
        "credentialed_test",
        "poc_validation",
        "patch_validation",
        "range_reset",
        "engagement_termination",
    ]:
        assert f'"{action_class}"' in text
    assert 'input.engagement_id != ""' in text
