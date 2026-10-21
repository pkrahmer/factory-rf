"""The tick deletes the branch a killed discard left behind, between the restore and evaluation."""

import os
from pathlib import Path

import pytest

from definition_support import pipeline_definition
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.handlers.closed import ClosedHandler
from factory.application.tick import IdleHandler, Tick, TickOutcome
from factory.domain.events import Event
from factory.domain.identifiers import branch_name
from factory.domain.journal import HUMAN, JournalRecord
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.work_item import (
    WorkItemDocument,
    WorkItemSnapshot,
    WorkItemState,
    initial_state,
)
from git_support import CHECKOUT, install_agents, remote_commit
from human_clone import HumanClone
from log_support import log_lines
from stage_run_support import INSTANCE
from tick_support import handlers_of

WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
FEATURE = "factory/features/F0001-example"
BACKLOG_PATH = f"{FEATURE}/backlog/F0001-S0001-first.md"
PATH = f"{FEATURE}/in-progress/F0001-S0001-first.md"
BRANCH_BODY = "# First story\n\nRewritten by the factory on the branch.\n"


class Recording(Handler):
    """Records every event it is handed."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


def _discard_killed_after_push(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    kill_points: KillPoints,
) -> None:
    number = hosting.create_pull_request(BRANCH, f"{WORK_ITEM}: first", "body", draft=True).number
    human.start(BACKLOG_PATH)
    created = JournalRecord(number=1, speaker=HUMAN, kind="created")
    state = WorkItemState(stage="doing", pull_request=number, journal=[created])
    text = boundaries.work_item_writer.render(WorkItemDocument(state=state, body=BRANCH_BODY))
    human.push_file(BRANCH, PATH, text)
    hosting.close_by_human(number)
    checkout.fetch()
    snapshot = WorkItemSnapshot(
        id=WORK_ITEM,
        path=PATH,
        folder="in-progress",
        branch=BRANCH,
        branch_commit=checkout.resolve(f"origin/{BRANCH}"),
        document=boundaries.work_item_reader.parse(text),
    )
    main = remote_commit(remote, "main")
    assert main is not None
    kill_points.arm(KillPoint.AFTER_PUSH)
    with pytest.raises(InjectedKill):
        ClosedHandler(boundaries, pipeline_definition(boundaries)).handle(
            Event(kind="closed", work_item=snapshot, remote_state=main)
        )
    assert remote_commit(remote, BRANCH) is not None


@pytest.fixture
def discarded(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    kill_points: KillPoints,
    agent_home: Path,
) -> None:
    """Discard a started story with a kill after the move was pushed; install the agents."""
    _discard_killed_after_push(
        boundaries,
        remote=remote,
        human=human,
        checkout=checkout,
        hosting=hosting,
        kill_points=kill_points,
    )
    install_agents(agent_home, pipeline_definition(boundaries).roles)


@pytest.mark.usefixtures("discarded")
def test_the_next_tick_deletes_the_branch_a_killed_discard_left_and_stays_idle(
    boundaries: Boundaries, checkout: GitCli
) -> None:
    recording = Recording()
    tick = Tick(boundaries, INSTANCE, handlers_of({"idle": IdleHandler(), "run": recording}))

    outcome = tick.run()

    assert checkout.resolve(f"origin/{BRANCH}") is None
    assert outcome.event is not None
    assert outcome.event.kind == "idle"
    assert outcome.dispatch is not None
    assert recording.events == []


@pytest.mark.usefixtures("discarded")
def test_a_story_started_again_after_the_cleanup_starts_from_the_first_stage(
    boundaries: Boundaries, human: HumanClone
) -> None:
    recording = Recording()
    tick = Tick(boundaries, INSTANCE, handlers_of({"idle": IdleHandler(), "run": recording}))
    tick.run()
    human.start(BACKLOG_PATH)

    outcome = tick.run()

    assert outcome.event is not None
    assert outcome.event.kind == "run"
    assert [event.kind for event in recording.events] == ["run"]
    work_item = outcome.event.work_item
    assert work_item is not None
    assert work_item.branch_commit is None
    assert work_item.document.state == initial_state(pipeline_definition(boundaries).first_stage())


def test_a_tick_that_ends_at_a_repository_stop_deletes_nothing(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, human: HumanClone
) -> None:
    human.push_file(BRANCH, "marker.txt", "x\n")
    checkout.fetch()
    before = remote_commit(remote, BRANCH)
    tick = Tick(boundaries, INSTANCE, handlers_of({"idle": IdleHandler(), "run": Recording()}))

    outcome = tick.run()

    assert outcome == TickOutcome(stopped="pipeline_definition_invalid")
    assert before is not None
    assert remote_commit(remote, BRANCH) == before


@pytest.mark.skipif(os.geteuid() == 0, reason="root removes files in unwritable directories")
def test_a_tick_that_ends_at_the_restore_stop_deletes_nothing(
    boundaries: Boundaries,
    *,
    remote: Path,
    checkout: GitCli,
    human: HumanClone,
    agent_home: Path,
    tmp_path: Path,
) -> None:
    install_agents(agent_home, pipeline_definition(boundaries).roles)
    human.push_file(BRANCH, "marker.txt", "x\n")
    checkout.fetch()
    before = remote_commit(remote, BRANCH)
    locked = tmp_path / CHECKOUT / "locked"
    locked.mkdir()
    (locked / "file.txt").write_text("cannot be removed\n", encoding="utf-8")
    locked.chmod(0o555)
    tick = Tick(boundaries, INSTANCE, handlers_of({"idle": IdleHandler(), "run": Recording()}))
    try:
        outcome = tick.run()
    finally:
        locked.chmod(0o755)

    assert outcome == TickOutcome(stopped="checkout_restore_failed")
    assert before is not None
    assert remote_commit(remote, BRANCH) == before

    tick.run()

    assert remote_commit(remote, BRANCH) is None


def test_a_tick_that_ends_at_the_fetch_stop_tries_no_deletion(
    boundaries: Boundaries,
    *,
    remote: Path,
    checkout: GitCli,
    human: HumanClone,
    agent_home: Path,
    tmp_path: Path,
) -> None:
    install_agents(agent_home, pipeline_definition(boundaries).roles)
    human.push_file(BRANCH, "marker.txt", "x\n")
    checkout.fetch()
    away = remote.rename(tmp_path / "away.git")
    tick = Tick(boundaries, INSTANCE, handlers_of({"idle": IdleHandler(), "run": Recording()}))

    outcome = tick.run()

    assert outcome == TickOutcome(stopped="fetch_failed")
    assert not [line for line in log_lines(tmp_path) if "stale branch" in line]

    away.rename(remote)
    tick.run()

    assert remote_commit(remote, BRANCH) is None
