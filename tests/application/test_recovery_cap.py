"""A crash at the crash cap is not rerun: the question is recorded, pushed, then posted."""

from pathlib import Path

import pytest

from crash_support import (
    BRANCH,
    PATH,
    STAGE,
    STORY,
    STORY_TITLE,
    WORK_ITEM,
    Rerun,
    claim,
    crash_event,
    document_at,
    handler,
    open_pull_request,
    remote_head,
    remote_state,
    snapshot,
)
from factory.adapters.clock import ManualClock
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService
from factory.application.dispatcher import Handler
from factory.domain.errors import CannotHandle, HostingServiceError
from factory.domain.events import Event
from factory.domain.hosting import PostKey
from factory.domain.journal import (
    FACTORY,
    JournalRecord,
    NewEntry,
    append_entry,
    entry_text,
    last_record,
)
from factory.domain.post_texts import crash_cap_question
from factory.domain.work_item import Blocked, WorkItemSnapshot, WorkItemState
from git_support import PIPELINE_YAML, remote_commit
from human_clone import HumanClone
from stage_run_support import INSTANCE

CAP = 2


def _state_of(work_item: WorkItemSnapshot) -> WorkItemState:
    state = work_item.document.state
    assert state is not None
    return state


def _question(boundaries: Boundaries) -> JournalRecord:
    question = last_record(
        document_at(boundaries, f"origin/{BRANCH}"), speaker=FACTORY, kind="question"
    )
    assert question is not None
    return question


class _ClaimsAndFails(Handler):
    """Claims the stage again on the event's work item, then fails at the hosting service."""

    def __init__(self, claims: ClaimService) -> None:
        self.events: list[Event] = []
        self._claims = claims

    def handle(self, event: Event) -> None:
        self.events.append(event)
        work_item = event.work_item
        assert work_item is not None
        self._claims.claim(work_item.branch, work_item.path, work_item.document, STAGE)
        raise HostingServiceError("post_comment", "injected failure")


@pytest.mark.parametrize(
    ("crashes", "cap", "asks"),
    [(0, 1, True), (0, 2, False), (1, 2, True), (1, 3, False), (2, 3, True)],
)
def test_the_handler_asks_exactly_when_the_crash_reaches_the_cap(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    hosting: FakeHostingService,
    crashes: int,
    cap: int,
    asks: bool,
) -> None:
    claimed = claim(boundaries, human, crashes=crashes, pull_request=open_pull_request(hosting))
    definition = claimed.definition.model_copy(update={"crash_cap": cap})
    rerun = Rerun()

    handler(boundaries, definition, rerun).handle(crash_event(snapshot(boundaries)))

    after = remote_state(boundaries)
    assert after.crashes == crashes + 1
    if asks:
        assert rerun.events == []
        assert after.blocked == "crash_cap"
    else:
        assert len(rerun.events) == 1
        assert after.blocked is None


def test_at_the_cap_the_stage_is_not_rerun_and_the_crash_commit_is_the_remote_head(
    boundaries: Boundaries, *, human: HumanClone, hosting: FakeHostingService
) -> None:
    claimed = claim(boundaries, human, pull_request=open_pull_request(hosting))
    rerun = Rerun()

    handler(boundaries, claimed.definition, rerun).handle(crash_event(snapshot(boundaries)))

    assert rerun.events == []
    head = remote_head(boundaries)
    [crash_commit] = boundaries.git.log(f"origin/{BRANCH}", since=claimed.start.commit)
    assert crash_commit.commit == head
    after = remote_state(boundaries)
    assert [record.kind for record in after.journal].count("started") == 1


def test_at_the_cap_the_work_item_is_blocked_with_the_crashes_counted_and_no_claim(
    boundaries: Boundaries, *, human: HumanClone, hosting: FakeHostingService
) -> None:
    claimed = claim(boundaries, human, attempts=1, pull_request=open_pull_request(hosting))

    handler(boundaries, claimed.definition, Rerun()).handle(crash_event(snapshot(boundaries)))

    after = remote_state(boundaries)
    assert after.blocked == "crash_cap"
    assert after.crashes == CAP
    assert after.attempts == 1
    assert after.claim is None


