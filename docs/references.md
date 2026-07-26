# References

## Project materials

- `(ISC)² CISSP CBK Reference`, Domain 3 (security architecture), Domain 4 (network security), Domain 5 (IAM), Domain 6 (assessment/testing), and Domain 7 (operations).
- `(ISC)² CISSP Official Study Guide`, secure design principles, penetration-testing planning/authorization, BAS, logging, and vulnerability-remediation workflow.
- `TCP/IP Illustrated`, protocol behavior, firewall/NAT, routing, ICMP, DNS, TCP/UDP, and packet-level evidence interpretation.
- `AGENTS.md`, repository security invariants and validation obligations.

## Primary standards and official technical sources

- NIST SP 800-115, *Technical Guide to Information Security Testing and Assessment*: https://doi.org/10.6028/NIST.SP.800-115
- NIST SP 800-53 Rev. 5, *Security and Privacy Controls for Information Systems and Organizations*: https://doi.org/10.6028/NIST.SP.800-53r5
- NIST SP 800-53A Rev. 5, *Assessing Security and Privacy Controls*: https://doi.org/10.6028/NIST.SP.800-53Ar5
- NIST SP 800-207, *Zero Trust Architecture*: https://doi.org/10.6028/NIST.SP.800-207
- NIST SP 800-207A, *Zero Trust Architecture for Cloud-Native Applications*: https://doi.org/10.6028/NIST.SP.800-207A
- NIST SP 800-190, *Application Container Security Guide*: https://doi.org/10.6028/NIST.SP.800-190
- NIST SP 800-218, *Secure Software Development Framework*: https://doi.org/10.6028/NIST.SP.800-218
- NIST AI RMF 1.0: https://doi.org/10.6028/NIST.AI.100-1
- NIST AI 600-1, *Generative AI Profile*: https://doi.org/10.6028/NIST.AI.600-1
- OpenAI GPT-5.6 System Card: https://deploymentsafety.openai.com/gpt-5-6
- OpenAI GPT-5.6 release: https://openai.com/index/gpt-5-6/
- Firecracker design and security model: https://github.com/firecracker-microvm/firecracker/blob/main/docs/design.md
- Kata Containers architecture: https://github.com/kata-containers/kata-containers/blob/main/docs/design/architecture/README.md
- Open Policy Agent documentation: https://www.openpolicyagent.org/docs
- Kubernetes security concepts: https://kubernetes.io/docs/concepts/security/
- OpenTofu documentation: https://opentofu.org/docs/
- OpenTelemetry specification: https://opentelemetry.io/docs/specs/otel/
- Sigstore documentation: https://docs.sigstore.dev/
- in-toto specification: https://in-toto.io/
- SLSA specification: https://slsa.dev/spec/

## Research caution

Virtualization boundaries reduce but do not eliminate microarchitectural risk. Dedicated hosts, current CPU microcode, kernel mitigations, disabled SMT where required, and single-tenant scheduling remain necessary for high-risk scenarios.

## Phase 04 official runtime sources

- Podman `run` reference, including rootless behavior, `--network=none`, `--read-only`, CPU, memory, PID, and no-new-privileges controls: https://docs.podman.io/en/latest/markdown/podman-run.1.html
- Podman pull policy, including `never` for local-only images: https://docs.podman.io/en/stable/markdown/podman-pull.1.html
- Podman Desktop Windows installation and WSL2 machine requirements: https://podman-desktop.io/docs/installation/windows-install

## Phase 06 official OpenAI sources

- OpenAI Responses API quickstart and server-side API credential handling:
  https://platform.openai.com/docs/quickstart/make-your-first-api-request
- OpenAI Structured Outputs, strict JSON Schema adherence, refusals, and limitations:
  https://openai.com/index/introducing-structured-outputs-in-the-api/
- OpenAI Responses API structured text format and tool-choice controls:
  https://platform.openai.com/docs/api-reference/responses
- OpenAI API data controls and `store` behavior for `/v1/responses`:
  https://platform.openai.com/docs/models/default-usage-policies-by-endpoint
- OpenAI API backward compatibility and pinned-model recommendation:
  https://platform.openai.com/docs/api-reference/backward-compatibility


## Phase 07 assurance sources

- NIST SP 800-53A Rev. 5, assessment methodology and procedures: https://doi.org/10.6028/NIST.SP.800-53Ar5
- NIST SP 800-53 Rev. 5 Release 5.2.0 control catalog: https://csrc.nist.gov/projects/risk-management/sp800-53-controls/downloads
- GitHub Actions secure-use guidance, including full commit SHA pinning: https://docs.github.com/en/actions/reference/security/secure-use
- OpenAI GPT-5.6 Sol model documentation: https://developers.openai.com/api/docs/models/gpt-5.6-sol
