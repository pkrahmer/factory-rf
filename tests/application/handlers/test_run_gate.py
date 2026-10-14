"""The run gate: the pull request is read before a stage runs, a close or a merge goes first."""

import dataclasses
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.handlers.closed import ClosedHandler
from factory.application.handlers.merged import MergedHandler
from factory.application.handlers.run_gate import RunGate
from factory.domain.errors import HostingServiceError
from factory.domain.events import Event, EventKind
from factory.domain.hosting import PullRequestView
from factory.domain.journal import HUMAN, JournalRecord
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState
from git_support import PIPELINE_YAML, remote_commit
from human_clone import HumanClone

WORK_ITEM = "F0001-S0001"
BRANCH = f"work-item/{WORK_ITEM}"
FEATURE = "factory/features/F0001-example"
BACKLOG_PATH = f"{FEATURE}/backlog/F0001-S0001-first.md"
PATH = f"{FEATURE}/in-progress/F0001-S0001-first.md"
DONE_PATH = f"{FEATURE}/done/F0001-S0001-first.md"
BODY = "# First story\n\n## Journal\n\n1. 2026-10-12 human: created.\n"

EventOf = Callable[[EventKind, WorkItemSnapshot | None], Event]
SnapshotOf = Callable[[WorkItemState | None], WorkItemSnapshot]
StateWith = Callable[[int | None], WorkItemState]


class CountingHosting(FakeHostingService):
    """The fake hosting service that counts its reads of a pull request."""

    def __init__(self) -> None:
        """Start without pull requests and without reads."""
        super().__init__()
        self.reads = 0

    def get_pull_request(self, number: int) -> PullRequestView:
        """Count the read, then read the pull request."""
        self.reads += 1
        return super().get_pull_request(number)


class Recording(Handler):
    """A stand-in handler that records every event it is handed and the reads before it."""

    def __init__(self, hosting: CountingHosting | None = None) -> None:
        """Record nothing yet; look at the reads of `hosting` when entered."""
        self.events: list[Event] = []
        self.reads_on_entry: list[int] = []
        self._hosting = hosting

    def handle(self, event: Event) -> None:
        """Record the event and the reads done so far."""
        if self._hosting is not None:
            self.reads_on_entry.append(self._hosting.reads)
        self.events.append(event)


class Gate:
    """A gate over three recording handlers, on a counting hosting service."""

    def __init__(self, boundaries: Boundaries) -> None:
        """Build the gate on `boundaries` with a counting hosting service."""
        self.hosting = CountingHosting()
        self.run = Recording(self.hosting)
        self.closed = Recording(self.hosting)
        self.merged = Recording(self.hosting)
        gated = dataclasses.replace(boundaries, hosting=self.hosting)
        self.gate = RunGate(gated, self.run, self.closed, self.merged)

    def opened(self) -> int:
        """Return the number of a new open pull request of the work item's branch."""
        return self.hosting.create_pull_request(BRANCH, "first", "body", draft=True).number


@pytest.fixture
def gate(boundaries: Boundaries) -> Gate:
    """Return a gate over recording handlers."""
    return Gate(boundaries)


def _run_event(
    number: int | None, state_with: StateWith, snapshot_of: SnapshotOf, event_of: EventOf
) -> Event:
    return event_of("run", snapshot_of(state_with(number)))


def test_a_work_item_without_a_pull_request_runs_unchanged_without_a_read(
    gate: Gate, *, state_with: StateWith, snapshot_of: SnapshotOf, event_of: EventOf
) -> None:
    event = _run_event(None, state_with, snapshot_of, event_of)
    gate.hosting.fail_next("get_pull_request")

    gate.gate.handle(event)

    assert gate.run.events == [event]
    assert gate.closed.events == []
    assert gate.merged.events == []
    assert gate.hosting.reads == 0


def test_an_open_pull_request_is_read_once_and_the_stage_runs_with_the_view(
    gate: Gate, *, state_with: StateWith, snapshot_of: SnapshotOf, event_of: EventOf
) -> None:
    number = gate.opened()
    view = gate.hosting.get_pull_request(number)
    gate.hosting.reads = 0
    event = _run_event(number, state_with, snapshot_of, event_of)

    gate.gate.handle(event)

    assert gate.hosting.reads == 1
    [received] = gate.run.events
    assert received.pull_request == view
    assert received.kind == "run"
    assert received.work_item == event.work_item
    assert gate.closed.events == []
    assert gate.merged.events == []


