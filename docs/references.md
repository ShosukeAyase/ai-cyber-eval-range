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
