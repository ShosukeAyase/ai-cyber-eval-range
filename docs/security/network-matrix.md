# Network Matrix

Default policy is **deny**. “Allow” entries require mutual identity, a job/engagement binding, and a documented port/protocol profile.

| Source | Destination | Purpose | Protocol | Decision | Conditions |
|---|---|---|---|---|---|
| Operator workstation | Control ingress | Submit/review engagements | HTTPS | Allow | MFA, managed device, role checks |
| Agent Orchestrator | Model Gateway | Model request | HTTPS | Allow | Redacted context, model allowlist |
| Model Gateway | OpenAI API | GPT-5.6 inference | HTTPS | Allow | Fixed destination allowlist, org identity, no range path |
| Scheduler | Runner Lifecycle Manager | Create/stop runner | mTLS API | Allow | One-time job grant |
| Tool Gateway | Policy Engine | Authorization decision | mTLS API | Allow | Fail closed, signed decision log |
| Tool Gateway | Credential Broker | Token exchange | mTLS API | Allow | Target/action/audience-bound |
| Runner | Authorized range target | Approved test | Scenario profile | Allow | Exact destination tuple and rate limit |
| Runner | Range DNS/PKI/IdP/mirror | Scenario support | Profile-specific | Allow | Internal-only endpoints |
| Runner | Observability gateway | Telemetry/evidence | TLS, write-only | Allow | No query/delete operation |
| Range sensors | Observability gateway | Packet/process/file telemetry | TLS, write-only | Allow | Sensor identity only |
| Execution/range | General internet | Any | Any | Deny | Hard route absence plus firewall deny |
| Execution/range | Corporate/production | Any | Any | Deny | Hard route absence plus firewall deny |
| Runner | Cloud metadata | Metadata access | Any | Deny | Block link-local metadata ranges |
| Runner | Docker/container runtime sockets | Host control | Unix/TCP | Deny | Socket not mounted; host policy blocks |
| Runner | Kubernetes management API | Cluster administration | HTTPS | Deny by default | Only dedicated adapter with scoped service account for approved cases |
| Range | Control plane | Callback/lateral movement | Any | Deny | No route; state reported through observability only |
| Execution | Evidence store | Modify/delete evidence | Any | Deny | Write-only gateway; separate IAM |

## Required negative tests

- No default route in execution and range namespaces.
- Explicit rejection of public, private-corporate, production, metadata, and management address classes not registered to the scenario.
- DNS resolution cannot return an address outside the scenario allocation.
- Egress rules are removed before credential revocation completes only during emergency isolation; otherwise credentials are revoked first.
- Any loss of firewall policy synchronization terminates the job.

## Phase 03 local MVP network posture

The Phase 03 process opens no listener and imports no socket, HTTP client/server, cloud SDK,
container client, or Kubernetes client. Model, Tool Gateway, Credential Broker, Policy Engine,
and Emergency Stop interactions are in-process method calls. SQLite uses a local file or
`:memory:` database only.

This zero-network local profile is narrower than the future production matrix. It does not grant
permission to add loopback HTTP APIs, public endpoints, arbitrary URLs/IPs, or a route to a
cyber range. Such changes require a separate approved phase and updated matrix entries.
