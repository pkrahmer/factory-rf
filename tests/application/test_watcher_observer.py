"""A watcher that looks from outside the tick judges its own instance's claim by the lease."""

from datetime import timedelta

import pytest

from factory.adapters.clock import ManualClock
from factory.adapters.work_item_markdown import FrontmatterWorkItemWriter
from factory.application.acceptance import AcceptanceService
from factory.application.boundaries import Boundaries
from factory.application.watcher import Watcher
from factory.domain.acceptance import AcceptanceState
from factory.domain.events import Event
from factory.domain.identifiers import branch_name
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import Claim, WorkItemDocument, initial_state
from git_support import PIPELINE_YAML
from human_clone import HumanClone

INSTANCE = "factory-1"
OTHER_INSTANCE = "factory-2"
STORY = "F0001-S0001"
STORY_BRANCH = branch_name(STORY)
STORY_FEATURE = "factory/features/F0001-example"
BACKLOG_PATH = f"{STORY_FEATURE}/backlog/F0001-S0001-first.md"
STORY_PATH = f"{STORY_FEATURE}/in-progress/F0001-S0001-first.md"
ACCEPTANCE = "F0002-A0001"
ACCEPTANCE_BRANCH = f"work-item/{ACCEPTANCE}"
TODO = "factory/features/F0002-todo"
REPORT = f"{TODO}/in-progress/F0002-A0001-acceptance.md"


@pytest.fixture
def definition(boundaries: Boundaries) -> PipelineDefinition:
    """Return the test remote's pipeline definition, with the acceptance stage `acceptance`."""
    return boundaries.pipeline_reader.parse(PIPELINE_YAML)


def _claim(clock: ManualClock, instance: str, stage: str, age: int) -> Claim:
    return Claim(
        instance=instance,
        stage=stage,
        started_at=clock.now() - timedelta(minutes=age),
        lease_duration=60,
    )


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
    human.start(BACKLOG_PATH)
    claim = _claim(clock, instance, "intake", age)
    state = initial_state("intake").model_copy(update={"claim": claim})
    text = FrontmatterWorkItemWriter().render(WorkItemDocument(state=state, body="# First story\n"))
    human.push_file(STORY_BRANCH, STORY_PATH, text)

    event = _evaluate(boundaries, definition, observer)

    assert _outcome(event) == outcome


def _push_complete_todo(human: HumanClone) -> None:
    human.push_file("main", f"{TODO}/feature.md", "# Todo service\n")
    human.push_file("main", f"{TODO}/done/F0002-S0001-a.md", "# A\n")
    human.push_file("main", f"{TODO}/done/F0002-S0002-b.md", "# B\n")


def _push_acceptance_claim(
    boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone, claim: Claim
) -> None:
    boundaries.git.fetch()
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
    _push_complete_todo(human)
    _push_acceptance_claim(
        boundaries, definition, human, _claim(clock, INSTANCE, "acceptance", age)
    )

    event = _evaluate(boundaries, definition, observer)

    assert _outcome(event) == outcome
