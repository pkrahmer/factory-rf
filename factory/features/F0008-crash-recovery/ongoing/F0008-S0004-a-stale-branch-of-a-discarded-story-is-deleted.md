---
stage: doing
pr: 98
blocked: null
comments_seen: 2
round: 0
attempts: 0
---
# A discarded story's stale branch is deleted by the tick

## Assignment (as of log entry 1)

Make the tick delete the remote branch that a kill left behind for a story that is already back in the backlog. F0007's `ClosedHandler` (S0004) moves a discarded story to `backlog/` on `main` and only then deletes its branch `work-item/<id>`; a kill, or a deletion the remote refuses, between the two leaves the old branch with its closed pull request on the remote. When the human then starts the story again, the factory reads the old state from that branch, the `RunGate` discards the story again, and a story started again does not start with an empty bill (GH4.3 fails on this path). F0007 decision 21 names the cure and builds none: the tick deletes the remote branch of any work item whose file is in `backlog/` on `origin/main`, so the recovery after a kill needs no human. This story builds it as a function of this feature's recovery module and one new step of the tick (F0006-S0004): after the restore of the checkout and before the evaluation, the tick calls `delete_stale_branches`. A refused deletion is a log line and is tried again on the next tick; it never stops the tick. A branch is kept when its id also has a story file in `in-progress/` (two work items with one id are F0006's `duplicate` case, which reports it). The branch of a story in `done/` is deleted the same way: `MergedHandler` (F0007-S0003) pushes the archive to `main` before it deletes the branch, so a kill or a refused deletion between the two leaves the merged branch, which no later event reads (F0007 decision 6, decision 17 of the feature). Covers GH4.3 on the path of a kill (the discard itself is F0007-S0004's); keeps kept thing 3 (the remote is the truth: the step reads only the remote-tracking branches and `origin/main`) and kept thing 11 (the discard question's promise that the branch and the bill are deleted). Uses `RemoteWorkItems` (F0006-S0001), `Git.remote_branches`, `Git.delete_remote_branch` (F0001) and `work_item_of_branch` (F0002). It adds a step to the order of the tick that F0006-S0004 states in the project guide, which this story's docs criterion corrects, and changes no test of F0006. No morning observation.

## Interface

`src/factory/application/recovery.py` (added to the module of S0001)

```python
def delete_stale_branches(boundaries: Boundaries) -> list[str]: ...
```

- It lists the story files of `origin/main` with `RemoteWorkItems(boundaries.git, boundaries.work_item_reader).list_stories(folder)` for `"backlog"`, `"done"` and `"in-progress"`. The stale ids are those of the backlog and done stories that no `in-progress` story file shares.
- For every branch of `boundaries.git.remote_branches()` whose `work_item_of_branch(name)` is a stale id, in the order of the branch names, it calls `boundaries.git.delete_remote_branch(name)`. For the outcome `"pushed"` it writes the log line `deleted stale branch <name>: its story is back in the backlog` (`deleted stale branch <name>: its story is done` when the id's file is in `done/`) with `boundaries.log.line` and adds the name to the result. For any other outcome (`"rejected"`, `"unreachable"`) it writes `could not delete stale branch <name>: <outcome>` and goes on; it raises nothing for an outcome.
- It returns the names of the deleted branches, in the order of the branch names. With no stale branch it writes no line and returns `[]`.
- It reads `origin/main` and the remote-tracking branches only, never a local branch or the work tree, and it makes no call to the hosting service: a pull request on a deleted branch is left as it is (the hosting service may close an open one when its branch goes). A `GitError` leaves the function unchanged and uncaught.

`src/factory/application/tick.py` (F0006-S0004; one step added)

- `Tick.run` calls `delete_stale_branches(boundaries)` after the restore of the checkout and before the evaluation. The order of a tick is fetch, load, restore, clean up, evaluate, dispatch. A repository stop of an earlier step ends the tick before the cleanup. `TickOutcome` and the stops are unchanged.

Tests: `tests/application/test_stale_branches.py` and `tests/application/test_tick_stale_branch.py` (new files: `tests/application/test_tick.py` is F0006-S0004's and stays as it is). The tests use the shared fixtures `remote`, `checkout`, `human`, `hosting`, `kill_points`, `clock`, `agent_home` and `boundaries`; the tick tests install the agents with `install_agents(agent_home, <the roles of the fixture's pipeline definition>)` from `tests/git_support.py`, as F0006-S0004's tests do, because `PipelineLoader` ends the tick with `pipeline_definition_invalid` when an agent is missing. The fixture's backlog story is `F0001-S0001` under `factory/features/F0001-example/backlog/`; a stale branch is made with `human.push_file("work-item/F0001-S0001", "marker.txt", "x\n")` followed by `checkout.fetch()`; a story in `in-progress/` is made with `human.start`, one in `done/` with `human.push_file("main", <a path under done/>, "# T\n")`, and a second file with the same id in `in-progress/` with `human.push_file` as well. A refused deletion is made by setting `receive.denyDeletes` to `true` in the bare remote's configuration, as in F0007-S0004's tests. The tick test discards a started story with F0007's `ClosedHandler` while `kill_points.arm(KillPoint.AFTER_PUSH)` is set (the kill leaves the story in `backlog/` and the branch on the remote, as F0007-S0004's criterion 9), then runs `Tick(boundaries, "factory-1", <a handler factory whose result is {"idle": IdleHandler(), "run": <a recording subclass of Handler>}>)`.

## Acceptance criteria

1. A remote branch `work-item/<id>` whose story file is in `backlog/` on `origin/main` is deleted: `delete_stale_branches` returns `["work-item/<id>"]`, `git.resolve("origin/work-item/<id>")` is `None`, and the branch is gone from the bare remote.
2. The branch of a story in `in-progress/` stays, and the function returns `[]`.
3. A remote branch that no work item owns stays: `main`, `scratch` and `work-item/not-an-id` (three cases, one test).
4. A story in `backlog/` that has no branch changes nothing: the function returns `[]`, the factory log gets no line and the remote is as it was; a story file moved from `in-progress/` to `backlog/` in the checkout's work tree only (not pushed) leaves its branch on the remote.
5. An id with a story file in `backlog/` and another in `in-progress/` keeps its branch, and the function returns `[]`.
6. Two stale branches are both deleted, and the function returns their names in the order of the names.
7. For a deleted branch the factory log holds exactly one line that ends with `deleted stale branch work-item/<id>: its story is back in the backlog`.
8. A refused deletion is no error: with `receive.denyDeletes` set to `true` in the bare remote, the function returns `[]` and raises nothing, the branch is still on the remote, and the factory log holds a line that ends with `could not delete stale branch work-item/<id>: rejected`; a second call after the setting is removed deletes the branch and returns its name.
9. The cleanup touches nothing else: the pull request of the deleted branch (closed by `hosting.close_by_human`) is still `closed`, the hosting service holds no factory post, and `git.status().branch` and the head of the local `main` are as they were.
10. A story discarded by F0007's `ClosedHandler` and killed after the move was pushed (`KillPoint.AFTER_PUSH`) has its branch deleted by the next `Tick.run`: afterwards `checkout.resolve("origin/work-item/<id>")` is `None`, and the tick has evaluated and dispatched an `idle` event, not a `run` event.
11. After that tick and a new start by the human (`human.start` on the file under `backlog/`), the next `Tick.run` dispatches a `run` event whose work item has `branch_commit` `None` and a state equal to `initial_state(<the first stage>)`: no closed pull request, no counter and no bill of the discarded story come back (GH4.3 after a kill).
12. A tick that ends at a repository stop deletes nothing: with a stale branch on the remote and the agent home left empty, `Tick.run` returns `TickOutcome(stopped="pipeline_definition_invalid")` and the branch is still on the remote.
13. The remote branch of a story whose file is in `done/` on `origin/main` is deleted: the function returns `["work-item/<id>"]`, the branch is gone from the bare remote, and the factory log holds exactly one line that ends with `deleted stale branch work-item/<id>: its story is done`.
14. make check stays green.
15. docs: `docs/operator-guide.md` says that the tick deletes the remote branch of any story that is back in the backlog (the leftover of a kill or of a refused deletion in a discard), that this closes a pull request still open on it, that a refused deletion is logged and tried again on the next tick, that a story started before that tick still finds the old branch, and that the branch a kill or a refused deletion left behind for a merged story (its file in `done/`) is deleted the same way; `docs/project-guide.md` states the order of a tick as fetch, load, restore, clean up, evaluate, dispatch; `docs/decisions.md` records why the cleanup is the tick's and not the discard handler's.

## Demo

```bash
uv run python -c "
import subprocess, tempfile
from datetime import UTC, datetime
from pathlib import Path
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.adapters.clock import ManualClock
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader, JsonLinesCostRecordWriter
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.adapters.health_file import JsonHealthStatusFile
from factory.adapters.make_commands import MakeProjectCommands
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.application.boundaries import Boundaries
from factory.application.recovery import delete_stale_branches
tmp = Path(tempfile.mkdtemp())
work = tmp / 'work'
def sh(*args, cwd=tmp):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)
sh('git', 'init', '--bare', '-b', 'main', 'remote.git')
sh('git', 'clone', 'remote.git', 'work')
sh('git', 'config', 'user.name', 'demo', cwd=work)
sh('git', 'config', 'user.email', 'demo@example.com', cwd=work)
sh('git', 'checkout', '-B', 'main', cwd=work)
rel = work / 'factory/features/F0001-demo/backlog/F0001-S0001-demo.md'
rel.parent.mkdir(parents=True)
rel.write_text('# Demo\n')
sh('git', 'add', '-A', cwd=work)
sh('git', 'commit', '-m', 'story', cwd=work)
sh('git', 'push', 'origin', 'main', cwd=work)
git = GitCli(work)
git.checkout('work-item/F0001-S0001', start_point='origin/main')
(work / 'marker.txt').write_text('x\n')
git.commit('leftover of the discarded story')
git.push('work-item/F0001-S0001')
git.checkout('main', start_point='origin/main')
clock = ManualClock(datetime(2026, 10, 12, tzinfo=UTC))
boundaries = Boundaries(git=git, hosting=FakeHostingService(), agent_runtime=FakeAgentRuntime(), project_commands=MakeProjectCommands(work), work_item_reader=FrontmatterWorkItemReader(), work_item_writer=FrontmatterWorkItemWriter(), cost_reader=JsonLinesCostRecordReader(), cost_writer=JsonLinesCostRecordWriter(), clock=clock, log=TimestampedFactoryLog(tmp / 'factory.log', clock), health=JsonHealthStatusFile(tmp / 'health.json'), pipeline_reader=RuamelPipelineDefinitionReader(), agent_definitions=FrontmatterAgentDefinitionReader(tmp / 'agents'), checkout=work)
print(delete_stale_branches(boundaries))
print(git.resolve('origin/work-item/F0001-S0001'))
print([branch.name for branch in git.remote_branches()])
print(delete_stale_branches(boundaries))
"
```
Expect: the factory log line on standard output first, time-stamped and ending with `deleted stale branch work-item/F0001-S0001: its story is back in the backlog`, then four more lines: `['work-item/F0001-S0001']` (the stale branch was deleted), `None` (its remote-tracking ref is gone), `['main']` (only `main` is left) and `[]` (a second call has nothing to delete).

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: `delete_stale_branches(boundaries) -> list[str]` in `src/factory/application/recovery.py` and the one added step in `Tick.run` are concrete. The inputs and outputs are `RemoteWorkItems.list_stories`, `Git.remote_branches`, `Git.delete_remote_branch` and `work_item_of_branch`. The log lines and the return order are fixed.
   - Criteria: each is testable by one test function. Every Interface rule has a criterion for both sides. Deletion is covered by 1, 6, 7, 10 and 13. The kept side is covered by 2, 3, 4 and 5, plus 12 for a tick that stops early. The refused or unreachable deletion is covered by 8. Reads limited to `origin/main` are covered by the unpushed move in 4. Nothing else touched is covered by 9. GH4.3 after a kill is covered by 10 and 11.
   - Demo: the script runs on the real modules and `Expect:` names five checkable outputs (the log line, `['work-item/F0001-S0001']`, `None`, `['main']`, `[]`).
   - Architecture: the function sits in the application layer's recovery module and uses only existing interfaces (`Git`, the log). The tick step is in `tick.py`. No new dependency and no hosting call.
   - Scope: this is within FEATURE.md Scope (last bullet) and Decisions 17 and 19, and touches nothing under Out of scope.
   - Not asked, for the tester to know: the "keep when the id also has an `in-progress` file" rule is tested only with a backlog story (criterion 5). The same rule for a `done/` story is in the Interface and the test setup text but has no criterion of its own. I judged it covered by the same code path and did not add a criterion.
3. tester: Wrote the red tests for every acceptance criterion except 14 and 15.

   Mapping:
   - criterion 1: tests/application/test_stale_branches.py::test_the_branch_of_a_story_back_in_the_backlog_is_deleted
   - criterion 2: tests/application/test_stale_branches.py::test_the_branch_of_a_story_in_progress_stays
   - criterion 3: tests/application/test_stale_branches.py::test_a_branch_no_work_item_owns_stays (parametrized: `main`, `scratch`, `work-item/not-an-id`)
   - criterion 4: tests/application/test_stale_branches.py::test_a_backlog_story_without_a_branch_changes_nothing and ::test_a_story_moved_back_in_the_work_tree_only_keeps_its_branch (the move is a rename in the checkout's work tree after `reset_to("origin/main")`, never committed or pushed)
   - criterion 5: tests/application/test_stale_branches.py::test_an_id_with_a_story_file_in_progress_as_well_keeps_its_branch (parametrized over `backlog` and `done`). The `done` case is the Interface's rule "backlog and done stories that no in-progress story file shares", which intake judged covered without a criterion of its own. It uses id F0001-S0002 with a second file `F0001-S0002-other.md` in `in-progress/`.
   - criterion 6: tests/application/test_stale_branches.py::test_two_stale_branches_are_deleted_in_the_order_of_their_names (the S0002 branch is pushed first)
   - criterion 7: tests/application/test_stale_branches.py::test_a_deleted_branch_is_named_in_one_log_line
   - criterion 8: tests/application/test_stale_branches.py::test_a_refused_deletion_is_logged_and_tried_again_on_the_next_call (`receive.denyDeletes` is set, then removed with `git config --unset`)
   - criterion 9: tests/application/test_stale_branches.py::test_the_cleanup_leaves_the_pull_request_the_hosting_service_and_the_checkout
   - criterion 10: tests/application/test_tick_stale_branch.py::test_the_next_tick_deletes_the_branch_a_killed_discard_left_and_stays_idle
   - criterion 11: tests/application/test_tick_stale_branch.py::test_a_story_started_again_after_the_cleanup_starts_from_the_first_stage
   - criterion 12: tests/application/test_tick_stale_branch.py::test_a_tick_that_ends_at_a_repository_stop_deletes_nothing. This test probably passes already, because the stop comes before any cleanup. It guards the order of the steps.
   - criterion 13: tests/application/test_stale_branches.py::test_the_branch_of_a_done_story_is_deleted
   - criteria 14 and 15: no test (`make check` and docs)

   Files created: tests/application/test_stale_branches.py and tests/application/test_tick_stale_branch.py. tests/application/test_tick.py is unchanged.

   Setup of the tick tests: the `discarded` fixture runs F0007's `ClosedHandler` with `KillPoint.AFTER_PUSH` armed, checks that the branch is still on the remote, and installs the agents. Criterion 12 installs no agents.

   Not tested: the `"unreachable"` outcome, because no criterion names it.

   `make test` result: collection fails with `ImportError: cannot import name 'delete_stale_branches' from 'factory.application.recovery'`. This is the missing function and the right failure. The tick test file imports only names that already exist, so it fails at runtime once collection gets past the missing function.

   `make lint` is green.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
4. coder: question about a test that fails in its own setup. The implementation is committed in 983df7a.

   Built:
   - `delete_stale_branches(boundaries)` is in `src/factory/application/recovery.py`. It collects the ids of the `backlog` and `done` stories on `origin/main` that no `in-progress` file shares. If an id is in both `backlog` and `done`, the log line says "done". It deletes each matching remote-tracking branch, in name order, through `Git.delete_remote_branch`. A `"pushed"` outcome is logged as `deleted stale branch …` and added to the result. Any other outcome is logged as `could not delete stale branch …: <outcome>`.
   - `Tick.run` in `src/factory/application/tick.py` calls it after the restore step and before the evaluation. A stop ends the tick before the cleanup is reached.
   - Rejected: putting the cleanup inside `_restore`. A `GitError` there would raise `checkout_restore_failed`, but the Interface says a `GitError` from the cleanup is left uncaught.

   The question: in `make check`, every other test passes and coverage is 99%. The one failure is `tests/application/test_stale_branches.py::test_a_story_moved_back_in_the_work_tree_only_keeps_its_branch`, and it fails in its own setup before the function under test runs:
   - `human.start(BACKLOG_PATH)` moves the fixture's only backlog story, so the `backlog/` directory is empty.
   - Git does not keep empty directories, so after `checkout.reset_to("origin/main")` the checkout has no `factory/features/F0001-example/backlog/` directory.
   - `(directory / IN_PROGRESS_PATH).rename(directory / BACKLOG_PATH)` then raises `FileNotFoundError`.

   No change to the code under test can make this pass.

   Options:
   - (a) Recommended: the tester adds `(directory / BACKLOG_PATH).parent.mkdir(parents=True, exist_ok=True)` just before the rename. The test then checks criterion 4's second half as intended. I expect it to pass against the current implementation, but I have not run it.
   - (b) Drop that test and leave the work-tree half of criterion 4 untested. I advise against this.

   Refactor step: not done yet, because `make check` is not green. The diff is small (one function, one helper, one call in the tick) and I see nothing to clean up so far. The refactor will follow once the test is fixed.

   Not touched: `docs/` (criterion 15 is the documenter's).
5. human (pull request comment, 2026-10-14): (a): the tester adds `(directory / BACKLOG_PATH).parent.mkdir(parents=True, exist_ok=True)` just before the rename in `test_a_story_moved_back_in_the_work_tree_only_keeps_its_branch`, and changes nothing else. End with `tests` and name exactly that change.
