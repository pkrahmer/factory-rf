"""The push of a stage's result or a recorded change, tried again when a wait may cure it."""

from datetime import timedelta

from factory.application.boundaries import Boundaries
from factory.hosting.application.git import Git
from factory.hosting.domain.git import PushOutcome, push_is_retried, push_reason
from factory.shared.domain.errors import PushFailed

# A short outage of the hosting service passes within a minute; a longer one is a crash.
RETRY_WAITS = (timedelta(seconds=5), timedelta(seconds=15), timedelta(seconds=45))


def push_failure(git: Git, branch: str, outcome: PushOutcome) -> PushFailed:
    """The `PushFailed` of the push of `branch` that just ended in `outcome`, with git's reason."""
    return PushFailed(branch, outcome, push_reason(git.last_push_output()))


def push_with_retries(boundaries: Boundaries, branch: str) -> None:
    """Push `branch`; a server refusal or an unreachable remote is pushed again after each wait.

    Raises `PushFailed` with git's reason at once for any other refusal, and after the last
    wait when every try failed.
    """
    git = boundaries.git
    retries = len(RETRY_WAITS)
    for number in range(retries + 1):
        outcome = git.push(branch)
        if outcome == "pushed":
            return
        output = git.last_push_output()
        reason = push_reason(output)
        if number == retries or not push_is_retried(outcome, output):
            raise PushFailed(branch, outcome, reason)
        wait = RETRY_WAITS[number]
        seconds = int(wait.total_seconds())
        boundaries.log.line(f"push: retry {number + 1} of {retries} in {seconds} s: {reason}")
        boundaries.waiter.wait(wait)
