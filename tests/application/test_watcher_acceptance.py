"""The watcher's evaluation sees the acceptances in flight and the features that are due."""

from pathlib import Path
from typing import Literal

import pytest

from factory.adapters.fake_hosting import FakeHostingService
from factory.application.acceptance_reading import AcceptanceReader
from factory.application.boundaries import Boundaries
from factory.application.watcher import Watcher
from factory.domain.events import Event
from factory.domain.pipeline_definition import PipelineDefinition
from git_support import remote_commit
from human_clone import HumanClone
from stage_run_support import INSTANCE
from watch_support import (
    ACCEPTANCE,
    ACCEPTANCE_BRANCH,
    FEATURES,
    acceptance_branch_state,
    open_acceptance,
    push_acceptance_state,
    push_complete,
)

ARCHIVED = ["F0002-S0001", "F0002-S0002"]


def _evaluate(boundaries: Boundaries, definition: PipelineDefinition) -> Event:
    boundaries.git.fetch()
    return Watcher(boundaries, INSTANCE).evaluate(definition)


def test_an_in_flight_acceptance_without_a_claim_runs(
    boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone
) -> None:
    push_complete(human, "F0002-todo")
    open_acceptance(boundaries, definition, "F0002")

    event = _evaluate(boundaries, definition)

    assert event.kind == "run"
    assert event.work_item is not None
    assert event.work_item.id == ACCEPTANCE


@pytest.mark.parametrize("directory", ["F0002-2fa", "F0002"], ids=["digit-slug", "no-slug"])
def test_a_started_story_of_the_feature_runs_before_its_in_flight_acceptance(
    boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone, directory: str
) -> None:
    push_complete(human, directory)
    open_acceptance(boundaries, definition, "F0002")
    backlog = f"{FEATURES}/{directory}/backlog/F0002-S0003-c.md"
    human.push_file("main", backlog, "# C\n")
    human.start(backlog)

    event = _evaluate(boundaries, definition)

    assert event.kind == "run"
    assert event.work_item is not None
    assert event.work_item.id == "F0002-S0003"


@pytest.mark.parametrize("method", ["merge", "squash", "rebase"])
def test_a_merged_acceptance_at_its_approval_is_a_merged_event(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    human: HumanClone,
    hosting: FakeHostingService,
    remote: Path,
    method: Literal["merge", "squash", "rebase"],
) -> None:
    push_complete(human, "F0002-todo")
    open_acceptance(boundaries, definition, "F0002")
    view = hosting.create_pull_request(
        ACCEPTANCE_BRANCH, f"{ACCEPTANCE}: acceptance", "", draft=False
    )
    update = {"stage": "approval", "pull_request": view.number, "handed_over": "approval"}
    push_acceptance_state(
        boundaries, human, acceptance_branch_state(boundaries).model_copy(update=update)
    )
    human.merge(ACCEPTANCE_BRANCH, method)
    main = remote_commit(remote, "main")
    assert main is not None
    hosting.merge_by_human(view.number, main)
    boundaries.git.fetch()
    [snapshot] = AcceptanceReader(boundaries, definition).snapshots()

    event = _evaluate(boundaries, definition)

    assert event.kind == "merged"
    assert event.work_item == snapshot
    assert event.pull_request == hosting.get_pull_request(view.number)


def test_a_due_feature_is_an_acceptance_due_event_at_mains_head(
    boundaries: Boundaries, definition: PipelineDefinition, *, human: HumanClone, remote: Path
) -> None:
    push_complete(human, "F0002-todo")

    event = _evaluate(boundaries, definition)

    assert (event.kind, event.feature, event.work_item) == ("acceptance_due", "F0002", None)
    assert event.remote_state == remote_commit(remote, "main")


def test_without_an_acceptance_stage_acceptances_and_due_features_are_not_seen(
    boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone
) -> None:
    push_complete(human, "F0002-todo")
    open_acceptance(boundaries, definition, "F0002")
    push_complete(human, "F0003-later")
    without = definition.model_copy(update={"acceptance_stage": None})

    event = _evaluate(boundaries, without)

    assert event.kind == "idle"


def test_a_stage_change_the_definition_forbids_on_an_acceptance_branch_is_rejected(
    boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone
) -> None:
    push_complete(human, "F0002-todo")
    open_acceptance(boundaries, definition, "F0002")
    push_acceptance_state(
        boundaries,
        human,
        acceptance_branch_state(boundaries).model_copy(update={"stage": "intake"}),
    )

    event = _evaluate(boundaries, definition)

    assert event.kind == "reject"
    assert event.work_item is not None
    assert event.work_item.id == ACCEPTANCE
