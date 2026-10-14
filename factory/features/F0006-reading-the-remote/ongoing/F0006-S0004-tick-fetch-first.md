---
stage: demo
pr: 74
blocked: null
comments_seen: 4
round: 0
attempts: 0
---
# The tick: fetch first, then the remote's state

## Assignment (as of log entry 1)

Build the tick: one pass of fetch, load, restore, evaluate and dispatch, in that order, where the remote is the only truth and the local checkout is disposable. The tick fetches first, and a failed fetch (an expired token fails the same way) is a repository stop and ends the tick. It loads and validates the pipeline definition from `origin/main`; an invalid one ends the tick, and the stop for it is the loader's (F0003-S0006), not the tick's. It restores the checkout to `origin/main`, discarding uncommitted changes and writing one line that names them, and it deletes the local branches of the work items, so that the next stage starts from the remote's branch. It evaluates the remote's state and hands the one event to a dispatcher that it builds after the load, from a handler factory, because the handlers take the loaded pipeline definition (F0006-S0007 builds the production factory). The tick keeps the tick status across ticks. Because nothing local is ever read, a rejected push leaves no trace: the next tick judges the remote's state, and at most one report is posted over all later ticks on that state. A push to a work item's remote branch retries the capped event. A capped event holds back all new work, as a waiting work item does (the decision for the human in `FEATURE.md`). A fresh clone continues every work item. A work item whose file cannot be read stops the tick with the error, not with a stop. The tick reads and writes no run record and no lock; v1's leftover files in `.git/` change nothing. Covers GH5.2, GH5.3, GH5.5, GH1.5 and the tick's side of GH5.4; keeps kept thing 3 (the remote is the truth) and 16 (an idle tick costs a fetch and at most one lookup). Uses `Git` (F0001), `PipelineLoader` (F0003-S0006), `StopService` (F0003-S0002), `Watcher` (F0006-S0002), `Dispatcher` (F0006-S0003) and `RemoteWorkItems` (F0006-S0001).

## Interface

`src/factory/application/tick.py`

```python
HandlerFactory = Callable[[PipelineDefinition], Mapping[EventKind, Handler]]

class TickOutcome(BaseModel):                     # frozen, forbids unknown keys
    stopped: RepositoryStopReason | None = None   # set when the tick ended at a repository stop
    event: Event | None = None                    # the evaluated event; None when stopped
    dispatch: DispatchOutcome | None = None       # None when stopped

class IdleHandler(Handler):
    def handle(self, event: Event) -> None: ...   # does nothing

class Tick:
    def __init__(self, boundaries: Boundaries, instance: Name, handlers: HandlerFactory,
                 status: TickStatus | None = None) -> None: ...
        # status None is an empty TickStatus
    @property
    def status(self) -> TickStatus: ...           # the counts after the last dispatch
    def run(self) -> TickOutcome: ...
        # WorkItemFormatError, ValueError (from the evaluation) and GitError (outside the fetch and the restore)
        # are not caught: no stop exists for them and the tick raises them
```

Rules for `Tick.run`, in this order; a repository stop ends the tick with `TickOutcome(stopped=<reason>)`, and nothing after it runs:

- Fetch: `boundaries.git.fetch()`. `FetchFailed` raises the stop `fetch_failed` with `detail=str(error)`. When it succeeds the stop `fetch_failed` is cleared.
- Load: `PipelineLoader(boundaries).load()`. On `PipelineDefinitionInvalid` the tick ends with `TickOutcome(stopped="pipeline_definition_invalid")`. The loader has raised the stop and clears it on a later success (F0003-S0006); the tick raises and clears no stop for the definition.
- Restore: the checkout is put on branch `main` at `origin/main` with no uncommitted change and no untracked file (ignored paths stay), and every local branch `work-item/<id>` is deleted (`Git.delete_branch`), for each id that has a branch `origin/work-item/<id>` or a story file in `in-progress/` on `origin/main`, after `main` is checked out. When `Git.status()` lists changes before that, one line `discarded uncommitted changes: <path>, <path>` (the paths in the order of `status`) is written to `boundaries.log`; with no changes no line is written. A `GitError` in this step raises the stop `checkout_restore_failed` with `detail=str(error)`. When it succeeds that stop is cleared.
- Evaluate: `Watcher(boundaries, instance).evaluate(definition)`.
- Dispatch: a `Dispatcher(handlers(definition), <the tick's status>, StopService(boundaries), boundaries.log)` dispatches the event; the tick's status becomes the dispatcher's status; the outcome is `TickOutcome(event=event, dispatch=<outcome>)`.
- Every stop raised here is `RepositoryStop(scope="repository", reason=..., detail=..., at=boundaries.clock.now())` raised through `StopService.raise_stop`.
- The tick reads neither a run record nor a lock, and creates none.

