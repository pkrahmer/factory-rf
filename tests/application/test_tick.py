"""The tick fetches, loads, restores the checkout, evaluates the remote and dispatches one event."""

import os
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from factory.adapters.clock import ManualClock
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.adapters.work_item_markdown import FrontmatterWorkItemWriter
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.tick import IdleHandler, Tick, TickOutcome
from factory.domain.errors import PushFailed, WorkItemFormatError
from factory.domain.events import Event, EventKind
from factory.domain.git import GitOptions, PushOutcome
from factory.domain.hosting import PullRequestComment, PullRequestView
from factory.domain.identifiers import branch_name
from factory.domain.work_item import WorkItemDocument, WorkItemState, initial_state
from git_support import (
    CHECKOUT,
    PIPELINE_YAML,
    TEST_IDENTITY,
    remote_commit,
    write_files,
)
from human_clone import HumanClone
from log_support import log_lines
from source_search import SRC
from tick_support import handlers_of

INSTANCE = "factory-1"
WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
SECOND_ITEM = "F0001-S0002"
SECOND_BRANCH = branch_name(SECOND_ITEM)
FEATURE = "factory/features/F0001-example"
BACKLOG_PATH = f"{FEATURE}/backlog/F0001-S0001-first.md"
PATH = f"{FEATURE}/in-progress/F0001-S0001-first.md"
SECOND_BACKLOG_PATH = f"{FEATURE}/backlog/F0001-S0002-second.md"
SECOND_PATH = f"{FEATURE}/in-progress/F0001-S0002-second.md"
BODY = "# First story\n"
STAMP = "2026-10-12T12:00:00Z "
V1_FILES = ("factory-run.json", "factory-tick.lock", "factory-tick.json")


class Recording(Handler):
    """Records every event it is handed."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class Failing(Handler):
    """Records every event it is handed and fails."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)
        raise RuntimeError("handler failed")


class StalePush(Handler):
    """Commits on the work item's branch made from an older commit and pushes it."""

    def __init__(
        self,
        git: GitCli,
        directory: Path,
        *,
        base: str | None = None,
        meanwhile: Callable[[], None] | None = None,
    ) -> None:
        self.events: list[Event] = []
        self.outcomes: list[PushOutcome] = []
        self.on_main_at_origin: list[bool] = []
        self._git = git
        self._directory = directory
        self._base = base
        self._meanwhile = meanwhile

    def handle(self, event: Event) -> None:
        self.events.append(event)
        status = self._git.status()
        at_origin = status.head == self._git.resolve("origin/main")
        self.on_main_at_origin.append(status.branch == "main" and at_origin)
        start = event.remote_state if self._base is None else self._base
        if self._meanwhile is not None:
            self._meanwhile()
            self._meanwhile = None
        self._git.checkout(BRANCH, start_point=start)
        write_files(self._directory, {"notes.txt": f"attempt {len(self.events)}\n"})
        self._git.commit("handler work")
        outcome = self._git.push(BRANCH)
        self.outcomes.append(outcome)
        if outcome != "pushed":
            raise PushFailed(BRANCH, outcome)


