---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Kill-point tests

## Assignment (as of log entry 1)

Prove recovery by injection. Six named cases, one per kill point of the recovery proof (the tick dies during an agent run; the agent run dies while the tick lives; the tick dies between a commit and its push; the tick dies between a post and its record; the tick dies at any other point; the container is lost), each drive a real work item through the real tick against a real local bare remote in `tmp_path`, the fake hosting client and the fake agent runtime, kill it at the kill point, restart with the same instance name and check the pass list of the crash class or of the stall class. The six cases are also data (`KILL_POINT_CASES`), so that the project guide, the document check of F0011-S0005 and the fault-injection paths of F0011-S0002 and F0011-S0003 name the same ids. The story also proves the two caps that repeated failures reach: the crash cap and the attempts cap. It covers WE1.1 and R36 and keeps kept thing 13 (recover by construction). The mechanisms under test were built by F0001 and F0004 to F0009; a scenario that fails is a defect to fix under `src/`, never a test to bend. WE1.4 (the baseline run) is not built tonight.

## Interface

`src/factory/domain/kill_point_cases.py`

```python
from typing import Literal

from pydantic import BaseModel, ConfigDict

from factory.domain.kill_points import KillPoint

Dies = Literal["tick", "agent-run", "container"]
ResultClass = Literal["crash", "stall"]


class KillPointCase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    dies: Dies
    kill_point: KillPoint | None
    result_class: ResultClass
    charges_crash: bool


KILL_POINT_CASES: tuple[KillPointCase, ...]
```

The six rows, in this order (`kill_point` is the `KillPoint` member with that name):

| id | dies | kill_point | result_class | charges_crash |
|---|---|---|---|---|
| `agent-run-tick` | tick | `AGENT_RUN` | crash | true |
| `agent-run-dies` | agent-run | none | stall | false |
| `commit-push` | tick | `BEFORE_PUSH` | crash | true |
| `post-record` | tick | `AFTER_POST` | crash | false |
| `tick-other` | tick | `AFTER_PUSH` | crash | true |
| `container` | container | `AGENT_RUN` | crash | true |

Rules of `KillPointCase` (each a `ValueError` from a model validator, so a `pydantic.ValidationError` for the caller):

- `kill_point` is `None` exactly when `result_class` is `"stall"`.
- a stall never charges a crash: `result_class == "stall"` requires `charges_crash` to be false.

The model is closed: `frozen=True` refuses the assignment of a field and `extra="forbid"` refuses an unknown key, each with a `pydantic.ValidationError`; a value outside `Dies`, outside `ResultClass` or outside `KillPoint` is refused with it too.

`charges_crash` is true exactly when a stage was in flight at the kill, that is, when its stage-start commit was pushed and its result commit was not.

`tests/proof_support.py` (written by the tester; no production module imports it; F0011-S0002, F0011-S0003 and F0011-S0004 import it too)

