package cyber_eval.gateway_fail_closed

default dispatch_allowed := false

# Missing, malformed, denied, or unavailable Policy Engine responses never authorize dispatch.
dispatch_allowed if {
  input.policy_response_received == true
  input.policy_response_valid == true
  input.policy_response.allowed == true
  input.policy_response.request_id == input.request_id
  input.policy_response.policy_version == input.expected_policy_version
}
