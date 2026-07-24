# Risk Register

Scales: Likelihood (L) and Impact (I) are 1–5. Score = L × I.

| ID | Risk | L | I | Score | Treatment | Owner | Residual / decision needed |
|---|---|---:|---:|---:|---|---|---|
| R-001 | Hypervisor or microarchitectural escape crosses runner boundary | 2 | 5 | 10 | Dedicated hosts for high-risk jobs, patched firmware/kernel, no SMT where required, no mixed tenancy | Infrastructure | Accept only after hardware profile review |
| R-002 | Misconfigured route enables internet/corporate access | 2 | 5 | 10 | Physically/logically separate network, no default route, independent reachability tests, continuous sensor | Network | Human sign-off on topology |
| R-003 | Prompt injection induces unsafe tool intent | 4 | 4 | 16 | No ambient authority, closed schemas, policy mediation, injection test suite | AI Security | Residual model manipulation remains |
| R-004 | Policy Engine outage or stale bundle blocks work | 3 | 3 | 9 | Fail closed, local verified bundle cache, bounded grace only for read-only actions | Platform | Define acceptable availability target |
| R-005 | Credential leaks through tool output | 3 | 5 | 15 | In-memory adapter use, redaction, canary tokens, output scanner, immediate revocation | IAM | Select broker technology |
| R-006 | Approval fatigue leads to unsafe approvals | 3 | 4 | 12 | Risk-tiered approval, concise evidence, expiry, dual control for highest risk | Governance | Define approver staffing and SLA |
| R-007 | Evidence store is mutable or execution-accessible | 2 | 5 | 10 | Separate admin/account, write-only path, WORM lock, signed manifests | Evidence | Select WORM implementation |
| R-008 | Supply-chain compromise of scanner/tool/image | 3 | 5 | 15 | Pinning, mirror quarantine, provenance, signature, SBOM, reproducible build | Supply Chain | Choose trust roots and exception process |
| R-009 | Destruction is incomplete due to snapshots/backups | 3 | 4 | 12 | Inventory, cryptographic erasure, key destruction, lifecycle attestation, backup exclusions | Range | Resolve retention/destruction conflict |
| R-010 | Kubernetes control plane becomes a shared blast-radius amplifier | 3 | 5 | 15 | Separate management cluster, no runner API access, strict admission, dedicated nodes/runtime classes | Platform | Decide whether K8s is allowed for v1 control plane |
| R-011 | Model provider data handling conflicts with evidence/privacy rules | 2 | 4 | 8 | Minimize/redact context, contractual settings, no secrets/PII, retention review | Legal/AI | Approve provider configuration |
| R-012 | Scoring can be gamed by agent or scenario author | 3 | 3 | 9 | Independent scoring, hidden canaries, immutable ground truth, manual review | Evaluation | Define benchmark governance |
| R-013 | Windows range licensing and patch state are non-reproducible | 3 | 3 | 9 | Golden images, offline update repository, license review, snapshot manifests | Range | Legal/licensing decision |
| R-014 | Local-first environment lacks strong account separation | 3 | 4 | 12 | Separate hosts, admin groups, keys, VLANs, and management planes | Security | Minimum physical topology approval |
| R-015 | GPT-5.6 capability changes over time | 3 | 4 | 12 | Pin model snapshot/profile, regression evals, capability-based policy, change review | AI Platform | Define model-change governance |
| R-016 | Telemetry loss leaves blind execution | 2 | 5 | 10 | Health heartbeat, independent sensors, automatic stop | SRE | Set stop thresholds |
| R-017 | Synthetic scenario accidentally includes real secrets or PII | 2 | 5 | 10 | Secret/PII scanning, provenance, review, quarantine | Data | Define release gate |
| R-018 | Tool allowlist is too broad and becomes a shell surrogate | 3 | 5 | 15 | Narrow adapters, semantic parameters, no command strings, code review and negative tests | Pentest Lead | Approve each tool profile |

| R-019 | Local SQLite audit is mutable by the laptop owner and is not WORM | 4 | 4 | 16 | Label local audit as MVP-only, use append-only service APIs, transactional tests, replace with independently administered WORM before external use | Evidence | Production evidence design remains mandatory |
| R-020 | Broad reciprocal bootstrap grants are reused beyond local development | 3 | 5 | 15 | Explicit `local_dev` composition root, distinct identities, expiry and use limits, architecture documentation, no production deployment path | Governance | Replace with signed identity-backed approvals |
| R-021 | Single-process SQLite profile is mistaken for a resilient control plane | 3 | 4 | 12 | Document no HA/concurrency guarantee, local-only naming, integration tests limited to one process | Platform | Distributed transaction and recovery design deferred |
| R-022 | Deterministic model, tool, or credential mocks are mistaken for production integrations | 3 | 4 | 12 | Mock-specific class names, no network imports, `accepted_no_execution`, no material fields, architecture tests | Platform | Independent review required before any adapter is added |
