import pytest

from cyber_eval.domain import ApprovalState, EngagementState, JobState, RunnerState
from cyber_eval.errors import InvalidTransitionError
from cyber_eval.state_machine import (
    APPROVAL_MACHINE,
    ENGAGEMENT_MACHINE,
    JOB_MACHINE,
    RUNNER_MACHINE,
)


def test_valid_approval_transition():
    assert (
        APPROVAL_MACHINE.transition(ApprovalState.REQUESTED, ApprovalState.APPROVED)
        is ApprovalState.APPROVED
    )


@pytest.mark.parametrize(
    ("machine", "current", "target"),
    [
        (APPROVAL_MACHINE, ApprovalState.REQUESTED, ApprovalState.CONSUMED),
        (APPROVAL_MACHINE, ApprovalState.CONSUMED, ApprovalState.APPROVED),
        (JOB_MACHINE, JobState.REQUESTED, JobState.RUNNING),
        (JOB_MACHINE, JobState.DENIED, JobState.AUTHORIZED),
        (RUNNER_MACHINE, RunnerState.ISOLATED, RunnerState.ACTIVE),
        (RUNNER_MACHINE, RunnerState.DESTROYED, RunnerState.CREATING),
        (ENGAGEMENT_MACHINE, EngagementState.CLOSED, EngagementState.ACTIVE),
    ],
)
def test_invalid_transitions_are_rejected(machine, current, target):
    with pytest.raises(InvalidTransitionError):
        machine.transition(current, target)


def test_emergency_termination_is_available_before_terminal_state():
    assert (
        ENGAGEMENT_MACHINE.transition(
            EngagementState.ACTIVE,
            EngagementState.TERMINATED,
        )
        is EngagementState.TERMINATED
    )
