"""The split sends a work item's event to the story's handler or to the acceptance's."""

import pytest

from factory.application.acceptance import SplitByWorkItemKind
from factory.application.dispatcher import Handler
from factory.domain.errors import CannotHandle
from factory.domain.events import Event, EventKind
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState

REMOTE_STATE = "a" * 40


class Recording(Handler):
    """Keeps every event it is handed."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


def _event(kind: EventKind, work_item: str) -> Event:
    document = WorkItemDocument(state=WorkItemState(stage="approval"), body="# T\n")
    snapshot = WorkItemSnapshot(
        id=work_item,
        path=f"factory/features/F0001-x/in-progress/{work_item}-y.md",
        folder="in-progress",
        branch=f"work-item/{work_item}",
        branch_commit=None,
        document=document,
    )
    return Event(kind=kind, work_item=snapshot, remote_state=REMOTE_STATE)


@pytest.mark.parametrize("kind", ["hand_over", "merged", "closed"])
@pytest.mark.parametrize("acceptance", [False, True], ids=["story", "acceptance"])
def test_an_event_goes_to_the_handler_of_its_work_items_kind_only(
    kind: EventKind, *, acceptance: bool
) -> None:
    story_handler = Recording()
    acceptance_handler = Recording()
    split = SplitByWorkItemKind(story_handler, acceptance_handler)
    event = _event(kind, "F0001-A0001" if acceptance else "F0001-S0001")

    split.handle(event)

    chosen, other = (
        (acceptance_handler, story_handler) if acceptance else (story_handler, acceptance_handler)
    )
    assert chosen.events == [event]
    assert other.events == []
    assert split.story is story_handler
    assert split.acceptance is acceptance_handler


def test_an_event_without_a_work_item_goes_to_neither_handler() -> None:
    story_handler = Recording()
    acceptance_handler = Recording()
    split = SplitByWorkItemKind(story_handler, acceptance_handler)

    with pytest.raises(CannotHandle) as raised:
        split.handle(Event(kind="idle", work_item=None, remote_state=REMOTE_STATE))

    assert (raised.value.kind, raised.value.reason) == ("idle", "no work item")
    assert story_handler.events == []
    assert acceptance_handler.events == []
