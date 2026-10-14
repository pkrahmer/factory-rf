"""A work item claimed by this instance, ready to crash, for the crash-cap tests."""

from dataclasses import dataclass
from datetime import date

from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService, StageStart
from factory.application.dispatcher import Handler
from factory.application.recovery import RecoveryHandler
from factory.domain.events import Event
from factory.domain.identifiers import branch_name
from factory.domain.journal import HUMAN, NewEntry, append_entry
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import (
    WorkItemDocument,
    WorkItemSnapshot,
    WorkItemState,
    initial_state,
)
from git_support import PIPELINE_YAML
from human_clone import HumanClone

INSTANCE = "factory-1"
STAGE = "doing"
WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
STORY_TITLE = "First story"
STORY = f"# {STORY_TITLE}\n\n## Journal\n\n"


class Rerun(Handler):
    """Records each event it is given."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


@dataclass(frozen=True)
class Claimed:
    """The definition the work item was claimed under and its pushed stage start."""

    definition: PipelineDefinition
    start: StageStart


def claim(
    boundaries: Boundaries,
    human: HumanClone,
    *,
    crashes: int = 1,
    attempts: int = 1,
    pull_request: int | None = None,
    body: str = STORY,
) -> Claimed:
    """Start the story, check its branch out and claim the stage as `INSTANCE`."""
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    git = boundaries.git
    git.fetch()
    git.checkout(BRANCH, start_point="origin/main")
    state = initial_state(STAGE).model_copy(
        update={"crashes": crashes, "attempts": attempts, "pull_request": pull_request}
    )
    created = NewEntry(speaker=HUMAN, kind="created", text="created.", on=date(2026, 10, 12))
    document = append_entry(WorkItemDocument(state=state, body=body), created)
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    start = ClaimService(boundaries, INSTANCE, definition).claim(BRANCH, PATH, document, STAGE)
    return Claimed(definition=definition, start=start)


def remote_head(boundaries: Boundaries) -> str:
    """The commit `origin/<branch>` points to after a fetch."""
    boundaries.git.fetch()
    head = boundaries.git.resolve(f"origin/{BRANCH}")
    assert head is not None
    return head


def document_at(boundaries: Boundaries, ref: str) -> WorkItemDocument:
    """The work item document at `ref`."""
    text = boundaries.git.show_file(ref, PATH)
    assert text is not None
    return boundaries.work_item_reader.parse(text)


def remote_state(boundaries: Boundaries) -> WorkItemState:
    """The work item's state on `origin/<branch>`."""
    remote_head(boundaries)
    state = document_at(boundaries, f"origin/{BRANCH}").state
    assert state is not None
    return state


def snapshot(boundaries: Boundaries) -> WorkItemSnapshot:
    """The work item as the remote-tracking branch shows it after a fetch."""
    head = remote_head(boundaries)
    return WorkItemSnapshot(
        id=WORK_ITEM,
        path=PATH,
        folder="in-progress",
        branch=BRANCH,
        branch_commit=head,
        document=document_at(boundaries, f"origin/{BRANCH}"),
    )


def crash_event(work_item: WorkItemSnapshot) -> Event:
    """The crash event of the work item as it is on the remote."""
    assert work_item.branch_commit is not None
    return Event(kind="crash", work_item=work_item, remote_state=work_item.branch_commit)


def handler(
    boundaries: Boundaries, definition: PipelineDefinition, run: Handler
) -> RecoveryHandler:
    """A new recovery handler for `INSTANCE` that reruns with `run`."""
    return RecoveryHandler(
        boundaries, definition, ClaimService(boundaries, INSTANCE, definition), run
    )