Tests: `tests/application/test_tick.py`, with the shared fixtures `remote`, `checkout`, `human`, `hosting`, `clock`, `kill_points` and `boundaries`, whose log and health file already sit under `tmp_path / "state"`. The agent files come from `install_agents(agent_home, <the roles of the fixture's pipeline definition>)` in `tests/git_support.py`. Handler factories are plain functions that return `Handler` test classes. A fetch is made to fail by moving the bare remote away; a restore is made to fail by an untracked directory that has been made unwritable (the test is skipped when `os.geteuid() == 0`). The closed-model test builds `TickOutcome` through a variable typed `type[BaseModel]` and assigns with `setattr`, the field's name in a variable. Hosting-service calls are counted by a test subclass of `FakeHostingService` that overrides every operation except `post_comment` (`tests/test_hosting_fake_search.py` refuses a test class that defines it); posts are counted with `factory_posts`.

## Acceptance criteria

1. `run` fetches before it reads: a commit that the human pushed to a runnable work item's remote branch since the last tick is the `remote_state` of the event this tick dispatches, and the test never fetches.
2. GH5.3: when the fetch fails, `run` returns `TickOutcome(stopped="fetch_failed")` with no event and no dispatch, the handler is not called, and the health status holds exactly one stop with scope `repository`, reason `fetch_failed`, a non-empty `detail` and `at` equal to `clock.now()`.
3. For that stop the factory log holds a line that begins with the clock's UTC time stamp.
4. On the first tick after the remote is back, the stop `fetch_failed` is gone from the health status and the tick dispatches an event.
5. An invalid pipeline definition on `origin/main` (a missing key without a default) makes `run` return `TickOutcome(stopped="pipeline_definition_invalid")` whose stop names the missing key in `detail`; nothing is dispatched, a file left untracked in the checkout is still there, and the factory log holds exactly one line for that stop from this tick (one line that contains `stop repository pipeline_definition_invalid`).
6. After the definition is repaired on `origin/main`, the next tick clears that stop.
7. The restore restores a modified tracked file to its content on `origin/main` and removes an untracked file, leaves the checkout on `main` at the head of `origin/main`, and writes one line equal to `discarded uncommitted changes: <path>, <path>` with the two paths in the order of `Git.status()`; an ignored file in the checkout is still there, and on a clean checkout no such line is written.
8. When the restore cannot remove an untracked file, `run` returns `TickOutcome(stopped="checkout_restore_failed")` with the stop in the health status and nothing dispatched; the next tick, after the file can be removed, clears the stop.
9. GH5.2: a handler of `run` that commits on a copy of the work item's branch made from an older commit and pushes it gets the outcome `rejected` because the human pushed to the branch meanwhile, and raises `PushFailed`; the next tick's event has `remote_state` equal to the head of the remote branch, and the checkout is back on `main` at `origin/main`.
10. GH5.2: with that handler failing on every tick, six ticks give the dispatch outcomes `error`, `error`, `reported`, `capped`, `capped`, `capped`, and the hosting service holds exactly one factory post on the work item's pull request.
11. GH5.4: after that report, a new commit pushed by the human to the work item's remote branch makes the next tick call the handler again.
12. GH5.5: a tick in a fresh clone made with `GitCli.clone` into an empty directory (no local branch of any work item) dispatches the same event for the same work item, with the same `remote_state` and the state the branch holds, as a tick in the original checkout; two work items in different stages are both read from their branches.
13. GH1.5: with v1's leftover files `.git/factory-run.json`, `.git/factory-tick.lock` and `.git/factory-tick.json` in the checkout, each valid, unreadable or absent, a tick dispatches the same event with the same outcome, and leaves those files as they were.
14. GH1.5: none of the modules `factory.application.tick`, `factory.application.watcher`, `factory.application.work_items` and `factory.domain.evaluation` contains `run_record`, `RunRecord`, `factory-run.json`, `factory-tick.lock`, `factory-tick.json`, or a match of the regular expression `\block\b`.
15. A tick on a repository with no work item in progress makes no hosting-service call; with one waiting work item whose pull request is open it makes exactly one `get_pull_request` and one `list_comments`.
16. The `IdleHandler` changes nothing: a tick whose event is `idle`, with `{"idle": IdleHandler()}` as the handler factory's result, returns dispatch outcome `handled` and leaves the checkout, the remote and the hosting service as they were.
17. With a handler factory that returns only `{"idle": IdleHandler()}`, a tick whose event is `run` returns dispatch outcome `error`, and the status holds `UnhandledEvent: no handler for event kind run` as the last error (SI2.4 end to end).
18. A started story whose remote branch exists and whose local branch `work-item/<id>` holds a commit that the remote does not have (the rejected claim push of F0004, made in the test with `checkout.checkout(branch, start_point="origin/main")` and `checkout.commit`) has no local branch `work-item/<id>` after the next tick (`checkout.resolve("work-item/<id>")` is `None`) and `checkout.resolve("origin/work-item/<id>")` is unchanged, so that the next stage starts from the remote's branch; a local branch with another name (`scratch`) is still there.
19. A story whose branch file has no front matter makes `run` raise `WorkItemFormatError` naming the story's path, with nothing dispatched and no stop in the health status; a work item in a stage that the definition lacks makes `run` raise `ValueError`.
20. A capped event holds back all new work: with two runnable work items, a handler of `run` that always fails and records the work item of each call, the ticks after the report give dispatch outcome `capped` for the first work item, and the handler is never called for the second; after the human pushes to the first work item's branch, the next tick calls the handler for the first work item again.
21. The tick keeps its status across ticks: after two failing ticks on one event `tick.status` holds one entry with `count == 2`; a new `Tick` built with no status (a restart) counts the same event from 1.
22. `TickOutcome` refuses an unknown key and an assignment to a field; `stopped` accepts `"fetch_failed"` and `None` and refuses `"other"`, and `dispatch` accepts `"capped"` and refuses `"other"`, all with `ValidationError`.
23. A started story whose file is in `in-progress/` on `origin/main`, with no `origin/work-item/<id>` and a local branch `work-item/<id>` (the claim push was rejected before any remote branch existed), has no local branch `work-item/<id>` after the next tick (`checkout.resolve("work-item/<id>")` is `None`).
24. make check stays green.
25. docs: `docs/operator-guide.md` lists the stops `fetch_failed`, `pipeline_definition_invalid` and `checkout_restore_failed`, what each means and what to do, says that an expired or revoked token shows as `fetch_failed`, and says that a work item file that cannot be read stops the tick with an error until a human repairs it; `docs/project-guide.md` states the order of a tick; `docs/decisions.md` records that the checkout is disposable and restored to `origin/main` at the start of every tick, and that a capped event holds back all new work.

