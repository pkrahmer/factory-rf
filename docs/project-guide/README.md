# Project guide

The guide for agents working on `factory-rf`: how the code is laid out, where a change belongs, which conventions the checks do not catch, and what to read first. It is this index and one file per domain: read the index, then the files of the domains your story touches. It grows with each story: the documenter stage fills it in from the stories' docs criteria. `CLAUDE.md` holds the rules every change follows.

A file of the guide is split by the same rule before it passes about 600 lines: its sections go by domain to a new file, and the new file is named here.

## The files

Each file starts with a title and a sentence on what it covers.

- `README.md` (this index): what holds for all code. Sections: *The files*, *Errors*, *The models' configuration*, *Kill points*, *Fault-injection paths*.
- `git-and-hosting.md`: git and the hosting service. It describes the hosting-service interface with its PyGithub and fake implementations (`factory.application.hosting`, `factory.adapters.pygithub_hosting`, `factory.adapters.fake_hosting`, `factory.domain.hosting`) and the git wrapper (`factory.application.git`, `factory.adapters.git_cli`, `factory.domain.git`). It also names `factory.domain.settings`. Sections: *The hosting service*, *The git wrapper*.
- `processes-and-checks.md`: processes, project commands and this repository's checks. It describes the project-commands interface and its make implementation (`factory.application.project_commands`, `factory.adapters.make_commands`), the one module that starts processes (`factory.adapters.process`), and the commands behind `make duplicates`, `make documents` and `make mutants` (`factory.domain.duplicates`, `factory.domain.documents`, `factory.domain.mutants`). It also names `factory.adapters.record_log_jsonl`, `factory.application.disk_records`, `factory.application.known_results`, `factory.application.preflight`, `factory.domain.checks`, `factory.domain.command_records`, `factory.domain.disk`, `factory.domain.known_results`, `factory.entry.check_demos`, `factory.entry.check_documents`, `factory.entry.check_duplicates`, `factory.entry.check_mutants`, `factory.entry.inputs`. Sections: *Project commands*, *Starting a process*, *The duplicates report*, *The document check*, *The demos*, *Mutation testing* (with *The report of a mutation run*).
- `agents.md`: the agent runtime, the agent files, the shipped agents and the template. It describes the agent-runtime interface and its implementations (`factory.application.agent_runtime`, `factory.adapters.claude_runtime`, `factory.adapters.agent_launch`, `factory.domain.agent_runs`), the agent files reader (`factory.adapters.agent_files`) and the files under `claude/`. It also names `factory.adapters.fake_agent_runtime`, `factory.adapters.opencode_runtime`, `factory.adapters.validation_faults`, `factory.application.project_agents`, `factory.domain.provider_limits`. Sections: *The agent runtime*, *The agent definition reader*, *The shipped agents, settings and template*, *Replaced from v1*. Subsections other files refer to: *The opencode runtime*.
- `write-guard.md`: the write paths, the guard, the undo, the kernel's guard and the start wrapper. It describes `factory.application.write_paths`, `factory.domain.write_paths`, `factory.application.undo`, `factory.adapters.landlock`, `factory.domain.confinement` and `factory.entry.confine` (`factory-confine`). It also names `factory.adapters.claude_guard`, `factory.entry.guard`. Sections: *The write paths*, *The guard command*, *The undo*, *The kernel's write guard*, *The start wrapper*.
- `work-items.md`: the identity, data, files, sections and form of a work item. It describes `factory.domain.identifiers`, `factory.domain.paths`, `factory.domain.work_item`, `factory.domain.journal`, `factory.domain.sections`, `factory.domain.story_form`, `factory.adapters.work_item_markdown` and `factory.entry.check_story`. It also names `factory.application.acceptance`, `factory.application.acceptance_reading`, `factory.application.files`, `factory.application.work_items`, `factory.domain.acceptance`, `factory.domain.contract`, `factory.domain.times`, `factory.entry.contract`. Sections: *Identity, order and places of work items*, *The data of a work item*, *Reading and writing a work item file*, *Sections of a Markdown body*, *The form check of a story*. Subsections other files refer to: *The records contract*, *The feature acceptance*.
- `costs.md`: cost records and bills. It describes `factory.domain.cost_records`, `factory.adapters.cost_records_jsonl`, `factory.application.costs`, `factory.domain.bills` and `factory.entry.bill` (`factory-bill`). It also names `factory.domain.human_waits`. Sections: *Cost records*, *Bills*.
- `stages.md`: the pipeline definition and a stage from the claim to the result commit. It describes `factory.application.claims`, `factory.domain.lease`, `factory.domain.pipeline_definition`, `factory.application.pipeline_loading`, `factory.application.task`, `factory.domain.prompts`, `factory.application.opening`, `factory.application.stage` and `factory.application.stalls`. It also names `factory.adapters.pipeline_yaml`, `factory.application.provider_limits`, `factory.domain.decisions`, `factory.domain.errors`, `factory.domain.labels`, `factory.domain.post_texts`. Sections: *The claim service*, *The pipeline definition*, *The prompt and the request for a stage*, *Opening a work item*, *Starting a stage*, *Stalls*, *After the agent run*, *The decision rules*, *The stage protocol*.
- `watching.md`: the evaluation, the tick, its handlers, the stops and the boundaries. It describes `factory.domain.evaluation`, `factory.application.watcher`, `factory.application.tick`, `factory.application.handlers`, `factory.application.recovery`, `factory.domain.stops`, `factory.application.stops` and `factory-watch`, `factory-run`. It also names `factory.adapters.atomic_file`, `factory.adapters.clock`, `factory.adapters.disk_space`, `factory.adapters.factory_log`, `factory.adapters.health_file`, `factory.adapters.preflight_stamp_file`, `factory.application.board`, `factory.application.boundaries`, `factory.application.dispatcher`, `factory.application.machine`, `factory.application.scheduler`, `factory.application.sealed_runs`, `factory.application.handlers.closed`, `factory.application.handlers.comments`, `factory.application.handlers.hand_over`, `factory.application.handlers.lookups`, `factory.application.handlers.merged`, `factory.application.handlers.questions`, `factory.application.handlers.recording`, `factory.application.handlers.reject`, `factory.application.handlers.run`, `factory.application.handlers.run_gate`, `factory.domain.answers`, `factory.domain.archive`, `factory.domain.board`, `factory.domain.events`, `factory.domain.hand_over`, `factory.domain.move_rule`, `factory.domain.preflight`, `factory.domain.recovery`, `factory.domain.send_back`, `factory.domain.stop_table`, `factory.domain.tick_status`, `factory.entry.run`, `factory.entry.watch`, `factory.entry.wiring`. Sections: *The evaluation*, *The tick*, *The handlers of the events*, *Stops, the clock and the factory log*. Subsections other files refer to: *Boundaries*.

