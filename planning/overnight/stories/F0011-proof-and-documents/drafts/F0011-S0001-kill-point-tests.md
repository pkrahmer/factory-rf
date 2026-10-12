# Kill-point tests

## Assignment (as of log entry 1)

Prove recovery by injection. Six named cases, one per kill point of the recovery proof (the tick dies during an agent run; the agent run dies while the tick lives; the tick dies between a commit and its push; the tick dies between a post and its record; the tick dies at any other point; the container is lost), each drive a real work item through the real tick against a real local bare remote in `tmp_path`, the fake hosting client and the fake agent runtime, kill it at the kill point, restart with the same instance name and check the pass list of the crash class or of the stall class. The six cases are also data (`KILL_POINT_CASES`), so that the project guide, the document check of F0011-S0004 and the fault-injection paths of F0011-S0002 name the same ids. The story also proves the two caps that repeated failures reach: the crash cap and the attempts cap. It covers WE1.1 and R36 and keeps kept thing 13 (recover by construction). The mechanisms under test were built by F0001, F0004, F0005, F0007 and F0008; a scenario that fails is a defect to fix under `src/`, never a test to bend. WE1.4 (the baseline run) is not built tonight.

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

`charges_crash` is true exactly when a stage was in flight at the kill, that is, when its stage-start commit was pushed and its result commit was not.

`tests/proof_support.py` (written by the tester; no production module imports it; F0011-S0002 and F0011-S0003 import it too)

```python
MARKER: Final[str] = "interrupted-run-marker"
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
    instance: str


@dataclass(frozen=True)
class CaseResult:
    world: World
    work_item: WorkItemId
    killed_point: KillPoint | None
    killed_at: datetime | None
    stage_start: CommitId | None


SCENARIOS: dict[str, Callable[[World], CaseResult]]


def start_story(world: World, title: str = "Example") -> WorkItemId: ...
def leak_writes(world: World, work_item: WorkItemId, *, stage: str | None = None) -> dict[str, str]: ...
def completed(decision: str, entry: str = "ok", *, writes: dict[str, str] | None = None) -> ScriptedRun: ...
def died(*, writes: dict[str, str] | None = None) -> ScriptedRun: ...
def run_ticks(world: World, count: int = 1) -> None: ...
def restart(world: World, *, empty_disk: bool = False) -> World: ...
def run_case(case: KillPointCase, world: World) -> CaseResult: ...
def head_state(world: World, work_item: WorkItemId) -> WorkItemState: ...
def head_journal(world: World, work_item: WorkItemId) -> list[JournalRecord]: ...
def pull_request_of(world: World, work_item: WorkItemId) -> PullRequestView: ...
def posts(world: World, work_item: WorkItemId, kind: PostKind | None = None) -> list[PullRequestComment]: ...
def repeated_posts(world: World) -> list[str]: ...
def markers_in_history(world: World, work_item: WorkItemId) -> list[str]: ...
def violations(result: CaseResult, case: KillPointCase, conditions: Sequence[str]) -> list[str]: ...
```

`tests/conftest.py` gains one fixture, `world`, a `World` over the shared fixtures `boundaries`, `hosting`, `agent_runtime`, `kill_points`, `clock` and `human`, with the instance name `factory-1`.

How the helpers behave, as far as the criteria rely on it:

- `start_story` writes a story that passes the story form into the fixture's feature folder under `backlog/`, pushes it, moves it to `in-progress/` with `human.start` and returns its id.
- `leak_writes` returns the writes of an interrupted agent run: `src/leak.py` holding `MARKER` (outside every write path) and the work item's own file with one extra paragraph holding `MARKER` under `## Description` (inside the write paths); with `stage="doing"` the work item's `stage:` line in that file reads `doing` too.
- `completed(decision, entry)` is a `ScriptedRun` whose result has `end_reason="completed"`, that decision and entry, a duration of one second and no turns, tokens or cost. `died()` is the same with `end_reason="died"`, no decision and no entry.
- `run_ticks` runs `count` ticks of the tick service of F0006-S0004 (`factory.application.tick`), wired with the handlers of F0005 to F0009 as `factory.entry.wiring` wires them, against `world.boundaries`; it does not advance the clock.
- `restart` returns a new `World`: new run record, health status and tick status stores, a new `FakeAgentRuntime`, a new `Boundaries` over the same checkout directory and state directory and the same instance name; `remote`, `hosting`, `kill_points` and `clock` are kept. With `empty_disk=True` the checkout directory and the state directory are deleted first and the checkout is cloned again from the remote with `GitCli.clone`.
- `run_case` plays `SCENARIOS[case.id]` on a fresh world and returns the world after the restart and three ticks (for a stall: after three ticks), the id of its work item, the kill point that fired, the clock reading at the kill and the stage-start commit that was newest at the kill.