## Demo

```bash
uv run python -c "
import re, subprocess, tempfile
from pathlib import Path
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.adapters.clock import SystemClock
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader, JsonLinesCostRecordWriter
from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.git_cli import GitCli
from factory.adapters.health_file import JsonHealthStatusFile
from factory.adapters.make_commands import MakeProjectCommands
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.application.boundaries import Boundaries
from factory.application.tick import Tick
base = Path(tempfile.mkdtemp())
checkout = base / 'checkout'
subprocess.run(['git', 'init', '-b', 'main', str(checkout)], check=True, capture_output=True)
subprocess.run(['git', 'remote', 'add', 'origin', str(base / 'missing.git')], cwd=checkout, check=True, capture_output=True)
clock = SystemClock()
boundaries = Boundaries(git=GitCli(checkout), hosting=FakeHostingService(), agent_runtime=FakeAgentRuntime(), project_commands=MakeProjectCommands(checkout), work_item_reader=FrontmatterWorkItemReader(), work_item_writer=FrontmatterWorkItemWriter(), cost_reader=JsonLinesCostRecordReader(), cost_writer=JsonLinesCostRecordWriter(), clock=clock, log=TimestampedFactoryLog(base / 'factory.log', clock), health=JsonHealthStatusFile(base / 'health.json'), pipeline_reader=RuamelPipelineDefinitionReader(), agent_definitions=FrontmatterAgentDefinitionReader(base), checkout=checkout)
tick = Tick(boundaries, 'factory-1', lambda definition: {})
outcome = tick.run()
print(outcome.stopped, outcome.event, outcome.dispatch)
print([stop.scope + ':' + stop.reason for stop in boundaries.health.read().stops])
lines = (base / 'factory.log').read_text().splitlines()
print(bool(lines) and all(re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z ', line) for line in lines))
"
```
Expect: the last three lines of the output are `fetch_failed None None` (the fetch from the missing remote stopped the tick before anything was read or dispatched), then `['repository:fetch_failed']`, then `True` (every line the stop wrote to the factory log begins with a UTC time stamp). Before them stand the stop's own stamped lines, which the factory log also writes to standard output: git's message about the missing remote, one stamped line for each line of it.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: 1. Interface, Restore rule: the line is `discarded uncommitted changes: <path>, <path>` with "the paths in the order of `status`". No criterion tests that order. Criterion 7 only says the line names both paths, so two coders could order them differently and both pass. Options: (a) extend criterion 7 so the line equals the exact text with the paths in `Git.status()` order (my choice); (b) drop the order from the Interface comment.
   2. Interface, Restore rule: local `work-item/<id>` branches are deleted for each id that has `origin/work-item/<id>` OR a story file in `in-progress/` on `origin/main`. Criterion 18 covers only the case with a remote branch. A started story with no remote branch and a local `work-item/<id>` branch (the claim push was rejected before any branch existed) has no criterion. Options: (a) add a criterion for that case (my choice); (b) narrow the Interface to ids with a remote branch.

   Everything else I checked is fine: the Interface names concrete modules and signatures, the criteria are single-test and cover both sides of the rules (the fetch fails and recovers in 2 to 4, the definition is invalid and repaired in 5 and 6, the restore fails and recovers in 8, `TickOutcome` refuses bad values in 22), the Demo is runnable with a checkable `Expect:`, and the story fits the layers and the feature's scope. The format check passed.
