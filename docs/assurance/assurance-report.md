# Independent Assurance Report

## Executive decision

**Production decision: NO-GO.**

The Phase 1-6 repository demonstrates a coherent local-development safety architecture and a
substantial deterministic test suite. The strongest controls are default-deny authorization,
transactional audit-before-state-change behavior, object-ID-only tool contracts, a no-network
fixed Runner workload, deterministic synthetic-range reset/destruction, and a proposal-only GPT
integration with no provider tools.

The system is not production-ready because the review identified **17 unresolved high-risk
control deficiencies**. The governing rule for this review is that any unresolved critical or
high risk prevents a production-ready determination. No critical finding was assigned, but the
high-risk count is sufficient to require NO-GO.

The current system remains suitable only for the explicitly documented local MVP profiles using
synthetic data and non-production targets.

## Review scope

- Repository: `ShosukeAyase/ai-cyber-eval-range`
- Reviewed commit: `a6ebab812c0047395fb1c54af4d2d244f7e0ac3f`
- Review date: 2026-07-26
- Components: Control Plane, Scope/ROE, Approval Service, Policy Engine adapter, Tool Gateway,
  Credential Broker mock, Emergency Stop, SQLite audit/state, Podman Runner, synthetic Cyber
  Range, GPT Agent integration, schemas, workflows, tests, and governance/security documents.
- Excluded: a live OpenAI provider request, an independent live Podman packet capture, host or
  hypervisor penetration testing, physical security assessment, and legal advice.

## Method

The review followed an examine-test-analyze approach consistent with the assessment principles in
NIST SP 800-53A Rev. 5. It included:

1. Source and architecture review across all Phase 1-6 files.
2. Review of the uploaded CISSP, cybersecurity, and TCP/IP reference corpus for least privilege,
   separation of duties, fail-safe defaults, auditability, confinement, network behavior, and
   supply-chain principles. The scanned TCP/IP Volume 3 had no usable text layer, so its front and
   index portions were OCR-checked.
3. Full deterministic regression execution.
4. Targeted negative authorization, outage, isolation, resource, reset/destruction, and
   prompt-injection tests.
5. Static supply-chain, runtime-isolation, identity, audit-integrity, and secret-management checks.
6. Comparison with NIST SP 800-53 Rev. 5, SP 800-53A Rev. 5, SP 800-190, SP 800-218,
   NIST AI 600-1, GitHub Actions security guidance, and official OpenAI model/API documentation.

## Test results

| Test group | Result | Assurance interpretation |
|---|---:|---|
| Complete repository regression | 157 passed | Strong deterministic regression baseline |
| Negative authorization | 4 passed | Scope, self-approval, and unapproved write denial work in local profile |
| Network isolation | 3 passed | Static/no-network local controls pass; not an independent network assessment |
| Secret exposure | 2 passed | Repository scan and model-context redaction pass |
| Policy outage | 2 passed | Local policy failures deny operations |
| Logging outage | 4 passed | Tested writes roll back or prevent runtime creation |
| Kill Switch | 3 passed | Local in-process stop behavior works |
| Resource exhaustion | 3 passed | Local Runner/Agent bounds work for tested cases |
| Restore and destroy | 16 passed | Deterministic local reset/destruction works |
| Prompt-injection red team | 11 passed | Scripted adversarial outputs are rejected or contained |

The raw machine-readable review result is in
`docs/assurance/phase7-assurance-evidence.json`. Selected test logs are packaged with the Phase 7
review artifact.

## Review by required area

