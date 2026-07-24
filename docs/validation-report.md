# Validation Report

Date: 2026-07-24

## Executed

| Command | Result |
|---|---|
| `make validate` | PASS: 21 tests |
| `python3 -m compileall -q scripts tests` | PASS |
| `git diff --check` | PASS |
| `make optional-tools` | Completed inventory; tools below unavailable |

## Test coverage

- Seven JSON Schemas conform to JSON Schema Draft 2020-12.
- Engagement, ROE, and scenario examples validate.
- Root schema objects reject additional properties.
- Dangerous action classes require human approval.
- Scenario destruction controls are mandatory.
- Four planes and fail-closed/default-deny terms are present.
- Network matrix includes mandatory deny paths.
- Required threat actors, stop conditions, ten diagrams, and fourteen ADRs are present.
- Tool API documentation does not introduce arbitrary command/IP/URL execution APIs.
- ROE prohibited actions and scenario no-public-route properties are enforced.
- Markdown relative links resolve.

## Not executed

The following tools are not installed in the environment:

- OPA
- OpenTofu/Terraform
- markdownlint
- Trivy
- Syft
- Grype
- Cosign
- Gitleaks

No IaC modules, runtime dependency lockfiles, container images, or VM images exist in Phase 01. Therefore IaC validation/security scanning, dependency scanning, runtime SBOM generation, signature verification, and image scanning remain Phase 02 gates and are not reported as passed.