3. human (pull request comment, 2026-10-14): 1 (a): extend criterion 7 so the line equals the exact text `discarded uncommitted changes: <path>, <path>` with the paths in `Git.status()` order.
   2 (a): add a criterion: a story file in `in-progress/` on `origin/main` with no `origin/work-item/<id>` and a local `work-item/<id>` branch has that local branch deleted by the restore.
   The Interface stays as it is.
4. intake: accepted. I checked the story again with the human's answer in log entry 3. Both answers changed the story, so I wrote exactly them in:
   - Criterion 7 now says the line equals `discarded uncommitted changes: <path>, <path>`, with the paths in `Git.status()` order (answer 1a).
   - New criterion 23 covers a started story with no `origin/work-item/<id>` and a local `work-item/<id>` branch: the restore deletes that branch (answer 2a). It sits before the two closing criteria, which are now 24 (`make check`) and 25 (`docs:`).
   - The Interface and the Assignment are unchanged, as the human said.

   Checks:
   - Interface: it names `src/factory/application/tick.py` with concrete signatures (`Tick`, `TickOutcome`, `IdleHandler`, `HandlerFactory`). The restore rule's ordering and its two-source branch deletion now each have a criterion.
   - Criteria: each can be tested by one test function. Every rule has its failing side: the fetch fails and recovers (2 to 4), the definition is invalid and repaired (5, 6), the restore fails and recovers (8), `TickOutcome` refuses bad values (22), and unreadable files and a missing handler raise or count as errors (17, 19).
   - Demo: it is runnable. Its `Expect:` line is checkable against the output.
   - Architecture: `application/tick.py` uses only the `Git`, `PipelineLoader`, `StopService`, `Watcher` and `Dispatcher` interfaces. The `Boundaries` wiring and the fakes are used the way `CLAUDE.md` describes.
   - Scope: the story is inside F0006. It touches no handler of F0007 to F0010, and it matches the feature's decisions 2, 10, 11 and 14.
