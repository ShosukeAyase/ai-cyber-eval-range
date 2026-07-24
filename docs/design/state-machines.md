# State Machines

## Engagement

`draft -> validated -> approved -> active -> stopping -> closed`

Any state may transition to `terminated` after an emergency stop. Changes to scope or ROE create a new immutable version and return to `draft`.

## Approval

```mermaid
stateDiagram-v2
  [*] --> Requested
  Requested --> Approved: independent approver signs
  Requested --> Denied
  Requested --> Expired
  Approved --> Consumed: authorized execution starts
  Approved --> Revoked: scope/policy/stop change
  Approved --> Expired
  Consumed --> [*]
  Denied --> [*]
  Expired --> [*]
  Revoked --> [*]
```

## Job

`requested -> policy_pending -> approval_pending? -> authorized -> provisioning -> ready -> running -> collecting -> destroying -> completed`

Failure transitions:

- any pre-run state -> `denied` or `expired`;
- running -> `quarantined` on stop condition;
- quarantined -> `collecting` -> `destroying` -> `terminated`;
- lifecycle failure -> `failed`, with emergency cleanup still required.

## Runner

`absent -> creating -> attested -> networked -> active -> isolated -> destroyed`

A runner cannot move from `isolated` back to `active`; a new runner is required.
## Phase 02 executable contract boundary

`src/cyber_eval/state_machine.py` encodes the documented edges as pure allowlists. It performs no provisioning, execution, cleanup, or external communication. Invalid edges raise `InvalidTransitionError`. Negative tests cover skipped approval, denied-job reactivation, isolated-runner reactivation, destroyed-runner recreation, and closed-engagement reactivation.