```python
MARKER: Final[str] = "interrupted-run-marker"
JOURNAL_LEAK: Final[str] = "interrupted-journal-edit"
KILL_TO_RERUN: Final[timedelta] = timedelta(seconds=5)
CRASH_CONDITIONS: Final[tuple[str, ...]] = (
    "resumes-at-first-tick", "kill-to-rerun-recorded", "no-repeated-post", "no-repeated-step",
    "no-interrupted-write-in-history", "stage-start-kept", "no-discarded-cost-record", "counters",
)
STALL_CONDITIONS: Final[tuple[str, ...]] = (
    "attempt-charged", "outside-writes-undone", "state-restored", "inside-writes-kept",
    "cost-record-kept",
)


@dataclass(frozen=True)
class World:
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
    world: World
    work_item: WorkItemId
    killed_point: KillPoint | None
    killed_at: datetime | None
    stage_start: CommitId | None


SCENARIOS: dict[str, Callable[[World], CaseResult]]


def build_world(root: Path) -> World: ...
def start_story(world: World, title: str = "Example") -> WorkItemId: ...
def leak_writes(world: World, work_item: WorkItemId, *, stage: str | None = None) -> dict[str, str]: ...
def completed(
    decision: str, entry: str = "ok", *, writes: dict[str, str] | None = None, kill: bool = False
) -> ScriptedRun: ...
def died(*, writes: dict[str, str] | None = None, kill: bool = False) -> ScriptedRun: ...
def run_ticks(world: World, count: int = 1) -> None: ...
def restart(world: World, *, empty_disk: bool = False) -> World: ...
def run_case(case: KillPointCase, root: Path) -> CaseResult: ...
def head_state(world: World, work_item: WorkItemId) -> WorkItemState: ...
def head_journal(world: World, work_item: WorkItemId) -> list[JournalRecord]: ...
def pull_request_of(world: World, work_item: WorkItemId) -> PullRequestView: ...
def posts(world: World, work_item: WorkItemId, kind: PostKind | None = None) -> list[PullRequestComment]: ...
def repeated_posts(world: World) -> list[str]: ...
def markers_in_history(world: World, work_item: WorkItemId) -> list[str]: ...
def violations(result: CaseResult, case: KillPointCase, conditions: Sequence[str]) -> list[str]: ...
```

`tests/conftest.py` gains one fixture, `world`, which returns `build_world(tmp_path)`.

How the helpers behave, as far as the criteria rely on it:

- `build_world(root)` builds one `World` under the directory `root`, with the instance name `factory-1`, in the way the shared fixtures of `tests/conftest.py` build theirs (`make_remote(root / "origin")`, a `GitCli` on a clone at `root / CHECKOUT` with `GitOptions(kill_points=<the world's>, identity=TEST_IDENTITY)`, a `FakeHostingService` and a `FakeAgentRuntime` on the same `KillPoints`, a `ManualClock` at the fixture's start, `HumanClone(root / "human", remote)`, `MakeProjectCommands`, the readers and writers, `TimestampedFactoryLog` and `JsonHealthStatusFile` under `state = root / "state"`), and with the agent home `root / "agent-home"` filled by `install_agents(agent_home, <the roles of PIPELINE_YAML>)` (`tests/git_support.py`): without the agent files `PipelineLoader` refuses the fixture's definition and every tick ends at the `pipeline_definition_invalid` stop. `World.remote` and `World.state` are the paths it built, and `World.tick` is the one `Tick` of the world (see `run_ticks`). It is the one place that builds a world; the `world` fixture and `run_case` call it.
- `start_story` writes a story that passes the story form and writes the next free id of the fixture's feature `F0001-example`: the first call replaces `backlog/F0001-S0001-first.md` at that path (the fixture's backlog story has form findings), each further call writes `backlog/F0001-S000<n>-<slug of the title>.md` for the number after the highest story number found in `backlog/`, `in-progress/` and `done/`. It pushes the file with `human.push_file("main", ...)`, moves it to `in-progress/` with `human.start` and returns its id, so that after it no story file remains in `backlog/` (a story file left there keeps the feature incomplete, F0009 decision 3).
- `leak_writes` returns the writes of an interrupted agent run: `src/leak.py` holding `MARKER` (outside every write path) and the work item's own file, changed in two places inside the write paths: `MARKER` as the last paragraph under `## Description`, and the line `JOURNAL_LEAK` as the last line under `## Journal`. The file is the work item's file as the next stage finds it: its text on `origin/<branch>` (after `world.boundaries.git.fetch()`) when that branch exists; before the work item's first tick, the file the opening writes: the body of the started story on `origin/main` with the section `## Journal` and entry 1 (as `WorkItemOpening` and `append_entry` make it), under front matter rendered by `FrontmatterWorkItemWriter` from `initial_state("intake")`. With `stage` given, the state's `stage` is replaced by it, so that the front matter reads `stage: <stage>`.
- `completed(decision, entry)` is a `ScriptedRun` whose result has `end_reason="completed"`, that decision and entry, a duration of one second and no turns, tokens or cost. `died()` is the same with `end_reason="died"`, no decision and no entry. `kill` is `ScriptedRun.kill` (F0001): the fake runtime applies the writes and then reaches the kill point `agent-run` only for a run queued with `kill=True`, so every run whose tick is said to raise at `AGENT_RUN` is queued with `kill=True`; the fake disarms a point when it fires, so a second kill at `AGENT_RUN` needs the point armed again.
- `run_ticks` calls `run()` `count` times on the world's one `Tick(world.boundaries, world.instance, handler_factory(world.boundaries, world.instance, agent_environment(<a scripts directory under the world's root>, <a home under the world's root>)))` (`factory.application.tick.Tick`, F0006-S0004; `handler_factory` and `agent_environment` of `factory.entry.wiring`, F0006-S0007, with the handlers that F0007-S0010, F0008-S0001, F0008-S0003 and F0009-S0010 register, so `NOT_YET_HANDLED` is empty); it does not advance the clock.
- `restart` returns a new `World`: a new `FakeAgentRuntime(world.kill_points)`, a new `Boundaries` over the same checkout directory and state directory (its `JsonHealthStatusFile` and `TimestampedFactoryLog` read and append the files already there) and the same instance name, and a new `Tick`, whose `TickStatus` starts empty (the tick status is a local cache, questionnaire 1, Q28); `remote`, `hosting`, `kill_points`, `clock` and `human` are kept. The checkout's git is `GitCli(<checkout>, GitOptions(kill_points=world.kill_points, identity=TEST_IDENTITY))`, as the built `checkout` fixture makes it. With `empty_disk=True` the checkout directory and the state directory are deleted first and the checkout is cloned again with `GitCli.clone(str(world.remote))`.
- `run_case(case, root)` builds a world with `build_world(root)`, plays `SCENARIOS[case.id]` on it and returns the world after the restart and three ticks (for a stall: after three ticks), the id of its work item, the kill point that fired, the clock reading at the kill and the stage-start commit that was newest at the kill. `tests/test_kill_points.py` calls it from a module-scoped fixture parametrized over the six ids, with `tmp_path_factory.mktemp(case.id)` as `root`, so each case runs once per module; a module-scoped fixture uses no function-scoped fixture.
- `head_state` and `head_journal` fetch and read the work item's file on `origin/<branch>` with `FrontmatterWorkItemReader`; `pull_request_of` returns the pull request of `branch_name(work_item)` from `hosting.pull_requests()`, in any state; `posts` returns the factory's comments on it (`hosting.factory_posts`), those of one kind when `kind` is given.