5. tester: I wrote the tests for criteria 1 to 23 in `tests/application/test_tick.py`, which is a new file. The branch is now red on purpose. `make test` stops at collection with `ModuleNotFoundError: No module named 'factory.application.tick'`, the module the coder writes. `make lint` is green. I skipped the type check, as the stage says.

   Which test covers which criterion (all in tests/application/test_tick.py):
   - criterion 1: test_the_tick_fetches_before_it_reads_the_remote
   - criterion 2: test_a_failed_fetch_is_a_repository_stop_and_ends_the_tick
   - criterion 3: test_the_fetch_stop_is_logged_with_the_clock_stamp
   - criterion 4: test_the_first_tick_after_the_remote_is_back_clears_the_fetch_stop
   - criterion 5: test_an_invalid_pipeline_definition_ends_the_tick_before_the_restore. The missing key is `contract`.
   - criterion 6: test_the_tick_after_the_definition_is_repaired_clears_its_stop
   - criterion 7: test_the_restore_discards_changes_and_names_them_in_one_line, and test_a_clean_checkout_writes_no_discarded_line. The ignored file is ignored through `.git/info/exclude`. A newer commit on `main` makes the restore actually move the checkout. The expected order of the two paths is taken from `checkout.status()` before the tick.
   - criterion 8: test_a_failed_restore_is_a_repository_stop_cleared_by_the_next_tick. It is skipped when running as root.
   - criterion 9: test_a_rejected_push_leaves_no_trace_for_the_next_tick. The handler `StalePush` checks at the start of each call whether the checkout is on `main` at `origin/main`. It has to check there because on the second tick its push succeeds and the checkout moves off `main`.
   - criterion 10: test_a_failing_handler_is_reported_once_and_then_capped. Each tick, `StalePush` works on a copy of the branch made from the older commit, so its push is rejected every time.
   - criterion 11: test_a_human_push_after_the_report_retries_the_capped_event
   - criterion 12: test_a_fresh_clone_continues_every_work_item_from_its_branch. The first work item's branch holds stage `done`, which has no role, so the event goes to the second work item at `doing`. That `run` event only comes out this way if both work items were read from their branches.
   - criterion 13: test_v1_leftover_files_change_nothing, run once each for the files being valid, unreadable and absent.
   - criterion 14: test_the_tick_knows_no_run_record_and_no_lock, run once for each of the four modules.
   - criterion 15: test_an_idle_tick_makes_no_hosting_call, and test_a_waiting_work_item_costs_one_lookup_and_its_comments
   - criterion 16: test_the_idle_handler_changes_nothing
   - criterion 17: test_an_event_without_a_handler_is_a_counted_error
   - criterion 18: test_the_restore_deletes_a_local_branch_the_remote_has_not_taken
   - criterion 19: test_an_unreadable_work_item_file_raises_without_a_stop, and test_a_work_item_in_an_unknown_stage_raises_value_error
   - criterion 20: test_a_capped_event_holds_back_all_new_work
   - criterion 21: test_the_tick_keeps_its_status_across_ticks_and_a_restart_counts_from_one
   - criterion 22: test_tick_outcome_refuses_an_unknown_key, test_tick_outcome_refuses_an_assignment, and test_tick_outcome_accepts_only_its_values
   - criterion 23: test_the_restore_deletes_a_local_branch_of_a_started_story_without_a_remote_branch

   Notes for the coder:
   - Agent files for every role of `PIPELINE_YAML` are installed by an autouse fixture.
   - Hosting-service calls are counted by `_CountingHosting`, a subclass of `FakeHostingService` that does not override `post_comment`.
   - I did not add `assert` lines on the hosting service for criterion 15 beyond the call list; the criterion asks for exactly one `get_pull_request` and one `list_comments`, and the test compares the sorted call list to those two.

   Nothing is open. I did not have to interpret any criterion.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
6. coder: I built `src/factory/application/tick.py` (commit 447294b). It has `HandlerFactory`, `TickOutcome`, `IdleHandler` and `Tick`, following the Interface: fetch, then load, then restore, then evaluate, then dispatch. A private `_Stopped` exception ends the tick once a stop has been raised. The restore works in this order:
   - It reads `status` and writes the discarded line.
   - `reset_to("HEAD")` cleans the checkout on whatever branch it is on.
   - `checkout("main", start_point="origin/main")` puts the checkout on main.
   - `delete_branch` runs for every id that has a remote `work-item/` branch or an `in-progress/` story on origin/main.
   Cleaning before the switch means the switch to main never meets a local change. I rejected the other order, `reset_to("origin/main")` on the current branch, because it would move a non-work-item branch such as `scratch` when the checkout sits on it.

   lint, types, layers, sast, secrets and licenses are green, and so is every tick test except two. `make test` is red only on these two, and I believe both tests are wrong, not the code.

   1. `test_a_rejected_push_leaves_no_trace_for_the_next_tick` (criterion 9). On the second tick, `StalePush` starts from `event.remote_state`, which is the remote head, so its push succeeds, as the tester's note says. The test checks `second.event.remote_state == remote_commit(remote, BRANCH)` and `handler.events[1].remote_state == remote_commit(remote, BRANCH)` after that push, so the remote has already moved one commit past the event. Observed: event `cc1ae958…`, remote `3bc18f7f…`. No implementation can pass this. Options:
      - (a) Record `remote_commit(remote, BRANCH)` right after the first `tick.run()` and compare against that. This is my choice, because it is exactly what criterion 9 says: the head the human pushed meanwhile.
      - (b) Give the handler a `base` or another switch so its second push is not made.
   2. `test_an_unreadable_work_item_file_raises_without_a_stop` (criterion 19). The test calls `human.push_file(BRANCH, PATH, BODY)`, but `BODY` is `"# First story\n"`, which is exactly what `human.start` already put at `PATH`. The commit is empty and `GitCli.commit` raises `NothingToCommit` in the setup, before the tick runs. This is the trap `CLAUDE.md` warns about. Options:
      - (a) Push a different text without front matter, for example `"# First story, edited\n"`. This is my choice.
      - (b) Push the file to a different path.

   Refactor: not done yet, because `make check` is not green. The diff is one new module and I saw nothing to change in it. Once you answer, I will end with `tests` naming the two changes.
