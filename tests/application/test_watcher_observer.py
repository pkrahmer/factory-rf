"""A watcher that looks from outside the tick judges its own instance's claim by the lease."""

import pytest

from factory.adapters.clock import ManualClock
from factory.application.boundaries import Boundaries
from factory.application.watcher import Watcher
from factory.domain.events import Event
from factory.domain.pipeline_definition import PipelineDefinition
from human_clone import HumanClone
from stage_run_support import INSTANCE
from watch_support import (
    ACCEPTANCE,
    STORY,
    aged_claim,
    push_acceptance_claim,
    push_complete,
    push_story_claim,
)

OTHER_INSTANCE = "factory-2"


def _evaluate(
    boundaries: Boundaries, definition: PipelineDefinition, observer: bool | None
) -> Event:
    boundaries.git.fetch()
    if observer is None:
        return Watcher(boundaries, INSTANCE).evaluate(definition)
    return Watcher(boundaries, INSTANCE, observer=observer).evaluate(definition)


def _outcome(event: Event) -> tuple[str, str | None, str]:
    work_item = None if event.work_item is None else event.work_item.id
    return event.kind, work_item, event.detail if event.kind == "idle" else ""


@pytest.mark.parametrize(
    ("observer", "instance", "age", "outcome"),
    [
        pytest.param(
            True,
            INSTANCE,
            59,
            ("idle", None, f"{STORY} is held by {INSTANCE}"),
            id="observer-own-within-lease",
        ),
        pytest.param(True, INSTANCE, 60, ("crash", STORY, ""), id="observer-own-at-lease"),
        pytest.param(
            True,
            OTHER_INSTANCE,
            59,
            ("idle", None, f"{STORY} is held by {OTHER_INSTANCE}"),
            id="observer-other-within-lease",
        ),
        pytest.param(
            True, OTHER_INSTANCE, 60, ("expired", STORY, ""), id="observer-other-at-lease"
        ),
        pytest.param(None, INSTANCE, 0, ("crash", STORY, ""), id="tick-own-at-start"),
        pytest.param(None, INSTANCE, 59, ("crash", STORY, ""), id="tick-own-within-lease"),
    ],
)
def test_a_story_claim_is_judged_from_outside_by_its_lease(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    human: HumanClone,
    clock: ManualClock,
    *,
    observer: bool | None,
    instance: str,
    age: int,
    outcome: tuple[str, str | None, str],
) -> None:
    push_story_claim(boundaries, human, aged_claim(clock, instance, "intake", age))

    event = _evaluate(boundaries, definition, observer)

    assert _outcome(event) == outcome


@pytest.mark.parametrize(
    ("observer", "age", "outcome"),
    [
        pytest.param(
            True,
            59,
            ("idle", None, f"{ACCEPTANCE} is held by {INSTANCE}"),
            id="observer-within-lease",
        ),
        pytest.param(True, 60, ("crash", ACCEPTANCE, ""), id="observer-at-lease"),
        pytest.param(None, 59, ("crash", ACCEPTANCE, ""), id="tick-within-lease"),
    ],
)
def test_an_acceptance_claim_is_judged_from_outside_by_its_lease(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    human: HumanClone,
    clock: ManualClock,
    *,
    observer: bool | None,
    age: int,
    outcome: tuple[str, str | None, str],
) -> None:
    push_complete(human)
    claim = aged_claim(clock, INSTANCE, "acceptance", age)
    push_acceptance_claim(boundaries, definition, human, claim)

    event = _evaluate(boundaries, definition, observer)

    assert _outcome(event) == outcome
