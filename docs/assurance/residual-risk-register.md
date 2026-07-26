# Residual Risk Register

## Decision rule

Any unresolved **critical** or **high** risk requires a production **NO-GO** decision. Scores use
Likelihood (L) and Impact (I) from 1 to 5; score is `L x I`.

| ID | Risk | L | I | Score | Status | Required treatment | Suggested owner |
|---|---|---:|---:|---:|---|---|---|
| AUTH-001 | Caller-supplied actor IDs are not authenticated identities | 4 | 5 | 20 | Open - High | External IdP, phishing-resistant MFA, workload identity, signed tokens, role enforcement | IAM |
| AUD-001 | Local administrator can alter or roll back SQLite audit/state | 4 | 5 | 20 | Open - High | Independent append-only audit service and WORM retention | Evidence |
| AUD-002 | Audit records lack chain, signature, trusted time, and monotonic sequence | 4 | 4 | 16 | Open - High | Chained digests, HSM-backed signing, timestamping, verification tooling | Evidence |
| POL-001 | Policy stub supplies authoritative facts as constants | 4 | 5 | 20 | Open - High | Independent PDP, signed bundles, authoritative fact providers, bundle rollback tests | Platform Security |
| TOOL-001 | Mock Tool Gateway cannot authenticate real adapters or results | 4 | 5 | 20 | Open - High | Narrow adapters, mTLS/workload identity, destination resolver, signed receipts | Tooling |
| APR-001 | Approval is not bound to enterprise identity, role, signature, or nonce | 4 | 5 | 20 | Open - High | Signed approval package, SoD roles, anti-replay, dual control | Governance |
| KILL-001 | Kill Switch shares process, database, host, and administration | 3 | 5 | 15 | Open - High | Independent stop controller, network cut-off, runtime/power authority, heartbeat | SRE/Security |
| RUN-001 | Rootless Podman on the same laptop is not a production sandbox boundary | 3 | 5 | 15 | Open - High | Dedicated VM/microVM hosts, explicit seccomp/MAC, immutable host, escape tests | Infrastructure |
| NET-001 | Network denial is not enforced/observed by an independent control plane | 3 | 5 | 15 | Open - High | No-route topology, firewall, controlled proxy, DNS policy, sensor, stop-on-loss | Network Security |
| SEC-001 | Provider credential is environment-based; no production secret broker | 4 | 5 | 20 | Open - High | KMS/HSM, short-lived workload credentials, rotation/revocation, direct delivery | IAM |
| SCM-001 | GitHub Actions use mutable tags | 3 | 5 | 15 | Open - High | Pin every action to a verified full commit SHA and enforce repository policy | Supply Chain |
| SCM-002 | Build and validation dependencies lack hash lock/internal mirror | 3 | 5 | 15 | Open - High | Hash-locked dependencies, internal mirror, offline inputs, reproducibility | Supply Chain |
| SCM-003 | No operational SBOM, provenance, artifact signature, or verification gate | 3 | 5 | 15 | Open - High | Generate and verify SBOM, SLSA provenance, Cosign/in-toto signatures | Supply Chain |
| AI-001 | Durable model ID can change behavior without repository change | 3 | 5 | 15 | Open - High | Immutable snapshot or signed model config plus regression gate and rollback | AI Platform |
| RNG-001 | Public answer keys and unsigned scenarios permit grading/release manipulation | 4 | 4 | 16 | Open - High | Private grader, separated keys, signed scenario bundles, review workflow | Evaluation |
| ROE-001 | Legal authorization and target ownership are not digitally evidenced | 3 | 5 | 15 | Open - High | Signed authorization, ownership validation, jurisdiction/counsel review | Legal/Governance |
| RES-001 | Single process/SQLite has no HA, DR, protected restore, or rollback defense | 4 | 4 | 16 | Open - High | RTO/RPO, redundancy, protected backups, restore drills, rollback detection | Platform/SRE |
| DOS-001 | No global rate, concurrency, cost, storage, or audit-growth budget | 3 | 4 | 12 | Open - Medium | Quotas, budget circuit breakers, storage limits, backpressure | SRE/AI Platform |
| RST-001 | Deletion tests exclude backups, snapshots, crash remnants, and key erasure | 3 | 4 | 12 | Open - Medium | Asset inventory, backup exclusion, cryptographic erasure, independent verification | Range/Evidence |
| CFG-001 | Build backend inputs remain ranged and unhashed | 3 | 3 | 9 | Open - Medium | Pin and hash build backend artifacts | Supply Chain |

## Risk acceptance constraints

- High risks cannot be accepted solely by the implementation team.
- Any temporary acceptance must identify an accountable executive risk owner, expiry date,
  compensating controls, and measurable exit criteria.
- No acceptance may authorize public vulnerable services, real credentials in model context,
  arbitrary commands, general Internet access from the Runner/Range, or unapproved targets.
- Risk acceptance does not change the current NO-GO determination.
