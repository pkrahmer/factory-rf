"""Shared data of the watcher's tests: a claimed story, the due `F0002-todo`, its acceptance."""

from datetime import timedelta

from factory.adapters.clock import ManualClock
from factory.application.acceptance import AcceptanceService
from factory.application.boundaries import Boundaries
from factory.domain.acceptance import AcceptanceState
from factory.domain.identifiers import branch_name
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import Claim, WorkItemDocument, initial_state
from human_clone import HumanClone

FEATURES = "factory/features"
STORY = "F0001-S0001"
STORY_BRANCH = branch_name(STORY)
STORY_FEATURE = f"{FEATURES}/F0001-example"
BACKLOG_PATH = f"{STORY_FEATURE}/backlog/F0001-S0001-first.md"
STORY_PATH = f"{STORY_FEATURE}/in-progress/F0001-S0001-first.md"
ACCEPTANCE = "F0002-A0001"
ACCEPTANCE_BRANCH = f"work-item/{ACCEPTANCE}"
TODO = f"{FEATURES}/F0002-todo"
REPORT = f"{TODO}/in-progress/F0002-A0001-acceptance.md"


def aged_claim(clock: ManualClock, instance: str, stage: str, age: int) -> Claim:
    """Return `instance`'s 60-minute claim of `stage`, started `age` minutes before `clock`."""
    return Claim(
        instance=instance,
        stage=stage,
        started_at=clock.now() - timedelta(minutes=age),
        lease_duration=60,
    )


def push_story_claim(boundaries: Boundaries, human: HumanClone, claim: Claim) -> None:
    """Start the story `F0001-S0001` and push its branch state at stage `intake` with `claim`."""
    human.start(BACKLOG_PATH)
    state = initial_state("intake").model_copy(update={"claim": claim})
    document = WorkItemDocument(state=state, body="# First story\n")
    human.push_file(STORY_BRANCH, STORY_PATH, boundaries.work_item_writer.render(document))


def push_complete(human: HumanClone, directory: str = "F0002-todo") -> None:
    """Push the feature in `directory` to `main`: its feature file and two archived stories."""
    feature = directory.split("-", maxsplit=1)[0]
    human.push_file("main", f"{FEATURES}/{directory}/feature.md", "# Todo service\n")
    human.push_file("main", f"{FEATURES}/{directory}/done/{feature}-S0001-a.md", "# A\n")
    human.push_file("main", f"{FEATURES}/{directory}/done/{feature}-S0002-b.md", "# B\n")


def open_acceptance(boundaries: Boundaries, definition: PipelineDefinition, feature: str) -> str:
    """Open the acceptance of `feature` and return its branch."""
    boundaries.git.fetch()
    return AcceptanceService(boundaries, definition).open(feature).branch


def acceptance_branch_state(boundaries: Boundaries) -> AcceptanceState:
    """Return the state of `F0002-A0001` on its branch."""
    boundaries.git.fetch()
    text = boundaries.git.show_file(f"origin/{ACCEPTANCE_BRANCH}", REPORT)
    assert text is not None
    state = boundaries.work_item_reader.parse(text).state
    assert isinstance(state, AcceptanceState)
    return state


def push_acceptance_state(
    boundaries: Boundaries, human: HumanClone, state: AcceptanceState
) -> None:
    """Push `state` as the state of `F0002-A0001` on its branch."""
    document = WorkItemDocument(state=state, body="# Acceptance of Todo service\n")
    human.push_file(ACCEPTANCE_BRANCH, REPORT, boundaries.work_item_writer.render(document))


def push_acceptance_claim(
    boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone, claim: Claim
) -> None:
    """Open the acceptance of `F0002`; push its branch state at stage `acceptance` with `claim`."""
    open_acceptance(boundaries, definition, "F0002")
    update = {"stage": "acceptance", "claim": claim}
    push_acceptance_state(
        boundaries, human, acceptance_branch_state(boundaries).model_copy(update=update)
    )
