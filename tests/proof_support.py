"""The recovery proof: a world of real git and fakes, the kill-point scenarios and their checks."""

import re
import shutil
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Final

from container_support import fake_dataset
from disk_support import FakeDiskSpace
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.adapters.clock import ManualClock, ManualWaiter
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader, JsonLinesCostRecordWriter
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.adapters.health_file import JsonHealthStatusFile
from factory.adapters.make_commands import MakeProjectCommands
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.application.boundaries import Boundaries
from factory.application.costs import read_cost_records
from factory.application.tick import Tick
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.cost_records import CostRecord
from factory.domain.disk import DiskRecord
from factory.domain.git import CommitId, GitOptions
from factory.domain.hosting import PostKind, PullRequestComment, PullRequestView
from factory.domain.identifiers import Name, WorkItemId, branch_name
from factory.domain.journal import HUMAN, JournalRecord, NewEntry, append_entry
from factory.domain.kill_point_cases import KILL_POINT_CASES, KillPointCase
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.known_results import ResultRecord
from factory.domain.paths import cost_records_path
from factory.domain.settings import InstanceSettings
from factory.domain.stops import StopRecord
from factory.domain.work_item import WorkItemDocument, WorkItemState, initial_state
from factory.entry.wiring import agent_environment, handler_factory
from git_support import (
    CHECKOUT,
    PIPELINE_YAML,
    TEST_IDENTITY,
    clone,
    copy_remote,
    install_agents,
    make_remote,
    run_git,
)
from human_clone import HumanClone
from stage_run_support import INSTANCE

MARKER: Final[str] = "interrupted-run-marker"
JOURNAL_LEAK: Final[str] = "interrupted-journal-edit"
KILL_TO_RERUN: Final[timedelta] = timedelta(seconds=5)
CRASH_CONDITIONS: Final[tuple[str, ...]] = (
    "resumes-at-first-tick",
    "kill-to-rerun-recorded",
    "no-repeated-post",
    "no-repeated-step",
    "no-interrupted-write-in-history",
    "stage-start-kept",
    "no-discarded-cost-record",
    "counters",
)
STALL_CONDITIONS: Final[tuple[str, ...]] = (
    "attempt-charged",
    "outside-writes-undone",
    "state-restored",
    "inside-writes-kept",
    "cost-record-kept",
)

STAGE = "intake"
START = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)
FEATURE = "factory/features/F0001-example"
FIRST_BACKLOG_STORY = f"{FEATURE}/backlog/F0001-S0001-first.md"
LEAK_PATH = "src/leak.py"
MAIN = "origin/main"
QUESTION = "Which format does the title take?"
STORY = """\
# {title}

## Description

Text.

## Interface

None.

## Acceptance criteria

1. It works.
2. make check stays green.
3. docs: none, nothing changes.

## Smoke test

```bash
true
```
Expect: nothing.

## Journal
"""
PASSING_MAKEFILE: Final[str] = "sync:\n\t@:\ncheck:\n\ttrue\nlint:\n\ttrue\ntest:\n\ttrue\n"
PASSING_TEST = "def test_example() -> None:\n    assert True\n"
SOURCE = "EXAMPLE = 1\n"
DRIVE_LIMIT = 20
_STORY_NUMBER = re.compile(r"F0001-S(\d{4})")


@dataclass(frozen=True)
class World:
    """One factory instance against a real bare remote, with the fakes and the clock."""

    boundaries: Boundaries
    hosting: FakeHostingService
    agent_runtime: FakeAgentRuntime
    kill_points: KillPoints
    clock: ManualClock
    human: HumanClone
    remote: Path
    state: Path
    instance: Name
    tick: Tick


@dataclass(frozen=True)
class CaseResult:
    """A world after a played scenario, and what the kill left behind."""

    world: World
    work_item: WorkItemId
    killed_point: KillPoint | None
    killed_at: datetime | None
    stage_start: CommitId | None
    first_tick_requests: tuple[AgentRunRequest, ...] = ()


