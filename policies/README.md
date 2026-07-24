# Policy templates

These Rego files are reviewable rule templates only. Phase 02 does not start OPA, distribute bundles, expose a decision endpoint, or connect the Tool Gateway to a production Policy Engine.

- `tool_authorization.rego` expresses default-deny scope, limits, destination, and approval requirements.
- `gateway_fail_closed.rego` expresses the caller-side rule that a missing or invalid Policy Engine response cannot authorize dispatch.
- `stop_conditions.rego` and `data_handling.rego` retain the Phase 01 contracts.

The executable Python package contains a pure local stub for negative testing. It is not a substitute for production policy enforcement.
