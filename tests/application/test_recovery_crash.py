"""An own crash discards the dead stage's work, records the crash, pushes it and reruns at once."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from factory.adapters.clock import ManualClock
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService, StageStart
from factory.application.dispatcher import Handler
from factory.application.machine import Clock
from factory.application.recovery import RecoveryHandler
from factory.domain.cost_records import CostRecord
from factory.domain.errors import CannotHandle, GitError, PushFailed
from factory.domain.events import Event, EventKind
from factory.domain.git import ChangedPath
from factory.domain.identifiers import branch_name
from factory.domain.journal import (
    FACTORY,
    HUMAN,
    JournalRecord,
    NewEntry,
    append_entry,
    entry_text,
    last_record,
)
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.paths import cost_records_path
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.recovery import crash_entry_text
from factory.domain.work_item import (
    Claim,
    WorkItemDocument,
    WorkItemSnapshot,
    WorkItemState,
    initial_state,
)
from git_support import PIPELINE_YAML, remote_commit, write_files
from human_clone import HumanClone
from stage_run_support import INSTANCE

OTHER_INSTANCE = "factory-2"
STAGE = "doing"
WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
STORY = "# First story\n\n## Journal\n\n"
UNTRACKED = "src/dead.py"
COMMITTED = "src/committed.py"
TRACKED = "factory/story-form.md"
NOTE_PATH = "docs/note.md"
NOTE = "A note of the human.\n"
STARTED_AT = datetime(2026, 10, 12, 11, 0, tzinfo=UTC)
INTAKE_RECORD = CostRecord(
    run="a" * 32,
    work_item=WORK_ITEM,
    stage="intake",
    role="intake",
    attempt=0,
    status="completed",
    started_at=STARTED_AT,
    duration_seconds=60.0,
    end_reason="completed",
    cost_usd=Decimal("0.25"),
)
DEAD_RECORD = CostRecord(
    run="b" * 32,
    work_item=WORK_ITEM,
    stage=STAGE,
    role="coder",
    attempt=0,
    status="started",
    started_at=STARTED_AT,
)


class _Rerun(Handler):
    """Records each event it is given and the time on the clock when it was given."""

    def __init__(self, clock: Clock) -> None:
        self.events: list[Event] = []
        self.times: list[datetime] = []
        self._clock = clock

    def handle(self, event: Event) -> None:
        self.events.append(event)
        self.times.append(self._clock.now())


class _RerunFails(Exception):
    """The failure of the rerun in a test."""


class _FailingRerun(Handler):
    """Records each event it is given and raises the exception it was built with."""

    def __init__(self, error: Exception) -> None:
        self.events: list[Event] = []
        self._error = error

    def handle(self, event: Event) -> None:
        self.events.append(event)
        raise self._error


@dataclass(frozen=True)
class _Claimed:
    definition: PipelineDefinition
    claims: ClaimService
    start: StageStart


def _claim(
    boundaries: Boundaries,
    human: HumanClone,
    *,
    attempts: int = 0,
    pull_request: int | None = None,
    costs: list[CostRecord] | None = None,
) -> _Claimed:
    """Start the story, check its branch out and claim the stage as `INSTANCE`."""
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    git = boundaries.git
    git.fetch()
    git.checkout(BRANCH, start_point="origin/main")
    state = initial_state(STAGE).model_copy(
        update={"attempts": attempts, "pull_request": pull_request}
    )
    created = NewEntry(speaker=HUMAN, kind="created", text="created.", on=date(2026, 10, 12))
    document = append_entry(WorkItemDocument(state=state, body=STORY), created)
    if costs is not None:
        boundaries.cost_writer.write(boundaries.checkout / cost_records_path(PATH), costs)
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    claims = ClaimService(boundaries, INSTANCE, definition)
    start = claims.claim(BRANCH, PATH, document, STAGE)
    return _Claimed(definition=definition, claims=claims, start=start)


def _dead_run(boundaries: Boundaries) -> None:
    """Leave what a killed run leaves: a local commit never pushed, changed and untracked files."""
    write_files(boundaries.checkout, {COMMITTED: "y = 2\n"})
    boundaries.git.commit("work of the dead run")
    write_files(boundaries.checkout, {UNTRACKED: "x = 1\n"})
    with (boundaries.checkout / TRACKED).open("a", encoding="utf-8") as tracked:
        tracked.write("Changed by the dead run.\n")


def _remote_head(boundaries: Boundaries) -> str:
    head = boundaries.git.resolve(f"origin/{BRANCH}")
    assert head is not None
    return head


def _document_at(boundaries: Boundaries, ref: str) -> WorkItemDocument:
    text = boundaries.git.show_file(ref, PATH)
    assert text is not None
    return boundaries.work_item_reader.parse(text)


def _state_at(boundaries: Boundaries, ref: str) -> WorkItemState:
    state = _document_at(boundaries, ref).state
    assert state is not None
    return state


def _snapshot(boundaries: Boundaries) -> WorkItemSnapshot:
    """The work item as the remote-tracking branch shows it."""
    return WorkItemSnapshot(
        id=WORK_ITEM,
        path=PATH,
        folder="in-progress",
        branch=BRANCH,
        branch_commit=_remote_head(boundaries),
        document=_document_at(boundaries, f"origin/{BRANCH}"),
    )


def _event(snapshot: WorkItemSnapshot, kind: EventKind = "crash") -> Event:
    return Event(kind=kind, work_item=snapshot, remote_state=snapshot.branch_commit or "a" * 40)


def _handler(
    boundaries: Boundaries, definition: PipelineDefinition, run: Handler, instance: str = INSTANCE
) -> RecoveryHandler:
    """A new handler with a new claim service, as after a restart under `instance`."""
    return RecoveryHandler(
        boundaries, definition, ClaimService(boundaries, instance, definition), run
    )


def _crash(boundaries: Boundaries, human: HumanClone, clock: ManualClock) -> _Claimed:
    """Claim, leave a dead run behind and handle the crash event with a recording rerun."""
    claimed = _claim(boundaries, human)
    _dead_run(boundaries)
    snapshot = _snapshot(boundaries)
    _handler(boundaries, claimed.definition, _Rerun(clock)).handle(_event(snapshot))
    return claimed


def test_no_remote_branch_holds_a_file_the_dead_run_wrote(
    boundaries: Boundaries, human: HumanClone, clock: ManualClock
) -> None:
    _crash(boundaries, human, clock)

    git = boundaries.git
    for branch in git.remote_branches():
        for path in (UNTRACKED, COMMITTED):
            assert git.show_file(f"origin/{branch.name}", path) is None, (branch.name, path)


def test_the_checkout_holds_none_of_the_dead_runs_writes(
    boundaries: Boundaries, human: HumanClone, clock: ManualClock
) -> None:
    _crash(boundaries, human, clock)

    git = boundaries.git
    assert git.status().changes == []
    assert not (boundaries.checkout / UNTRACKED).exists()
    assert git.resolve(BRANCH) == git.resolve(f"origin/{BRANCH}")


def test_the_stage_start_commit_and_its_started_entry_stay(
    boundaries: Boundaries, human: HumanClone, clock: ManualClock
) -> None:
    claimed = _claim(boundaries, human)
    _dead_run(boundaries)
    before = _snapshot(boundaries).document
    started = last_record(before, kind="started")
    assert started is not None

    _handler(boundaries, claimed.definition, _Rerun(clock)).handle(_event(_snapshot(boundaries)))

    git = boundaries.git
    assert git.is_ancestor(claimed.start.commit, f"origin/{BRANCH}")
    after = _document_at(boundaries, f"origin/{BRANCH}")
    assert after.state is not None
    assert after.state.journal[started.number - 1] == started
    assert entry_text(after, started.number) == entry_text(before, started.number)


def test_the_crash_changes_only_the_work_item_since_the_stage_start(
    boundaries: Boundaries, human: HumanClone, clock: ManualClock
) -> None:
    claimed = _crash(boundaries, human, clock)

    assert boundaries.git.changed_paths(claimed.start.commit) == [
        ChangedPath(path=PATH, change="modified")
    ]


@pytest.mark.parametrize("attempts", [0, 1])
def test_a_crash_counts_one_crash_clears_the_claim_and_charges_no_attempt(
    boundaries: Boundaries, human: HumanClone, clock: ManualClock, attempts: int
) -> None:
    claimed = _claim(boundaries, human, attempts=attempts)
    _dead_run(boundaries)
    snapshot = _snapshot(boundaries)
    before = snapshot.document.state
    assert before is not None
    assert before.crashes == 0

    _handler(boundaries, claimed.definition, _Rerun(clock)).handle(_event(snapshot))

    after = _state_at(boundaries, f"origin/{BRANCH}")
    assert after.crashes == 1
    assert after.attempts == attempts
    assert after.claim is None
    unchanged = {"stage", "blocked", "round", "pull_request", "comments_read", "handed_over"}
    assert after.model_dump(include=unchanged) == before.model_dump(include=unchanged)


def test_the_journal_ends_with_one_factory_crash_record(
    boundaries: Boundaries, human: HumanClone, clock: ManualClock
) -> None:
    claimed = _claim(boundaries, human)
    _dead_run(boundaries)
    snapshot = _snapshot(boundaries)
    before = snapshot.document.state
    assert before is not None

    _handler(boundaries, claimed.definition, _Rerun(clock)).handle(_event(snapshot))

    after = _state_at(boundaries, f"origin/{BRANCH}")
    assert after.journal[:-1] == before.journal
    assert after.journal[-1] == JournalRecord(
        number=before.journal[-1].number + 1,
        speaker=FACTORY,
        kind="crash",
        at=clock.now(),
        stage=before.stage,
    )


def test_the_crash_entry_names_the_stage_and_the_stage_start_commit(
    boundaries: Boundaries, human: HumanClone, clock: ManualClock
) -> None:
    claimed = _crash(boundaries, human, clock)

    after = _document_at(boundaries, f"origin/{BRANCH}")
    crash = last_record(after, kind="crash")
    assert crash is not None
    assert entry_text(after, crash.number) == crash_entry_text(STAGE, 1, claimed.start.commit)


def test_the_crash_commit_is_pushed(
    boundaries: Boundaries, human: HumanClone, clock: ManualClock
) -> None:
    claimed = _crash(boundaries, human, clock)

    git = boundaries.git
    pushed = _remote_head(boundaries)
    assert pushed == git.resolve(BRANCH)
    assert pushed != claimed.start.commit
    assert _state_at(boundaries, pushed).crashes == 1


def test_the_dead_stages_cost_records_are_discarded_and_earlier_ones_stay(
    boundaries: Boundaries, human: HumanClone, clock: ManualClock
) -> None:
    claimed = _claim(boundaries, human, costs=[INTAKE_RECORD])
    sidecar = boundaries.checkout / cost_records_path(PATH)
    boundaries.cost_writer.write(sidecar, [INTAKE_RECORD, DEAD_RECORD])
    snapshot = _snapshot(boundaries)

    _handler(boundaries, claimed.definition, _Rerun(clock)).handle(_event(snapshot))

    assert JsonLinesCostRecordReader().read(sidecar) == [INTAKE_RECORD]


def test_an_own_crash_posts_nothing(
    boundaries: Boundaries, human: HumanClone, clock: ManualClock, hosting: FakeHostingService
) -> None:
    pull_request = hosting.create_pull_request(
        BRANCH, f"{WORK_ITEM}: First story", "body", draft=True
    )
    number = pull_request.number
    claimed = _claim(boundaries, human, pull_request=number)
    _dead_run(boundaries)
    snapshot = _snapshot(boundaries)
    pull_requests = hosting.pull_requests()
    event = Event(
        kind="crash",
        work_item=snapshot,
        pull_request=hosting.get_pull_request(number),
        remote_state=_remote_head(boundaries),
    )

    _handler(boundaries, claimed.definition, _Rerun(clock)).handle(event)

    assert hosting.factory_posts(number) == []
    assert hosting.pull_requests() == pull_requests


@pytest.mark.parametrize("restart", [False, True], ids=["same-service", "restart"])
def test_the_stage_reruns_at_once_in_the_same_call(
    boundaries: Boundaries, human: HumanClone, clock: ManualClock, restart: bool
) -> None:
    claimed = _claim(boundaries, human)
    _dead_run(boundaries)
    snapshot = _snapshot(boundaries)
    rerun = _Rerun(clock)
    claims = ClaimService(boundaries, INSTANCE, claimed.definition) if restart else claimed.claims
    handler = RecoveryHandler(boundaries, claimed.definition, claims, rerun)

    handler.handle(_event(snapshot))

    assert rerun.times == [claimed.start.claim.started_at]
    [event] = rerun.events
    pushed = _remote_head(boundaries)
    assert event.kind == "run"
    assert event.remote_state == pushed
    assert event.work_item is not None
    assert event.work_item.branch_commit == pushed
    state = event.work_item.document.state
    assert state is not None
    assert state.crashes == 1
    assert state.claim is None


@pytest.mark.parametrize(
    ("minutes", "status"), [(0, "held"), (60, "expired")], ids=["held", "expired"]
)
def test_a_crash_event_on_another_instances_claim_is_not_rerun(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    clock: ManualClock,
    remote: Path,
    minutes: int,
    status: str,
) -> None:
    claimed = _claim(boundaries, human)
    snapshot = _snapshot(boundaries)
    assert snapshot.document.state is not None
    clock.advance(timedelta(minutes=minutes))
    other = ClaimService(boundaries, OTHER_INSTANCE, claimed.definition)
    assert other.status(snapshot.document.state) == status
    rerun = _Rerun(clock)

    with pytest.raises(CannotHandle) as raised:
        RecoveryHandler(boundaries, claimed.definition, other, rerun).handle(_event(snapshot))

    assert raised.value.kind == "crash"
    assert remote_commit(remote, BRANCH) == claimed.start.commit
    assert rerun.events == []


def test_an_event_of_another_kind_is_refused_before_anything_is_touched(
    boundaries: Boundaries, human: HumanClone, clock: ManualClock, remote: Path
) -> None:
    claimed = _claim(boundaries, human)
    _dead_run(boundaries)
    rerun = _Rerun(clock)

    with pytest.raises(CannotHandle) as raised:
        _handler(boundaries, claimed.definition, rerun).handle(_event(_snapshot(boundaries), "run"))

    assert raised.value.kind == "run"
    assert remote_commit(remote, BRANCH) == claimed.start.commit
    assert (boundaries.checkout / UNTRACKED).exists()
    assert rerun.events == []


def _without_claim(snapshot: WorkItemSnapshot) -> WorkItemSnapshot:
    state = snapshot.document.state
    assert state is not None
    released = state.model_copy(update={"claim": None})
    document = snapshot.document.model_copy(update={"state": released})
    return snapshot.model_copy(update={"document": document})


def _without_state(snapshot: WorkItemSnapshot) -> WorkItemSnapshot:
    document = snapshot.document.model_copy(update={"state": None})
    return snapshot.model_copy(update={"document": document})


def _without_branch_commit(snapshot: WorkItemSnapshot) -> WorkItemSnapshot:
    return snapshot.model_copy(update={"branch_commit": None})


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        (_without_claim, None),
        (_without_state, f"work item {WORK_ITEM} has no state"),
        (_without_branch_commit, None),
    ],
    ids=["no-claim", "no-state", "no-branch-commit"],
)
def test_a_crash_event_without_an_own_claim_on_the_remote_is_refused(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    clock: ManualClock,
    remote: Path,
    change: Callable[[WorkItemSnapshot], WorkItemSnapshot],
    reason: str | None,
) -> None:
    claimed = _claim(boundaries, human)
    snapshot = change(_snapshot(boundaries))
    rerun = _Rerun(clock)

    with pytest.raises(CannotHandle) as raised:
        _handler(boundaries, claimed.definition, rerun).handle(
            Event(kind="crash", work_item=snapshot, remote_state=claimed.start.commit)
        )

    assert raised.value.kind == "crash"
    if reason is not None:
        assert raised.value.reason == reason
    assert remote_commit(remote, BRANCH) == claimed.start.commit
    assert rerun.events == []


def test_a_commit_the_human_pushed_to_the_branch_is_kept(
    boundaries: Boundaries, human: HumanClone, clock: ManualClock, checkout: GitCli
) -> None:
    claimed = _claim(boundaries, human)
    human.push_file(BRANCH, NOTE_PATH, NOTE)
    checkout.fetch()
    human_commit = _remote_head(boundaries)
    _dead_run(boundaries)
    snapshot = _snapshot(boundaries)

    _handler(boundaries, claimed.definition, _Rerun(clock)).handle(_event(snapshot))

    git = boundaries.git
    assert git.show_file(f"origin/{BRANCH}", NOTE_PATH) == NOTE
    assert git.is_ancestor(human_commit, f"origin/{BRANCH}")
    assert git.is_ancestor(claimed.start.commit, f"origin/{BRANCH}")
    after = _document_at(boundaries, f"origin/{BRANCH}")
    crash = last_record(after, kind="crash")
    assert crash is not None
    assert entry_text(after, crash.number) == crash_entry_text(STAGE, 1, human_commit)


def test_a_rejected_push_raises_push_failed_and_does_not_rerun(
    boundaries: Boundaries, human: HumanClone, clock: ManualClock
) -> None:
    claimed = _claim(boundaries, human)
    _dead_run(boundaries)
    snapshot = _snapshot(boundaries)
    human.push_file(BRANCH, NOTE_PATH, NOTE)
    rerun = _Rerun(clock)

    with pytest.raises(PushFailed) as raised:
        _handler(boundaries, claimed.definition, rerun).handle(_event(snapshot))

    assert raised.value.outcome == "rejected"
    assert raised.value.branch == BRANCH
    assert rerun.events == []


def test_a_kill_at_the_push_is_counted_once_after_a_restart(
    boundaries: Boundaries,
    human: HumanClone,
    clock: ManualClock,
    remote: Path,
    kill_points: KillPoints,
) -> None:
    claimed = _claim(boundaries, human)
    _dead_run(boundaries)
    event = _event(_snapshot(boundaries))
    kill_points.arm(KillPoint.BEFORE_PUSH)

    with pytest.raises(InjectedKill):
        _handler(boundaries, claimed.definition, _Rerun(clock)).handle(event)

    assert remote_commit(remote, BRANCH) == claimed.start.commit
    _handler(boundaries, claimed.definition, _Rerun(clock)).handle(event)
    after = _state_at(boundaries, f"origin/{BRANCH}")
    assert after.crashes == 1
    assert [record.kind for record in after.journal].count("crash") == 1


def test_an_exception_from_the_rerun_propagates_and_the_crash_stays_recorded(
    boundaries: Boundaries, human: HumanClone
) -> None:
    claimed = _claim(boundaries, human)
    _dead_run(boundaries)
    error = _RerunFails("the rerun failed")

    with pytest.raises(_RerunFails) as raised:
        _handler(boundaries, claimed.definition, _FailingRerun(error)).handle(
            _event(_snapshot(boundaries))
        )

    assert raised.value is error
    after = _state_at(boundaries, f"origin/{BRANCH}")
    assert after.crashes == 1
    assert after.claim is None


def test_a_git_error_from_the_discard_propagates_and_nothing_is_pushed(
    boundaries: Boundaries, clock: ManualClock, remote: Path
) -> None:
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    claim = Claim(instance=INSTANCE, stage=STAGE, started_at=clock.now(), lease_duration=60)
    state = initial_state(STAGE).model_copy(update={"claim": claim})
    snapshot = WorkItemSnapshot(
        id=WORK_ITEM,
        path=PATH,
        folder="in-progress",
        branch=BRANCH,
        branch_commit="a" * 40,
        document=WorkItemDocument(state=state, body=STORY),
    )
    main = remote_commit(remote, "main")
    rerun = _Rerun(clock)

    with pytest.raises(GitError):
        _handler(boundaries, definition, rerun).handle(_event(snapshot))

    assert rerun.events == []
    assert remote_commit(remote, BRANCH) is None
    assert remote_commit(remote, "main") == main