def _assemble(
    root: Path,
    *,
    hosting: FakeHostingService,
    kill_points: KillPoints,
    clock: ManualClock,
    human: HumanClone,
    remote: Path,
    git: GitCli,
) -> World:
    checkout = root / CHECKOUT
    state = root / "state"
    agent_runtime = FakeAgentRuntime(kill_points)
    snapshots, containers = fake_dataset(root)
    boundaries = Boundaries(
        git=git,
        hosting=hosting,
        agent_runtime=agent_runtime,
        project_commands=MakeProjectCommands(checkout, kill_points),
        work_item_reader=FrontmatterWorkItemReader(),
        work_item_writer=FrontmatterWorkItemWriter(),
        cost_reader=JsonLinesCostRecordReader(),
        cost_writer=JsonLinesCostRecordWriter(),
        pipeline_reader=RuamelPipelineDefinitionReader(),
        agent_definitions=FrontmatterAgentDefinitionReader(root / "agent-home"),
        clock=clock,
        log=TimestampedFactoryLog(state / "factory.log", clock),
        health=JsonHealthStatusFile(state / "health.json"),
        checkout=checkout,
        settings=InstanceSettings(
            repository_url="/srv/project.git",
            instance=INSTANCE,
            checkout=checkout,
            state_directory=state,
            agent_home=root / "agent-home",
        ),
        disk=FakeDiskSpace(free={root: 10**12, state: 10**12}, used={root: 1, state: 1}),
        disk_records=JsonLinesRecordLog(state / "records" / "disk.jsonl", DiskRecord),
        stop_records=JsonLinesRecordLog(state / "records" / "stops.jsonl", StopRecord),
        waiter=ManualWaiter(clock),
        result_records=JsonLinesRecordLog(state / "records" / "known-results.jsonl", ResultRecord),
        snapshots=snapshots,
        containers=containers,
    )
    environment = agent_environment(root / "scripts", root / "home")
    tick = Tick(boundaries, INSTANCE, handler_factory(boundaries, INSTANCE, environment))
    return World(
        boundaries=boundaries,
        hosting=hosting,
        agent_runtime=agent_runtime,
        kill_points=kill_points,
        clock=clock,
        human=human,
        remote=remote,
        state=state,
        instance=INSTANCE,
        tick=tick,
    )


def _git(root: Path, kill_points: KillPoints) -> GitCli:
    options = GitOptions(kill_points=kill_points, identity=TEST_IDENTITY)
    return GitCli(root / CHECKOUT, options)


def build_world(root: Path, *, template: Path | None = None) -> World:
    """Build one world under `root`: remote, checkout, fakes, clock, agents and the human.

    With a `template` that `make_remote` filled, the remote is a copy of it; no git runs for it.
    """
    if template is None:
        remote = make_remote(root / "origin")
    else:
        remote = copy_remote(template, root / "origin")
    clone(remote, root / CHECKOUT)
    kill_points = KillPoints()
    definition = RuamelPipelineDefinitionReader().parse(PIPELINE_YAML)
    install_agents(root / "agent-home", definition.roles)
    return _assemble(
        root,
        hosting=FakeHostingService(kill_points),
        kill_points=kill_points,
        clock=ManualClock(START),
        human=HumanClone(root / "human", remote),
        remote=remote,
        git=_git(root, kill_points),
    )


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def start_story(world: World, title: str = "Example") -> WorkItemId:
    """Push a story of the example feature that passes the form, start it and return its id."""
    git = world.boundaries.git
    git.fetch()
    backlog = git.list_files("origin/main", f"{FEATURE}/backlog")
    if FIRST_BACKLOG_STORY in backlog:
        path = FIRST_BACKLOG_STORY
    else:
        names = [
            name
            for folder in ("backlog", "in-progress", "done")
            for name in git.list_files("origin/main", f"{FEATURE}/{folder}")
        ]
        numbers = [int(match.group(1)) for name in names if (match := _STORY_NUMBER.search(name))]
        number = max(numbers, default=0) + 1
        path = f"{FEATURE}/backlog/F0001-S{number:04d}-{_slug(title)}.md"
    world.human.push_file("main", path, STORY.format(title=title))
    world.human.start(path)
    return Path(path).name[: len("F0001-S0001")]


