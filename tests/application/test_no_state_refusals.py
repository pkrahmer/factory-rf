"""A document without a state is refused by each call that needs one, before anything is written."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from crash_support import Rerun
from definition_support import pipeline_definition
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService
from factory.application.recovery import RecoveryHandler
from factory.application.stalls import StallContext, StallService
from factory.application.task import TaskComposer, TaskContext
from factory.domain.agent_runs import AgentDefinition, GuardSettings
from factory.domain.errors import CannotHandle, WorkItemFormatError
from factory.domain.identifiers import branch_name
from factory.domain.journal import JournalRecord
from factory.domain.work_item import Claim, WorkItemDocument, WorkItemSnapshot, WorkItemState
from git_support import CHECKOUT, remote_commit
from human_clone import HumanClone

INSTANCE = "factory-1"
WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
STORY = "# First story\n\n## Description\n\nText.\n\n## Journal\n"
BODY = STORY + "\n1. 2026-10-12 human: created.\n"
CREATED = JournalRecord(number=1, speaker="human", kind="created")
STATELESS = WorkItemDocument(state=None, body=BODY)
CLAIM = Claim(
    instance=INSTANCE,
    stage="intake",
    started_at=datetime(2026, 10, 12, 12, 0, tzinfo=UTC),
    lease_duration=60,
)


def _branch_head(remote: Path) -> str:
    commit = remote_commit(remote, BRANCH)
    assert commit is not None
    return commit


@pytest.fixture
def opened(boundaries: Boundaries, human: HumanClone) -> None:
    """Start the story on `main` and push its branch with a document in stage `tests`."""
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    document = WorkItemDocument(state=WorkItemState(stage="tests", journal=[CREATED]), body=BODY)
    human.push_file(BRANCH, PATH, boundaries.work_item_writer.render(document))
    boundaries.git.fetch()


@pytest.mark.usefixtures("opened")
def test_a_claim_of_a_document_without_a_state_is_refused_and_pushes_nothing(
    boundaries: Boundaries, remote: Path
) -> None:
    boundaries.git.checkout(BRANCH, start_point=f"origin/{BRANCH}")
    before = _branch_head(remote)
    service = ClaimService(boundaries, INSTANCE, pipeline_definition(boundaries))

    with pytest.raises(ValueError) as raised:
        service.claim(BRANCH, PATH, STATELESS, "tests")

    assert str(raised.value) == "the work item has no state to claim"
    assert _branch_head(remote) == before


@pytest.mark.parametrize(
    "state",
    [None, WorkItemState(stage="intake", journal=[CREATED], claim=CLAIM)],
    ids=["no-state", "claimed"],
)
def test_a_release_refuses_a_document_without_a_state_and_clears_a_claim(
    boundaries: Boundaries, state: WorkItemState | None
) -> None:
    service = ClaimService(boundaries, INSTANCE, pipeline_definition(boundaries))
    document = WorkItemDocument(state=state, body=BODY)

    if state is None:
        with pytest.raises(ValueError) as raised:
            service.release(document)
        assert str(raised.value) == "the work item has no state to release"
    else:
        released = service.release(document)
        assert released.state is not None
        assert released.state.claim is None


def test_asking_the_crash_cap_question_of_a_document_without_a_state_is_refused_and_posts_nothing(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    definition = pipeline_definition(boundaries)
    claims = ClaimService(boundaries, INSTANCE, definition)
    recovery = RecoveryHandler(boundaries, definition, claims, Rerun())
    snapshot = WorkItemSnapshot(
        id=WORK_ITEM,
        path=PATH,
        folder="in-progress",
        branch=BRANCH,
        branch_commit="a" * 40,
        document=STATELESS,
    )

    with pytest.raises(CannotHandle) as raised:
        recovery.ask_crash_cap(snapshot)

    assert raised.value.kind == "crash"
    assert raised.value.reason == f"work item {snapshot.id} has no state"
    assert hosting.pull_requests() == []


def test_composing_a_task_for_a_document_without_a_state_is_refused_with_its_path(
    boundaries: Boundaries, tmp_path: Path
) -> None:
    composer = TaskComposer(boundaries, pipeline_definition(boundaries), {"PATH": "/usr/bin"})
    context = TaskContext(
        work_item=WORK_ITEM,
        path=PATH,
        stage="tests",
        document=STATELESS,
        branch=BRANCH,
        pull_request=7,
        findings=[],
        guard=GuardSettings(
            root=tmp_path / CHECKOUT, write_paths=["tests/*"], protected_paths=["factory/*"]
        ),
    )
    agent = AgentDefinition(
        name="tester", model="sonnet", tools=["Read"], budget_usd=1, instructions="Do the work."
    )

    with pytest.raises(WorkItemFormatError) as raised:
        composer.compose(context, agent)

    assert raised.value.fault == "the document has no state"
    assert raised.value.path == context.path


@pytest.mark.usefixtures("opened")
def test_a_stall_of_a_document_without_a_state_is_refused_and_pushes_and_posts_nothing(
    boundaries: Boundaries, remote: Path, hosting: FakeHostingService
) -> None:
    pull_request = hosting.create_pull_request(BRANCH, "First story", "body", draft=True)
    before = _branch_head(remote)
    context = StallContext(
        work_item=WORK_ITEM,
        stage="tests",
        branch=BRANCH,
        path=PATH,
        stage_start=None,
        document=STATELESS,
        pull_request=pull_request,
        cost=None,
    )
    service = StallService(boundaries, INSTANCE, pipeline_definition(boundaries))

    with pytest.raises(ValueError) as raised:
        service.stall(context, "died")

    assert str(raised.value) == "the work item has no state to stall"
    assert _branch_head(remote) == before
    assert hosting.factory_posts(pull_request.number) == []
