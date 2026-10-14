"""The crash and the expiry: the count they raise and the journal texts that record the discard."""

from factory.domain.git import CommitId
from factory.domain.work_item import WorkItemState


def crashed(state: WorkItemState) -> WorkItemState:
    """Return a copy of `state` with one more crash; the claim is released elsewhere."""
    return state.model_copy(update={"crashes": state.crashes + 1})


def crash_entry_text(stage: str, crashes: int, head: CommitId) -> str:
    """Return the journal text of crash number `crashes`, discarded back to commit `head`."""
    return (
        f"crash {crashes}: the run of stage {stage} ended without a result. "
        f"Its work is discarded back to commit {head}."
    )


def expiry_entry_text(stage: str, crashes: int, head: CommitId) -> str:
    """Return the journal text of an expiry counted as crash `crashes`, discarded back to `head`."""
    return (
        f"expiry {crashes}: the lease of stage {stage} ran out. "
        f"Its work is discarded back to commit {head}."
    )


def at_crash_cap(state: WorkItemState, crash_cap: int) -> bool:
    """Return whether the crashes counted in `state` have reached `crash_cap`."""
    return state.crashes >= crash_cap


def asking_crash_cap(state: WorkItemState) -> WorkItemState:
    """Return a copy of `state` blocked on the crash-cap question."""
    return state.model_copy(update={"blocked": "crash_cap"})