def test_the_crash_commit_at_the_cap_holds_the_crash_and_the_question_and_nothing_else(
    boundaries: Boundaries, *, human: HumanClone, hosting: FakeHostingService, clock: ManualClock
) -> None:
    claimed = claim(boundaries, human, pull_request=open_pull_request(hosting))
    before = _state_of(snapshot(boundaries))

    handler(boundaries, claimed.definition, Rerun()).handle(crash_event(snapshot(boundaries)))

    after = remote_state(boundaries)
    last = before.journal[-1].number
    assert after.journal[:-2] == before.journal
    assert after.journal[-2:] == [
        JournalRecord(
            number=last + 1, speaker=FACTORY, kind="crash", at=clock.now(), stage=before.stage
        ),
        JournalRecord(
            number=last + 2,
            speaker=FACTORY,
            kind="question",
            at=clock.now(),
            stage=before.stage,
            blocked="crash_cap",
        ),
    ]
    assert len(boundaries.git.log(f"origin/{BRANCH}", since=claimed.start.commit)) == 1


def test_the_question_entry_is_the_crash_cap_question(
    boundaries: Boundaries, *, human: HumanClone, hosting: FakeHostingService
) -> None:
    claimed = claim(boundaries, human, pull_request=open_pull_request(hosting))

    handler(boundaries, claimed.definition, Rerun()).handle(crash_event(snapshot(boundaries)))

    document = document_at(boundaries, f"origin/{BRANCH}")
    question = _question(boundaries)
    assert entry_text(document, question.number) == crash_cap_question(STAGE, CAP, CAP)


def test_the_question_is_posted_once_on_the_pull_request_under_its_key(
    boundaries: Boundaries, *, human: HumanClone, hosting: FakeHostingService
) -> None:
    number = open_pull_request(hosting)
    claimed = claim(boundaries, human, pull_request=number)

    handler(boundaries, claimed.definition, Rerun()).handle(crash_event(snapshot(boundaries)))

    question = _question(boundaries)
    [post] = hosting.factory_posts(number)
    assert post.key == PostKey(work_item=WORK_ITEM, kind="crash_cap", n=str(question.number))
    assert post.body.startswith(f"factory: {crash_cap_question(STAGE, CAP, CAP)}")


def test_the_question_is_recorded_and_pushed_before_it_is_posted(
    boundaries: Boundaries, *, human: HumanClone, hosting: FakeHostingService
) -> None:
    number = open_pull_request(hosting)
    claimed = claim(boundaries, human, pull_request=number)
    hosting.fail_next("post_comment")

    with pytest.raises(HostingServiceError):
        handler(boundaries, claimed.definition, Rerun()).handle(crash_event(snapshot(boundaries)))

    assert remote_state(boundaries).blocked == "crash_cap"
    _question(boundaries)
    assert hosting.factory_posts(number) == []
    handler(boundaries, claimed.definition, Rerun()).ask_crash_cap(snapshot(boundaries))
    assert len(hosting.factory_posts(number)) == 1


def test_asking_again_posts_nothing(
    boundaries: Boundaries, *, human: HumanClone, hosting: FakeHostingService
) -> None:
    number = open_pull_request(hosting)
    claimed = claim(boundaries, human, pull_request=number)
    recovery = handler(boundaries, claimed.definition, Rerun())
    recovery.handle(crash_event(snapshot(boundaries)))

    again = recovery.ask_crash_cap(snapshot(boundaries))

    assert again.outcome == "already_posted"
    assert len(hosting.factory_posts(number)) == 1


@pytest.mark.parametrize(
    ("body", "title"),
    [
        (STORY, f"{WORK_ITEM}: {STORY_TITLE}"),
        ("A story without a title.\n\n## Journal\n\n", WORK_ITEM),
    ],
    ids=["titled", "untitled"],
)
def test_at_the_cap_without_a_pull_request_a_draft_is_opened_and_its_number_recorded(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    hosting: FakeHostingService,
    body: str,
    title: str,
) -> None:
    claimed = claim(boundaries, human, body=body)

    handler(boundaries, claimed.definition, Rerun()).handle(crash_event(snapshot(boundaries)))

    [pull_request] = hosting.pull_requests()
    assert pull_request.branch == BRANCH
    assert pull_request.draft
    assert pull_request.title == title
    assert len(hosting.factory_posts(pull_request.number)) == 1
    assert remote_state(boundaries).pull_request == pull_request.number
    assert len(boundaries.git.log(f"origin/{BRANCH}", since=claimed.start.commit)) == 2


