"""What an answer does to a waiting work item: the wait ends and its own counter starts over."""

from factory.domain.work_item import WorkItemState


def unblock(state: WorkItemState) -> WorkItemState:
    """Return the state with its wait ended, resetting the counter that caused the wait.

    An answer at the round cap starts the count of rounds over; an answer to any other
    wait keeps `round`, so a later send-back past the cap asks again.
    """
    if state.blocked is None:
        return state
    update: dict[str, object] = {"blocked": None}
    if state.blocked == "attempts_cap":
        update["attempts"] = 0
    if state.blocked == "crash_cap":
        update["crashes"] = 0
    if state.blocked == "round_cap":
        update["round"] = 0
    return state.model_copy(update=update)