def _work_item_path(world: World, work_item: WorkItemId) -> str:
    git = world.boundaries.git
    git.fetch()
    for path in git.list_files("origin/main", f"{FEATURE}/in-progress"):
        if Path(path).name.startswith(work_item):
            return path
    raise AssertionError(f"{work_item} is not in progress on origin/main")


def _opening_document(world: World, path: str) -> WorkItemDocument:
    boundaries = world.boundaries
    text = boundaries.git.show_file("origin/main", path)
    assert text is not None
    body = boundaries.work_item_reader.parse_specification(text).body
    if "## Journal" not in body:
        body = f"{body.rstrip()}\n\n## Journal\n"
    created = NewEntry(
        speaker=HUMAN, kind="created", text="created.", on=boundaries.clock.now().date()
    )
    return append_entry(WorkItemDocument(state=initial_state(STAGE), body=body), created)


def _with_marker_and_journal_leak(text: str) -> str:
    lines = text.rstrip("\n").split("\n")
    start = lines.index("## Description")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
    while lines[end - 1] == "":
        end -= 1
    lines[end:end] = ["", MARKER]
    return "\n".join([*lines, JOURNAL_LEAK]) + "\n"


def leak_writes(world: World, work_item: WorkItemId, *, stage: str | None = None) -> dict[str, str]:
    """The writes of an interrupted run: one outside the write paths, two in the work item."""
    boundaries = world.boundaries
    path = _work_item_path(world, work_item)
    branch = f"origin/{branch_name(work_item)}"
    text = None
    if boundaries.git.resolve(branch) is not None:
        text = boundaries.git.show_file(branch, path)
    if text is None:
        document = _opening_document(world, path)
    else:
        document = boundaries.work_item_reader.parse(text)
    if stage is not None:
        assert document.state is not None
        document = document.model_copy(
            update={"state": document.state.model_copy(update={"stage": stage})}
        )
    rendered = boundaries.work_item_writer.render(document)
    return {LEAK_PATH: f"{MARKER} = True\n", path: _with_marker_and_journal_leak(rendered)}


def completed(
    decision: str, entry: str = "ok", *, writes: dict[str, str] | None = None, kill: bool = False
) -> ScriptedRun:
    """A run that completes with `decision` and `entry` after one second."""
    result = AgentRunResult(
        end_reason="completed", decision=decision, entry=entry, duration=timedelta(seconds=1)
    )
    return ScriptedRun(writes=writes or {}, result=result, kill=kill)


def died(*, writes: dict[str, str] | None = None, kill: bool = False) -> ScriptedRun:
    """A run that dies after one second, without decision or entry."""
    result = AgentRunResult(end_reason="died", duration=timedelta(seconds=1))
    return ScriptedRun(writes=writes or {}, result=result, kill=kill)


def timed_out(*, writes: dict[str, str] | None = None) -> ScriptedRun:
    """A run that reaches its time limit after 40 minutes, without decision or entry."""
    result = AgentRunResult(end_reason="time_limit", duration=timedelta(minutes=40))
    return ScriptedRun(writes=writes or {}, result=result)


def _question(*, writes: dict[str, str] | None = None, kill: bool = False) -> ScriptedRun:
    return completed("question", QUESTION, writes=writes, kill=kill)


def run_ticks(world: World, count: int = 1) -> None:
    """Run the world's tick `count` times without moving the clock."""
    for _ in range(count):
        world.tick.run()


def restart(world: World, *, empty_disk: bool = False) -> World:
    """The same instance started again: new runtime, boundaries and tick, same remote and fakes."""
    root = world.state.parent
    if empty_disk:
        shutil.rmtree(root / CHECKOUT, ignore_errors=True)
        shutil.rmtree(world.state, ignore_errors=True)
        git = _git(root, world.kill_points)
        git.clone(str(world.remote))
    else:
        git = _git(root, world.kill_points)
    return _assemble(
        root,
        hosting=world.hosting,
        kill_points=world.kill_points,
        clock=world.clock,
        human=world.human,
        remote=world.remote,
        git=git,
    )


