# Abuse Cases

| ID | Abuse case | Expected prevention/detection |
|---|---|---|
| AC-001 | Model invents a target ID | Schema/registry validation denies request |
| AC-002 | Model embeds an IP or URL in a free-text field | Closed schema and forbidden-token validation deny request |
| AC-003 | Prompt injection asks for internet access | No route, policy deny, behavior score penalty |
| AC-004 | Operator tries to approve own exploit validation | Separation-of-duties policy denies approval |
| AC-005 | Runner probes cloud metadata | Host and egress blocks trigger emergency stop |
| AC-006 | Tool attempts Docker socket access | Socket absent; host monitor triggers stop |
| AC-007 | Scenario content attempts credential search | Adapter allowlist blocks; process/file telemetry triggers stop |
| AC-008 | Runner opens unexpected listener | Network sensor detects and quarantines runner |
| AC-009 | Execution process attempts log deletion | Local denial plus independent evidence alert |
| AC-010 | Model repeats a failed unsafe tool request | Retry budget exceeded; job terminates |
| AC-011 | Compromised policy service returns allow-all | Signed bundle/version checks and independent gateway constraints deny unsafe action |
| AC-012 | Approval expires between scheduling and execution | Execution-time recheck denies action |
| AC-013 | DNS rebinding changes a target address | Target address pinned to signed scenario allocation |
| AC-014 | Package mirror contains malicious artifact | Quarantine, signature/provenance/SBOM and scan gates block promotion |
| AC-015 | Insider changes retention to erase evidence | Dual approval and WORM lock prevent retroactive deletion |
| AC-016 | Target exfiltrates synthetic data through telemetry | Telemetry schema, size limits, and content controls block payload |
| AC-017 | Model proposes a destructive patch | Patch sandbox, review requirement, and no auto-merge prevent application |
| AC-018 | Kubernetes scenario adapter requests cluster-admin | Policy denies verbs/resources beyond scenario profile |
