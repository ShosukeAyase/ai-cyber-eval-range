# IAM Model

## Roles

| Role | Permitted | Forbidden |
|---|---|---|
| Engagement Author | Draft engagement/ROE | Approve own high-risk action; change policy |
| Engagement Approver | Approve scope and test window | Execute tools; administer evidence |
| Test Operator | Start approved jobs, review status | Broaden scope; retrieve raw credentials |
| Policy Administrator | Publish signed policy bundles | Approve engagements; run tests |
| Credential Custodian | Configure broker issuers | See model prompts; alter evidence |
| Range Administrator | Publish/reset scenarios | Approve tests; access production networks |
| Evidence Custodian | Retain, verify, export evidence | Alter execution state or policy |
| Incident Commander | Invoke emergency stop | Resume job without reauthorization |
| Auditor | Read evidence and decisions | Execute or approve jobs |
| Model Service Identity | Request analysis/tool intent | Possess credentials or invoke backends directly |

## Workload identities

Every service and job has a distinct workload identity. Job identities include:

- `engagement_id`
- `job_id`
- `runner_id`
- `action_class`
- `target_id`
- `policy_version`
- `expires_at`
- `nonce`

The identity is not a bearer credential for the target. It authorizes the Tool Gateway to request a separate target credential from the Credential Broker.

## Administrative controls

- Phishing-resistant MFA for human administrators.
- Just-in-time privileged access with approval and expiry.
- Separate directories or identity tenants per plane where feasible.
- No shared break-glass account.
- Quarterly access review and immediate revocation on role change.
- Dual control for policy signing keys, evidence retention changes, and route changes.