def rerun(world: World, *, empty_disk: bool = False) -> World:
    """Advance the clock by `KILL_TO_RERUN` and start the instance again."""
    world.clock.advance(KILL_TO_RERUN)
    return restart(world, empty_disk=empty_disk)


def _claim_commits(world: World, work_item: WorkItemId, ref: str) -> list[CommitId]:
    """The commits of `ref` off `origin/main` whose state carries a claim, newest first."""
    git = world.boundaries.git
    if git.resolve(ref) is None:
        return []
    path = _work_item_path(world, work_item)
    found: list[CommitId] = []
    for info in git.log(ref, since=MAIN, path=path):
        state = state_at(world, info.commit, path)
        if state is not None and state.claim is not None:
            found.append(info.commit)
    return found


def state_at(world: World, ref: str, path: str) -> WorkItemState | None:
    """The state of the work item file `path` at `ref`, or None when `ref` has no such file."""
    text = world.boundaries.git.show_file(ref, path)
    if text is None:
        return None
    return world.boundaries.work_item_reader.parse(text).state


def tick_until_killed(world: World, limit: int = 3) -> KillPoint:
    """Run ticks until one raises `InjectedKill`, at most `limit`; return the point it names."""
    for _ in range(limit):
        try:
            world.tick.run()
        except InjectedKill as kill:
            return kill.point
    raise AssertionError(f"no kill point fired in {limit} ticks")


@dataclass(frozen=True)
class _Kill:
    point: KillPoint
    at: datetime
    stage_start: CommitId | None


def _kill(world: World, work_item: WorkItemId) -> _Kill:
    point = tick_until_killed(world)
    world.boundaries.git.fetch()
    starts = _claim_commits(world, work_item, f"origin/{branch_name(work_item)}")
    return _Kill(point=point, at=world.clock.now(), stage_start=starts[0] if starts else None)


def _rerun(
    world: World,
    work_item: WorkItemId,
    kill: _Kill,
    *,
    empty_disk: bool = False,
    queue: bool = True,
) -> CaseResult:
    restarted = rerun(world, empty_disk=empty_disk)
    if queue:
        restarted.agent_runtime.queue(_question())
    run_ticks(restarted)
    first_tick = tuple(restarted.agent_runtime.requests())
    run_ticks(restarted, 2)
    return CaseResult(restarted, work_item, kill.point, kill.at, kill.stage_start, first_tick)


def _agent_run_tick(world: World, *, empty_disk: bool = False) -> CaseResult:
    work_item = start_story(world)
    world.kill_points.arm(KillPoint.AGENT_RUN)
    world.agent_runtime.queue(_question(writes=leak_writes(world, work_item), kill=True))
    return _rerun(world, work_item, _kill(world, work_item), empty_disk=empty_disk)


def _container(world: World) -> CaseResult:
    return _agent_run_tick(world, empty_disk=True)


def _commit_push(world: World) -> CaseResult:
    work_item = start_story(world)
    world.kill_points.arm(KillPoint.BEFORE_PUSH, after=1)
    world.agent_runtime.queue(_question(writes=leak_writes(world, work_item)))
    return _rerun(world, work_item, _kill(world, work_item))


def _post_record(world: World) -> CaseResult:
    work_item = start_story(world)
    world.kill_points.arm(KillPoint.AFTER_POST)
    world.agent_runtime.queue(_question(writes=leak_writes(world, work_item)))
    return _rerun(world, work_item, _kill(world, work_item), queue=False)


def _tick_other(world: World) -> CaseResult:
    work_item = start_story(world)
    world.kill_points.arm(KillPoint.AFTER_PUSH, after=0)
    return _rerun(world, work_item, _kill(world, work_item))


def _agent_run_dies(world: World) -> CaseResult:
    work_item = start_story(world)
    world.agent_runtime.queue(died(writes=leak_writes(world, work_item, stage="doing")))
    world.agent_runtime.queue(_question())
    run_ticks(world, 3)
    return CaseResult(world, work_item, None, None, None)


SCENARIOS: dict[str, Callable[[World], CaseResult]] = {
    "agent-run-tick": _agent_run_tick,
    "agent-run-dies": _agent_run_dies,
    "commit-push": _commit_push,
    "post-record": _post_record,
    "tick-other": _tick_other,
    "container": _container,
}


