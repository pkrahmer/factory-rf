"""What an answer does to a waiting work item: the wait ends and its own counter starts over."""

from factory.domain.work_item import WorkItemState


def unblock(state: WorkItemState) -> WorkItemState:
    """Return the state with its wait ended, resetting the counter that caused the wait.

    `round` is kept, so a later send-back at the round cap asks again.
    """
    if state.blocked is None:
        return state
    update: dict[str, object] = {"blocked": None}
    if state.blocked == "attempts_cap":
        update["attempts"] = 0
    if state.blocked == "crash_cap":
        update["crashes"] = 0
    return state.model_copy(update=update)
