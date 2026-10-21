"""An expired lease of another instance is taken over as a crash: recorded, noted, then rerun."""

from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from crash_support import (
    BRANCH,
    LEASE,
    OTHER_INSTANCE,
    STAGE,
    STORY,
    STORY_TITLE,
    WORK_ITEM,
    Rerun,
    claim,
    document_at,
    expired_claim,
    expired_event,
    open_pull_request,
    other_handler,
    remote_head,
    remote_state,
    snapshot,
)
from factory.adapters.clock import ManualClock
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService
from factory.application.recovery import RecoveryHandler
from factory.domain.errors import CannotHandle, HostingServiceError
from factory.domain.hosting import PostKey
from factory.domain.journal import FACTORY, JournalRecord, entry_text, last_record
from factory.domain.post_texts import crash_cap_question, expiry_note
from factory.domain.recovery import expiry_entry_text
from factory.domain.work_item import WorkItemSnapshot
from git_support import remote_commit, write_files
from human_clone import HumanClone
from stage_run_support import INSTANCE

CAP = 2
UNTRACKED = "src/dead.py"
COMMITTED = "src/committed.py"


def _expiry(boundaries: Boundaries) -> JournalRecord:
    record = last_record(document_at(boundaries, f"origin/{BRANCH}"), kind="expiry")
    assert record is not None
    return record


@pytest.mark.parametrize(
    ("age", "handled"),
    [(timedelta(minutes=59, seconds=59), False), (LEASE, True)],
    ids=["59:59", "60:00"],
)
def test_an_expired_event_is_handled_only_once_the_lease_has_run_out(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    clock: ManualClock,
    hosting: FakeHostingService,
    remote: Path,
    age: timedelta,
    handled: bool,
) -> None:
    claimed = claim(boundaries, human, crashes=0, pull_request=open_pull_request(hosting))
    clock.advance(age)
    rerun = Rerun()
    recovery = other_handler(boundaries, claimed, rerun)
    event = expired_event(snapshot(boundaries))

    if not handled:
        with pytest.raises(CannotHandle) as raised:
            recovery.handle(event)
        assert raised.value.kind == "expired"
        assert remote_commit(remote, BRANCH) == claimed.start.commit
        assert rerun.events == []
        return

    recovery.handle(event)

    assert remote_state(boundaries).crashes == 1
    assert len(rerun.events) == 1


def _without_claim(work_item: WorkItemSnapshot) -> WorkItemSnapshot:
    state = work_item.document.state
    assert state is not None
    document = work_item.document.model_copy(
        update={"state": state.model_copy(update={"claim": None})}
    )
    return work_item.model_copy(update={"document": document})


def _unchanged(work_item: WorkItemSnapshot) -> WorkItemSnapshot:
    return work_item


@pytest.mark.parametrize(
    ("instance", "minutes", "change"),
    [
        (INSTANCE, 0, _unchanged),
        (INSTANCE, 60, _unchanged),
        (OTHER_INSTANCE, 60, _without_claim),
    ],
    ids=["own", "own-after-the-lease", "no-claim"],
)
def test_an_expired_event_on_an_own_claim_or_no_claim_is_refused_and_pushes_nothing(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    clock: ManualClock,
    hosting: FakeHostingService,
    remote: Path,
    instance: str,
    minutes: int,
    change: Callable[[WorkItemSnapshot], WorkItemSnapshot],
) -> None:
    number = open_pull_request(hosting)
    claimed = claim(boundaries, human, crashes=0, pull_request=number)
    clock.advance(timedelta(minutes=minutes))
    rerun = Rerun()
    claims = ClaimService(boundaries, instance, claimed.definition)
    recovery = RecoveryHandler(boundaries, claimed.definition, claims, rerun)

    with pytest.raises(CannotHandle) as raised:
        recovery.handle(expired_event(change(snapshot(boundaries))))

    assert raised.value.kind == "expired"
    assert remote_commit(remote, BRANCH) == claimed.start.commit
    assert rerun.events == []
    assert hosting.factory_posts(number) == []