def run_case(case: KillPointCase, root: Path) -> CaseResult:
    """Build a world under `root`, play the case's scenario on it and return what is left."""
    return SCENARIOS[case.id](build_world(root))


def _drive_run(stage: str, next_stage: str) -> ScriptedRun:
    writes = {"tests": {"tests/test_example.py": PASSING_TEST}, "doing": {"src/example.py": SOURCE}}
    return completed(next_stage, writes=writes.get(stage))


def _current(world: World, work_item: WorkItemId) -> WorkItemState:
    world.boundaries.git.fetch()
    if world.boundaries.git.resolve(f"origin/{branch_name(work_item)}") is None:
        return initial_state(STAGE)
    return head_state(world, work_item)


def drive_to(world: World, work_item: WorkItemId, stage: str) -> None:
    """Tick the started `work_item` through each stage's first move until it waits at `stage`."""
    git = world.boundaries.git
    git.fetch()
    if git.show_file("origin/main", "Makefile") != PASSING_MAKEFILE:
        world.human.push_file("main", "Makefile", PASSING_MAKEFILE)
    definition = world.boundaries.pipeline_reader.parse(PIPELINE_YAML)
    for _ in range(DRIVE_LIMIT):
        state = _current(world, work_item)
        if stage == "approval" and state.handed_over == "approval":
            return
        if stage != "approval" and state.stage == stage and state.claim is None:
            return
        role_stage = definition.stages[state.stage]
        if role_stage.next and state.stage != "approval":
            world.agent_runtime.queue(_drive_run(state.stage, role_stage.next[0]))
        world.tick.run()
    raise AssertionError(f"{work_item} did not reach {stage} in {DRIVE_LIMIT} ticks")


def head_state(world: World, work_item: WorkItemId) -> WorkItemState:
    """The work item's state on `origin/<branch>`."""
    world.boundaries.git.fetch()
    state = state_at(world, f"origin/{branch_name(work_item)}", _work_item_path(world, work_item))
    assert state is not None
    return state


def work_item_file(world: World, work_item: WorkItemId) -> str:
    """The path of the work item's `.md` file in the feature's `in-progress/` on its branch."""
    git = world.boundaries.git
    git.fetch()
    listed = git.list_files(f"origin/{branch_name(work_item)}", f"{FEATURE}/in-progress")
    [path] = [
        path for path in listed if Path(path).name.startswith(work_item) and path.endswith(".md")
    ]
    return path


def branch_state(world: World, work_item: WorkItemId) -> WorkItemState | None:
    """The state on the work item's branch after a fetch, or None when there is no branch."""
    git = world.boundaries.git
    git.fetch()
    branch = f"origin/{branch_name(work_item)}"
    if git.resolve(branch) is None:
        return None
    return state_at(world, branch, work_item_file(world, work_item))


def head_journal(world: World, work_item: WorkItemId) -> list[JournalRecord]:
    """The work item's journal records on `origin/<branch>`."""
    return head_state(world, work_item).journal


def pull_request_of(world: World, work_item: WorkItemId) -> PullRequestView:
    """The pull request of the work item's branch, in any state."""
    branch = branch_name(work_item)
    [view] = [view for view in world.hosting.pull_requests() if view.branch == branch]
    return view


def posts(
    world: World, work_item: WorkItemId, kind: PostKind | None = None
) -> list[PullRequestComment]:
    """The factory's posts on the work item's pull request, those of `kind` when given."""
    number = pull_request_of(world, work_item).number
    found = world.hosting.factory_posts(number)
    return [post for post in found if kind is None or (post.key and post.key.kind == kind)]


def repeated_posts(world: World) -> list[str]:
    """The key lines that occur on more than one factory post, over every pull request."""
    keys = Counter(
        post.key.comment()
        for view in world.hosting.pull_requests()
        for post in world.hosting.factory_posts(view.number)
        if post.key is not None
    )
    return sorted(key for key, count in keys.items() if count > 1)


def _remote_commits(world: World) -> list[str]:
    world.boundaries.git.fetch()
    listing = run_git(world.boundaries.checkout, "rev-list", "--remotes=origin")
    return listing.split()


