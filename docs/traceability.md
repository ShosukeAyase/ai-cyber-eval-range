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
| Phase 03 implementation plan | `exec-plans/completed/phase-03-control-plane-mvp.md` | required-file and documentation-index tests |

| Phase 03 all operations carry engagement context | `design/control-plane-mvp.md`, typed service methods | `test_all_public_service_operations_require_engagement_id` |
| Phase 03 Scope deviation rejection | `ScopeRoeService`, `LocalPolicyEngineAdapter` | `test_scope_deviation_is_denied` |
| Phase 03 expired ROE rejection | `ScopeRoeService`, `LocalPolicyEngineAdapter` | `test_expired_roe_is_denied` |
| Phase 03 self-approval rejection | `ApprovalService` | `test_self_approval_is_rejected` |
| Phase 03 audit fail-closed | `LocalControlPlaneStore.audited_transaction` | `test_audit_failure_rolls_back_state_change`, `test_audit_failure_prevents_model_mock_invocation` |
| Phase 03 independent Kill Switch | `EmergencyStopService` | `test_emergency_stop_is_independent_and_blocks_policy`, `test_emergency_stop_has_no_model_or_runner_dependency` |
| Phase 03 write approval enforcement | `ApprovalService`, `ToolGatewayMock`, `CredentialBrokerMock` | `test_write_tool_without_approval_is_denied`, `test_control_plane_mvp_integration_flow` |
| Phase 03 object-ID-only model/tool APIs | `model-request.schema.json`, `ModelRequest`, `ToolRequest` | `test_phase_03_model_request_rejects_raw_network_and_command_fields`, `test_model_and_tool_contracts_have_no_destination_or_command_fields` |
| Phase 03 no credential material | `credential-reference.schema.json`, `CredentialReference` | `test_credential_reference_schema_has_no_material_properties`, `test_credential_reference_has_no_secret_value_fields` |
| Phase 03 local integration | `design/control-plane-mvp.md`, `ControlPlaneMvp` | `test_control_plane_mvp_integration_flow` |

| Phase 04 prohibited communication | `design/isolated-runner-mvp.md`, `PodmanCommandBuilder` | `test_podman_plan_enforces_isolation_and_resource_limits` |
| Phase 04 Scope rejection | `RunnerCoordinator` and local registry | `test_scope_outside_target_is_rejected_before_runtime` |
| Phase 04 resource enforcement | `RunnerLimits`, Podman flags, fixed workload bounds | `test_runner_limits_reject_unbounded_profiles`, command-plan test |
| Phase 04 audit separation | no audit mount in execution spec | command-plan test and audit-failure integration test |
| Phase 04 Kill Switch | `KillSwitchMonitor` | `test_kill_switch_terminates_blocked_runner_and_cleanup_completes` |
| Phase 04 destruction | runtime `destroy` and destruction attestation | `test_runner_collects_evidence_and_destroys_all_ephemeral_state` |

| Requirement | Design/control | Automated evidence |
|---|---|---|
| Phase 05 scenario isolation | `LocalCyberRangeRuntime` disjoint roots and asset allowlists | `test_scenario_instances_have_disjoint_state_roots`, `test_different_scenarios_cannot_share_or_reference_state` |
| Phase 05 external communication denial | no network imports/listeners and `network.mode=none` | `test_external_communication_operation_is_blocked`, `test_range_source_has_no_network_or_process_execution_imports`, catalog test |
| Phase 05 deterministic reset | verified baseline copy and SHA-256 | `test_reset_reproduces_baseline_for_every_scenario`, `test_reset_reproduces_baseline_and_clears_observations` |
| Phase 05 complete destruction | runtime destroy plus attestation | `test_every_scenario_is_completely_destroyed`, `test_destruction_removes_all_range_state` |
| Phase 05 automatic scoring | host answer key and safe markers | `test_every_scenario_can_be_automatically_scored`, `test_complete_scenario_is_scored_from_answer_key` |
| Phase 05 malicious-content resistance | prompt/scope refusal markers | `test_prompt_and_scope_scenarios_reward_refusal_markers` |
| Phase 05 audit fail-closed | audited transaction before create/action | `test_audit_failure_prevents_range_creation` |
