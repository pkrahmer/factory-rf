"""Builders for the handlers' tests: a work item snapshot, an event, a published work item."""

from collections.abc import Callable

import pytest

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.domain.events import Event, EventKind
from factory.domain.journal import HUMAN, JournalRecord
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState
from human_clone import HumanClone

WORK_ITEM = "F0001-S0001"
BRANCH = f"work-item/{WORK_ITEM}"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
BODY = "# First story\n\n## Journal\n\n1. 2026-10-12 human: created.\n"


def _state(pull_request: int | None) -> WorkItemState:
    created = JournalRecord(number=1, speaker=HUMAN, kind="created")
    return WorkItemState(stage="doing", pull_request=pull_request, journal=[created])


def _snapshot(document: WorkItemDocument, branch_commit: str | None = None) -> WorkItemSnapshot:
    return WorkItemSnapshot(
        id=WORK_ITEM,
        path=PATH,
        folder="in-progress",
        branch=BRANCH,
        branch_commit=branch_commit,
        document=document,
    )


@pytest.fixture
def snapshot_of() -> Callable[[WorkItemState | None], WorkItemSnapshot]:
    """Return a builder of a snapshot, not on the remote, whose document holds the given state."""

    def build(state: WorkItemState | None) -> WorkItemSnapshot:
        return _snapshot(WorkItemDocument(state=state, body=BODY))

    return build


@pytest.fixture
def state_with() -> Callable[[int | None], WorkItemState]:
    """Return a builder of a state at `doing` with one journal record and the pull request."""
    return _state


@pytest.fixture
def event_of() -> Callable[[EventKind, WorkItemSnapshot | None], Event]:
    """Return a builder of an event of the kind about the snapshot."""

    def build(kind: EventKind, snapshot: WorkItemSnapshot | None) -> Event:
        return Event(kind=kind, work_item=snapshot, remote_state="a" * 40)

    return build


@pytest.fixture
def pull_request(hosting: FakeHostingService) -> int:
    """Return the number of an open draft pull request of the work item's branch."""
    return hosting.create_pull_request(BRANCH, f"{WORK_ITEM}: first", "body", draft=True).number


@pytest.fixture
def work_item(
    boundaries: Boundaries, *, human: HumanClone, checkout: GitCli, pull_request: int
) -> WorkItemSnapshot:
    """Return the snapshot of a work item the human pushed to its branch, fetched locally."""
    text = boundaries.work_item_writer.render(
        WorkItemDocument(state=_state(pull_request), body=BODY)
    )
    human.push_file(BRANCH, PATH, text)
    checkout.fetch()
    return _snapshot(boundaries.work_item_reader.parse(text), checkout.resolve(f"origin/{BRANCH}"))
