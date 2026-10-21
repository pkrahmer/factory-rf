"""The stage-start commit carries the claim and its "started" entry, and its push is the claim."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from factory.adapters.clock import ManualClock
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService, StageStart, started_text
from factory.application.handlers.recording import commit_subject
from factory.domain.errors import PushFailed
from factory.domain.git import GitOptions, WorkTreeStatus
from factory.domain.identifiers import branch_name
from factory.domain.journal import JournalRecord
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import Claim, WorkItemDocument, WorkItemState
from git_support import PIPELINE_YAML, TEST_IDENTITY, remote_commit
from human_clone import HumanClone
from stage_run_support import INSTANCE
from work_item_support import CREATED, checkout_text, created_state, put_work_item

STAGE = "intake"
WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
OTHER_BRANCH = branch_name("F0001-S0002")
NOTES = "factory/features/F0001-example/in-progress/notes.md"
PIPELINE_FILE = "factory/pipeline.yml"
BEFORE_JOURNAL = "# First story\n\n## Description\n\nOriginal.\n\n"
BODY = BEFORE_JOURNAL + "## Journal\n\n1. 2026-10-12 human: created.\n"
LEASE_45_YAML = PIPELINE_YAML.replace(
    'intake: {write_paths: ["{work_item}"]}',
    'intake: {write_paths: ["{work_item}"], lease_duration: 45}',
)
LEASE_5_YAML = PIPELINE_YAML.replace(
    'intake: {write_paths: ["{work_item}"]}',
    'intake: {write_paths: ["{work_item}"], lease_duration: 5, time_limit: 5}',
)
OTHER_INSTANCE = "factory-2"


def _state(stage: str = STAGE) -> WorkItemState:
    return created_state(stage)


def _definition(boundaries: Boundaries, text: str = PIPELINE_YAML) -> PipelineDefinition:
    return boundaries.pipeline_reader.parse(text)


def _prepare(
    boundaries: Boundaries,
    *,
    state: WorkItemState | None = None,
    committed: bool = True,
) -> WorkItemDocument:
    """Put the work item on its branch, created from `origin/main`, and return its document."""
    document = WorkItemDocument(state=_state() if state is None else state, body=BODY)
    put_work_item(boundaries, BRANCH, PATH, document, committed=committed)
    return document


def _claim(
    boundaries: Boundaries, document: WorkItemDocument, definition: PipelineDefinition | None = None
) -> StageStart:
    service = ClaimService(boundaries, INSTANCE, definition or _definition(boundaries))
    return service.claim(BRANCH, PATH, document, STAGE)


def _second_clone(tmp_path: Path, remote: Path) -> GitCli:
    git = GitCli(tmp_path / "second", GitOptions(identity=TEST_IDENTITY))
    git.clone(str(remote))
    return git


def _pushed_document(boundaries: Boundaries, git: GitCli, commit: str) -> WorkItemDocument:
    text = git.show_file(commit, PATH)
    assert text is not None
    return boundaries.work_item_reader.parse(text)


def _snapshot(
    boundaries: Boundaries, remote: Path, branch: str, path: str
) -> tuple[WorkTreeStatus, str | None, str | None]:
    return boundaries.git.status(), checkout_text(boundaries, path), remote_commit(remote, branch)


def test_claim_records_instance_stage_and_start_time_in_utc(
    boundaries: Boundaries, clock: ManualClock
) -> None:
    document = _prepare(boundaries)

    start = _claim(boundaries, document)

    assert start.claim.instance == INSTANCE
    assert start.claim.stage == STAGE
    assert start.claim.started_at == clock.now()
    assert start.claim.started_at.utcoffset() == timedelta(0)


@pytest.mark.parametrize(
    ("pipeline", "lease"),
    [(None, 60), (LEASE_45_YAML, 45)],
    ids=["role-default", "role-sets-45"],
)
def test_claim_copies_the_lease_duration_of_the_stages_role(
    boundaries: Boundaries, human: HumanClone, pipeline: str | None, lease: int
) -> None:
    definition = None
    if pipeline is not None:
        human.push_file("main", PIPELINE_FILE, pipeline)
        definition = _definition(boundaries, pipeline)
    document = _prepare(boundaries)

    start = _claim(boundaries, document, definition)

    assert start.claim.lease_duration == lease


def test_stage_start_commit_is_pushed_to_the_remote(
    boundaries: Boundaries, tmp_path: Path, remote: Path
) -> None:
    document = _prepare(boundaries)

    start = _claim(boundaries, document)

    assert boundaries.git.resolve(f"origin/{BRANCH}") == start.commit
    assert boundaries.git.status().head == start.commit
    assert _second_clone(tmp_path, remote).resolve(f"origin/{BRANCH}") == start.commit


def test_stage_start_commit_is_one_commit_on_the_previous_head_with_its_subject(
    boundaries: Boundaries,
) -> None:
    document = _prepare(boundaries)
    previous = boundaries.git.status().head

    start = _claim(boundaries, document)

    newest = boundaries.git.log(start.commit)[0]
    assert newest.commit == start.commit
    assert newest.parents == [previous]
    assert newest.subject == commit_subject(WORK_ITEM, f"{STAGE} starts as {INSTANCE}")


def test_pushed_work_item_holds_the_returned_claim(
    boundaries: Boundaries, tmp_path: Path, remote: Path
) -> None:
    document = _prepare(boundaries)

    start = _claim(boundaries, document)

    pushed = _pushed_document(boundaries, _second_clone(tmp_path, remote), start.commit)
    assert pushed.state is not None
    assert pushed.state.claim == start.claim


def test_claim_appends_one_started_journal_entry(
    boundaries: Boundaries, tmp_path: Path, remote: Path, clock: ManualClock
) -> None:
    document = _prepare(boundaries)

    start = _claim(boundaries, document)

    pushed = _pushed_document(boundaries, _second_clone(tmp_path, remote), start.commit)
    assert pushed.state is not None
    assert pushed.state.journal == [
        CREATED,
        JournalRecord(number=2, speaker="factory", kind="started", at=clock.now(), stage=STAGE),
    ]
    assert started_text(STAGE, INSTANCE) == f"started {STAGE} as {INSTANCE}."
    assert pushed.body.rstrip("\n").splitlines()[-1] == (
        f"2. factory: started {STAGE} as {INSTANCE}."
    )


def test_claim_keeps_every_other_state_field_and_the_body_outside_the_journal(
    boundaries: Boundaries, tmp_path: Path, remote: Path
) -> None:
    given = _state().model_copy(
        update={
            "round": 1,
            "attempts": 1,
            "crashes": 1,
            "pull_request": 48,
            "comments_read": [3, 5],
            "handed_over": "tester",
        }
    )
    document = _prepare(boundaries, state=given)

    start = _claim(boundaries, document)

    pushed = _pushed_document(boundaries, _second_clone(tmp_path, remote), start.commit)
    assert pushed.state is not None
    assert pushed.state.model_copy(update={"claim": None, "journal": given.journal}) == given
    assert pushed.body.startswith(BEFORE_JOURNAL + "## Journal\n")


def test_a_document_with_a_claim_is_claimed_anew(
    boundaries: Boundaries, clock: ManualClock
) -> None:
    old = Claim(
        instance="factory-2",
        stage=STAGE,
        started_at=datetime(2026, 10, 12, 9, 0, tzinfo=UTC),
        lease_duration=60,
    )
    _prepare(boundaries, state=_state().model_copy(update={"claim": old}))
    first = _claim(boundaries, boundaries.work_item_reader.read(boundaries.checkout / PATH))
    clock.advance(timedelta(minutes=90))

    second = _claim(boundaries, boundaries.work_item_reader.read(boundaries.checkout / PATH))

    assert first.claim != old
    assert second.claim.started_at == clock.now()
    pushed = _pushed_document(boundaries, GitCli(boundaries.checkout), second.commit)
    assert pushed.state is not None
    assert pushed.state.claim == second.claim
    assert [record.kind for record in pushed.state.journal] == ["created", "started", "started"]


def test_a_rejected_push_raises_push_failed_and_leaves_the_remote_without_claim(
    boundaries: Boundaries, human: HumanClone, remote: Path
) -> None:
    document = _prepare(boundaries)
    previous = boundaries.git.status().head
    human.push_file(BRANCH, "notes.txt", "the human was here\n")
    remote_head = remote_commit(remote, BRANCH)

    with pytest.raises(PushFailed) as caught:
        _claim(boundaries, document)

    assert caught.value.branch == BRANCH
    assert caught.value.outcome == "rejected"
    assert BRANCH in str(caught.value)
    assert "rejected" in str(caught.value)
    assert remote_commit(remote, BRANCH) == remote_head
    local = boundaries.git.log(BRANCH)[0]
    assert local.parents == [previous]
    assert local.subject == commit_subject(WORK_ITEM, f"{STAGE} starts as {INSTANCE}")


def test_an_unreachable_remote_raises_push_failed(
    boundaries: Boundaries, tmp_path: Path, remote: Path
) -> None:
    document = _prepare(boundaries)
    remote.rename(tmp_path / "moved.git")

    with pytest.raises(PushFailed) as caught:
        _claim(boundaries, document)

    assert caught.value.branch == BRANCH
    assert caught.value.outcome == "unreachable"


def test_a_kill_before_push_is_not_caught_and_leaves_the_remote_without_claim(
    boundaries: Boundaries, remote: Path, kill_points: KillPoints
) -> None:
    document = _prepare(boundaries)
    previous = boundaries.git.status().head
    kill_points.arm(KillPoint.BEFORE_PUSH)

    with pytest.raises(InjectedKill):
        _claim(boundaries, document)

    assert remote_commit(remote, BRANCH) == previous
    local = boundaries.git.log(BRANCH)[0]
    assert local.parents == [previous]
    assert local.subject == commit_subject(WORK_ITEM, f"{STAGE} starts as {INSTANCE}")


@pytest.mark.parametrize(
    ("document_stage", "stage"),
    [(None, STAGE), (STAGE, "tests"), ("approval", "approval"), ("nowhere", "nowhere")],
    ids=["no-state", "other-stage", "stage-without-role", "unknown-stage"],
)
def test_claim_refuses_a_document_or_stage_it_cannot_claim_and_writes_nothing(
    boundaries: Boundaries, remote: Path, document_stage: str | None, stage: str
) -> None:
    _prepare(boundaries)
    state = None if document_stage is None else _state(document_stage)
    document = WorkItemDocument(state=state, body=BODY)
    before = _snapshot(boundaries, remote, BRANCH, PATH)
    service = ClaimService(boundaries, INSTANCE, _definition(boundaries))

    with pytest.raises(ValueError, match=r".+"):
        service.claim(BRANCH, PATH, document, stage)

    assert _snapshot(boundaries, remote, BRANCH, PATH) == before


def test_claim_refuses_when_another_branch_is_checked_out_and_writes_nothing(
    boundaries: Boundaries, remote: Path
) -> None:
    document = _prepare(boundaries)
    boundaries.git.checkout("main", start_point="origin/main")
    before = _snapshot(boundaries, remote, BRANCH, PATH)

    with pytest.raises(ValueError, match=r".+"):
        _claim(boundaries, document)

    assert _snapshot(boundaries, remote, BRANCH, PATH) == before


@pytest.mark.parametrize(
    "name",
    ["Factory-1", "1factory", "factory_1", ""],
    ids=["upper", "digit", "underscore", "empty"],
)
def test_service_refuses_an_instance_name_that_is_no_name(
    boundaries: Boundaries, name: str
) -> None:
    with pytest.raises(ValueError, match=r".*"):
        ClaimService(boundaries, name, _definition(boundaries))


@pytest.mark.parametrize("name", ["factory-1", "f"])
def test_service_accepts_an_instance_name(boundaries: Boundaries, name: str) -> None:
    ClaimService(boundaries, name, _definition(boundaries))


def test_claim_refuses_a_branch_that_is_not_the_work_items_own_and_writes_nothing(
    boundaries: Boundaries, remote: Path
) -> None:
    document = _prepare(boundaries)
    boundaries.git.checkout(OTHER_BRANCH, start_point=BRANCH)
    before = _snapshot(boundaries, remote, OTHER_BRANCH, PATH)
    service = ClaimService(boundaries, INSTANCE, _definition(boundaries))

    with pytest.raises(ValueError, match=r".+"):
        service.claim(OTHER_BRANCH, PATH, document, STAGE)

    assert _snapshot(boundaries, remote, OTHER_BRANCH, PATH) == before


def test_claim_refuses_a_path_whose_file_name_is_no_work_items_and_writes_nothing(
    boundaries: Boundaries, remote: Path
) -> None:
    document = _prepare(boundaries)
    before = _snapshot(boundaries, remote, BRANCH, NOTES)
    service = ClaimService(boundaries, INSTANCE, _definition(boundaries))

    with pytest.raises(ValueError, match=r".+"):
        service.claim(BRANCH, NOTES, document, STAGE)

    assert _snapshot(boundaries, remote, BRANCH, NOTES) == before
    assert checkout_text(boundaries, NOTES) is None


def test_claim_on_a_new_branch_commits_the_uncommitted_opening_on_main(
    boundaries: Boundaries, remote: Path
) -> None:
    document = _prepare(boundaries, committed=False)
    main = boundaries.git.resolve("origin/main")
    assert remote_commit(remote, BRANCH) is None

    start = _claim(boundaries, document)

    assert boundaries.git.log(start.commit)[0].parents == [main]
    pushed = _pushed_document(boundaries, GitCli(boundaries.checkout), start.commit)
    assert pushed.state is not None
    assert pushed.state.claim == start.claim
    assert boundaries.git.resolve(f"origin/{BRANCH}") == start.commit


@pytest.mark.parametrize(
    ("commit", "accepted"),
    [("a" * 40, True), ("a" * 39, False), ("A" * 40, False)],
    ids=["forty-lowercase", "thirty-nine", "uppercase"],
)
def test_stage_start_commit_is_a_commit_id(clock: ManualClock, commit: str, accepted: bool) -> None:
    claim = Claim(instance=INSTANCE, stage=STAGE, started_at=clock.now(), lease_duration=60)

    if accepted:
        assert StageStart(commit=commit, claim=claim).commit == commit
    else:
        with pytest.raises(ValidationError):
            StageStart(commit=commit, claim=claim)


def _service(boundaries: Boundaries, text: str = PIPELINE_YAML) -> ClaimService:
    return ClaimService(boundaries, INSTANCE, _definition(boundaries, text))


def _claimed_state(instance: str, started_at: datetime, lease_duration: int = 60) -> WorkItemState:
    claim = Claim(
        instance=instance, stage=STAGE, started_at=started_at, lease_duration=lease_duration
    )
    return _state().model_copy(update={"claim": claim})


def test_status_follows_the_boundaries_clock(boundaries: Boundaries, clock: ManualClock) -> None:
    service = _service(boundaries)
    own = _claimed_state(INSTANCE, clock.now())
    other = _claimed_state(OTHER_INSTANCE, clock.now())

    assert service.status(_state()) == "none"
    assert service.status(own) == "own"
    clock.advance(timedelta(minutes=59))
    assert service.status(other) == "held"
    clock.advance(timedelta(minutes=1))
    assert service.status(other) == "expired"
    assert service.status(own) == "own"


def test_status_judges_by_the_claims_own_lease_duration(
    boundaries: Boundaries, clock: ManualClock
) -> None:
    service = _service(boundaries, LEASE_5_YAML)
    state = _claimed_state(OTHER_INSTANCE, clock.now(), lease_duration=60)
    clock.advance(timedelta(minutes=30))

    assert service.status(state) == "held"


def test_release_clears_the_claim_and_keeps_everything_else(
    boundaries: Boundaries, clock: ManualClock
) -> None:
    given = _claimed_state(OTHER_INSTANCE, clock.now()).model_copy(
        update={
            "round": 1,
            "attempts": 1,
            "crashes": 1,
            "pull_request": 48,
            "comments_read": [3, 5],
            "handed_over": "tester",
        }
    )
    document = WorkItemDocument(state=given, body=BODY)

    released = _service(boundaries).release(document)

    assert released.state is not None
    assert released.state.claim is None
    assert released.state.journal == given.journal
    assert released.state.model_copy(update={"claim": given.claim}) == given
    assert released.body == BODY
    assert released.ignored_keys == document.ignored_keys


def test_release_of_a_document_without_a_claim_returns_an_equal_document(
    boundaries: Boundaries,
) -> None:
    document = WorkItemDocument(state=_state(), body=BODY)

    assert _service(boundaries).release(document) == document


def test_release_of_a_document_without_state_raises_value_error(boundaries: Boundaries) -> None:
    document = WorkItemDocument(state=None, body=BODY)

    with pytest.raises(ValueError, match=r".+"):
        _service(boundaries).release(document)
