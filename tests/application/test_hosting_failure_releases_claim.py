"""A hosting failure after a stage's claim releases the claim, so the next tick charges no crash."""

import re
import shlex
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from factory.adapters.fake_hosting import FakeHostingService
from factory.application.handlers.recording import commit_subject
from factory.application.opening import PreparedWorkItem, WorkItemOpening
from factory.application.stage import StageLauncher
from factory.domain.errors import HostingServiceError, WorkItemFormatError
from factory.domain.git import CommitInfo
from factory.domain.hosting import PullRequestView
from factory.domain.identifiers import WorkItemId, branch_name
from factory.domain.kill_points import KillPoints
from factory.domain.work_item import WorkItemDocument
from git_support import PIPELINE_YAML
from proof_support import (
    FEATURE,
    STAGE,
    World,
    branch_state,
    completed,
    head_state,
    run_ticks,
    state_at,
    work_item_file,
)
from stage_run_support import ENVIRONMENT, INSTANCE

RELEASE_TEXT = "claim released: hosting failed"
HANDLER_ERROR = re.compile(r"handler error (\S+) (\d+) of 3: HostingServiceError: ")


class _RaisingHosting(FakeHostingService):
    """The fake hosting service, whose next pull request creation raises one known error."""

    def __init__(self, kill_points: KillPoints, error: HostingServiceError) -> None:
        super().__init__(kill_points)
        self.error = error

    def create_pull_request(
        self, branch: str, title: str, body: str, *, draft: bool
    ) -> PullRequestView:
        del branch, title, body, draft  # the creation fails whatever it is asked for
        raise self.error


@dataclass(frozen=True)
class _Launch:
    """A launcher on the world whose hosting service raises `error`, and the prepared story."""

    launcher: StageLauncher
    prepared: PreparedWorkItem
    error: HostingServiceError


def _release_subject(work_item: WorkItemId) -> str:
    return commit_subject(work_item, RELEASE_TEXT)


def _refuse_releases(world: World, work_item: WorkItemId, refusals: int) -> None:
    """Make the remote refuse the next `refusals` pushes whose head is the release commit."""
    left = world.remote / "release-refusals-left"
    left.write_text(f"{refusals}\n", encoding="utf-8")
    hooks = world.remote / "hooks"
    hooks.mkdir(exist_ok=True)
    hook = hooks / "pre-receive"
    subject = shlex.quote(_release_subject(work_item))
    hook.write_text(
        "#!/bin/sh\n"
        f"left=$(cat {shlex.quote(str(left))})\n"
        "while read old new ref; do\n"
        '  if [ "$(git log -1 --format=%s "$new")" = ' + subject + ' ] && [ "$left" -gt 0 ]; then\n'
        f"    echo $((left - 1)) > {shlex.quote(str(left))}\n"
        "    echo 'Internal Server Error' >&2\n"
        "    exit 1\n"
        "  fi\n"
        "done\n"
        "exit 0\n",
        encoding="utf-8",
    )
    hook.chmod(0o755)


def _branch_commits(world: World, work_item: WorkItemId) -> list[CommitInfo]:
    git = world.boundaries.git
    git.fetch()
    return git.log(f"origin/{branch_name(work_item)}", since="origin/main")


def _log_text(world: World) -> str:
    log = world.state / "factory.log"
    return log.read_text(encoding="utf-8") if log.exists() else ""


def _handler_errors(world: World) -> list[tuple[str, str]]:
    return [(match[1], match[2]) for match in HANDLER_ERROR.finditer(_log_text(world))]


def _queue_stage_run(world: World) -> None:
    definition = world.boundaries.pipeline_reader.parse(PIPELINE_YAML)
    world.agent_runtime.queue(completed(definition.stages[STAGE].next[0]))


def _crashes_in_journal(world: World, work_item: WorkItemId) -> int:
    journal = head_state(world, work_item).journal
    return [(record.speaker, record.kind) for record in journal].count(("factory", "crash"))


@pytest.fixture
def failed_tick(world: World, work_item: WorkItemId) -> World:
    """A world whose first tick claimed the work item and then met a hosting failure."""
    del work_item  # requested only so that the story exists before the tick
    world.hosting.fail_next("create_pull_request")
    run_ticks(world)
    return world