7. human (pull request comment, 2026-10-14): 1 (a): record `remote_commit(remote, BRANCH)` right after the first `tick.run()` and compare both assertions against that recorded head, as criterion 9 says.
   2 (a): push a different text without front matter, `"# First story, edited\n"` (the empty-commit trap in `CLAUDE.md`).
   End with `tests` and name exactly these two changes.
8. coder: the human's answer in log entry 7 asks for two test changes. I do not edit tests, so I am sending the story back to the tester with exactly these changes, both in `tests/application/test_tick.py`:
   1. `test_a_rejected_push_leaves_no_trace_for_the_next_tick` (criterion 9): record `remote_commit(remote, BRANCH)` right after the first `tick.run()`. Compare both `second.event.remote_state` and `handler.events[1].remote_state` against that recorded head, not against `remote_commit(remote, BRANCH)` read after the second tick.
   2. `test_an_unreadable_work_item_file_raises_without_a_stop` (criterion 19): pass `"# First story, edited\n"` to `human.push_file(BRANCH, PATH, …)` instead of `BODY`. The text still has no front matter, but it no longer matches what `human.start` already put there, so the commit is not empty.

   The code stays as it is in 447294b (`src/factory/application/tick.py`). Every other part of `make check` was green, and these two tests were the only red ones. I have not done the refactor pass yet. I will do it once these tests are fixed and `make check` is green.
9. tester: I made the two test changes the human approved in log entry 7, as the coder named them in log entry 8. Both are in `tests/application/test_tick.py`, and I changed nothing else.
   1. `test_a_rejected_push_leaves_no_trace_for_the_next_tick` (criterion 9): the test now saves `remote_commit(remote, BRANCH)` as `head` right after the first `tick.run()`. Both `second.event.remote_state` and `handler.events[1].remote_state` are compared against that saved head. Before, the test read the remote again after the second tick, and by then the handler's successful push had moved it one commit further. That is why no implementation could pass. Criterion 9 asks for the head the human pushed in the meantime, which is the saved one.
   2. `test_an_unreadable_work_item_file_raises_without_a_stop` (criterion 19): `human.push_file(BRANCH, PATH, …)` now pushes `"# First story, edited\n"` instead of `BODY`. The text still has no front matter. It now differs from what `human.start` had already put at `PATH`, so the commit is no longer empty and `NothingToCommit` is not raised during setup (the trap described in `CLAUDE.md`).

   I ran `make test` once and it passed, coverage 99.39 %. `make lint` passed.

   `make lint`: lint: green
   `make test`: test: green
10. coder: The tester's two changes from log entry 9 are in, and `make check` is green with no change to the feature code (commit 447294b): all 23 criteria pass and coverage is 99.39 %.

    What I built: `src/factory/application/tick.py`, which holds `HandlerFactory`, `TickOutcome`, `IdleHandler` and `Tick`. A tick runs fetch, load, restore, evaluate and dispatch, in that order. A private `_Stopped` exception ends the tick once a repository stop has been raised through `StopService`. When the fetch or the restore succeeds, its stop is cleared. The definition's stop is left to `PipelineLoader`.

    Main design decision: the restore does these steps in order:
    1. It reads `status` and writes the discarded line.
    2. It runs `reset_to("HEAD")` to clean the current branch in place.
    3. It runs `checkout("main", start_point="origin/main")`.
    4. It deletes the local `work-item/<id>` branch of every id that has an `origin/work-item/` branch or an `in-progress/` story on `origin/main`.

    Rejected: `reset_to("origin/main")` on the current branch. It would move a non-work-item branch such as `scratch` when the checkout is on it.

    Refactor (commit 7cc0e7f): I typed `_stop` as `NoReturn`, since it always raises. That makes the end of the fetch and restore steps explicit. Nothing else needed changing.

    Noticed but not touched: nothing.

    `make check`: check: green
