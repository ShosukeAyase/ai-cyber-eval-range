package cyber_eval.data_handling

default allow_scenario := false

allow_scenario if {
  input.synthetic_data_only == true
  input.dummy_credentials_only == true
  input.secret_scan_passed == true
  input.pii_scan_passed == true
  input.public_endpoint_count == 0
}
