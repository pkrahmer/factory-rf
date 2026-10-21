"""The watcher rejects a stage change the pipeline definition forbids, but never a merge."""

from pathlib import Path
from typing import Literal

import pytest

from branch_reading import push_state
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.adapters.work_item_markdown import FrontmatterWorkItemWriter
from factory.application.boundaries import Boundaries
from factory.application.watcher import Watcher
from factory.domain.events import Event
from factory.domain.identifiers import branch_name
from factory.domain.journal import JournalKind, JournalRecord
from factory.domain.move_rule import FactoryMove, factory_moves
from factory.domain.work_item import WorkItemDocument, WorkItemState
from git_support import PIPELINE_YAML, remote_commit
from human_clone import HumanClone

INSTANCE = "factory-1"
WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
FEATURE = "factory/features/F0001-example"
BACKLOG_PATH = f"{FEATURE}/backlog/F0001-S0001-first.md"
PATH = f"{FEATURE}/in-progress/F0001-S0001-first.md"
BODY = "# First story\n"

FIXTURE = RuamelPipelineDefinitionReader().parse(PIPELINE_YAML)


def _journal(*kinds: JournalKind) -> list[JournalRecord]:
    return [
        JournalRecord(number=number, speaker="factory", kind=kind)
        for number, kind in enumerate(kinds, start=1)
    ]


def _state(
    stage: str, pull_request: int, journal: list[JournalRecord] | None = None
) -> WorkItemState:
    # An approval stage is handed over, so the only thing left to notice is the stage change.
    approval = stage in FIXTURE.stages and FIXTURE.stages[stage].approval
    return WorkItemState(
        stage=stage,
        pull_request=pull_request,
        handed_over=stage if approval else None,
        journal=[] if journal is None else journal,
    )


def _open(human: HumanClone, hosting: FakeHostingService, stage: str) -> int:
    human.start(BACKLOG_PATH)
    number = hosting.create_pull_request(BRANCH, "First story", "", draft=False).number
    push_state(human, _state(stage, number))
    return number


def _evaluate(boundaries: Boundaries) -> Event:
    boundaries.git.fetch()
    return Watcher(boundaries, INSTANCE).evaluate(FIXTURE)


def _merge(
    human: HumanClone,
    hosting: FakeHostingService,
    remote: Path,
    number: int,
    method: Literal["merge", "squash", "rebase"],
) -> None:
    human.merge(BRANCH, method)
    merge_commit = remote_commit(remote, "main")
    assert merge_commit is not None
    hosting.merge_by_human(number, merge_commit)


def test_a_hand_made_stage_change_the_definition_forbids_is_rejected(
    boundaries: Boundaries, human: HumanClone, hosting: FakeHostingService
) -> None:
    number = _open(human, hosting, "tests")
    push_state(human, _state("review", number))

    event = _evaluate(boundaries)

    assert event.kind == "reject"
    assert event.work_item is not None
    assert event.work_item.id == WORK_ITEM
    assert "tests" in event.detail
    assert "review" in event.detail
    assert hosting.get_pull_request(number).state == "open"


def test_the_correction_commit_ends_the_reject(
    boundaries: Boundaries, human: HumanClone, hosting: FakeHostingService
) -> None:
    number = _open(human, hosting, "tests")
    push_state(human, _state("review", number, _journal("started")))
    assert _evaluate(boundaries).kind == "reject"
    push_state(human, _state("tests", number, _journal("started", "move_back")))

    event = _evaluate(boundaries)

    assert event.kind != "reject"


@pytest.mark.parametrize("method", ["merge", "squash", "rebase"])
def test_a_merge_by_any_method_is_merged_and_never_a_reject(
    boundaries: Boundaries,
    human: HumanClone,
    hosting: FakeHostingService,
    remote: Path,
    method: Literal["merge", "squash", "rebase"],
) -> None:
    number = _open(human, hosting, "smoke-test")
    push_state(human, _state("approval", number))
    _merge(human, hosting, remote, number, method)

    event = _evaluate(boundaries)

    assert event.kind == "merged"


@pytest.mark.parametrize(("merged", "kind"), [(True, "merged"), (False, "reject")])
def test_an_illegal_change_beside_a_merged_pull_request_is_merged(
    boundaries: Boundaries,
    human: HumanClone,
    hosting: FakeHostingService,
    remote: Path,
    *,
    merged: bool,
    kind: str,
) -> None:
    number = _open(human, hosting, "tests")
    push_state(human, _state("approval", number))
    if merged:
        _merge(human, hosting, remote, number, "squash")

    event = _evaluate(boundaries)

    assert event.kind == kind


def test_the_opening_commit_of_a_started_story_is_no_reject(
    boundaries: Boundaries, human: HumanClone
) -> None:
    on_main = WorkItemDocument(state=WorkItemState(stage="review"), body=BODY)
    human.push_file("main", BACKLOG_PATH, FrontmatterWorkItemWriter().render(on_main))
    human.start(BACKLOG_PATH)
    push_state(human, WorkItemState(stage=FIXTURE.first_stage()))

    event = _evaluate(boundaries)

    assert event.kind != "reject"


@pytest.mark.parametrize(
    "move", factory_moves(FIXTURE), ids=lambda move: f"{move.from_stage}-{move.to_stage}"
)
def test_every_factory_move_is_no_reject(
    boundaries: Boundaries, human: HumanClone, hosting: FakeHostingService, move: FactoryMove
) -> None:
    number = _open(human, hosting, move.from_stage)
    push_state(human, _state(move.to_stage, number))

    event = _evaluate(boundaries)

    assert event.kind != "reject"
