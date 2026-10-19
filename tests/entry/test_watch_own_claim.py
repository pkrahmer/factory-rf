"""factory-watch shows its own instance's claim as held while the claim's lease runs."""

import io
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.clock import ManualClock
from factory.application.acceptance import AcceptanceService
from factory.application.boundaries import Boundaries
from factory.domain.acceptance import AcceptanceState
from factory.domain.identifiers import branch_name
from factory.domain.work_item import Claim, WorkItemDocument, initial_state
from factory.entry.watch import run_watch
from git_support import PIPELINE_YAML, install_agents
from human_clone import HumanClone

INSTANCE = "factory-1"
STORY = "F0001-S0001"
STORY_BRANCH = branch_name(STORY)
STORY_FEATURE = "factory/features/F0001-example"
BACKLOG_PATH = f"{STORY_FEATURE}/backlog/F0001-S0001-first.md"
STORY_PATH = f"{STORY_FEATURE}/in-progress/F0001-S0001-first.md"
ACCEPTANCE = "F0002-A0001"
ACCEPTANCE_BRANCH = f"work-item/{ACCEPTANCE}"
TODO = "factory/features/F0002-todo"
REPORT = f"{TODO}/in-progress/F0002-A0001-acceptance.md"


@pytest.fixture(autouse=True)
def _agents(agent_home: Path, boundaries: Boundaries) -> None:
    install_agents(agent_home, boundaries.pipeline_reader.parse(PIPELINE_YAML).roles)


def _claim(clock: ManualClock, stage: str, age: int) -> Claim:
    return Claim(
        instance=INSTANCE,
        stage=stage,
        started_at=clock.now() - timedelta(minutes=age),
        lease_duration=60,
    )


def _push_story(boundaries: Boundaries, human: HumanClone, claim: Claim) -> None:
    human.start(BACKLOG_PATH)
    state = initial_state("intake").model_copy(update={"claim": claim})
    document = WorkItemDocument(state=state, body="# First story\n")
    human.push_file(STORY_BRANCH, STORY_PATH, boundaries.work_item_writer.render(document))


def _push_acceptance(boundaries: Boundaries, human: HumanClone, claim: Claim) -> None:
    human.push_file("main", f"{TODO}/feature.md", "# Todo service\n")
    human.push_file("main", f"{TODO}/done/F0002-S0001-a.md", "# A\n")
    human.push_file("main", f"{TODO}/done/F0002-S0002-b.md", "# B\n")
    boundaries.git.fetch()
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    AcceptanceService(boundaries, definition).open("F0002")
    boundaries.git.fetch()
    text = boundaries.git.show_file(f"origin/{ACCEPTANCE_BRANCH}", REPORT)
    assert text is not None
    state = boundaries.work_item_reader.parse(text).state
    assert isinstance(state, AcceptanceState)
    claimed = state.model_copy(update={"stage": "acceptance", "claim": claim})
    document = WorkItemDocument(state=claimed, body="# Acceptance of Todo service\n")
    human.push_file(ACCEPTANCE_BRANCH, REPORT, boundaries.work_item_writer.render(document))


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
    human: HumanClone,
    clock: ManualClock,
    *,
    acceptance: bool,
    age: int,
    first_line: str,
    work_item: str,
) -> None:
    if acceptance:
        _push_acceptance(boundaries, human, _claim(clock, "acceptance", age))
    else:
        _push_story(boundaries, human, _claim(clock, "intake", age))
    boundaries.git.fetch()
    out, err = io.StringIO(), io.StringIO()

    status = run_watch(boundaries, INSTANCE, out, err)

    lines = out.getvalue().splitlines()
    rows = [line for line in lines[1:] if line.startswith(work_item)]
    assert (status, lines[0], err.getvalue()) == (0, first_line, "")
    assert len(rows) == 1
    assert f"claim={INSTANCE}" in rows[0]