## Errors

`factory.domain.errors.FactoryError` is the root of every error the factory raises on purpose. Later stories add their error types under it. `InjectedKill` (below) is deliberately not one.

`BoundaryError` (a `FactoryError`) is the root of the errors for an outside party that failed. `HostingServiceError(operation, detail)` is its first subtype: every implementation of the hosting-service interface raises it for every failing call, and its message is `hosting service <operation> failed: <detail>`. `operation` and `detail` are attributes.

`GitError(command, exit_status, output_tail)` is its second subtype, for the git wrapper. `command` is `git ` and the arguments (`git fetch --prune origin`); `exit_status` is `None` when git could not be started or hit its time limit; `output_tail` is the last 30 lines of the output, stdout and stderr merged (all of it when shorter). The message is `<command> failed (exit <status>): <tail>`, or `failed (no exit status)` when the status is `None`. `FetchFailed` is a `GitError` that `fetch` raises for every failure. `NothingToCommit` is a `GitError` that `commit` raises when nothing is staged.

`ProjectCommandError(command, detail)` is its third subtype, for the project commands: it is raised only when a command cannot be started (an invalid name, or an executable the operating system cannot start). The message is `project command <command> failed: <detail>`; `command` and `detail` are attributes. A red command is a result, not this error.

`AgentRuntimeError(detail)` is its fourth subtype, for the agent runtime. The message is `agent runtime failed: <detail>`; `detail` is an attribute. A run that dies, hits its `time_limit` or runs out of budget is a result, not this error (see *The agent runtime*).