| Area | Local MVP assessment | Production assessment | Key finding |
|---|---|---|---|
| Threat model | Substantive and appropriately cautious | Partial | Production abuse paths are documented but not operationally mitigated |
| Trust boundaries | Clear in design | Not implemented as independent planes | Shared process, host, database, and administration collapse multiple boundaries |
| IAM | Role model documented | Ineffective | Caller-supplied actor IDs are not authenticated identities |
| Network separation | Runner uses `--network=none`; Range has no network API | Insufficient | No independent firewall/sensor/proxy enforcement or continuous route validation |
| Secret management | Secret values are generally absent from MVP objects | Insufficient | Provider key is an environment variable; broker is metadata-only; no KMS/HSM |
| Policy Engine | Default-deny logic and outage tests exist | Ineffective | Runtime uses a Python stub with several authorization facts hardcoded true |
| Tool Gateway | All Agent proposals route through the mock | Ineffective | No production adapter, destination resolver, workload identity, or signed result channel |
| Human Approval | Self-approval and expiry/use limits are tested | Insufficient | No external IAM role enforcement, signed approval package, nonce, or legal identity binding |
| Kill Switch | Local activation and termination tests pass | Insufficient | Same process/SQLite trust domain; no independent network or power/runtime authority |
| Audit trail | State changes are transactionally audit-bound | Ineffective for evidence | Mutable local SQLite, no chain/signature/WORM/trusted timestamp |
| Runner isolation | Strong container flags for a local static workload | Insufficient | Same-host rootless container, host bind mount, no explicit seccomp/MAC or microVM |
| Supply chain | Dev dependencies are exact-version pinned | Ineffective | Mutable Actions tags, no hash lock, signature, SBOM, provenance, or verification gate |
| Reset/destruction | Deterministic local deletion tests pass | Partial | Snapshots, backups, crash remnants, and cryptographic erasure are untested |
| Prompt injection | Strong proposal-only architecture and negative tests | Partial but promising | No continuous live-model red-team baseline or immutable model snapshot |
| Fail closed | Strong for tested local outages | Partial | Shared trust domain and unavailable independent monitors limit assurance |
| Scenario safety | Synthetic, non-networked, marker-driven scenarios | Insufficient for protected evaluation | Public answer keys and unsigned scenario packages weaken integrity |
| Legal authorization/ROE | Typed scope and expiry controls exist | Ineffective | No signed authorization, ownership/jurisdiction verification, or counsel workflow |

## Unresolved high-risk findings

1. `AUTH-001` - No production authentication or workload identity enforcement.
2. `AUD-001` - Audit evidence is mutable local SQLite and not independently retained.
3. `AUD-002` - Audit records lack cryptographic chaining, signing, and trusted time.
4. `POL-001` - Policy evaluation uses a local stub and hardcoded facts.
5. `TOOL-001` - Tool Gateway is a mock, not an authenticated execution mediation service.
6. `APR-001` - Human approval is not bound to external roles, signatures, or anti-replay data.
7. `KILL-001` - Kill Switch is not independent of the Control Plane trust domain.
8. `RUN-001` - Runner container isolation is insufficient for production/high-risk workloads.
9. `NET-001` - Network isolation lacks independent enforcement and continuous observation.
10. `SEC-001` - Provider and target secret custody lacks KMS/HSM-backed brokering.
11. `SCM-001` - GitHub Actions are referenced by mutable tags rather than full commit SHAs.
12. `SCM-002` - Dependencies/build inputs are not hash-locked through an internal mirror.
13. `SCM-003` - Image/scenario SBOM, provenance, signature generation, and verification are absent.
14. `AI-001` - `gpt-5.6-sol` is treated as pinned but is not an immutable dated snapshot.
15. `RNG-001` - Public answer keys and unsigned scenarios undermine scoring/release integrity.
16. `ROE-001` - Legal authorization and target ownership are not digitally evidenced.
17. `RES-001` - No HA, disaster recovery, protected backup, restore drill, or rollback protection.

## Positive assurance observations

- Model output cannot directly invoke provider tools or select arbitrary destinations.
- Agent findings require registered or Tool Gateway-derived evidence identifiers.
- Secret-reference context is excluded from model input.
- Scope expansion and forbidden tool requests are rejected before execution.
- Policy and audit outages fail closed in tested local workflows.
- Runner input is read-only, root is read-only, capabilities are dropped, and network is disabled.
- Synthetic scenarios use harmless markers and deterministic state roots.
- Reset and destruction tests cover all seven scenarios.
- The project accurately labels many production controls as deferred rather than implemented.

## Final determination

The architecture is a defensible **local security-evaluation research MVP**, not a production
security control system. The review does not authorize use against real systems, production data,
real credentials, or untrusted high-risk workloads.

Production reconsideration requires closure and independent re-test of every critical/high item in
`residual-risk-register.md`, completion of every mandatory gate in `go-no-go-checklist.md`, and
objective evidence for the controls in `production-readiness-gaps.md`.

## Primary references

- NIST SP 800-53 Rev. 5, Security and Privacy Controls for Information Systems and Organizations.
- NIST SP 800-53A Rev. 5, Assessing Security and Privacy Controls.
- NIST SP 800-190, Application Container Security Guide.
- NIST SP 800-218, Secure Software Development Framework.
- NIST AI 600-1, Generative AI Profile.
- GitHub Actions Secure Use Reference, full-length commit SHA pinning guidance.
- OpenAI GPT-5.6 Sol model documentation and Responses API documentation.