class _CountingHosting(FakeHostingService):
    """The fake hosting service, recording every operation the tick could call."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[str] = []

    def create_pull_request(
        self, branch: str, title: str, body: str, *, draft: bool
    ) -> PullRequestView:
        self.calls.append("create_pull_request")
        return super().create_pull_request(branch, title, body, draft=draft)

    def find_open_pull_request(self, branch: str) -> PullRequestView | None:
        self.calls.append("find_open_pull_request")
        return super().find_open_pull_request(branch)

    def get_pull_request(self, number: int) -> PullRequestView:
        self.calls.append("get_pull_request")
        return super().get_pull_request(number)

    def list_comments(self, number: int) -> list[PullRequestComment]:
        self.calls.append("list_comments")
        return super().list_comments(number)

    def close(self, number: int) -> None:
        self.calls.append("close")
        super().close(number)

    def reopen(self, number: int) -> None:
        self.calls.append("reopen")
        super().reopen(number)

    def set_draft(self, number: int, draft: bool) -> None:
        self.calls.append("set_draft")
        super().set_draft(number, draft)

    def set_description(self, number: int, body: str) -> None:
        self.calls.append("set_description")
        super().set_description(number, body)

    def set_labels(self, number: int, labels: Sequence[str]) -> None:
        self.calls.append("set_labels")
        super().set_labels(number, labels)


pytestmark = pytest.mark.usefixtures("installed_agents")


def _tick(boundaries: Boundaries, handlers: Mapping[EventKind, Handler]) -> Tick:
    return Tick(boundaries, INSTANCE, handlers_of(handlers))


def _push_state(human: HumanClone, state: WorkItemState, *, path: str = PATH) -> None:
    text = FrontmatterWorkItemWriter().render(WorkItemDocument(state=state, body=BODY))
    branch = BRANCH if path == PATH else SECOND_BRANCH
    human.push_file(branch, path, text)


def _start_second(human: HumanClone) -> None:
    human.push_file("main", SECOND_BACKLOG_PATH, "# Second story\n")
    human.start(SECOND_BACKLOG_PATH)


def _texts(lines: list[str]) -> list[str]:
    return [line.split(" ", 1)[1] if " " in line else "" for line in lines]


def _move_remote_away(remote: Path, tmp_path: Path) -> Path:
    moved = tmp_path / "moved.git"
    remote.rename(moved)
    return moved


def test_the_tick_fetches_before_it_reads_the_remote(
    boundaries: Boundaries, human: HumanClone, remote: Path
) -> None:
    human.start(BACKLOG_PATH)
    _push_state(human, initial_state("intake"))
    handler = Recording()
    tick = _tick(boundaries, {"run": handler})
    tick.run()
    human.push_file(BRANCH, "notes-human.txt", "a human commit\n")

    outcome = tick.run()

    assert outcome.event is not None
    assert outcome.event.remote_state == remote_commit(remote, BRANCH)
    assert handler.events[-1].remote_state == remote_commit(remote, BRANCH)


def test_a_failed_fetch_is_a_repository_stop_and_ends_the_tick(
    boundaries: Boundaries, remote: Path, tmp_path: Path, clock: ManualClock
) -> None:
    handler = Recording()
    _move_remote_away(remote, tmp_path)

    outcome = _tick(boundaries, {"idle": handler, "run": handler}).run()

    assert outcome == TickOutcome(stopped="fetch_failed")
    assert outcome.event is None
    assert outcome.dispatch is None
    assert handler.events == []
    stops = boundaries.health.read().stops
    assert len(stops) == 1
    assert stops[0].scope == "repository"
    assert stops[0].reason == "fetch_failed"
    assert stops[0].detail.strip()
    assert stops[0].at == clock.now()


def test_the_fetch_stop_is_logged_with_the_clock_stamp(
    boundaries: Boundaries, remote: Path, tmp_path: Path
) -> None:
    _move_remote_away(remote, tmp_path)

    _tick(boundaries, {"idle": IdleHandler()}).run()

    lines = [line for line in log_lines(tmp_path) if "stop repository fetch_failed" in line]
    assert lines
    assert all(line.startswith(STAMP) for line in lines)


def test_the_first_tick_after_the_remote_is_back_clears_the_fetch_stop(
    boundaries: Boundaries, remote: Path, tmp_path: Path
) -> None:
    tick = _tick(boundaries, {"idle": IdleHandler()})
    moved = _move_remote_away(remote, tmp_path)
    tick.run()
    moved.rename(remote)

    outcome = tick.run()

    assert all(stop.reason != "fetch_failed" for stop in boundaries.health.read().stops)
    assert outcome.stopped is None
    assert outcome.event is not None
    assert outcome.dispatch is not None


def test_an_invalid_pipeline_definition_ends_the_tick_before_the_restore(
    boundaries: Boundaries, human: HumanClone, tmp_path: Path
) -> None:
    human.push_file("main", "factory/pipeline.yml", PIPELINE_YAML.replace('contract: "1.0"\n', ""))
    untracked = tmp_path / CHECKOUT / "scratch.txt"
    untracked.write_text("left by someone\n", encoding="utf-8")
    handler = Recording()
    before = len(log_lines(tmp_path))

    outcome = _tick(boundaries, {"idle": handler, "run": handler}).run()

    assert outcome == TickOutcome(stopped="pipeline_definition_invalid")
    assert handler.events == []
    stops = [
        stop
        for stop in boundaries.health.read().stops
        if stop.reason == "pipeline_definition_invalid"
    ]
    assert len(stops) == 1
    assert "contract" in stops[0].detail
    assert untracked.exists()
    lines = log_lines(tmp_path)[before:]
    assert (
        len([line for line in lines if "stop repository pipeline_definition_invalid" in line]) == 1
    )


def test_the_tick_after_the_definition_is_repaired_clears_its_stop(
    boundaries: Boundaries, human: HumanClone
) -> None:
    tick = _tick(boundaries, {"idle": IdleHandler()})
    human.push_file("main", "factory/pipeline.yml", PIPELINE_YAML.replace('contract: "1.0"\n', ""))
    tick.run()
    human.push_file("main", "factory/pipeline.yml", PIPELINE_YAML)

    outcome = tick.run()

    assert outcome.stopped is None
    reasons = [stop.reason for stop in boundaries.health.read().stops]
    assert "pipeline_definition_invalid" not in reasons


def test_the_restore_discards_changes_and_names_them_in_one_line(
    boundaries: Boundaries, checkout: GitCli, human: HumanClone, tmp_path: Path
) -> None:
    human.push_file("main", "notes/main.txt", "a newer main\n")
    directory = tmp_path / CHECKOUT
    (directory / ".git" / "info" / "exclude").write_text("ignored.log\n", encoding="utf-8")
    (directory / "ignored.log").write_text("kept\n", encoding="utf-8")
    (directory / "factory" / "story-form.md").write_text("changed\n", encoding="utf-8")
    (directory / "scratch.txt").write_text("untracked\n", encoding="utf-8")
    paths = [change.path for change in checkout.status().changes]
    assert len(paths) == 2

    _tick(boundaries, {"idle": IdleHandler()}).run()

    assert (directory / "factory" / "story-form.md").read_text(encoding="utf-8") == (
        checkout.show_file("origin/main", "factory/story-form.md")
    )
    assert not (directory / "scratch.txt").exists()
    assert (directory / "ignored.log").exists()
    status = checkout.status()
    assert status.branch == "main"
    assert status.head == checkout.resolve("origin/main")
    assert status.changes == []
    expected = f"discarded uncommitted changes: {paths[0]}, {paths[1]}"
    assert _texts(log_lines(tmp_path)).count(expected) == 1


def test_a_clean_checkout_writes_no_discarded_line(boundaries: Boundaries, tmp_path: Path) -> None:
    _tick(boundaries, {"idle": IdleHandler()}).run()

    assert not [line for line in log_lines(tmp_path) if "discarded uncommitted changes" in line]


@pytest.mark.skipif(os.geteuid() == 0, reason="root removes files in unwritable directories")
def test_a_failed_restore_is_a_repository_stop_cleared_by_the_next_tick(
    boundaries: Boundaries, tmp_path: Path
) -> None:
    locked = tmp_path / CHECKOUT / "locked"
    locked.mkdir()
    (locked / "file.txt").write_text("cannot be removed\n", encoding="utf-8")
    locked.chmod(0o555)
    handler = Recording()
    tick = _tick(boundaries, {"idle": handler, "run": handler})
    try:
        outcome = tick.run()
    finally:
        locked.chmod(0o755)

    assert outcome == TickOutcome(stopped="checkout_restore_failed")
    assert handler.events == []
    reasons = [stop.reason for stop in boundaries.health.read().stops]
    assert reasons == ["checkout_restore_failed"]

    tick.run()

    reasons = [stop.reason for stop in boundaries.health.read().stops]
    assert "checkout_restore_failed" not in reasons


def test_a_rejected_push_leaves_no_trace_for_the_next_tick(
    boundaries: Boundaries, checkout: GitCli, human: HumanClone, remote: Path, tmp_path: Path
) -> None:
    human.start(BACKLOG_PATH)
    _push_state(human, initial_state("intake"))

    def human_pushes() -> None:
        human.push_file(BRANCH, "notes-human.txt", "meanwhile\n")

    handler = StalePush(checkout, tmp_path / CHECKOUT, meanwhile=human_pushes)
    tick = _tick(boundaries, {"run": handler})

    first = tick.run()
    head = remote_commit(remote, BRANCH)

    assert handler.outcomes == ["rejected"]
    assert first.dispatch == "error"
    assert tick.status.errors[0].last_error.startswith("PushFailed")

    second = tick.run()

    assert second.event is not None
    assert second.event.remote_state == head
    assert handler.events[1].remote_state == head
    assert handler.on_main_at_origin[1]


def _stale_branch(human: HumanClone, remote: Path) -> str:
    human.start(BACKLOG_PATH)
    _push_state(human, initial_state("intake"))
    older = remote_commit(remote, BRANCH)
    assert older is not None
    human.push_file(BRANCH, "notes-human.txt", "newer\n")
    return older


def test_a_failing_handler_is_reported_once_and_then_capped(
    boundaries: Boundaries,
    checkout: GitCli,
    human: HumanClone,
    *,
    hosting: FakeHostingService,
    remote: Path,
    tmp_path: Path,
) -> None:
    older = _stale_branch(human, remote)
    handler = StalePush(checkout, tmp_path / CHECKOUT, base=older)
    tick = _tick(boundaries, {"run": handler})

    outcomes = [tick.run().dispatch for _ in range(6)]

    assert outcomes == ["error", "error", "reported", "capped", "capped", "capped"]
    numbers = [pull.number for pull in hosting.pull_requests() if pull.branch == BRANCH]
    assert len(numbers) == 1
    assert len(hosting.factory_posts(numbers[0])) == 1


def test_a_human_push_after_the_report_retries_the_capped_event(
    boundaries: Boundaries, checkout: GitCli, human: HumanClone, remote: Path, tmp_path: Path
) -> None:
    older = _stale_branch(human, remote)
    handler = StalePush(checkout, tmp_path / CHECKOUT, base=older)
    tick = _tick(boundaries, {"run": handler})
    for _ in range(3):
        tick.run()
    human.push_file(BRANCH, "notes-human.txt", "newest\n")

    tick.run()

    assert len(handler.events) == 4
    assert handler.events[-1].remote_state == remote_commit(remote, BRANCH)


def test_a_fresh_clone_continues_every_work_item_from_its_branch(
    boundaries: Boundaries, human: HumanClone, remote: Path, tmp_path: Path
) -> None:
    human.start(BACKLOG_PATH)
    _start_second(human)
    _push_state(human, initial_state("done"))
    _push_state(human, initial_state("doing"), path=SECOND_PATH)
    original = Recording()
    _tick(boundaries, {"run": original}).run()
    fresh_directory = tmp_path / "fresh"
    fresh_directory.mkdir()
    fresh_git = GitCli(fresh_directory, GitOptions(identity=TEST_IDENTITY))
    fresh_git.clone(str(remote))
    fresh = Recording()

    _tick(replace(boundaries, git=fresh_git, checkout=fresh_directory), {"run": fresh}).run()

    assert len(original.events) == 1
    assert len(fresh.events) == 1
    expected, actual = original.events[0], fresh.events[0]
    assert actual.kind == expected.kind == "run"
    assert actual.work_item is not None
    assert expected.work_item is not None
    assert actual.work_item.id == expected.work_item.id == SECOND_ITEM
    assert actual.remote_state == expected.remote_state == remote_commit(remote, SECOND_BRANCH)
    assert actual.work_item.document.state == expected.work_item.document.state
    assert actual.work_item.document.state == initial_state("doing")


@pytest.mark.parametrize("v1_state", ["valid", "unreadable", "absent"])
def test_v1_leftover_files_change_nothing(
    boundaries: Boundaries, human: HumanClone, remote: Path, tmp_path: Path, v1_state: str
) -> None:
    human.start(BACKLOG_PATH)
    git_directory = tmp_path / CHECKOUT / ".git"
    contents = {
        "valid": '{"work_item": "F0001-S0001", "stage": "intake"}\n',
        "unreadable": "\x00{not json",
    }
    if v1_state != "absent":
        for name in V1_FILES:
            (git_directory / name).write_text(contents[v1_state], encoding="utf-8")
    handler = Recording()

    outcome = _tick(boundaries, {"run": handler}).run()

    assert outcome.dispatch == "handled"
    assert outcome.event is not None
    assert outcome.event.kind == "run"
    assert outcome.event.work_item is not None
    assert outcome.event.work_item.id == WORK_ITEM
    assert outcome.event.remote_state == remote_commit(remote, "main")
    for name in V1_FILES:
        path = git_directory / name
        if v1_state == "absent":
            assert not path.exists()
        else:
            assert path.read_text(encoding="utf-8") == contents[v1_state]


@pytest.mark.parametrize(
    "module",
    [
        "application/tick.py",
        "application/watcher.py",
        "application/work_items.py",
        "domain/evaluation.py",
    ],
)
def test_the_tick_knows_no_run_record_and_no_lock(module: str) -> None:
    text = (SRC / module).read_text(encoding="utf-8")

    for word in (
        "run_record",
        "RunRecord",
        "factory-run.json",
        "factory-tick.lock",
        "factory-tick.json",
    ):
        assert word not in text
    assert re.search(r"\block\b", text) is None


def test_an_idle_tick_makes_no_hosting_call(boundaries: Boundaries) -> None:
    hosting = _CountingHosting()

    _tick(replace(boundaries, hosting=hosting), {"idle": IdleHandler()}).run()

    assert hosting.calls == []


def test_a_waiting_work_item_costs_one_lookup_and_its_comments(
    boundaries: Boundaries, human: HumanClone
) -> None:
    hosting = _CountingHosting()
    number = hosting.create_pull_request(BRANCH, "First story", "", draft=False).number
    human.start(BACKLOG_PATH)
    state = WorkItemState(stage="approval", pull_request=number, handed_over="approval")
    _push_state(human, state)
    hosting.calls.clear()

    _tick(replace(boundaries, hosting=hosting), {"idle": IdleHandler()}).run()

    assert sorted(hosting.calls) == ["get_pull_request", "list_comments"]


def test_the_idle_handler_changes_nothing(
    boundaries: Boundaries, checkout: GitCli, hosting: FakeHostingService, remote: Path
) -> None:
    checkout.fetch()
    status = checkout.status()
    main = remote_commit(remote, "main")
    branches = checkout.remote_branches()

    outcome = _tick(boundaries, {"idle": IdleHandler()}).run()

    assert outcome.event is not None
    assert outcome.event.kind == "idle"
    assert outcome.dispatch == "handled"
    assert checkout.status() == status
    assert remote_commit(remote, "main") == main
    assert checkout.remote_branches() == branches
    assert hosting.pull_requests() == []


def test_an_event_without_a_handler_is_a_counted_error(
    boundaries: Boundaries, human: HumanClone
) -> None:
    human.start(BACKLOG_PATH)
    tick = _tick(boundaries, {"idle": IdleHandler()})

    outcome = tick.run()

    assert outcome.dispatch == "error"
    assert tick.status.errors[-1].last_error == "UnhandledEvent: no handler for event kind run"


def test_the_restore_deletes_a_local_branch_the_remote_has_not_taken(
    boundaries: Boundaries, checkout: GitCli, human: HumanClone, remote: Path, tmp_path: Path
) -> None:
    human.start(BACKLOG_PATH)
    _push_state(human, initial_state("intake"))
    checkout.checkout("scratch", start_point="origin/main")
    checkout.checkout(BRANCH, start_point="origin/main")
    write_files(tmp_path / CHECKOUT, {"claim.txt": "a rejected claim\n"})
    checkout.commit("claim")

    _tick(boundaries, {"run": Recording()}).run()

    assert checkout.resolve(BRANCH) is None
    assert checkout.resolve(f"origin/{BRANCH}") == remote_commit(remote, BRANCH)
    assert checkout.resolve("scratch") is not None


def test_the_restore_deletes_a_local_branch_of_a_started_story_without_a_remote_branch(
    boundaries: Boundaries, checkout: GitCli, human: HumanClone, tmp_path: Path
) -> None:
    human.start(BACKLOG_PATH)
    checkout.checkout(BRANCH, start_point="origin/main")
    write_files(tmp_path / CHECKOUT, {"claim.txt": "a rejected claim\n"})
    checkout.commit("claim")

    _tick(boundaries, {"run": Recording()}).run()

    assert checkout.resolve(BRANCH) is None


def test_an_unreadable_work_item_file_raises_without_a_stop(
    boundaries: Boundaries, human: HumanClone
) -> None:
    human.start(BACKLOG_PATH)
    human.push_file(BRANCH, PATH, "# First story, edited\n")
    handler = Recording()

    with pytest.raises(WorkItemFormatError, match=re.escape(PATH)):
        _tick(boundaries, {"run": handler, "idle": handler}).run()

    assert handler.events == []
    assert boundaries.health.read().stops == []


def test_a_work_item_in_an_unknown_stage_raises_value_error(
    boundaries: Boundaries, human: HumanClone
) -> None:
    human.start(BACKLOG_PATH)
    _push_state(human, initial_state("nowhere"))
    handler = Recording()

    with pytest.raises(ValueError, match="nowhere"):
        _tick(boundaries, {"run": handler, "idle": handler}).run()

    assert handler.events == []


def test_a_capped_event_holds_back_all_new_work(boundaries: Boundaries, human: HumanClone) -> None:
    human.start(BACKLOG_PATH)
    _start_second(human)
    handler = Failing()
    tick = _tick(boundaries, {"run": handler})
    for _ in range(3):
        tick.run()

    later = [tick.run().dispatch for _ in range(3)]

    assert later == ["capped", "capped", "capped"]
    called = [event.work_item.id for event in handler.events if event.work_item is not None]
    assert called == [WORK_ITEM] * 3

    _push_state(human, initial_state("intake"))
    tick.run()

    called = [event.work_item.id for event in handler.events if event.work_item is not None]
    assert called == [WORK_ITEM] * 4


def test_the_tick_keeps_its_status_across_ticks_and_a_restart_counts_from_one(
    boundaries: Boundaries, human: HumanClone
) -> None:
    human.start(BACKLOG_PATH)
    handlers: Mapping[EventKind, Handler] = {"run": Failing()}
    tick = _tick(boundaries, handlers)
    tick.run()
    tick.run()

    assert len(tick.status.errors) == 1
    assert tick.status.errors[0].count == 2

    restarted = Tick(boundaries, INSTANCE, handlers_of(handlers))
    restarted.run()

    assert len(restarted.status.errors) == 1
    assert restarted.status.errors[0].count == 1


@pytest.mark.parametrize(
    ("field", "value", "accepted"),
    [
        ("stopped", "fetch_failed", True),
        ("stopped", None, True),
        ("stopped", "other", False),
        ("dispatch", "capped", True),
        ("dispatch", "other", False),
    ],
)
def test_tick_outcome_accepts_only_its_values(
    field: str, value: str | None, accepted: bool
) -> None:
    model: type[BaseModel] = TickOutcome

    if accepted:
        assert getattr(model(**{field: value}), field) == value
    else:
        with pytest.raises(ValidationError):
            model(**{field: value})