`PushFailed(branch, outcome)` is a `FactoryError` for a push that did not reach the remote; `outcome` is the git wrapper's `PushOutcome` other than `"pushed"` (`rejected`, `unreachable`), and the message names the branch and the outcome. The claim service raises it (see *The claim service*).

`CannotHandle(kind, reason)` is a `FactoryError` that a handler raises when it cannot do its work, so the dispatcher counts it as an error; `kind` is the event's kind, and the message is `cannot handle <kind>: <reason>`.

`WorkItemFormatError(fault, path=None)` is a `FactoryError` for a work item file that cannot be read (see *The data of a work item*).

`ConfinementError(detail)` is a `FactoryError` for a write restriction the kernel guard cannot make (see *The kernel's write guard*); the message is `detail` itself, and it names the path or the call.

`CostRecordFormatError(line, fault)` is a `FactoryError` for a cost record file that cannot be read or written; `line` is counted from 1 and the message is `line <line>: <fault>`.

## The models' configuration

Every Pydantic model under `src/factory` is frozen and refuses unknown keys (`frozen=True`, `extra="forbid"`). `tests/test_model_configuration.py` checks that for all of them at once: it imports every module of the package and tests each model defined there, private ones included. A new model therefore needs no test of its own for an assignment or an unknown key. A test of a pattern, a `Literal`, a limit or a rule across fields is still the story's.

A model that reads a tool's own output declares `extra="ignore"`, so that a field the tool adds later does not break the factory. It joins the `EXCEPTIONS` list of that test by its dotted name. There are six: `_ToolInput` and `_Payload` in `factory.adapters.claude_guard`, and `_Usage`, `_Denial`, `_StructuredOutput` and `_Reply` in `factory.adapters.claude_runtime`. The test also checks that each exception is a model that ignores unknown keys, so an exception that becomes closed must leave the list.

## Kill points

A test that must show the factory survives its own death arms a kill point. The seam is `factory.domain.kill_points`; F0008's tests arm `BEFORE_PUSH` (`tests/application/test_recovery_crash.py`, a kill before the crash commit's push) and `AFTER_PUSH` (`tests/application/test_tick_stale_branch.py`, a discard killed after its push); `tests/test_kill_points.py` covers all four points (below).

There are four points, the members of `KillPoint`:

| Point | Value | Reached by |
|---|---|---|
| `AGENT_RUN` | `agent-run` | the two agent runtimes: the fake after the run's writes, `claude -p` after the last call and its result |
| `BEFORE_PUSH` | `before-push` | the git wrapper, before a push |
| `AFTER_PUSH` | `after-push` | the git wrapper, after a push |
| `AFTER_POST` | `after-post` | the fake hosting service and the PyGithub client, after posting |

Each wrapper in the table calls `kill_points.reach(point)` at its point; no other code reaches one.

A new `KillPoints` is inert. In a test, use the `kill_points` fixture from `tests/conftest.py`, which returns a new `KillPoints()` for each test, and hand it to the wrapper under test:

```python
def test_push_dies_after_the_second_try(kill_points: KillPoints) -> None:
    kill_points.arm(KillPoint.BEFORE_PUSH, after=1)
    with pytest.raises(InjectedKill):
        ...  # code that reaches BEFORE_PUSH twice
    assert kill_points.reached(KillPoint.BEFORE_PUSH) == 2
```