def test_an_expiry_counts_one_crash_clears_the_claim_and_charges_no_attempt(
    boundaries: Boundaries, *, human: HumanClone, clock: ManualClock, hosting: FakeHostingService
) -> None:
    claimed = expired_claim(boundaries, human, clock, pull_request=open_pull_request(hosting))
    work_item = snapshot(boundaries)
    before = work_item.document.state
    assert before is not None

    other_handler(boundaries, claimed, Rerun()).handle(expired_event(work_item))

    after = remote_state(boundaries)
    assert after.crashes == before.crashes + 1
    assert after.attempts == before.attempts
    assert after.claim is None
    unchanged = {"stage", "blocked", "round", "pull_request", "comments_read", "handed_over"}
    assert after.model_dump(include=unchanged) == before.model_dump(include=unchanged)


def test_the_journal_ends_with_a_factory_expiry_entry_naming_the_stage_start(
    boundaries: Boundaries, *, human: HumanClone, clock: ManualClock, hosting: FakeHostingService
) -> None:
    claimed = expired_claim(boundaries, human, clock, pull_request=open_pull_request(hosting))
    work_item = snapshot(boundaries)
    before = work_item.document.state
    assert before is not None

    other_handler(boundaries, claimed, Rerun()).handle(expired_event(work_item))

    after = remote_state(boundaries)
    assert after.journal[-1] == JournalRecord(
        number=before.journal[-1].number + 1,
        speaker=FACTORY,
        kind="expiry",
        at=clock.now(),
        stage=before.stage,
    )
    document = document_at(boundaries, f"origin/{BRANCH}")
    assert entry_text(document, after.journal[-1].number) == expiry_entry_text(
        STAGE, 1, claimed.start.commit
    )


def test_the_checkout_is_discarded_before_the_expiry_is_recorded(
    boundaries: Boundaries, *, human: HumanClone, clock: ManualClock, hosting: FakeHostingService
) -> None:
    claimed = expired_claim(boundaries, human, clock, pull_request=open_pull_request(hosting))
    write_files(boundaries.checkout, {COMMITTED: "y = 2\n"})
    boundaries.git.commit("work never pushed")
    write_files(boundaries.checkout, {UNTRACKED: "x = 1\n"})
    work_item = snapshot(boundaries)

    other_handler(boundaries, claimed, Rerun()).handle(expired_event(work_item))

    git = boundaries.git
    assert git.status().changes == []
    assert not (boundaries.checkout / UNTRACKED).exists()
    assert not (boundaries.checkout / COMMITTED).exists()
    assert git.show_file(f"origin/{BRANCH}", COMMITTED) is None
    assert git.resolve(BRANCH) == git.resolve(f"origin/{BRANCH}")


def test_the_expiry_note_is_posted_once_under_the_expiry_entrys_key(
    boundaries: Boundaries, *, human: HumanClone, clock: ManualClock, hosting: FakeHostingService
) -> None:
    number = open_pull_request(hosting)
    claimed = expired_claim(boundaries, human, clock, pull_request=number)

    other_handler(boundaries, claimed, Rerun()).handle(expired_event(snapshot(boundaries)))

    expiry = _expiry(boundaries)
    [post] = hosting.factory_posts(number)
    assert post.key == PostKey(work_item=WORK_ITEM, kind="expiry", n=str(expiry.number))
    assert post.body.startswith(expiry_note(1, CAP))


def test_below_the_cap_the_handling_instance_reruns_the_stage_once(
    boundaries: Boundaries, *, human: HumanClone, clock: ManualClock, hosting: FakeHostingService
) -> None:
    claimed = expired_claim(boundaries, human, clock, pull_request=open_pull_request(hosting))
    rerun = Rerun()

    other_handler(boundaries, claimed, rerun).handle(expired_event(snapshot(boundaries)))

    [event] = rerun.events
    assert event.kind == "run"
    assert event.work_item is not None
    assert event.work_item.branch_commit == remote_head(boundaries)
    state = event.work_item.document.state
    assert state is not None
    assert state.crashes == 1
    assert state.claim is None