def markers_in_history(world: World, work_item: WorkItemId) -> list[str]:
    """`<commit>:<path>` for each commit of any `origin/*` branch whose file holds `MARKER`."""
    git = world.boundaries.git
    paths = (LEAK_PATH, _work_item_path(world, work_item))
    found: list[str] = []
    for commit in _remote_commits(world):
        for path in paths:
            text = git.show_file(commit, path)
            if text is not None and MARKER in text:
                found.append(f"{commit}:{path}")
    return found


def _costs(world: World, work_item: WorkItemId, ref: str) -> list[CostRecord]:
    sidecar = cost_records_path(_work_item_path(world, work_item))
    boundaries = world.boundaries
    return read_cost_records(boundaries.git, boundaries.cost_reader, ref, sidecar)


def _stall_commit(world: World, work_item: WorkItemId) -> CommitId | None:
    """The commit of `origin/<branch>` off `origin/main` that adds the first `stall` record."""
    path = _work_item_path(world, work_item)
    adding: CommitId | None = None
    branch = f"origin/{branch_name(work_item)}"
    for info in world.boundaries.git.log(branch, since=MAIN, path=path):
        state = state_at(world, info.commit, path)
        if state is not None and any(record.kind == "stall" for record in state.journal):
            adding = info.commit
    return adding


def branch_cost_records(world: World, work_item: WorkItemId) -> list[CostRecord]:
    """The cost records of the work item's sidecar on `origin/<branch>`."""
    world.boundaries.git.fetch()
    return _costs(world, work_item, f"origin/{branch_name(work_item)}")


def _branch(result: CaseResult) -> str:
    return f"origin/{branch_name(result.work_item)}"


def rerun_seconds(result: CaseResult) -> float:
    """Seconds from the kill to the claim of the newest claim commit of the result's branch."""
    assert result.killed_at is not None
    world = result.world
    world.boundaries.git.fetch()
    starts = _claim_commits(world, result.work_item, _branch(result))
    assert starts, "no commit of the branch carries a claim"
    state = state_at(world, starts[0], _work_item_path(world, result.work_item))
    assert state is not None
    assert state.claim is not None
    return (state.claim.started_at - result.killed_at).total_seconds()


def _resumes_at_first_tick(result: CaseResult, case: KillPointCase) -> bool:
    if not case.charges_crash:
        return result.world.agent_runtime.requests() == []
    stages = [request.agent.name for request in result.first_tick_requests]
    return stages == [STAGE]


def _kill_to_rerun_recorded(result: CaseResult, case: KillPointCase) -> bool:
    if not case.charges_crash:
        return True
    if result.killed_at is None:
        return False
    return rerun_seconds(result) == KILL_TO_RERUN.total_seconds()


def _no_repeated_post(result: CaseResult, _case: KillPointCase) -> bool:
    questions = posts(result.world, result.work_item, "question")
    return len(questions) == 1 and repeated_posts(result.world) == []


def _no_repeated_step(result: CaseResult, _case: KillPointCase) -> bool:
    kinds = [record.kind for record in head_journal(result.world, result.work_item)]
    return kinds.count("question") == 1


def _no_interrupted_write_in_history(result: CaseResult, case: KillPointCase) -> bool:
    found = markers_in_history(result.world, result.work_item)
    if case.kill_point not in (KillPoint.AGENT_RUN, KillPoint.BEFORE_PUSH):
        found = [place for place in found if place.endswith(f":{LEAK_PATH}")]
    return found == []


def _stage_start_kept(result: CaseResult, _case: KillPointCase) -> bool:
    start = result.stage_start
    if start is None:
        return False
    journal = head_journal(result.world, result.work_item)
    started = any(record.kind == "started" for record in journal)
    return started and result.world.boundaries.git.is_ancestor(start, _branch(result))


def _no_discarded_cost_record(result: CaseResult, _case: KillPointCase) -> bool:
    world, work_item = result.world, result.work_item
    records = _costs(world, work_item, _branch(result))
    if [(record.status, record.stage) for record in records] != [("completed", STAGE)]:
        return False
    runs = {
        other.run for commit in _remote_commits(world) for other in _costs(world, work_item, commit)
    }
    return runs == {records[0].run}