- `arm(point)` makes the next `reach(point)` raise `InjectedKill`. `arm(point, after=n)` lets `n` reaches pass first and raises on the next; `after` counts from the arming. A negative `after` raises `ValueError` and changes nothing.
- A point fires once and is then inert again. Arming an armed point replaces the earlier arming. Arming one point never changes another, armed or not.
- `reached(point)` counts every reach, the one that raises included, armed or not.
- Each `KillPoints` instance has its own state.
- `str(InjectedKill(point))` is `injected kill at <point value>`, and `.point` is the point that fired.

`InjectedKill` is a `BaseException`; see `docs/decisions.md`.

### The kill-point cases

`tests/test_kill_points.py` proves recovery by injection. Each case drives a real work item through the real `Tick` against a real local bare remote, the fake hosting service and the fake agent runtime, kills it at the kill point, restarts with the same instance name and checks the result after three ticks. The cases are data, `KILL_POINT_CASES` in `factory.domain.kill_point_cases` (a closed, frozen `KillPointCase`), so that other tests and the document check name the same ids.

| Id | What dies | Class | Charges a crash |
|---|---|---|---|
| `agent-run-tick` | the tick, at `AGENT_RUN` | crash | yes |
| `agent-run-dies` | the agent run; the tick lives | stall | no |
| `commit-push` | the tick, at `BEFORE_PUSH` (between the result commit and its push) | crash | yes |
| `post-record` | the tick, at `AFTER_POST` (between a post and its record) | crash | no |
| `tick-other` | the tick, at `AFTER_PUSH` (after the claim's push) | crash | yes |
| `container` | the container: `agent-run-tick` restarted on an empty disk | crash | yes |

A crash case has a kill point; a stall has none and never charges a crash. A crash is charged exactly when a stage was in flight at the kill: its stage-start commit was pushed and its result commit was not. That is why `post-record`, killed after the result was pushed, charges none.

The checks live in `tests/proof_support.py`, which no production module imports. `SCENARIOS` holds one script per id, `run_case(case, root)` plays it, and `violations(result, case, conditions)` names the conditions that do not hold, from `CRASH_CONDITIONS` (resumed at the first tick, the rerun's claim five seconds after the kill, no repeated post or step, no write of the interrupted run in any commit, stage-start commit kept, no discarded cost record, counters) or `STALL_CONDITIONS` (attempt charged, writes outside the write paths undone, state restored, writes inside kept, cost record kept). Two further tests pin the caps: two kills in one stage reach the crash cap of 2, and two died runs reach `attempts_cap` 2; each ends with exactly one post and no further request.

Run the cases with:

```bash
uv run pytest tests/test_kill_points.py tests/domain/test_kill_point_cases.py
```

The `world` fixture (`tests/conftest.py`) returns `build_world(tmp_path, template=remote_template)`, the world on a copy of that remote, for a test of your own (`build_world(root)` without a template makes its own remote); `start_story`, `run_ticks` and `restart` are the steps a scenario is made of. The time from kill to rerun is read on the `ManualClock`: a scenario advances it by `KILL_TO_RERUN` (5 seconds) between the kill and the restart; `rerun(world, empty_disk=False)` does both. The `work_item` fixture (`tests/conftest.py`) returns `start_story(world)`. `work_item_file(world, work_item)` is the work item's `.md` file on its remote branch; its `.costs.jsonl` sidecar beside it is not counted.

## Fault-injection paths

`tests/test_fault_paths.py` (paths 1 to 6) and `tests/test_fault_paths_7_to_13.py` (paths 7 to 13) walk v1's thirteen behaviour paths (a question, a rework, a cap, a close, a hand edit), each with one kill or one stall added at the step the path adds. A test runs the path against a real local bare remote, the fake hosting service and the fake agent runtime, with the cases and helpers of `tests/proof_support.py`. The paths are data, `FAULT_PATHS` in `factory.domain.fault_paths` (a closed, frozen `FaultPath` with `number`, `title`, `case` and `test`), so that this guide and the document check name the same tests.

| Path | Title | Case | Test |
|---|---|---|---|
| 1 | intake asks: a behaviour without a criterion | `agent-run-tick` | `test_intake_question_tick_killed_during_intake_run_reruns_free_and_asks_once` |
| 2 | intake asks for an edge case | `commit-push` | `test_intake_edge_case_question_killed_between_commit_and_push_reruns_intake_and_posts_once` |
| 3 | the tester finds a criterion against the interface | `post-record` | `test_tester_question_killed_between_post_and_record_posts_once` |
| 4 | a review rework | `agent-run-dies` | `test_review_rework_after_reviewer_run_dies_charges_one_attempt_then_one_round` |
| 5 | a documenter finding | `tick-other` | `test_docs_finding_tick_killed_after_move_back_push_counts_round_once_and_next_stage_starts` |
| 6 | a smoke test finding | `agent-run-dies` | `test_smoke_test_finding_after_run_reaches_time_limit_charges_one_attempt_then_moves_back` |
| 7 | the round cap | `post-record` | `test_round_cap_question_killed_between_post_and_record_posts_once_and_waits` |
| 8 | the attempts cap and its retry | `agent-run-dies` | `test_attempts_cap_run_stalls_twice_asks_human_without_a_rerun_and_reruns_on_comment` |
| 9 | `reject` after a stage change by hand | `commit-push` | `test_reject_killed_before_push_reverts_once_and_leaves_main_clean` |
| 10 | two work items in progress | `tick-other` | `test_two_items_in_progress_tick_killed_after_claim_push_reruns_lower_id_and_other_waits` |
| 11 | a close at the approval | `tick-other` | `test_close_at_approval_tick_killed_after_close_recorded_reopens_once_and_asks_once` |
| 12 | a feature acceptance refused, or merged | `container` | `test_acceptance_container_lost_in_review_reruns_once_and_books_result` |
| 13 | a test change the human approves | `agent-run-tick` | `test_test_change_approved_tick_killed_during_tester_run_reruns_tests_without_round` |

The case names the kill point the path arms (see *The kill-point cases*); the path's own crash charge may differ from the case's. Path 5 arms `AFTER_PUSH` after the result's push, which charges no crash, although its case `tick-other` does. Paths 4 and 6 use `agent-run-dies`, whose stall is a scripted result and not an armed point. Path 9 walks `reject` with the kill between the correction's commit and its push (`BEFORE_PUSH`): the rerun reverts the hand-made stage change once, and `origin/main` and the checkout stay clean. Path 12 is one test run for both results, `refused` and `accepted`, and restarts on an empty disk. Path 1 has a second half: a smoke test without an `Expect:` line is caught by `check_story_form`, not by an agent.

No path is mapped to a removing item: the thirteen are behaviour paths, none of them a kill point, and v1.1 keeps every mechanism they exercise.

Four further paths that v1's run 1 walked are not rows:

- the restart during a stage: removed by the claim and the crash rules; walked by paths 1 and 13;
- the close while the stages work: recorded first, no test of its own;
- the discarded story started again: removed by the empty bill at start;
- the merge while the move-back question is open: no item names it.

A path that fails is a defect to fix under `src/`, never a test to bend. Run the paths with:

```bash
uv run pytest tests/test_fault_paths.py tests/test_fault_paths_7_to_13.py tests/test_fault_paths_table.py tests/domain/test_fault_paths.py tests/domain/test_fault_paths_all_rows.py
```

`rerun_seconds(result)` and `branch_state(world, work_item)` in `tests/proof_support.py` are the proof's helpers for the time from the kill to the rerun's claim and for a work item's state on its branch (`None` when there is no branch); the paths use them instead of reading git a second way.