def test_at_the_cap_the_note_and_then_the_question_are_posted_and_nothing_reruns(
    boundaries: Boundaries, *, human: HumanClone, clock: ManualClock, hosting: FakeHostingService
) -> None:
    number = open_pull_request(hosting)
    claimed = expired_claim(boundaries, human, clock, crashes=1, pull_request=number)
    before = snapshot(boundaries).document.state
    assert before is not None
    rerun = Rerun()

    other_handler(boundaries, claimed, rerun).handle(expired_event(snapshot(boundaries)))

    assert rerun.events == []
    after = remote_state(boundaries)
    assert after.blocked == "crash_cap"
    assert after.crashes == CAP
    last = before.journal[-1].number
    assert after.journal[-2:] == [
        JournalRecord(
            number=last + 1, speaker=FACTORY, kind="expiry", at=clock.now(), stage=before.stage
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
    note, question = hosting.factory_posts(number)
    assert note.key is not None
    assert note.key.kind == "expiry"
    assert note.body.startswith(expiry_note(CAP, CAP))
    assert "retrying" not in note.body.lower()
    assert question.key is not None
    assert question.key.kind == "crash_cap"
    assert question.body.startswith(f"factory: {crash_cap_question(STAGE, CAP, CAP)}")


def test_a_failed_note_raises_after_the_expiry_is_pushed_and_nothing_reruns(
    boundaries: Boundaries, *, human: HumanClone, clock: ManualClock, hosting: FakeHostingService
) -> None:
    claimed = expired_claim(boundaries, human, clock, pull_request=open_pull_request(hosting))
    hosting.fail_next("post_comment")
    rerun = Rerun()

    with pytest.raises(HostingServiceError):
        other_handler(boundaries, claimed, rerun).handle(expired_event(snapshot(boundaries)))

    after = remote_state(boundaries)
    assert after.crashes == 1
    assert after.claim is None
    assert rerun.events == []


@pytest.mark.parametrize(
    ("body", "title"),
    [
        (STORY, f"{WORK_ITEM}: {STORY_TITLE}"),
        ("A story without a title.\n\n## Journal\n\n", WORK_ITEM),
    ],
    ids=["titled", "untitled"],
)
def test_without_a_pull_request_the_note_opens_a_draft_whose_number_is_recorded_and_rerun(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    clock: ManualClock,
    hosting: FakeHostingService,
    body: str,
    title: str,
) -> None:
    claimed = expired_claim(boundaries, human, clock, body=body)
    rerun = Rerun()

    other_handler(boundaries, claimed, rerun).handle(expired_event(snapshot(boundaries)))

    [pull_request] = hosting.pull_requests()
    assert pull_request.branch == BRANCH
    assert pull_request.draft
    assert pull_request.title == title
    [post] = hosting.factory_posts(pull_request.number)
    assert post.key is not None
    assert post.key.kind == "expiry"
    assert remote_state(boundaries).pull_request == pull_request.number
    [event] = rerun.events
    assert event.work_item is not None
    state = event.work_item.document.state
    assert state is not None
    assert state.pull_request == pull_request.number


def test_at_the_cap_without_a_pull_request_both_posts_land_on_one_new_draft(
    boundaries: Boundaries, *, human: HumanClone, clock: ManualClock, hosting: FakeHostingService
) -> None:
    claimed = expired_claim(boundaries, human, clock, crashes=1)
    before = len(hosting.pull_requests())

    other_handler(boundaries, claimed, Rerun()).handle(expired_event(snapshot(boundaries)))

    pull_requests = hosting.pull_requests()
    assert len(pull_requests) == before + 1
    pull_request = pull_requests[-1]
    assert pull_request.draft
    assert remote_state(boundaries).pull_request == pull_request.number
    commits = boundaries.git.log(f"origin/{BRANCH}", since=claimed.start.commit)
    assert len(commits) == 2
    note, question = hosting.factory_posts(pull_request.number)
    assert note.key is not None
    assert note.key.kind == "expiry"
    assert question.key is not None
    assert question.key.kind == "crash_cap"
