# Requirements Traceability

| Requirement | Design evidence | Machine check |
|---|---|---|
| Four planes and boundaries | `ARCHITECTURE.md`, `security/trust-boundaries.md` | `test_required_architecture_terms` |
| Allowed/denied communication | `security/network-matrix.md` | `test_network_matrix_has_mandatory_denies` |
| Scope/ROE schema validation | `engagement.schema.json`, `roe.schema.json` | `test_every_schema_has_a_valid_synthetic_example` |
| Approval transitions | `design/state-machines.md`, `approval.schema.json` | `test_approval_states_match_typed_contract` |
| Credentials hidden from model | `security/credential-model.md`, `design/api-boundaries.md` | `test_phase_02_runtime_contract_has_no_credential_fields` |
| Stop/fail-closed behavior | threat model, incident response, stop policy | `test_stop_conditions_present` |
| Complete range destruction | reset/destruction design, scenario schema | `test_scenario_requires_destruction` |
| Target and agent scoring | scoring design, score schema | schema example validation |
| Required threat actors | threat model | `test_threat_actors_present` |
| High risks tracked | risk register | `test_risk_register_has_high_risks` |
| ADR traceability | `docs/adr/` | `test_required_adrs` |
| Requirement-design-test mapping | this file | `test_traceability_exists` |
| Phase 02 all schemas validate | `schemas/`, `examples/` | `test_schemas_are_valid_draft_2020_12`, `test_every_schema_has_a_valid_synthetic_example` |
| Phase 02 out-of-scope rejection | `design/repository-skeleton.md`, `gateway.py`, `policy.py` | `test_out_of_scope_target_is_rejected` |
| Phase 02 approval rejection | `design/repository-skeleton.md`, `tool_authorization.rego` | `test_unapproved_dangerous_action_is_rejected` |
| Phase 02 policy fail-closed | `gateway.py`, `gateway_fail_closed.rego` | `test_policy_engine_unavailable_fails_closed`, `test_policy_engine_exception_fails_closed` |
| Phase 02 negative state transitions | `design/state-machines.md`, `state_machine.py` | `test_invalid_transitions_are_rejected` |
| Phase 02 object-ID-only API | `tool-request.schema.json`, `domain.py` | `test_tool_request_rejects_raw_network_or_command_fields`, `test_no_arbitrary_model_api_examples` |
| Phase 02 non-executable skeleton | `design/repository-skeleton.md`, `NonExecutableToolGateway.dispatch` | source import/call/IaC tests and `test_dispatch_is_permanently_disabled_in_phase_02` |
| Phase 02 CI validation | `.github/workflows/phase-02-skeleton.yml`, `Makefile` | `test_required_files_exist`, local `make validate` |
| Next controlled implementation plan | `exec-plans/active/phase-03-implementation-plan.md` | required-file and documentation-index tests |
