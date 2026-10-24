# Project guide

The guide for agents working on `factory-rf`: how the code is laid out, where a change belongs, which conventions the checks do not catch, and what to read first. It is this index and one file per domain: read the index, then the files of the domains your story touches. It grows with each story: the documenter stage fills it in from the stories' docs criteria. `CLAUDE.md` holds the rules every change follows.

A file of the guide is split by the same rule before it passes about 600 lines: its sections go by domain to a new file, and the new file is named here.

## The files

Each file starts with a title and a sentence on what it covers.

- `README.md` (this index): what holds for all code. Sections: *The files*, *Shared test helpers*, *Errors*, *The models' configuration*, *Kill points*, *Fault-injection paths*.
- `git-and-hosting.md`: git and the hosting service. It describes the hosting-service interface with its PyGithub and fake implementations (`factory.application.hosting`, `factory.adapters.pygithub_hosting`, `factory.adapters.fake_hosting`, `factory.domain.hosting`) and the git wrapper (`factory.application.git`, `factory.adapters.git_cli`, `factory.domain.git`). It also names `factory.domain.settings`. Sections: *The hosting service*, *The git wrapper*.
- `processes-and-checks.md`: processes, project commands and this repository's checks. It describes the project-commands interface and its make implementation (`factory.application.project_commands`, `factory.adapters.make_commands`), the one module that starts processes (`factory.adapters.process`), and the commands behind `make duplicates` and `make documents` (`factory.domain.duplicates`, `factory.domain.documents`). It also names `factory.adapters.record_log_jsonl`, `factory.application.disk_records`, `factory.application.known_results`, `factory.application.preflight`, `factory.domain.checks`, `factory.domain.command_records`, `factory.domain.disk`, `factory.domain.known_results`, `factory.domain.sessions`, `factory.entry.check_demos`, `factory.entry.check_documents`, `factory.entry.check_duplicates`, `factory.entry.inputs`. Sections: *Project commands*, *Starting a process*, *The duplicates report*, *The document check*, *The demos*, *Mutation testing* (`make mutants`, the sweep form).
- `agents.md`: the agent runtime, the agent files, the shipped agents and the template. It describes the agent-runtime interface and its implementations (`factory.application.agent_runtime`, `factory.adapters.claude_runtime`, `factory.adapters.agent_launch`, `factory.domain.agent_runs`), the agent files reader (`factory.adapters.agent_files`) and the files under `claude/`. It also names `factory.adapters.fake_agent_runtime`, `factory.adapters.opencode_runtime`, `factory.adapters.validation_faults`, `factory.application.project_agents`, `factory.domain.provider_limits`. The fresh home (`factory.domain.agent_home`, `factory.application.agent_home`, `factory.adapters.agent_home`, `factory.adapters.home_files`, `factory.entry.fresh_home`) is in the same file. Sections: *The agent runtime*, *The agent definition reader*, *The shipped agents, settings and template*, *Replaced from v1*. Subsections other files refer to: *The opencode runtime*, *The fresh home*.
- `write-guard.md`: the write paths, the guard, the undo, the kernel's guard, the start wrapper and the program that ends a run's leftover processes. It describes `factory.application.write_paths`, `factory.domain.write_paths`, `factory.application.undo`, `factory.adapters.landlock`, `factory.domain.confinement`, `factory.entry.confine` (`factory-confine`), `factory.domain.leftovers` and `factory.entry.leftovers`, and names `factory.adapters.process` for `own_identity`, `signal_every_other` and `read_process_table`. Sections: *The write paths*, *The undo*, *The kernel's write guard*, *The start wrapper*, *The end of a run's processes*.
- `work-items.md`: the identity, data, files, sections and form of a work item. It describes `factory.domain.identifiers`, `factory.domain.paths`, `factory.domain.work_item`, `factory.domain.journal`, `factory.domain.sections`, `factory.domain.story_form`, `factory.adapters.work_item_markdown` and `factory.entry.check_story`. It also names `factory.application.acceptance`, `factory.application.acceptance_reading`, `factory.application.files`, `factory.application.work_items`, `factory.domain.acceptance`, `factory.domain.contract`, `factory.domain.times`, `factory.entry.contract`. Sections: *Identity, order and places of work items*, *The data of a work item*, *Reading and writing a work item file*, *Sections of a Markdown body*, *The form check of a story*. Subsections other files refer to: *The records contract*, *The feature acceptance*.
- `costs.md`: cost records and bills. It describes `factory.domain.cost_records`, `factory.adapters.cost_records_jsonl`, `factory.application.costs`, `factory.domain.bills` and `factory.entry.bill` (`factory-bill`). It also names `factory.domain.human_waits`. Sections: *Cost records*, *Bills*.
- `stages.md`: the pipeline definition and a stage from the claim to the result commit. It describes `factory.application.claims`, `factory.domain.lease`, `factory.domain.pipeline_definition`, `factory.application.pipeline_loading`, `factory.application.task`, `factory.domain.prompts`, `factory.application.opening`, `factory.application.stage` and `factory.application.stalls`. It also names `factory.adapters.pipeline_yaml`, `factory.application.provider_limits`, `factory.domain.decisions`, `factory.domain.errors`, `factory.domain.labels`, `factory.domain.post_texts`. Sections: *The claim service*, *The pipeline definition*, *The prompt and the request for a stage*, *Opening a work item*, *Starting a stage*, *Stalls*, *After the agent run*, *The decision rules*, *The stage protocol*.
- `watching.md`: the evaluation, the tick, its handlers, the stops and the boundaries. It describes `factory.domain.evaluation`, `factory.application.watcher`, `factory.application.tick`, `factory.application.handlers`, `factory.application.recovery`, `factory.domain.stops`, `factory.application.stops` and `factory-watch`, `factory-run`, `factory-health`. It also names `factory.adapters.atomic_file`, `factory.adapters.clock`, `factory.adapters.disk_space`, `factory.adapters.factory_log`, `factory.adapters.health_file`, `factory.adapters.preflight_stamp_file`, `factory.application.board`, `factory.application.boundaries`, `factory.application.dispatcher`, `factory.application.machine`, `factory.application.scheduler`, `factory.application.sealed_runs`, `factory.application.handlers.closed`, `factory.application.handlers.comments`, `factory.application.handlers.hand_over`, `factory.application.handlers.lookups`, `factory.application.handlers.merged`, `factory.application.handlers.questions`, `factory.application.handlers.recording`, `factory.application.handlers.reject`, `factory.application.handlers.run`, `factory.application.handlers.run_gate`, `factory.domain.answers`, `factory.domain.archive`, `factory.domain.board`, `factory.domain.events`, `factory.domain.hand_over`, `factory.domain.move_rule`, `factory.domain.preflight`, `factory.domain.recovery`, `factory.domain.send_back`, `factory.domain.stop_table`, `factory.domain.tick_status`, `factory.entry.health`, `factory.entry.run`, `factory.entry.watch`, `factory.entry.wiring`. Sections: *The evaluation*, *The tick*, *The handlers of the events*, *Stops, the clock and the factory log*. Subsections other files refer to: *Boundaries*.
- `stage-environment.md`: the dataset and the containers a stage runs on, behind interfaces. It describes `factory.application.snapshots`, `factory.application.containers`, `factory.domain.containers`, `factory.adapters.fake_snapshots` and `factory.adapters.fake_containers`. Sections: *The snapshots*, *The container runs*, *The fakes*.

