---
stage: review
pr: 145
blocked: asked
comments_seen: 3
round: 3
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

Tests: `tests/domain/test_kill_point_cases.py` (criteria 1 to 4); `tests/test_kill_points.py` (criteria 5 to 22), which parametrizes the crash criteria over the crash cases (criteria 9, 10 and 11 over all six cases) and the stall criteria over `agent-run-dies`, and runs each case once per module through the module-scoped fixture over `run_case`; the helpers are in `tests/proof_support.py`.

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
2. intake: accepted
   - Interface: `factory.domain.kill_point_cases` gives the full `KillPointCase` model, the six-row table, both validator rules and the closed-model rules. `tests/proof_support.py` gives helper signatures and scenario scripts. Every `KillPoint` member it names (`AGENT_RUN`, `BEFORE_PUSH`, `AFTER_POST`, `AFTER_PUSH`) exists in `factory/domain/kill_points.py`.
   - Criteria: 1-4 cover the table and the model rules, including the failing side of each (stall with a kill point, crash without one, stall that charges a crash, unknown key, assignment, bad values). 5-14 and 16-22 each pin one observable result, and the crash cap (16) and attempts cap (22) are covered. 15 checks the helpers are not vacuous. Every behaviour stated in the Interface comments has a criterion: the 5-second kill-to-rerun gap (8), the `charges_crash` rule (7 and 14), the stall undo and keep rules (17-21). 23 and 24 are the closing criteria.
   - Demo: the three commands are runnable, and each `Expect:` line gives output that can be checked (six named lines; three `rejected`; a pytest `passed` last line).
   - Architecture: the case data sits in `factory.domain` and is pure. The proof helpers sit in `tests/` and no production module imports them. Tests keep to the layout in `CLAUDE.md`: a real bare remote, the fake hosting service and the fake agent runtime, no fake git.
   - Scope: this is the first story of F0011 and falls under its "kill-point cases and the two caps" scope item. The baseline run (WE1.4), a real container kill and the document check are not touched.
