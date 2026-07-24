"""Pure allowlist-based state transitions with no lifecycle side effects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, Mapping, TypeVar

from cyber_eval.domain import ApprovalState, EngagementState, JobState, RunnerState
from cyber_eval.errors import InvalidTransitionError

StateT = TypeVar("StateT", bound=Enum)


@dataclass(frozen=True, slots=True)
class StateMachine(Generic[StateT]):
    name: str
    transitions: Mapping[StateT, frozenset[StateT]]

    def transition(self, current: StateT, target: StateT) -> StateT:
        allowed = self.transitions.get(current, frozenset())
        if target not in allowed:
            raise InvalidTransitionError(
                f"{self.name}: transition {current.value!r} -> {target.value!r} is not allowed"
            )
        return target


def _with_termination(
    transitions: dict[EngagementState, frozenset[EngagementState]],
) -> dict[EngagementState, frozenset[EngagementState]]:
    for state in EngagementState:
        if state is not EngagementState.TERMINATED:
            transitions[state] = transitions.get(state, frozenset()) | {
                EngagementState.TERMINATED
            }
    return transitions


APPROVAL_MACHINE = StateMachine(
    "approval",
    {
        ApprovalState.REQUESTED: frozenset(
            {ApprovalState.APPROVED, ApprovalState.DENIED, ApprovalState.EXPIRED}
        ),
        ApprovalState.APPROVED: frozenset(
            {ApprovalState.CONSUMED, ApprovalState.REVOKED, ApprovalState.EXPIRED}
        ),
    },
)

ENGAGEMENT_MACHINE = StateMachine(
    "engagement",
    _with_termination(
        {
            EngagementState.DRAFT: frozenset({EngagementState.VALIDATED}),
            EngagementState.VALIDATED: frozenset(
                {EngagementState.DRAFT, EngagementState.APPROVED}
            ),
            EngagementState.APPROVED: frozenset(
                {EngagementState.DRAFT, EngagementState.ACTIVE}
            ),
            EngagementState.ACTIVE: frozenset({EngagementState.STOPPING}),
            EngagementState.STOPPING: frozenset({EngagementState.CLOSED}),
        }
    ),
)

JOB_MACHINE = StateMachine(
    "job",
    {
        JobState.REQUESTED: frozenset(
            {JobState.POLICY_PENDING, JobState.DENIED, JobState.EXPIRED, JobState.FAILED}
        ),
        JobState.POLICY_PENDING: frozenset(
            {
                JobState.APPROVAL_PENDING,
                JobState.AUTHORIZED,
                JobState.DENIED,
                JobState.EXPIRED,
                JobState.FAILED,
            }
        ),
        JobState.APPROVAL_PENDING: frozenset(
            {JobState.AUTHORIZED, JobState.DENIED, JobState.EXPIRED, JobState.FAILED}
        ),
        JobState.AUTHORIZED: frozenset(
            {JobState.PROVISIONING, JobState.DENIED, JobState.EXPIRED, JobState.FAILED}
        ),
        JobState.PROVISIONING: frozenset({JobState.READY, JobState.FAILED}),
        JobState.READY: frozenset({JobState.RUNNING, JobState.FAILED}),
        JobState.RUNNING: frozenset(
            {JobState.COLLECTING, JobState.QUARANTINED, JobState.FAILED}
        ),
        JobState.QUARANTINED: frozenset({JobState.COLLECTING, JobState.FAILED}),
        JobState.COLLECTING: frozenset({JobState.DESTROYING, JobState.FAILED}),
        JobState.DESTROYING: frozenset(
            {JobState.COMPLETED, JobState.TERMINATED, JobState.FAILED}
        ),
    },
)

RUNNER_MACHINE = StateMachine(
    "runner",
    {
        RunnerState.ABSENT: frozenset({RunnerState.CREATING}),
        RunnerState.CREATING: frozenset({RunnerState.ATTESTED, RunnerState.DESTROYED}),
        RunnerState.ATTESTED: frozenset({RunnerState.NETWORKED, RunnerState.ISOLATED}),
        RunnerState.NETWORKED: frozenset({RunnerState.ACTIVE, RunnerState.ISOLATED}),
        RunnerState.ACTIVE: frozenset({RunnerState.ISOLATED}),
        RunnerState.ISOLATED: frozenset({RunnerState.DESTROYED}),
    },
)