def test_the_pull_request_is_read_before_the_run_handler_is_entered(
    gate: Gate, *, state_with: StateWith, snapshot_of: SnapshotOf, event_of: EventOf
) -> None:
    number = gate.opened()
    event = _run_event(number, state_with, snapshot_of, event_of)

    gate.gate.handle(event)

    assert gate.run.reads_on_entry == [1]


def test_a_closed_pull_request_goes_to_the_closed_handler_as_a_closed_event(
    gate: Gate, *, state_with: StateWith, snapshot_of: SnapshotOf, event_of: EventOf
) -> None:
    number = gate.opened()
    gate.hosting.close_by_human(number)
    view = gate.hosting.get_pull_request(number)
    event = _run_event(number, state_with, snapshot_of, event_of)

    gate.gate.handle(event)

    [received] = gate.closed.events
    assert received.kind == "closed"
    assert received.pull_request == view
    assert received.work_item == event.work_item
    assert gate.run.events == []
    assert gate.merged.events == []


def test_a_merged_pull_request_goes_to_the_merged_handler_as_a_merged_event(
    gate: Gate, *, state_with: StateWith, snapshot_of: SnapshotOf, event_of: EventOf
) -> None:
    number = gate.opened()
    gate.hosting.merge_by_human(number, "b" * 40)
    view = gate.hosting.get_pull_request(number)
    event = _run_event(number, state_with, snapshot_of, event_of)

    gate.gate.handle(event)

    [received] = gate.merged.events
    assert received.kind == "merged"
    assert received.pull_request == view
    assert received.work_item == event.work_item
    assert gate.run.events == []
    assert gate.closed.events == []


def test_a_failing_read_raises_and_calls_no_handler(
    gate: Gate, *, state_with: StateWith, snapshot_of: SnapshotOf, event_of: EventOf
) -> None:
    number = gate.opened()
    event = _run_event(number, state_with, snapshot_of, event_of)
    gate.hosting.fail_next("get_pull_request")

    with pytest.raises(HostingServiceError):
        gate.gate.handle(event)

    assert gate.run.events == []
    assert gate.closed.events == []
    assert gate.merged.events == []


def _pushed_story(boundaries: Boundaries, human: HumanClone, pull_request: int) -> WorkItemSnapshot:
    human.start(BACKLOG_PATH)
    created = JournalRecord(number=1, speaker=HUMAN, kind="created")
    state = WorkItemState(stage="doing", pull_request=pull_request, journal=[created])
    text = boundaries.work_item_writer.render(WorkItemDocument(state=state, body=BODY))
    human.push_file(BRANCH, PATH, text)
    return WorkItemSnapshot(
        id=WORK_ITEM,
        path=PATH,
        folder="in-progress",
        branch=BRANCH,
        branch_commit=None,
        document=boundaries.work_item_reader.parse(text),
    )


def _due_run(snapshot: WorkItemSnapshot, checkout: GitCli, remote: Path) -> Event:
    checkout.fetch()
    main = remote_commit(remote, "main")
    assert main is not None
    fetched = snapshot.model_copy(update={"branch_commit": checkout.resolve(f"origin/{BRANCH}")})
    return Event(kind="run", work_item=fetched, remote_state=main)


def _real_gate(boundaries: Boundaries, run: Handler) -> RunGate:
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    closed = ClosedHandler(boundaries, definition)
    return RunGate(boundaries, run, closed, MergedHandler(boundaries))


def test_a_story_closed_while_its_stage_was_due_is_discarded_without_a_run(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    pull_request: int,
) -> None:
    snapshot = _pushed_story(boundaries, human, pull_request)
    hosting.close_by_human(pull_request)
    event = _due_run(snapshot, checkout, remote)
    run = Recording()

    _real_gate(boundaries, run).handle(event)

    checkout.fetch()
    assert checkout.show_file("origin/main", BACKLOG_PATH) is not None
    assert checkout.show_file("origin/main", PATH) is None
    assert remote_commit(remote, BRANCH) is None
    assert run.events == []


def test_a_story_merged_while_its_stage_was_due_is_archived_without_a_run(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    pull_request: int,
) -> None:
    snapshot = _pushed_story(boundaries, human, pull_request)
    human.merge(BRANCH, "merge")
    merge_commit = remote_commit(remote, "main")
    assert merge_commit is not None
    hosting.merge_by_human(pull_request, merge_commit)
    event = _due_run(snapshot, checkout, remote)
    run = Recording()

    _real_gate(boundaries, run).handle(event)

    checkout.fetch()
    assert checkout.show_file("origin/main", DONE_PATH) is not None
    assert checkout.show_file("origin/main", PATH) is None
    assert run.events == []