- `head_state` and `head_journal` fetch and read the work item's file on `origin/<branch>` with `FrontmatterWorkItemReader`; `pull_request_of` returns the pull request of `branch_name(work_item)` from `hosting.pull_requests()`, in any state; `posts` returns the factory's comments on it (`hosting.factory_posts`), those of one kind when `kind` is given.

The scenarios (test inputs; "question run" is `completed("question", "Which format does the title take?")`; the stage is `intake`; every scenario starts with `start_story`):

- `agent-run-tick`: arm `AGENT_RUN`; queue a question run with `leak_writes`; the first tick raises `InjectedKill`; read the clock; advance it by `KILL_TO_RERUN`; `restart`; queue a question run without writes; three ticks.
- `commit-push`: as `agent-run-tick`, with `BEFORE_PUSH` armed with `after=1` (the first push of a work item's first stage is its claim, the second is its result).
- `container`: as `agent-run-tick`, restarted with `restart(world, empty_disk=True)`.
- `post-record`: arm `AFTER_POST`; queue a question run with `leak_writes`; the first tick that posts raises `InjectedKill`; advance the clock by `KILL_TO_RERUN`; `restart`; queue nothing; three ticks.
- `tick-other`: arm `AFTER_PUSH` with `after=0` (the claim's push); queue nothing; the first tick raises `InjectedKill`; advance the clock by `KILL_TO_RERUN`; `restart`; queue a question run without writes; three ticks.
- `agent-run-dies`: no kill; queue `died(writes=leak_writes(world, work_item, stage="doing"))`, then a question run without writes; three ticks.

Conditions (the names in `CRASH_CONDITIONS` and `STALL_CONDITIONS`; `violations` returns the names of those among `conditions` that do not hold):

- `resumes-at-first-tick`, `kill-to-rerun-recorded`, `no-repeated-post`, `no-repeated-step`, `no-interrupted-write-in-history`, `stage-start-kept`, `no-discarded-cost-record`, `counters`: the crash list, criteria 6 to 13.
- `attempt-charged`, `outside-writes-undone`, `state-restored`, `inside-writes-kept`, `cost-record-kept`: the stall list, criteria 16 to 20.

Tests: `tests/domain/test_kill_point_cases.py` (criteria 1 to 3); `tests/test_kill_points.py` (criteria 4 to 21), which parametrizes the crash criteria over the crash cases and the stall criteria over `agent-run-dies`, and runs each case once per module through a module-scoped use of `run_case`; the helpers are in `tests/proof_support.py`.

## Acceptance criteria

1. `KILL_POINT_CASES` holds exactly the six rows of the table above, in that order, with those ids, `dies` values, kill points, classes and `charges_crash` values.
2. A `KillPointCase` with `result_class="stall"` and a kill point, and one with `result_class="crash"` and no kill point, are each rejected with `pydantic.ValidationError`; a stall without a kill point and a crash with one are accepted.
3. A `KillPointCase` with `result_class="stall"` and `charges_crash=True` is rejected with `pydantic.ValidationError`; the same stall with `charges_crash=False` is accepted.
4. `SCENARIOS` has a scenario for every id in `KILL_POINT_CASES` and for no other id.
5. In each of the five crash cases the armed kill point fires during the first tick that reaches it and leaves the tick as `InjectedKill`: `run_case` returns `killed_point == case.kill_point` (the handlers above the point, which catch `Exception`, do not swallow it).
6. After the restart, in the crash cases that charge a crash (`agent-run-tick`, `commit-push`, `tick-other`, `container`), the first tick makes the restarted fake agent runtime receive one request for the stage `intake`, with no human act in between; in `post-record` the restarted runtime has received no request after three ticks.
7. In the crash cases that charge a crash, the newest commit of `origin/<branch>` whose work item state carries a claim (the rerun's stage-start commit) has `claim.started_at` exactly 5 seconds after the clock reading taken at the kill, so no lease and no idle pause was waited out; the test records that difference with `record_property("kill_to_rerun_seconds", 5.0)`.
8. In every case the factory's posts on the work item's pull request hold exactly one post of kind `question`, and no post key occurs twice.
9. In every case the work item's journal at `origin/<branch>` holds exactly one record of kind `question`: the interrupted step is not written twice.
10. In `agent-run-tick`, `commit-push` and `container`, `MARKER` is in no commit reachable from any `origin/*` branch, in `src/leak.py` or in the work item's file; in the other three cases it is in no commit's `src/leak.py`.
11. In every crash case the stage-start commit that was newest at the kill is an ancestor of `origin/<branch>` at the end, and the journal holds a record of kind `started`.
12. In every crash case the work item's cost sidecar at `origin/<branch>` holds exactly one record, with status `completed` and stage `intake`: the record of the run that finished; the record of the interrupted run is in no commit.
13. At the end of the crash cases `attempts` is 0, and `crashes` is 1 in the cases that charge a crash and 0 in `post-record`.
14. The proof helpers are not vacuous: with a branch pushed by hand whose `src/leak.py` holds `MARKER`, and one factory-marked comment body added twice with `hosting.add_human_comment`, `violations` names `no-interrupted-write-in-history`, and `repeated_posts` names the key.
15. Two kills in one stage reach the crash cap of 2 (`test_tick_killed_during_agent_run_twice_reaches_crash_cap_and_asks_human`): after the first kill and a restart the stage reruns and no post of kind `crash_cap` exists; after a second kill during that rerun and a restart, the first tick sends the restarted runtime no request, `posts(..., "crash_cap")` holds exactly one post, `blocked` is `crash_cap` and `crashes` is 2; two more ticks add no post and no request.
16. In `agent-run-dies` the work item has `attempts == 1` in the commit that adds the `stall` record, its `stage` is still `intake`, and its journal holds exactly one record of kind `stall`.
17. In `agent-run-dies` `src/leak.py` is absent from the commit that adds the `stall` record and from `origin/<branch>` at the end.
18. In `agent-run-dies` the work item's state in the commit that adds the `stall` record has `stage == "intake"`: the run's edit to `doing` is undone.
19. In `agent-run-dies` the paragraph holding `MARKER`, which the run wrote inside the write paths, is in the work item's file in the commit that adds the `stall` record and at the end.
20. In `agent-run-dies` the cost sidecar in the commit that adds the `stall` record holds one record with status `completed`, `end_reason == "died"` and a duration of one second, and its `turns`, `tokens` and `cost_usd` are all `None` (unknown, never 0).
21. With `attempts_cap` 2: after one `died` run `attempts` is 1 and no post of kind `attempts_cap` exists; after the second `died` run on the next tick `attempts` is 2, `blocked` is `attempts_cap`, exactly one post of kind `attempts_cap` exists and the runtime has received 2 requests; two more ticks add no request and no post.
22. make check stays green.
23. docs: `docs/project-guide.md` gets the section *Kill points*, a table with one row per case (id, what dies, class, whether it charges a crash) as `` `agent-run-tick` ``-style ids, and how to run `tests/test_kill_points.py`; `docs/decisions.md` records that the proof is injection only, that a kill after a stage's result is pushed charges no crash, and that the time from kill to rerun is measured on the manual clock. README and operator guide are untouched.

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
uv run pytest tests/test_kill_points.py tests/domain/test_kill_point_cases.py -q -p no:cacheprovider
```
Expect: the last line reports `passed` and neither `failed` nor `error`.

## Log (append only)

1. 2026-10-12 human: created.
