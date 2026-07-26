# Production Go/No-Go Checklist

## Current decision

**NO-GO** - unresolved high risks exist.

A production GO decision requires every mandatory item below to be `PASS`, no unresolved
critical/high risk, and independent evidence attached to the authorization record.

| Gate | Requirement | Current | Blocking risks/evidence |
|---|---|---|---|
| Scope | Approved production system boundary and data classification | FAIL | ROE-001 |
| Legal authorization | Signed authorization, target ownership, jurisdiction and counsel review | FAIL | ROE-001 |
| Human IAM | Phishing-resistant MFA, managed devices, enterprise roles | FAIL | AUTH-001 |
| Workload IAM | Distinct workload identities and short-lived signed credentials | FAIL | AUTH-001, SEC-001 |
| Separation of duties | Requestor, approver, operator, policy admin, evidence custodian separated | FAIL | APR-001 |
| Approval integrity | Signed, nonce-bound, audience-bound, expiring grants | FAIL | APR-001 |
| Policy Engine | Independent PDP, signed bundle, authoritative facts, rollback protection | FAIL | POL-001 |
| Tool Gateway | Production adapters, destination resolution, identity, signed receipts | FAIL | TOOL-001 |
| Network isolation | No default route, firewall deny, DNS control, independent sensor | FAIL | NET-001 |
| Model egress | Controlled proxy/allowlist and provider governance | FAIL | NET-001, AI-001 |
| Secret custody | KMS/HSM broker, rotation, revocation, no environment secret | FAIL | SEC-001 |
| Kill Switch | Independent stop authority and tested monitoring-loss activation | FAIL | KILL-001 |
| Audit integrity | Append-only/WORM, signatures, trusted time, independent administration | FAIL | AUD-001, AUD-002 |
| Runner boundary | Dedicated VM/microVM, explicit seccomp/MAC, escape assessment | FAIL | RUN-001 |
| Supply chain - source | Protected branches, required review, signed changes | NOT EVIDENCED | SCM-001 to SCM-003 |
| Supply chain - CI | Actions pinned to full commit SHAs | FAIL | SCM-001 |
| Supply chain - dependencies | Hash lock and internal mirror | FAIL | SCM-002, CFG-001 |
| Supply chain - artifacts | SBOM, provenance, signatures, verification | FAIL | SCM-003 |
| Scenario integrity | Signed bundles and confidential answer keys | FAIL | RNG-001 |
| Prompt injection | Continuous live-model red team and model-specific baseline | PARTIAL | AI-001 |
| Fail closed | Independent outage and partition testing | PARTIAL | POL-001, KILL-001, NET-001 |
| Resource governance | Global quotas, provider budget, storage and concurrency limits | PARTIAL | DOS-001 |
| Reset/destruction | Backups/snapshots/crash recovery/key erasure verified | PARTIAL | RST-001 |
| Recovery | HA, protected backup, restore drill, RTO/RPO | FAIL | RES-001 |
| Monitoring | Independent telemetry with stop-on-loss | FAIL | KILL-001, NET-001 |
| Vulnerability management | Dependency/image/host scanning with remediation SLA | FAIL | SCM-002, SCM-003 |
| Independent re-test | Closure evidence reviewed by a separate assessor | FAIL | Phase 7 follow-up required |

## Existing controls that passed local assurance

- Deterministic negative authorization tests.
- Local policy and logging outage fail-closed tests.
- Local Kill Switch behavior tests.
- Object-ID-only Agent and Runner contracts.
- No provider tools in the GPT integration.
- Secret-reference redaction from model context.
- Runner no-network command plan and isolation self-observations.
- Seven-scenario reset, scoring, and destruction tests.
- Scripted prompt-injection and forged-evidence negative tests.

These passes are necessary but not sufficient for production GO.

## Required sign-offs after remediation

- System owner
- Security architecture
- IAM owner
- Network security
- Platform/Runner owner
- Supply-chain owner
- Evidence/audit custodian
- Legal/ROE authority
- Independent assessor
- Executive risk owner