3. tester: red tests for the kill-point cases, the recovery proof and both caps.

   Criterion → test:
   - criterion 1: tests/domain/test_kill_point_cases.py::test_the_cases_are_the_six_rows_in_order
   - criterion 2: tests/domain/test_kill_point_cases.py::test_a_kill_point_is_given_exactly_for_a_crash (4 rows: stall with point, crash without, stall without, crash with)
   - criterion 3: tests/domain/test_kill_point_cases.py::test_a_stall_never_charges_a_crash (charges / free)
   - criterion 4: tests/domain/test_kill_point_cases.py::test_an_assignment_to_a_built_case_is_refused, ::test_a_case_outside_the_closed_model_is_refused (unknown key, dies="process", result_class="error", kill_point="never")
   - criterion 5: tests/test_kill_points.py::test_every_case_has_a_scenario_and_no_other_id_has_one
   - criterion 6: tests/test_kill_points.py::test_the_armed_kill_point_ends_the_tick_that_reaches_it (5 crash cases)
   - criterion 7: tests/test_kill_points.py::test_the_restarted_factory_reruns_a_charged_stage_at_its_first_tick (5 crash cases; post-record expects no request)
   - criterion 8: tests/test_kill_points.py::test_the_rerun_starts_five_seconds_after_the_kill (4 charging cases; record_property("kill_to_rerun_seconds", …))
   - criterion 9: tests/test_kill_points.py::test_the_question_is_posted_once_and_no_post_is_repeated (all 6)
   - criterion 10: tests/test_kill_points.py::test_the_interrupted_step_is_journalled_once (all 6)
   - criterion 11: tests/test_kill_points.py::test_no_write_of_the_interrupted_run_reaches_the_remote
   - criterion 12: tests/test_kill_points.py::test_the_stage_start_of_the_kill_is_kept
   - criterion 13: tests/test_kill_points.py::test_only_the_cost_record_of_the_finished_run_is_kept
   - criterion 14: tests/test_kill_points.py::test_a_crash_charges_a_crash_only_while_a_stage_was_in_flight
   - criterion 15: tests/test_kill_points.py::test_the_proof_helpers_find_a_leaked_marker_and_a_repeated_post
   - criterion 16: tests/test_kill_points.py::test_tick_killed_during_agent_run_twice_reaches_crash_cap_and_asks_human
   - criterion 17: tests/test_kill_points.py::test_a_died_run_charges_one_attempt_and_keeps_the_stage
   - criterion 18: tests/test_kill_points.py::test_a_died_run_loses_its_writes_outside_the_write_paths
   - criterion 19: tests/test_kill_points.py::test_a_died_run_loses_its_edits_of_state_and_journal
   - criterion 20: tests/test_kill_points.py::test_a_died_run_keeps_its_writes_inside_the_write_paths
   - criterion 21: tests/test_kill_points.py::test_a_died_run_keeps_its_cost_record_with_unknown_usage
   - criterion 22: tests/test_kill_points.py::test_two_died_runs_reach_the_attempts_cap_and_ask_the_human
   - criteria 23 and 24: these are for the coder and the documenter, so there are no tests for them.

   Files:
   - Created tests/domain/test_kill_point_cases.py, tests/test_kill_points.py and tests/proof_support.py.
   - Changed tests/conftest.py: it now has the `world` fixture, which returns `build_world(tmp_path)`.

   proof_support follows the Interface. These parts go beyond what the Interface names:
   - Extra private helpers, plus one public helper, `case_by_id`.
   - `violations` dispatches through two tables of small check functions, one for crashes and one for stalls.
   - `markers_in_history` returns `<commit>:<path>` strings. It looks at every commit from `git rev-list --remotes=origin`, run through `run_git` in the checkout.
   - `repeated_posts` returns the key lines (`PostKey.comment()`).
   - The "stage-start commit" is the newest commit on the branch whose work item state has a `claim`.
   - The commit that adds the stall is the oldest commit on the branch whose journal has a `stall` record.
   - In `post-record` the kill is expected within the first three ticks. The question post may only happen on the tick after the run.

   The module-scoped fixture `result` in test_kill_points.py is parametrized indirectly over case ids, so each case runs once per module.

   Import failures: `make test` stops at collection with `ModuleNotFoundError: No module named 'factory.domain.kill_point_cases'`. tests/conftest.py imports proof_support, so the whole suite is red until the coder adds that module.

   `make lint` is green. I skipped the type check as the stage says, so `make types` on these files is still unchecked.

   `make lint`: lint: green
   `make test`: E   ModuleNotFoundError: No module named 'factory.domain.kill_point_cases'
4. coder: the domain module is done, but two helpers in `tests/proof_support.py` contradict tested `src/` behaviour, so every case of `tests/test_kill_points.py` errors before it reaches the code under test.

   Built: `src/factory/domain/kill_point_cases.py` (commit 1599e19). It holds `KillPointCase` with its two model validators (a kill point exactly for a crash; a stall never charges a crash) and the six `KILL_POINT_CASES` rows. `tests/domain/test_kill_point_cases.py` passes (12 tests), and ruff and mypy --strict pass on both files.

   The two contradictions:
   1. `leak_writes` (`tests/proof_support.py:261`) calls `git.show_file("origin/work-item/F0001-S0001", path)` before the branch exists and expects `None` back. `GitCli.show_file` raises `GitError` for a missing ref. `tests/adapters/test_git_cli_reading.py::test_show_file_returns_none_for_no_file_and_raises_for_a_missing_ref` pins that, and so does the `Git` interface ("`None` when it is not a file there").
   2. `_state_at` (used by `_claim_commits` and `head_state`) calls `work_item_reader.parse` on every commit of `git.log("origin/<branch>", path=...)`. That log includes the commits on `main` where the story has no front matter yet, so `FrontmatterWorkItemReader.parse` raises `WorkItemFormatError("no front matter")`. `tests/adapters/test_work_item_markdown.py:208` pins that error.

   To check that nothing else blocks, I ran the module with a scratch pytest plugin outside the repository (nothing committed, no test file touched). It made `show_file` return `None` for a missing `origin/work-item/*` ref and made `_state_at` skip commits without front matter. With those two fixes all 55 tests in `tests/test_kill_points.py` pass against the current `src/`. No `src/` defect showed up.

   Options:
   - (a) The tester fixes the two helpers. `leak_writes` checks `git.resolve(f"origin/{branch}")` before `show_file`. `_state_at` returns `None` for a file without front matter, by catching `WorkItemFormatError`, or by checking `parse_specification`/front matter first, or by logging only `origin/main..origin/<branch>`.
   - (b) I change `GitCli.show_file` to return `None` for a missing ref, and `parse` to return a state-less document. That breaks two existing tests and the documented interface.

   I would choose (a). Once you answer, I end with `tests` and name exactly these two helper changes.

   Not done yet, because `make check` is red until then: the refactor pass and the final `make check`.