def _asking_without_pull_request(boundaries: Boundaries, human: HumanClone) -> WorkItemSnapshot:
    """Push a work item blocked on the crash cap with its question recorded, without a PR."""
    claimed = claim(boundaries, human, crashes=CAP)
    document = ClaimService(boundaries, INSTANCE, claimed.definition).release(
        snapshot(boundaries).document
    )
    question = NewEntry(speaker=FACTORY, kind="question", text=crash_cap_question(STAGE, CAP, CAP))
    document = append_entry(document, question)
    assert document.state is not None
    blocked = document.state.model_copy(update={"blocked": "crash_cap"})
    document = document.model_copy(update={"state": blocked})
    human.push_file(BRANCH, PATH, boundaries.work_item_writer.render(document))
    return snapshot(boundaries)


def test_asking_on_its_own_from_main_records_the_new_pull_request_on_the_branch(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    hosting: FakeHostingService,
    checkout: GitCli,
    remote: Path,
) -> None:
    work_item = _asking_without_pull_request(boundaries, human)
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    checkout.checkout("main", start_point="origin/main")
    main = remote_commit(remote, "main")

    handler(boundaries, definition, Rerun()).ask_crash_cap(work_item)

    [pull_request] = hosting.pull_requests()
    assert remote_state(boundaries).pull_request == pull_request.number
    assert len(boundaries.git.log(f"origin/{BRANCH}", since=work_item.branch_commit)) == 1
    assert remote_commit(remote, "main") == main
    assert len(hosting.factory_posts(pull_request.number)) == 1


def _with(
    work_item: WorkItemSnapshot, blocked: Blocked | None, question: NewEntry | None
) -> WorkItemSnapshot:
    document = work_item.document
    if question is not None:
        document = append_entry(document, question)
    assert document.state is not None
    state = document.state.model_copy(update={"blocked": blocked, "claim": None})
    return work_item.model_copy(update={"document": document.model_copy(update={"state": state})})


@pytest.mark.parametrize("blocked", [None, "question", "attempts_cap"])
def test_asking_for_a_work_item_not_blocked_on_the_crash_cap_is_refused(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    hosting: FakeHostingService,
    blocked: Blocked | None,
) -> None:
    number = open_pull_request(hosting)
    claimed = claim(boundaries, human, pull_request=number)
    question = NewEntry(speaker=FACTORY, kind="question", text="Try again?")
    work_item = _with(snapshot(boundaries), blocked, question)

    with pytest.raises(CannotHandle) as raised:
        handler(boundaries, claimed.definition, Rerun()).ask_crash_cap(work_item)

    assert raised.value.kind == "crash"
    assert hosting.factory_posts(number) == []


@pytest.mark.parametrize(
    "question",
    [None, NewEntry(speaker="reviewer", kind="question", text="Send it back?")],
    ids=["no-question", "question-of-a-role"],
)
def test_asking_without_a_recorded_factory_question_is_refused(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    hosting: FakeHostingService,
    question: NewEntry | None,
) -> None:
    number = open_pull_request(hosting)
    claimed = claim(boundaries, human, pull_request=number)
    work_item = _with(snapshot(boundaries), "crash_cap", question)

    with pytest.raises(CannotHandle) as raised:
        handler(boundaries, claimed.definition, Rerun()).ask_crash_cap(work_item)

    assert raised.value.kind == "crash"
    assert hosting.factory_posts(number) == []


def test_a_boundary_error_after_a_pushed_claim_repeats_into_the_crash_cap(
    boundaries: Boundaries, *, human: HumanClone, hosting: FakeHostingService
) -> None:
    number = open_pull_request(hosting)
    claimed = claim(boundaries, human, crashes=0, pull_request=number)
    run = _ClaimsAndFails(ClaimService(boundaries, INSTANCE, claimed.definition))

    with pytest.raises(HostingServiceError):
        handler(boundaries, claimed.definition, run).handle(crash_event(snapshot(boundaries)))

    first = remote_state(boundaries)
    assert len(run.events) == 1
    assert first.crashes == 1
    assert first.claim is not None
    assert first.claim.instance == INSTANCE

    handler(boundaries, claimed.definition, run).handle(crash_event(snapshot(boundaries)))

    second = remote_state(boundaries)
    assert second.crashes == CAP
    assert second.blocked == "crash_cap"
    assert second.claim is None
    [post] = hosting.factory_posts(number)
    assert post.key is not None
    assert post.key.kind == "crash_cap"
    assert len(run.events) == 1