@pytest.fixture
def launch(world: World, work_item: WorkItemId) -> _Launch:
    """A launcher whose hosting service raises a known error, and the story prepared for it."""
    error = HostingServiceError("create_pull_request", "injected failure")
    hosting = _RaisingHosting(world.kill_points, error)
    boundaries = replace(world.boundaries, hosting=hosting)
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    boundaries.git.fetch()
    [path] = [
        path
        for path in boundaries.git.list_files("origin/main", f"{FEATURE}/in-progress")
        if Path(path).name.startswith(work_item)
    ]
    prepared = WorkItemOpening(boundaries, definition).prepare(work_item, path)
    launcher = StageLauncher(boundaries, INSTANCE, definition, ENVIRONMENT)
    return _Launch(launcher=launcher, prepared=prepared, error=error)


def test_a_hosting_failure_after_the_claim_releases_it_and_the_next_tick_runs_the_stage(
    failed_tick: World, work_item: WorkItemId
) -> None:
    released = branch_state(failed_tick, work_item)
    assert released is not None
    assert released.claim is None
    assert failed_tick.agent_runtime.requests() == []

    _queue_stage_run(failed_tick)
    run_ticks(failed_tick)

    assert _crashes_in_journal(failed_tick, work_item) == 0
    assert head_state(failed_tick, work_item).crashes == 0
    assert len(failed_tick.agent_runtime.requests()) == 1


@pytest.mark.parametrize(
    ("refusals", "released"),
    [
        pytest.param(0, True, id="pushed-first-try"),
        pytest.param(2, True, id="pushed-after-two-refusals"),
        pytest.param(4, False, id="refused-four-times"),
    ],
)
def test_a_release_whose_push_is_refused_four_times_leaves_the_claim_and_a_crash_follows(
    world: World, work_item: WorkItemId, refusals: int, released: bool
) -> None:
    _refuse_releases(world, work_item, refusals)
    world.hosting.fail_next("create_pull_request")
    run_ticks(world)

    claimed = branch_state(world, work_item)
    assert claimed is not None
    assert (claimed.claim is None) is released

    _queue_stage_run(world)
    run_ticks(world)

    assert _crashes_in_journal(world, work_item) == (0 if released else 1)


@pytest.mark.parametrize("ticks", [pytest.param(1, id="one-tick"), pytest.param(3, id="three")])
def test_each_failing_tick_counts_its_handler_error_from_one_and_reaches_no_cap(
    world: World, work_item: WorkItemId, ticks: int
) -> None:
    world.hosting.fail_next("create_pull_request", times=ticks)
    run_ticks(world, ticks)

    errors = _handler_errors(world)
    assert [count for _key, count in errors] == ["1"] * ticks
    assert {key for key, _count in errors} == {key for key, _count in errors[:1]}
    assert all(key.endswith(f":{work_item}") for key, _count in errors)
    assert "error cap reached" not in _log_text(world)


def test_an_error_other_than_a_hosting_failure_after_the_claim_releases_nothing(
    world: World, work_item: WorkItemId, launch: _Launch
) -> None:
    document = launch.prepared.document
    untitled = "\n".join(line for line in document.body.split("\n") if not line.startswith("# "))
    prepared = launch.prepared.model_copy(
        update={"document": WorkItemDocument(state=document.state, body=untitled)}
    )

    with pytest.raises(WorkItemFormatError):
        launch.launcher.launch(prepared)

    claimed = branch_state(world, work_item)
    assert claimed is not None
    assert claimed.claim is not None
    subjects = [commit.subject for commit in _branch_commits(world, work_item)]
    assert _release_subject(work_item) not in subjects
    assert world.agent_runtime.requests() == []


@pytest.mark.parametrize(
    "refusals",
    [pytest.param(0, id="release-pushed"), pytest.param(4, id="release-refused")],
)
def test_the_hosting_failure_reaches_the_caller_as_the_same_exception(
    world: World, work_item: WorkItemId, launch: _Launch, refusals: int
) -> None:
    _refuse_releases(world, work_item, refusals)

    with pytest.raises(HostingServiceError) as raised:
        launch.launcher.launch(launch.prepared)

    assert raised.value is launch.error


def test_the_release_is_one_commit_with_its_subject_and_leaves_the_journal_and_counters(
    failed_tick: World, work_item: WorkItemId
) -> None:
    commits = _branch_commits(failed_tick, work_item)
    subjects = [commit.subject for commit in commits]
    assert subjects.count(_release_subject(work_item)) == 1
    release, claim = commits[0], commits[1]
    assert release.subject == _release_subject(work_item)
    assert release.parents == [claim.commit]

    path = work_item_file(failed_tick, work_item)
    released = state_at(failed_tick, release.commit, path)
    claimed = state_at(failed_tick, claim.commit, path)
    assert released is not None
    assert claimed is not None
    assert claimed.claim is not None
    assert released.journal == claimed.journal
    assert released.attempts == claimed.attempts
    assert released.round == claimed.round
    assert released.crashes == claimed.crashes
