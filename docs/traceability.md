# Requirements Traceability

| Requirement | Design evidence | Machine check |
|---|---|---|
| Four planes and boundaries | `ARCHITECTURE.md`, `trust-boundaries.md` | `test_required_architecture_terms` |
| Allowed/denied communication | `network-matrix.md` | `test_network_matrix_has_mandatory_denies` |
| Scope/ROE schema validation | `engagement.schema.json`, `roe.schema.json` | schema tests |
| Approval transitions | `state-machines.md`, `approval.schema.json` | `test_approval_states` |
| Credentials hidden from model | `credential-model.md`, API design | `test_no_secret_fields_in_model_contracts` |
| Stop/fail-closed behavior | threat model, incident response, stop policy | `test_stop_conditions_present` |
| Complete range destruction | reset/destruction design, scenario schema | `test_scenario_requires_destruction` |
| Target and agent scoring | scoring design, score schema | schema tests |
| Required threat actors | threat model | `test_threat_actors_present` |
| High risks tracked | risk register | `test_risk_register_has_high_risks` |
| ADR traceability | `docs/adr/` | `test_required_adrs` |
| Requirement-design-test mapping | this file | `test_traceability_exists` |
| Major open issues | assumptions, risk register, execution plan | required-file test |
| Design review checklist | `design-review-checklist.md` | required-file test |
| Next-phase dependency plan | `phase-02-implementation-plan.md` | required-file test |