## Shared test helpers

A helper that more than one test module uses lives in a module at the root of `tests/` (a fixture, in `tests/conftest.py`), and a test module imports it from there; `CLAUDE.md`'s standing leave to move a shared test helper intends this. Before writing a helper, look here: the reviewer counts a copy as a finding. The guards `tests/test_shared_*.py` fail on a copy of a shared helper, and `test_shared_bodies.py` finds a copy of `log_lines`, `pushed`, `pushed_state`, `remote_document` and `push_state` by its body under any name. A story that adds such a module names it in this list through its docs criterion. A story that adds a fixture to either conftest names it in that conftest's line through its docs criterion.

Every module `tests/*.py` whose name does not start with `test_`:

- `conftest.py`: the fixtures of the whole suite. Every test: `reopened_tmp_path` (autouse; after a test that uses `tmp_path`, gives its owner back every folder and file under it). Doubles and time: `kill_points` (inert kill points), `agent_runtime` and `hosting` (the fakes, on those kill points), `clock` (a manual clock at noon UTC on 2026-10-12). Git: `remote_template` (session-wide; one remote that each test's remote copies), `remote` (a bare repository whose `main` holds a small factory layout), `checkout` (a `GitCli` on a fresh clone of `remote`), `human` (the human's own `HumanClone`). Paths and settings: `agent_home` (a path in `tmp_path`; nothing is created), `local_settings` (instance settings whose checkout, state and agent home lie in `tmp_path`), `disk_settings` (settings whose checkout and state directory lie under `tmp_path`), `disk_records` (the disk record log in `tmp_path`), `probe_settings` (settings whose agents run as the user `agent`), `hosted_environment` (a valid environment with token and image identity files in `tmp_path`), `group_umask` (runs the test under the entrypoint's umask `0002`). The factory on those: `boundaries` (the interfaces on the test's checkout, fakes and clock), `definition` (the remote's parsed pipeline definition, with the acceptance stage `acceptance`), `installed_agents` (a valid agent file for every role of that definition), `walk` (an `AcceptanceWalk` over the feature `F0002-todo`, due with two archived stories). The recovery proof: `world` (a world built under `tmp_path`), `work_item` (a story started in that world). Image and runtime tests: `compose_service` (the service `factory` of the compose file), `layout` (a checkout with `src` and `other`, a home and a temporary root), `image_layout` (the entrypoint run's homes, state and stubs), `records` (the stop records in the test's state directory), `recorder` (replaces the runtime's `run_process` with a `Recorder`).
- `application/handlers/conftest.py`: the fixtures of the handlers' tests under `tests/application/handlers/` only: `snapshot_of` (builds a snapshot, not on the remote, holding a given state), `state_with` (builds a state at `doing` with one journal record and the pull request), `event_of` (builds an event of a kind about a snapshot), `pull_request` (the number of an open draft pull request of the work item's branch), `work_item` (the snapshot of a work item the human pushed to its branch, fetched locally: a published work item of the handlers' tests, not the root's started story).
- `acceptance_support.py`: `report_of`, a feature's acceptance report whose journal holds given entries.
- `acceptance_walk.py`: `AcceptanceWalk`, a walk of one feature's acceptances over real ticks with the human's acts between, and its constants.
- `bill_support.py`: `completed_records` and `sidecar_text`, completed cost records and the text of their sidecar.
- `branch_reading.py`: the work item on a work item's branch and the factory's posts on its pull request (`remote_document`, `error_posts`, `push_state`).
- `compose_support.py`: `COMPOSE`, the compose file the image ships.
- `confine_support.py`: the run layout, the stand-in `factory-confine` executable and the request of the runtime's guard tests (`build_layout`, `write_confine`, `run_request`, `confined_runtime`).
- `contract_support.py`: the contract command's output lines and `MainRow`, a row of `main`'s cases.
- `crash_support.py`: a work item claimed by this instance, ready to crash (`claim`, `expired_claim`, `crash_event`, `handler`), for the crash-cap tests.
- `definition_support.py`: `pipeline_definition`, the test remote's pipeline definition read through the boundaries' reader, which the `definition` fixture returns too, for helpers that take no fixtures.
- `disk_support.py`: `FakeDiskSpace`, a fake of the disk-space interface that answers per path.
- `dockerfile_support.py`: `dockerfile_instructions` and `DOCKERFILE`, for tests that read the image's Dockerfile.
- `document_texts.py`: builders for the four documents' texts, clean unless a test asks for a fault (`readme`, `operator_guide`, `project_guide`, `decision_log`, `write_documents`).
- `entrypoint_support.py`: the entrypoint tests' layout, stub executables and stamped lines.
- `evaluation_support.py`: the shared inputs of the evaluation's tests (a pipeline definition, snapshots, lookups, claims).
- `function_support.py`: `functions` (the top-level functions of a source text, read with `ast`) and `without_docstring` (a body's statements, a leading docstring left aside).
- `git_support.py`: helpers for tests against real git: isolated runs, the bare remote and its copies, stand-in executables, agent files (`run_git`, `make_remote`, `copy_remote`, `clone`, `commit_all`, `install_agents`).
- `human_clone.py`: `HumanClone`, a second clone of the test remote that acts as the human: starts stories, pushes, merges.
- `log_support.py`: `log_lines`, the factory log a test's state directory holds.
- `observing_runtime.py`: `ObservingRuntime`, an agent runtime that records what the remote and the hosting fake hold when a run starts.
- `preflight_support.py`: `fail_once` and `failed_once`, the preflight's rig after one probe of a red main.
- `probe_support.py`: the agent environment, the completed run and the opencode texts (`opencode_died`, `opencode_sso_hint`) of the probe tests.
- `process_support.py`: real child processes in tests (`python_argv`, `Recorder`, `is_gone`).
- `project_command_support.py`: `raising`, the answers for a recording stand-in of the project commands.
- `proof_support.py`: the recovery proof, described under *Kill points* and *Fault-injection paths*.
- `record_support.py`: `UnwritableRecordLog`, a record log that cannot be written.
- `recording_log.py`: `RecordingLog`, a factory log that keeps the lines written to it.
- `run_process_recorder.py`: `Recorder`, a stand-in for the runtime's `run_process` that keeps each request.
- `search_support.py`: `modules_matching`, a search of the test modules for a pattern.
- `settings_support.py`: `BASE`, the environment with the two required settings, and `raising`, for the tests that read settings.
- `shipped_agents.py`: `SHIPPED_AGENTS` and `ShippedAgent`, the seven shipped agents' front matter values and the opening of their bodies.
- `source_search.py`: reads the modules under `src/factory` with `ast`: `modules`, `imports`, `string_literals`, `reads_os_environ`.
- `stage_run_support.py`: builders for whole stage runs: a story started on `main`, its branch, a Makefile and a run (`open_story`, `run_stage`, `stage_makefile`), and the work item at the head of the remote's branch (`pushed`, `pushed_state`), and `INSTANCE`, the instance name `"factory-1"` that every test module naming that instance imports from here, and `ENVIRONMENT`, the environment the stage-run tests pass; `tests/test_shared_constants.py` fails on another top-level assignment of the instance name.
- `sudo_support.py`: a stand-in `sudo` that records each call's arguments, environment and working directory and runs the call or exits as planned (`write_sudo`, `Sudo`, `SudoCall`).
- `tick_support.py`: `handlers_of` and `Failing`, the tick's handler factory and a handler that records each event and raises the error it is given, `ValueError("boom")` by default.
- `tmp_path_support.py`: `reopen`, which gives the owner back every folder and file under a test's `tmp_path` so that pytest can remove it.
- `undo_support.py`: a claimed stage start on a work item's branch, and the undo (`start_stage`, `undo_stage`, `pipeline_text`).
- `watch_support.py`: the watcher's shared data: a claimed story, the due `F0002-todo`, its acceptance (`push_story_claim`, `open_acceptance`, `aged_claim`).
- `wiring_support.py`: `every_tool`, `ENVIRONMENT` (the environment the handler and wiring tests pass) and the constants the wiring and preflight tests share. `tests/test_shared_environments.py` fails on another top-level assignment of either `ENVIRONMENT` value, this one or `stage_run_support.py`'s.
- `work_item_support.py`: `put_work_item`, `created_state` and `checkout_text`, for tests that put a work item on its branch.
- `write_path_support.py`: `stage_start` and `push_definition`, for the write-path service tests.

## Errors

`factory.domain.errors.FactoryError` is the root of every error the factory raises on purpose. Later stories add their error types under it. `InjectedKill` (below) is deliberately not one.

`BoundaryError` (a `FactoryError`) is the root of the errors for an outside party that failed. `HostingServiceError(operation, detail)` is its first subtype: every implementation of the hosting-service interface raises it for every failing call, and its message is `hosting service <operation> failed: <detail>`. `operation` and `detail` are attributes.

`GitError(command, exit_status, output_tail)` is its second subtype, for the git wrapper. `command` is `git ` and the arguments (`git fetch --prune origin`); `exit_status` is `None` when git could not be started or hit its time limit; `output_tail` is the last 30 lines of the output, stdout and stderr merged (all of it when shorter). The message is `<command> failed (exit <status>): <tail>`, or `failed (no exit status)` when the status is `None`. `FetchFailed` is a `GitError` that `fetch` raises for every failure. `NothingToCommit` is a `GitError` that `commit` raises when nothing is staged.

`ProjectCommandError(command, detail)` is its third subtype, for the project commands: it is raised only when a command cannot be started (an invalid name, or an executable the operating system cannot start). The message is `project command <command> failed: <detail>`; `command` and `detail` are attributes. A red command is a result, not this error.

`AgentRuntimeError(detail)` is its fourth subtype, for the agent runtime. The message is `agent runtime failed: <detail>`; `detail` is an attribute. A run that dies, hits its `time_limit` or runs out of budget is a result, not this error (see *The agent runtime*).

`SnapshotError(command, detail)` and `ContainerError(command, detail)` are further `BoundaryError`s beside `ProjectCommandError`, for the snapshots and the container runs: a command that failed, could not start or reached its time limit. The messages are `snapshot command <command> failed: <detail>` and `container command <command> failed: <detail>` (see *The stage environment*, `stage-environment.md`).

`PushFailed(branch, outcome)` is a `FactoryError` for a push that did not reach the remote; `outcome` is the git wrapper's `PushOutcome` other than `"pushed"` (`rejected`, `unreachable`), and the message names the branch and the outcome. The claim service raises it (see *The claim service*).

`CannotHandle(kind, reason)` is a `FactoryError` that a handler raises when it cannot do its work, so the dispatcher counts it as an error; `kind` is the event's kind, and the message is `cannot handle <kind>: <reason>`.

`WorkItemFormatError(fault, path=None)` is a `FactoryError` for a work item file that cannot be read (see *The data of a work item*).

`ConfinementError(detail)` is a `FactoryError` for a write restriction the kernel guard cannot make (see *The kernel's write guard*); the message is `detail` itself, and it names the path or the call.

`CostRecordFormatError(line, fault)` is a `FactoryError` for a cost record file that cannot be read or written; `line` is counted from 1 and the message is `line <line>: <fault>`.

## The models' configuration

Every Pydantic model under `src/factory` is frozen and refuses unknown keys (`frozen=True`, `extra="forbid"`). `tests/test_model_configuration.py` checks that for all of them at once: it imports every module of the package and tests each model defined there, private ones included. A new model therefore needs no test of its own for an assignment or an unknown key. A test of a pattern, a `Literal`, a limit or a rule across fields is still the story's.

A model that reads a tool's own output declares `extra="ignore"`, so that a field the tool adds later does not break the factory. It joins the `EXCEPTIONS` list of that test by its dotted name. There are twelve: `_Usage`, `_Denial`, `_StructuredOutput` and `_Reply` in `factory.adapters.claude_runtime`, and `_Event`, `_Part`, `_Tokens`, `_CacheTokens`, `_ToolState`, `_Span`, `_Error` and `_ErrorData` in `factory.adapters.opencode_runtime`. The test also checks that each exception is a model that ignores unknown keys, so an exception that becomes closed must leave the list.

## Kill points

A test that must show the factory survives its own death arms a kill point. The seam is `factory.domain.kill_points`; the recovery tests arm `BEFORE_PUSH` (`tests/application/test_recovery_crash.py`, a kill before the crash commit's push) and `AFTER_PUSH` (`tests/application/test_tick_stale_branch.py`, a discard killed after its push); `tests/test_kill_points.py` covers all four points (below).

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