5. human (pull request comment, 2026-10-16): (a). The tester fixes the two helpers in `tests/proof_support.py`; `src/` and the existing tests stay as they are. `leak_writes` checks that the branch exists (`git.resolve(f"origin/{branch}")`) before `show_file`. `_state_at` reads only the branch's own commits (`origin/main..origin/<branch>`) or treats a text without front matter as no state; the tester picks one, with no catch-all.
6. coder: the human chose (a) in entry 5, so the fix belongs in the test helpers. I changed no test and no `src/`. The tester makes two changes in `tests/proof_support.py`:
   1. In `leak_writes` (line 261), only call `boundaries.git.show_file(f"origin/{branch}", path)` when `boundaries.git.resolve(f"origin/{branch}")` finds the branch. When it doesn't, use the opening file from `origin/main`, as the Interface describes.
   2. Stop `_state_at` (line 336) from parsing commits where the work item file has no front matter. Either have its callers log only `origin/main..origin/<branch>`, or treat a text without front matter as no state (`None`). The tester picks one, with no catch-all `except`.

   Why: `GitCli.show_file` raises `GitError` for a missing ref, and `FrontmatterWorkItemReader.parse` raises `WorkItemFormatError` for a file with no front matter. Both are pinned by existing adapter tests (`tests/adapters/test_git_cli_reading.py`, `tests/adapters/test_work_item_markdown.py:208`).

   Status: `src/factory/domain/kill_point_cases.py` is done (commit 1599e19), and `tests/domain/test_kill_point_cases.py` passes. With the two fixes simulated in a scratch plugin outside the repository, all 55 tests in `tests/test_kill_points.py` passed against the current `src/`.

   Still open for my next round: the refactor pass and the final `make check`.
7. tester: made the two helper changes in `tests/proof_support.py` that the human approved in entry 5, as the coder named them in entry 6. I changed no other test and nothing under `src/`.

   1. `leak_writes` now calls `git.resolve(f"origin/{branch}")` first. It reads the file with `show_file` only if the branch exists. If it does not, it falls back to the opening text from `origin/main`, as it did before for `None`.
   2. For `_state_at` I chose the first option the human offered: read only the branch's own commits. `_claim_commits` and `_stall_commit` now call `git.log(..., since=MAIN, path=...)` with a new constant `MAIN = "origin/main"`. `_state_at` itself is unchanged and there is no `except`. I didn't pick "a text without front matter is no state" because that would mean either a catch or a second front-matter check next to the reader's own. The other `_state_at` callers read the branch head or commits already taken from the branch, so main's front-matter-less story never reaches them. I updated the docstrings of both helpers to say they read the branch's own commits.

   `make test`: green, total coverage 99.55 %. `make lint`: green.

   `make lint`: lint: green
   `make test`: test: green
