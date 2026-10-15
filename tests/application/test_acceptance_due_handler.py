"""The handler of `acceptance_due` opens the event's feature and refuses every other event."""

from pathlib import Path

import pytest

from factory.application.acceptance import AcceptanceDueHandler
from factory.application.boundaries import Boundaries
from factory.domain.errors import CannotHandle
from factory.domain.events import Event
from factory.domain.pipeline_definition import PipelineDefinition
from git_support import PIPELINE_YAML, remote_commit, run_git
from human_clone import HumanClone

TODO = "factory/features/F0002-todo"
BRANCH = "work-item/F0002-A0001"
STATE = "a" * 40


@pytest.fixture
def definition(boundaries: Boundaries) -> PipelineDefinition:
    """Return the test remote's pipeline definition, with an acceptance stage."""
    return boundaries.pipeline_reader.parse(PIPELINE_YAML)


@pytest.fixture
def without_acceptance(definition: PipelineDefinition) -> PipelineDefinition:
    """Return the pipeline definition without an acceptance stage."""
    return definition.model_copy(update={"acceptance_stage": None})


def _due_event(feature: str | None = "F0002") -> Event:
    return Event.model_construct(
        kind="acceptance_due", work_item=None, feature=feature, remote_state=STATE
    )


def _run_event() -> Event:
    return Event.model_construct(kind="run", work_item=None, remote_state=STATE)


def test_an_acceptance_due_event_opens_its_feature(
    boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone, remote: Path
) -> None:
    human.push_file("main", f"{TODO}/feature.md", "# Todo service\n")
    human.push_file("main", f"{TODO}/done/F0002-S0001-a.md", "# A\n")
    boundaries.git.fetch()

    AcceptanceDueHandler(boundaries, definition).handle(
        Event(kind="acceptance_due", work_item=None, feature="F0002", remote_state=STATE)
    )

    assert remote_commit(remote, BRANCH) is not None


@pytest.mark.parametrize(
    ("event", "kind", "reason"),
    [
        (_run_event(), "run", "not an acceptance_due event"),
        (_due_event(None), "acceptance_due", "no feature"),
    ],
    ids=["other-kind", "no-feature"],
)
def test_an_event_the_handler_cannot_open_is_refused_and_pushes_nothing(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    remote: Path,
    event: Event,
    kind: str,
    reason: str,
) -> None:
    before = run_git(remote, "for-each-ref")

    with pytest.raises(CannotHandle) as raised:
        AcceptanceDueHandler(boundaries, definition).handle(event)

    assert (raised.value.kind, raised.value.reason) == (kind, reason)
    assert run_git(remote, "for-each-ref") == before


@pytest.mark.parametrize(
    ("event", "kind", "reason"),
    [
        (_due_event(), "acceptance_due", "no acceptance stage"),
        (_run_event(), "run", "not an acceptance_due event"),
    ],
    ids=["acceptance-due", "other-kind"],
)
def test_without_an_acceptance_stage_the_handler_is_built_and_refuses_every_event(
    boundaries: Boundaries,
    without_acceptance: PipelineDefinition,
    *,
    remote: Path,
    event: Event,
    kind: str,
    reason: str,
) -> None:
    handler = AcceptanceDueHandler(boundaries, without_acceptance)
    before = run_git(remote, "for-each-ref")

    with pytest.raises(CannotHandle) as raised:
        handler.handle(event)

    assert (raised.value.kind, raised.value.reason) == (kind, reason)
    assert run_git(remote, "for-each-ref") == before