The scenarios (test inputs; "question run" is `completed("question", "Which format does the title take?")`; the stage is `intake`; every scenario starts with `start_story`):

- `agent-run-tick`: arm `AGENT_RUN`; queue a question run with `leak_writes` and `kill=True`; the first tick raises `InjectedKill`; read the clock; advance it by `KILL_TO_RERUN`; `restart`; queue a question run without writes; three ticks.
- `commit-push`: arm `BEFORE_PUSH` with `after=1` (the first push of a work item's first stage is its claim, the second is its result); queue a question run with `leak_writes` (no `kill`); the first tick raises `InjectedKill`; then as `agent-run-tick`.
- `container`: as `agent-run-tick`, restarted with `restart(world, empty_disk=True)`.
- `post-record`: arm `AFTER_POST`; queue a question run with `leak_writes` (no `kill`); the first tick that posts raises `InjectedKill`; advance the clock by `KILL_TO_RERUN`; `restart`; queue nothing; three ticks.
- `tick-other`: arm `AFTER_PUSH` with `after=0` (the claim's push); queue nothing; the first tick raises `InjectedKill`; advance the clock by `KILL_TO_RERUN`; `restart`; queue a question run without writes; three ticks.
- `agent-run-dies`: no kill; queue `died(writes=leak_writes(world, work_item, stage="doing"))`, then a question run without writes; three ticks.

Conditions (the names in `CRASH_CONDITIONS` and `STALL_CONDITIONS`; `violations` returns the names of those among `conditions` that do not hold):

- `resumes-at-first-tick`, `kill-to-rerun-recorded`, `no-repeated-post`, `no-repeated-step`, `no-interrupted-write-in-history`, `stage-start-kept`, `no-discarded-cost-record`, `counters`: the crash list, criteria 7 to 14.
- `attempt-charged`, `outside-writes-undone`, `state-restored`, `inside-writes-kept`, `cost-record-kept`: the stall list, criteria 17 to 21.

Tests: `tests/domain/test_kill_point_cases.py` (criteria 1 to 4); `tests/test_kill_points.py` (criteria 5 to 22), which parametrizes the crash criteria over the crash cases (criteria 9 and 10 over all six cases) and the stall criteria over `agent-run-dies`, and runs each case once per module through the module-scoped fixture over `run_case`; the helpers are in `tests/proof_support.py`.

## Acceptance criteria

1. `KILL_POINT_CASES` holds exactly the six rows of the table above, in that order, with those ids, `dies` values, kill points, classes and `charges_crash` values.
2. A `KillPointCase` with `result_class="stall"` and a kill point, and one with `result_class="crash"` and no kill point, are each rejected with `pydantic.ValidationError`; a stall without a kill point and a crash with one are accepted.
3. A `KillPointCase` with `result_class="stall"` and `charges_crash=True` is rejected with `pydantic.ValidationError`; the same stall with `charges_crash=False` is accepted.
4. A `KillPointCase` is a closed model: assigning a field of a built one (`setattr` with the field name in a variable) and an unknown key are each rejected with `pydantic.ValidationError`, and so are `dies="process"`, `result_class="error"` and `kill_point="never"`, each constructed through a variable typed `type[BaseModel]`.
5. `SCENARIOS` has a scenario for every id in `KILL_POINT_CASES` and for no other id.
6. In each of the five crash cases the armed kill point fires during the first tick that reaches it and leaves the tick as `InjectedKill`: `run_case` returns `killed_point == case.kill_point` (the handlers above the point, which catch `Exception`, do not swallow it).
7. After the restart, in the crash cases that charge a crash (`agent-run-tick`, `commit-push`, `tick-other`, `container`), the first tick makes the restarted fake agent runtime receive one request for the stage `intake`, with no human act in between; in `post-record` the restarted runtime has received no request after three ticks.
8. In the crash cases that charge a crash, the newest commit of `origin/<branch>` whose work item state carries a claim (the rerun's stage-start commit) has `claim.started_at` exactly 5 seconds after the clock reading taken at the kill, so no lease and no idle pause was waited out; the test computes `(claim.started_at - killed_at).total_seconds()`, records it with `record_property("kill_to_rerun_seconds", <that value>)` and asserts that it equals 5.0.
9. In each of the six cases the factory's posts on the work item's pull request hold exactly one post of kind `question`, and no post key occurs twice.
10. In each of the six cases the work item's journal at `origin/<branch>` holds exactly one record of kind `question`: the interrupted step is not written twice.
11. In `agent-run-tick`, `commit-push` and `container`, `MARKER` is in no commit reachable from any `origin/*` branch, in `src/leak.py` or in the work item's file; in the other three cases it is in no commit's `src/leak.py`.
12. In every crash case the stage-start commit that was newest at the kill is an ancestor of `origin/<branch>` at the end, and the journal holds a record of kind `started`.
13. In every crash case the work item's cost sidecar at `origin/<branch>` holds exactly one record, with status `completed` and stage `intake`: the record of the run that finished; the record of the interrupted run is in no commit reachable from any `origin/*` branch.
14. At the end of the crash cases `attempts` is 0, and `crashes` is 1 in the cases that charge a crash and 0 in `post-record`.
15. The proof helpers are not vacuous: on a world after `start_story` and one tick with a question run queued, with `CaseResult(world, work_item, None, None, None)`, a branch pushed by hand (`human.push_file`) whose `src/leak.py` holds `MARKER` makes `violations` name `no-interrupted-write-in-history`, and one factory-marked comment body added twice with `hosting.add_human_comment` makes `repeated_posts` name the key.
16. Two kills in one stage reach the crash cap of 2 (`test_tick_killed_during_agent_run_twice_reaches_crash_cap_and_asks_human`): arm `AGENT_RUN` and queue a question run with `kill=True`; the first tick raises; after a `restart` (clock advanced by `KILL_TO_RERUN`) the stage reruns: arm `AGENT_RUN` again, queue a question run with `kill=True`, the tick raises, the restarted runtime has received one request and no post of kind `crash_cap` exists; after a second `restart` the first tick sends the restarted runtime no request, `posts(..., "crash_cap")` holds exactly one post, `blocked` is `crash_cap` and `crashes` is 2; two more ticks add no post and no request.
17. In `agent-run-dies` the work item has `attempts == 1` in the commit that adds the `stall` record, its `stage` is still `intake`, and its journal holds exactly one record of kind `stall`.
18. In `agent-run-dies` `src/leak.py` is absent from the commit that adds the `stall` record and from `origin/<branch>` at the end.
19. In `agent-run-dies` the work item's state in the commit that adds the `stall` record has `stage == "intake"`: the run's edit to `doing` is undone; and its journal in that commit equals the journal of the stage-start commit plus the `stall` record, with `JOURNAL_LEAK` in no commit.
20. In `agent-run-dies` the paragraph holding `MARKER`, which the run wrote inside the write paths, is in the work item's file in the commit that adds the `stall` record and at the end.
21. In `agent-run-dies` the cost sidecar in the commit that adds the `stall` record holds one record with status `completed`, `end_reason == "died"` and a duration of one second, and its `turns`, `tokens` and `cost_usd` are all `None` (unknown, never 0).
22. On a world after `start_story`, with `attempts_cap` 2 and two `died()` runs queued: after the first tick `attempts` is 1 and no post of kind `attempts_cap` exists; after the second tick `attempts` is 2 and no post of kind `attempts_cap` exists (the `ask` handler records and posts the question on the next tick); after the third tick `blocked` is `attempts_cap`, exactly one post of kind `attempts_cap` exists and the runtime has received 2 requests; two more ticks add no request and no post.
23. make check stays green.
24. docs: `docs/project-guide.md` renames its section `## Kill points: testing a crash` to `## Kill points` and adds there a table with one row per case (id, what dies, class, whether it charges a crash) as `` `agent-run-tick` ``-style ids, and how to run `tests/test_kill_points.py`; `docs/decisions.md` records that the proof is injection only, that a kill after a stage's result is pushed charges no crash, and that the time from kill to rerun is measured on the manual clock. README and operator guide are untouched.

## Demo

```bash
uv run python -c "
from factory.domain.kill_point_cases import KILL_POINT_CASES
for c in KILL_POINT_CASES:
    print(c.id, c.dies, c.kill_point.value if c.kill_point else '-', c.result_class, c.charges_crash)
"
```
Expect: six lines, `agent-run-tick tick agent-run crash True`, `agent-run-dies agent-run - stall False`, `commit-push tick before-push crash True`, `post-record tick after-post crash False`, `tick-other tick after-push crash True`, `container container agent-run crash True`.

```bash
uv run python -c "
from pydantic import ValidationError
from factory.domain.kill_point_cases import KillPointCase
for kwargs in (
    dict(kill_point='agent-run', result_class='stall', charges_crash=False),
    dict(kill_point=None, result_class='crash', charges_crash=True),
    dict(kill_point=None, result_class='stall', charges_crash=True),
):
    try:
        KillPointCase(id='x', dies='tick', **kwargs)
        print('accepted')
    except ValidationError:
        print('rejected')
"
```
Expect: three lines, each `rejected`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_kill_points.py tests/domain/test_kill_point_cases.py
```
Expect: the last line reports `passed` and neither `failed` nor `error`.

## Log (append only)

1. 2026-10-12 human: created.