8. coder: `make check` is green on the branch with the tester's helper fixes from entry 7. All the `src/` work for this story is the domain module from commit 1599e19.

   Built: `src/factory/domain/kill_point_cases.py`. It holds the `Dies` and `ResultClass` literals and the closed, frozen `KillPointCase` model. The model has two `mode="after"` validators: a kill point is given exactly when the class is crash, and a stall never charges a crash. The module also holds the six `KILL_POINT_CASES` rows in the order the Interface gives. One comment explains why `post-record` charges no crash: the kill comes after the stage's result is pushed.

   Recovery proof: no `src/` defect showed up. All of `tests/test_kill_points.py` passes against the existing tick, recovery, claim and cap code. Criteria 6 to 22, including the crash cap and the attempts cap, hold without any production change.

   Main design decision: two separate model validators, one per rule in the Interface, each with its own message. I rejected a single combined validator because it would mix the two refusal reasons.

   Refactor pass: I read `git diff main...HEAD -- . ':!factory' ':!tests'`. Outside the 84-line domain module, the only differences are the human's own files (`CLAUDE.md`, `planning/`, `docs/runs/`), which came in through the merges from main. Nothing needed renaming, simplifying or removing, so there is no refactor commit.

   Checks: all `make check` targets are green (lint, types, layers, sast, secrets, licenses, test), with coverage at 99.55 %.

   Open: criterion 24 (the project guide's `## Kill points` table and the `docs/decisions.md` entry) is the documenter's job. I did not touch it.

   `make check`: check: green
9. reviewer: two findings, both in group 1 (acceptance criteria). The tests need changing and the coder may not edit them (R9), so the coder should end with `tests` and name these two changes. `src/factory/domain/kill_point_cases.py` matches the Interface: the six rows in order, both validators, frozen and closed. Criteria 1–6, 8–10 and 12–22 have tests that check what they claim to. The changes to `CLAUDE.md`, `planning/` and `docs/runs/` in the diff are the human's own commits on the branch, so I did not review them. I stopped at group 1 and did not go on to architecture, security or quality.

   1. `tests/proof_support.py:521` (`_resumes_at_first_tick`), used by `tests/test_kill_points.py::test_the_restarted_factory_reruns_a_charged_stage_at_its_first_tick`. Criterion 7 says the rerun request comes at the *first* tick after the restart. The check only looks at `requests()` after all three ticks in `_rerun` (`proof_support.py:382`). Because `run_ticks` never moves the clock, the 5-second check of criterion 8 cannot tell the ticks apart either. So a factory that reruns at the second or third tick would still pass. Fix: in `_rerun`, run one tick, take a copy of `restarted.agent_runtime.requests()`, then run the other two ticks, and have the condition check that copy. That means adding a field to `CaseResult` beyond the Interface, which the tester should state in their entry.
   2. `tests/test_kill_points.py`, `test_no_write_of_the_interrupted_run_reaches_the_remote` is parametrized `@_over(CRASHES)`. Criterion 11 says that in "the other three cases" (`post-record`, `tick-other` and `agent-run-dies`) `MARKER` is in no commit's `src/leak.py`. `agent-run-dies` never runs this test. Criterion 18 only checks the stall commit and the branch end, not every commit. Fix: parametrize this test over `ALL`. `_no_interrupted_write_in_history` already filters to `src/leak.py` when `kill_point` is `None`. Note for the human: the Interface (ticket line 151, "the crash criteria over the crash cases") contradicts criterion 11 here. I'm treating criterion 11 as the one that counts.
10. coder: round 1. Both of the reviewer's findings in entry 9 are test changes, and the coder may not edit tests (R9), so this goes back to the tester. I changed nothing under `src/` or `tests/`. `src/factory/domain/kill_point_cases.py` (commit 1599e19) stays as it is.

    The tester makes exactly these two changes:
    1. Criterion 7, "first tick": in `tests/proof_support.py`, `_rerun` (line 382) runs one tick, saves a copy of `restarted.agent_runtime.requests()` in a new `CaseResult` field, then runs the remaining two ticks. `_resumes_at_first_tick` (line 521) checks that saved copy, not the requests after all three ticks. The new field goes beyond the Interface, and the tester's entry should say so.
    2. Criterion 11: in `tests/test_kill_points.py`, `test_no_write_of_the_interrupted_run_reaches_the_remote` is parametrized `@_over(ALL)` instead of `@_over(CRASHES)`, so `agent-run-dies` is covered too. `_no_interrupted_write_in_history` already limits itself to `src/leak.py` when `kill_point` is `None`.

    On finding 2, the Interface (ticket line 151, "the crash criteria over the crash cases") contradicts criterion 11, which names `agent-run-dies` explicitly. I go with the reviewer: criterion 11 wins, because it is the more specific statement and it is the one the acceptance checks against. If the human wants the Interface sentence brought in line, that is a ticket text edit for the next doing round.

    Expectation: neither change should need a `src/` change. Criterion 11 for `agent-run-dies` already overlaps with criterion 18, which passes, and the restart path reruns in its first tick by construction. If either one goes red, it is a `src/` defect and I fix it in the next doing round.
11. tester: made the two test changes the reviewer asked for in entry 9 and the coder named in entry 10. Nothing else changed: no other test and nothing under `src/`. An earlier tester run that was interrupted had already committed both changes in 8469746 ("work left uncommitted by an interrupted run"). I checked that diff against entry 10 line by line and it matches. This run adds no new edits.

    1. Criterion 7, "first tick": `tests/proof_support.py::_rerun` now runs one tick and saves `tuple(restarted.agent_runtime.requests())` in a new `CaseResult` field. Then it runs the other two ticks. `_resumes_at_first_tick` now checks that saved copy instead of the requests after all three ticks, so a factory that reruns only at its second or third tick fails. The new field is `CaseResult.first_tick_requests: tuple[AgentRunRequest, ...] = ()`. It goes beyond the Interface and is a test-helper field only. It defaults to empty for scenarios that don't go through `_rerun`.
    2. Criterion 11: `tests/test_kill_points.py::test_no_write_of_the_interrupted_run_reaches_the_remote` is now parametrized `@_over(ALL)` instead of `@_over(CRASHES)`, so `agent-run-dies` is covered too. `_no_interrupted_write_in_history` already limits itself to `src/leak.py` when `kill_point` is `None`.

    Still open: the ticket's Interface sentence "the crash criteria over the crash cases" (ticket line 151) still contradicts criterion 11. As entry 10 says, fixing that is a text edit to the ticket for the human or the next doing round, not a test change.

    `make test`: green, total coverage 99.55 %. `make lint`: green.

    `make lint`: lint: green
    `make test`: test: green
12. coder: round 1. The two findings from entry 9 are handled. Both were test changes, and the tester made them in entry 11 (commit 8469746). I didn't edit any tests or anything under `src/` this round. `src/factory/domain/kill_point_cases.py` (commit 1599e19) stays as it was.

    - Finding 1 (criterion 7, "first tick"): `_rerun` now saves `CaseResult.first_tick_requests` after the first tick, and `_resumes_at_first_tick` checks that saved copy. No `src/` change was needed: the restarted factory reruns the stage at its first tick.
    - Finding 2 (criterion 11 over `agent-run-dies`): `test_no_write_of_the_interrupted_run_reaches_the_remote` now runs over all six cases. It passes against the current `src/`.

    Ticket text: the Interface's Tests sentence (line 151) said "criteria 9 and 10 over all six cases", which contradicted criterion 11. I changed it to "criteria 9, 10 and 11 over all six cases", as entry 10 proposed. The Assignment and the criteria are unchanged. That edit is left in the working tree for the factory's commit.

    Refactor pass: there is no new `src/` diff this round, so I have nothing to refactor and no refactor commit.

    Open: criterion 24 (the docs) is still for the documenter.

    `make check`: check: green (coverage 99.55 %)

    `make check`: check: green
13. reviewer: round 1. One finding, in group 1 (acceptance criteria). The fix for it is a test change, and the coder may not edit tests (R9), so the coder should end with `tests` and name this change.

    The two findings from entry 9 are fixed. The tester made both changes in 8469746, and I checked them against the code:
    - `_rerun` (`tests/proof_support.py:383-385`) saves `first_tick_requests` after the first tick.
    - `test_no_write_of_the_interrupted_run_reaches_the_remote` is parametrized `@_over(ALL)`.

    `src/factory/domain/kill_point_cases.py` still matches the Interface: the six rows in order, both validators, frozen and closed. These criteria have tests that check what they claim to:
    - 1–6, 8–15 and 17–22.
    - 16 against the fixture's `crash_cap: 2`.
    - 22 against the fixture's `attempts_cap: 2`.

    I stopped at group 1, so groups 2 to 5 are not reviewed. The diff's changes to `CLAUDE.md`, `planning/` and `docs/runs/` come from the human's own commits, so I did not review them.

    1. `tests/proof_support.py:524-526` (`_resumes_at_first_tick`), used by `tests/test_kill_points.py::test_the_restarted_factory_reruns_a_charged_stage_at_its_first_tick[post-record]`.
       - What is wrong: criterion 7 says that in `post-record` the restarted runtime has received no request *after three ticks*. Since the round-1 change, the check for a case that charges no crash compares only `first_tick_requests` (taken after one tick) with `[]`. A factory that wrongly reran the stage at the second or third tick would still pass this test. The fake runtime records requests that raise as well (`fake_agent_runtime.py:40`), so a rerun would show up in `requests()`.
       - Fix: keep `first_tick_requests == [STAGE]` for a case that charges a crash. For a case that does not, check `result.world.agent_runtime.requests() == []`, which is the restarted runtime after all three ticks.
14. coder: round 2. The reviewer's one finding in entry 13 is a change to a test helper. The coder may not edit tests (R9), so this goes back to the tester. I changed nothing under `src/` or `tests/`. `src/factory/domain/kill_point_cases.py` (commit 1599e19) stays as it is.

    The tester makes exactly this change. In `tests/proof_support.py::_resumes_at_first_tick` (lines 524-526), split the check by `case.charges_crash`:
    - If the case charges a crash, keep the current check: the stage names in `result.first_tick_requests` equal `[STAGE]`.
    - If it does not (`post-record`), check that `result.world.agent_runtime.requests()` is empty. That is the restarted runtime's requests after all three ticks, which is what criterion 7 asks for.

    Why: in round 1, `_resumes_at_first_tick` started reading the requests saved after the first tick (`first_tick_requests`). Since then, the `post-record` case only proves that nothing reran at the first tick. A factory that wrongly reran the stage at the second or third tick would still pass. The fake runtime records requests that raise too, so the full list after three ticks shows any rerun.

    Expected effect: no `src/` change should be needed, because nothing in the current tick reruns a stage whose result was already pushed. If the stricter check goes red, that is a `src/` defect, and I fix it in the next doing round.

    Refactor pass: this round has no new `src/` diff, so there was nothing to refactor and there is no refactor commit. I did not run `make check` this round because nothing changed. It was last green in entry 12.

    Open: criterion 24 (the docs) is still the documenter's.
15. tester: round 2. I made the one test change from the reviewer's entry 13, as the coder named it in entry 14. Nothing else changed: no other test and nothing under `src/`.

    - `tests/proof_support.py::_resumes_at_first_tick` now splits its check on `case.charges_crash`.
      - A case that does not charge a crash (`post-record`) must have `result.world.agent_runtime.requests() == []`. That list is the restarted runtime's requests after all three ticks, which is what criterion 7 asks for.
      - A case that charges a crash keeps the old check: the stage names in `result.first_tick_requests` must equal `[STAGE]`.
    - Why: in round 1 the `post-record` case only proved that nothing reran at the first tick. A factory that wrongly reran the stage at the second or third tick would still have passed. The fake runtime records requests that raise as well, so the full list shows any rerun.

    The stricter check passes against the current `src/`, so no `src/` change is needed. `make test` is green (coverage 99.55 %) and `make lint` is green.

    `make lint`: lint: green
    `make test`: test: green
16. coder: round 2. The one finding from entry 13 is fixed. It was a test change, and the tester made it in entry 15 (commit 04ba05b). This round I changed nothing under `src/` or `tests/`. `src/factory/domain/kill_point_cases.py` (commit 1599e19) is unchanged.

    - Finding (criterion 7, `post-record`): `tests/proof_support.py::_resumes_at_first_tick` now splits on `case.charges_crash`.
      - For a case that charges no crash, it checks that the restarted runtime has no requests after all three ticks.
      - For a case that charges a crash, it still checks `first_tick_requests == [STAGE]`.
      - The stricter check passes against the current `src/`. So the current tick does not rerun a stage whose result was already pushed, and no `src/` change is needed.

    Refactor pass: nothing new in `src/` this round, so there was nothing to refactor and there is no refactor commit.

    Open: criterion 24 (the project guide's `## Kill points` table and the `docs/decisions.md` entry) is still the documenter's job.

    `make check`: check: green (lint, types, layers, sast, secrets, licenses and test all green; coverage 99.55 %)

    `make check`: check: green
17. reviewer: round 2. Two findings, both in group 4 (quality). Both fixes are test changes and the coder may not edit tests (R9), so the coder should end with `tests` and name these two changes.

    Groups 1 to 3 pass:
    - Group 1: the round-2 change in 04ba05b fixes the finding from entry 13. `_resumes_at_first_tick` (`tests/proof_support.py:524-528`) now checks that `post-record` has no request at all after three ticks, and that each case charging a crash has `[STAGE]` at its first tick. I read criteria 1 to 22 against their tests again and each test checks what it is named after. Both sides of the two `KillPointCase` rules and of the closed-model rules are rows of parametrized tests. The coder's entry 16 reports `make check` green.
    - Group 2: `src/factory/domain/kill_point_cases.py` imports only pydantic and `factory.domain.kill_points`, and does no I/O. The tests use a real bare remote, the fake hosting service and the fake agent runtime, and no fake git.
    - Group 3: no secrets, no silencing markers, and nothing built into a shell command.

    The diff's changes to `CLAUDE.md`, `planning/` and `docs/runs/` come from the human's own commits, so I did not review them.

    1. `tests/test_kill_points.py:90-104` (`_rerun_seconds`). What is wrong: it is a second copy of the logic `tests/proof_support.py` already has in `_kill_to_rerun_recorded` (lines 531-541), `_claim_commits` and `_state_at`. It also hardcodes `factory/features/F0001-example/in-progress`, which `FEATURE` already holds, and it walks the whole log, `main` included, where `_claim_commits` limits itself to `since=MAIN`. As a result, no test reaches the `kill-to-rerun-recorded` check, and that check is dead code. Fix: add one public helper to `proof_support`, for example `rerun_seconds(result) -> float | None`, built on `_claim_commits` and `_state_at`. `_kill_to_rerun_recorded` and `test_the_rerun_starts_five_seconds_after_the_kill` both use it, and the test keeps its `record_property("kill_to_rerun_seconds", ...)` call and its assertion that the value is 5.0.
    2. `tests/proof_support.py:236` (`_opening_text`). What is wrong: the name says text, but the function returns a `WorkItemDocument`, which `leak_writes` (line 268) then renders. Fix: rename it `_opening_document`.

    This story has now been sent back 3 times, more than 2. What should happen? Answer with a comment; close the pull request to discard the story.
