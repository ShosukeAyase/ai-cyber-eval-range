package cyber_eval.tool_authorization

default allow := false

dangerous_classes := {"state_change", "credentialed_test", "poc_validation", "patch_validation"}

allow if {
  input.manifest_valid == true
  input.roe_valid == true
  input.policy_version_current == true
  input.target_in_scope == true
  input.test_case_allowed == true
  input.within_limits == true
  input.destination_matches == true
  not input.emergency_stop_active
  approval_satisfied
}

approval_satisfied if {
  not input.action_class in dangerous_classes
}

approval_satisfied if {
  input.action_class in dangerous_classes
  input.approval.valid == true
  input.approval.independent == true
  input.approval.unexpired == true
  input.approval.target_id == input.target_id
  input.approval.action_class == input.action_class
}
