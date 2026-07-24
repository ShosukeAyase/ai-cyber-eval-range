# Security Principles

## Mandatory principles

1. **Default deny:** no action, route, credential, or tool is permitted without an explicit grant.
2. **Least privilege:** job identities are target-bound, action-bound, and short-lived.
3. **Complete mediation:** every tool request is checked at the Tool Gateway and every network flow is checked at the egress boundary.
4. **Separation of duties:** authors, approvers, operators, evidence custodians, and policy administrators are distinct roles.
5. **Fail closed:** unavailable policy, approval, identity, signature, telemetry, or scope services stop the job.
6. **Defense in depth:** policy, IAM, networking, sandboxing, quotas, monitoring, and human approval are independent controls.
7. **Compartmentalization:** engagement, scenario, runner, target, and credential scopes are separate compartments.
8. **Non-bypassability:** the model cannot reach an execution backend except through structured tools.
9. **Tamper evidence:** logs and evidence are signed, hashed, time-stamped, and stored outside the execution boundary.
10. **Ephemerality:** runners, credentials, targets, and writable storage are disposable.
11. **Reproducibility:** every finding links to immutable inputs, tool versions, policy version, and test results.
12. **Supply-chain integrity:** dependencies are pinned, mirrored, scanned, signed where possible, and represented in SBOMs.

## Reference-monitor properties

The combined Policy Engine and Tool Gateway must be:

- always invoked;
- tamper resistant relative to the model and runner;
- small enough to review and test;
- deterministic for the same signed input state; and
- observable through independent decision logs.

## Safety hierarchy

When availability conflicts with scope, authorization, evidence integrity, or containment, the system chooses containment and stops.