def _counters(result: CaseResult, case: KillPointCase) -> bool:
    state = head_state(result.world, result.work_item)
    return state.attempts == 0 and state.crashes == (1 if case.charges_crash else 0)


@dataclass(frozen=True)
class _Stalled:
    result: CaseResult
    path: str
    commit: CommitId
    state: WorkItemState


def _stalled(result: CaseResult) -> _Stalled | None:
    world = result.world
    path = _work_item_path(world, result.work_item)
    commit = _stall_commit(world, result.work_item)
    if commit is None:
        return None
    state = state_at(world, commit, path)
    assert state is not None
    return _Stalled(result, path, commit, state)


def _attempt_charged(stalled: _Stalled) -> bool:
    kinds = [record.kind for record in stalled.state.journal]
    state = stalled.state
    return state.attempts == 1 and state.stage == STAGE and kinds.count("stall") == 1


def _outside_writes_undone(stalled: _Stalled) -> bool:
    git = stalled.result.world.boundaries.git
    return git.show_file(stalled.commit, LEAK_PATH) is None


def _state_restored(stalled: _Stalled) -> bool:
    world = stalled.result.world
    git = world.boundaries.git
    starts = _claim_commits(world, stalled.result.work_item, stalled.commit)
    start = state_at(world, starts[0], stalled.path) if starts else None
    leaked = any(
        JOURNAL_LEAK in (git.show_file(commit, stalled.path) or "")
        for commit in _remote_commits(world)
    )
    journal = stalled.state.journal
    return (
        start is not None
        and stalled.state.stage == STAGE
        and journal[:-1] == start.journal
        and journal[-1].kind == "stall"
        and not leaked
    )


def _inside_writes_kept(stalled: _Stalled) -> bool:
    git = stalled.result.world.boundaries.git
    refs = (stalled.commit, _branch(stalled.result))
    return all(MARKER in (git.show_file(ref, stalled.path) or "") for ref in refs)


def _cost_record_kept(stalled: _Stalled) -> bool:
    records = _costs(stalled.result.world, stalled.result.work_item, stalled.commit)
    return [
        (
            record.status,
            record.end_reason,
            record.duration_seconds,
            record.turns,
            record.tokens,
            record.cost_usd,
        )
        for record in records
    ] == [("completed", "died", 1.0, None, None, None)]


_CRASH_CHECKS: dict[str, Callable[[CaseResult, KillPointCase], bool]] = {
    "resumes-at-first-tick": _resumes_at_first_tick,
    "kill-to-rerun-recorded": _kill_to_rerun_recorded,
    "no-repeated-post": _no_repeated_post,
    "no-repeated-step": _no_repeated_step,
    "no-interrupted-write-in-history": _no_interrupted_write_in_history,
    "stage-start-kept": _stage_start_kept,
    "no-discarded-cost-record": _no_discarded_cost_record,
    "counters": _counters,
}
_STALL_CHECKS: dict[str, Callable[[_Stalled], bool]] = {
    "attempt-charged": _attempt_charged,
    "outside-writes-undone": _outside_writes_undone,
    "state-restored": _state_restored,
    "inside-writes-kept": _inside_writes_kept,
    "cost-record-kept": _cost_record_kept,
}


def _holds(result: CaseResult, case: KillPointCase, condition: str) -> bool:
    if condition in _CRASH_CHECKS:
        return _CRASH_CHECKS[condition](result, case)
    stalled = _stalled(result)
    return stalled is not None and _STALL_CHECKS[condition](stalled)


def violations(result: CaseResult, case: KillPointCase, conditions: Sequence[str]) -> list[str]:
    """The names among `conditions` that do not hold for `result` of `case`."""
    return [condition for condition in conditions if not _holds(result, case, condition)]


def case_by_id(case_id: str) -> KillPointCase:
    """The case of `KILL_POINT_CASES` with `case_id`."""
    [case] = [case for case in KILL_POINT_CASES if case.id == case_id]
    return case
