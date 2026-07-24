# Validation Report

Date: 2026-07-24

## Phase 03 executed validation

| Command | Result |
|---|---|
| `make validate` | PASS: 73 tests |
| `make schemas` | PASS: 10 tests |
| `make policy` | PASS: 14 tests |
| `python3 -m pytest tests/unit` | PASS: 21 tests |
| `make integration` | PASS: 8 tests |
| `make architecture` | PASS: 28 tests |
| `make docs` | PASS: 3 tests |
| `make demo` | PASS: synthetic no-network demonstration completed |
| `python3 -m compileall -q src scripts tests` | PASS |
| source line-length check (`src`, `tests`, `scripts`) | PASS: no lines over 100 characters |
| `make optional-tools` | Inventory completed; unavailable tools listed below |

## Phase 03 completion evidence

- Fifteen JSON Schemas conform to JSON Schema Draft 2020-12.
- Every schema has a validating synthetic YAML example.
- Every root schema object rejects undeclared properties.
- Policy input now requires `engagement_id`.
- Model request schema rejects undeclared URL, IP, and command fields.
- Credential reference schema and typed record contain no credential-value fields.
- Scope deviation receives `target_out_of_scope`.
- Expired ROE receives `roe_expired`.
- Missing write approval receives `approval_required`.
- A requestor attempting to approve their own request receives `SelfApprovalError`.
- Policy Engine unavailability receives `policy_unavailable`.
- Active Emergency Stop receives `emergency_stop_active`.
- Injected audit failure rolls back engagement creation and does not consume approval use.
- Injected audit failure prevents the deterministic Model Gateway mock invocation count from changing.
- Emergency Stop has no model, Tool Gateway, or runner dependency.
- Write-class Tool Gateway mock requests consume an independent resource-scoped approval.
- Credential Broker mock issuance returns an opaque metadata reference only.
- Tool Gateway returns `accepted_no_execution` and has no execution adapter.
- All public service operations tested by the architecture suite require `engagement_id`.
- Architecture tests reject shell/dynamic execution primitives, network clients/servers, cloud SDKs, IaC, runtime image definitions, common secret patterns, and credential-value fields.
- Phase 03 requirements are mapped to design evidence and automated tests.

## Demonstration result

`make demo` created an in-memory synthetic engagement, registered Scope/ROE, activated the
engagement, called the deterministic Model Gateway mock, authorized a read-only Tool Gateway
mock request, activated Emergency Stop, and read audit events. It opened no network connection
and created no external resource.

## Formatting and type-check limitations

Ruff and mypy were not installed in the execution environment. Two installation attempts were
made: the configured internal package index returned no matching Ruff distribution, and direct
PyPI access failed because external DNS resolution was unavailable. Therefore Ruff formatting,
Ruff lint, and mypy are not reported as passed locally.

The read-only GitHub Actions workflow defines pinned Ruff and mypy checks. Its result must be
observed after the commit is pushed; workflow success is not inferred from the local tests.

## Executed but not passed

`python3 -m pip check` reported a pre-existing global environment conflict:

```text
moviepy 2.2.1 requires pillow<12.0,>=9.2.0, but pillow 12.2.0 is installed.
```

The Phase 03 project declares no runtime dependencies and uses only the Python standard library
at runtime. The conflict belongs to the shared execution environment, but dependency consistency
is not reported as passed.

## Not executed locally

The following tools were unavailable:

- OPA
- OpenTofu/Terraform
- markdownlint
- Ruff
- mypy
- pip-audit
- CycloneDX tooling
- Trivy
- Syft
- Grype
- Cosign
- Gitleaks

No IaC modules, cloud-resource definitions, container/VM images, execution adapters, external
model integration, production credential integration, exploit modules, or cyber-range resources
exist in Phase 03. IaC validation/scanning, dependency vulnerability scanning, runtime SBOM,
signature verification, and image scanning remain future mandatory gates and are not reported as
passed.
