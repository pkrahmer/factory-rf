"""factory-watch shows its own instance's claim as held while the claim's lease runs."""

import io

import pytest

from factory.adapters.clock import ManualClock
from factory.application.boundaries import Boundaries
from factory.domain.pipeline_definition import PipelineDefinition
from factory.entry.watch import run_watch
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

pytestmark = pytest.mark.usefixtures("installed_agents")


@pytest.mark.parametrize(
    ("acceptance", "age", "first_line", "work_item"),
    [
        pytest.param(
            False,
            59,
            f"event: idle:-  {STORY} is held by {INSTANCE}",
            STORY,
            id="story-within-lease",
        ),
        pytest.param(False, 60, f"event: crash:{STORY}", STORY, id="story-at-lease"),
        pytest.param(
            True,
            59,
            f"event: idle:-  {ACCEPTANCE} is held by {INSTANCE}",
            ACCEPTANCE,
            id="acceptance-within-lease",
        ),
    ],
)
def test_the_watch_judges_its_own_instances_claim_by_the_lease(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    human: HumanClone,
    clock: ManualClock,
    *,
    acceptance: bool,
    age: int,
    first_line: str,
    work_item: str,
) -> None:
    if acceptance:
        push_complete(human)
        push_acceptance_claim(
            boundaries, definition, human, aged_claim(clock, INSTANCE, "acceptance", age)
        )
    else:
        push_story_claim(boundaries, human, aged_claim(clock, INSTANCE, "intake", age))
    boundaries.git.fetch()
    out, err = io.StringIO(), io.StringIO()

    status = run_watch(boundaries, INSTANCE, out, err)

    lines = out.getvalue().splitlines()
    rows = [line for line in lines[1:] if line.startswith(work_item)]
    assert (status, lines[0], err.getvalue()) == (0, first_line, "")
    assert len(rows) == 1
    assert f"claim={INSTANCE}" in rows[0]