11. reviewer: no findings.

    What I read: the ticket, and `git diff main...HEAD -- . ':!factory'`. The diff is two files: `src/factory/application/tick.py` (new) and `tests/application/test_tick.py` (new). I also read the `GitCli` methods the restore depends on (`reset_to`, `checkout`, `delete_branch`, `remote_branches`) and `RemoteWorkItems.list_stories`, to check the restore's behaviour.

    1. Acceptance criteria:
       - Criteria 1 to 23 each have a test that checks what the criterion says. The coder's entry 10 reports `make check` green.
       - Failing sides are covered: the fetch fails and recovers (2 to 4), the definition is invalid and is repaired (5, 6), the restore fails and recovers (8), a clean checkout writes no discarded line (7), a local branch with another name, `scratch`, is kept (18), and both sources for deleting a branch are tested (18, 23).
       - The idle tick makes no hosting call, and a waiting work item costs exactly one lookup and one comment list (15). A missing handler is a counted error (17). An unreadable file and an unknown stage both raise without a stop (19). `TickOutcome` refuses bad keys, assignments and values (22).
       - The two test changes the human approved in entry 7 are in, as entry 9 describes.
    2. Architecture: `tick.py` imports only `factory.application` and `factory.domain`. It uses `Git`, `PipelineLoader`, `StopService`, `Watcher`, `Dispatcher` and `RemoteWorkItems`. It calls no tool directly and passes no `dict[str, Any]`. `IdleHandler` inherits `Handler`.
    3. Security: no secrets, no strings built into commands, and no suppression markers.
    4. Quality:
       - Module, class and public method docstrings are present and say what each thing is for.
       - The comments explain why: the definition's stop belongs to the loader, the checkout is cleaned before switching to `main`, and local work-item branches are deleted so the next stage starts from the remote.
       - `_stop` is typed `NoReturn`, which makes the end of each step explicit.
       - I checked the restore order against `GitCli`: `reset_to("HEAD")` is `reset --hard` followed by `clean -d` without `-x`, so ignored files stay. `switch --force-create main origin/main` follows. `delete_branch` does nothing when the branch is missing, so deleting by id from both sources is safe.
    5. Ticket hygiene:
       - Entry 10 names the main decision: clean in place, then switch, then delete branches. It also names the rejected option, `reset_to("origin/main")` on the current branch, which would move a `scratch` branch.
       - The Assignment matches what was built.
       - The docs criterion (25) still describes what the operator and the agents need to know.

    Open: nothing.
12. documenter: Docs for the tick; `make check` is green.

    Changed:
    - `docs/operator-guide.md`: new section "The stops of the tick". It covers `fetch_failed` (an expired or revoked token shows as this stop), `pipeline_definition_invalid` (points to its existing section) and `checkout_restore_failed`, each with meaning and remedy. It also covers the restore's discard line, the fact that an unreadable work item file ends the tick with an error until a human repairs it (not a stop), and the fact that v1's leftover `.git` files are ignored. I also replaced "Nothing calls the dispatcher yet" in "An event that keeps failing" with a sentence that the tick calls it.
    - `docs/project-guide.md`: new section "The tick", with the order fetch → load → restore → evaluate → dispatch, the `TickOutcome` and `IdleHandler` contracts, which errors propagate, and why a rejected push leaves no trace.
    - `docs/decisions.md`: two entries. One says the checkout is disposable and restored to `origin/main` every tick. The other says a capped event holds back all new work.

    Cross-read and found current against the diff: the operator guide's stop and health-status sections, and the project guide's evaluation, `RemoteWorkItems` and dispatcher text.

    Stale and left alone (not this story's): the project guide line about `status` and `reset_to` being "F0006" future uses is now true but unchanged.

    No findings for the coder. `src/factory/application/tick.py` matches the Interface and has its docstrings.

    `make check`: check: green
