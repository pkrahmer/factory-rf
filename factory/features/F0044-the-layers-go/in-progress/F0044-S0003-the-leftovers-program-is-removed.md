---
stage: tests
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 446
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T13:06:33.914663Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T13:06:33.920839Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-25T13:06:56.716175Z'
  stage: intake
  run: 7c7b7ef848924647ad7575fbfc3f35fc
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-25T13:07:16.845155Z'
  stage: tests
- number: 5
  speaker: tester
  kind: question
  at: '2026-10-25T13:11:49.015611Z'
  stage: tests
  run: 7d955ccbb648451a877ae899aa1b0286
  blocked: question
---

# The leftovers program is removed

## Description

Since F0027 (nothing a run leaves behind reaches the checks) every agent call and every project command run as the agent's user is followed by the leftovers program, `python -I -m factory.entry.leftovers --user <name>` started through `sudo`, which signals every process of that user but itself, so that nothing an agent started outlives its call. On a `container` instance a call ends with its container, and podman's `--timeout` ends a container whole (F0042-S0015 reads its 255 as the time limit); the program is never started there. This story removes the program and everything that starts, reads or configures it: the two modules, the process module's `own_identity` and `signal_every_other`, the launch module's leftovers launches, the runtimes' `leftovers` keyword and their `_end_leftovers`, the project commands' `CommandUser.leftovers`, and the wiring's `leftovers_command` with `build_boundaries`'s `end_leftovers`. It is built before S0004 (the fresh home) and S0005 (the second user), because the program exists only as a call of the second user (decision 1 of `feature.md`). What stays: the kill of a call at its time limit (the factory's own kill of the process's session, and under `sudo` the agent's own `timeout` until S0005); `killed_at_limit` and both kill-status sets; the process table reading, which the session kill still uses until S0010 (decision 7).

## Interface

Removed whole: `src/factory/entry/leftovers.py`, `src/factory/domain/leftovers.py`.

`factory.adapters.process` (`adapters`): `own_identity` and `signal_every_other` go, with the `pwd` import and the import of `Identity` from `factory.domain.leftovers` (nothing else reads either). `read_process_table`, `_kill_session` and `_kill_one` stay.

`factory.adapters.agent_launch` (`adapters`): `LEFTOVERS_TIME_LIMIT`, `LEFTOVERS_FAULT`, `leftovers_due`, `leftovers_launch`, `due_leftovers_launch`, `leftovers_fault` and the import of `LEFTOVERS_PREFIX` go; `Starters` loses `leftovers`:

```python
class Starters(BaseModel):
    sudo_executable: str
    login_files: LoginFiles
```

`factory.adapters.claude_runtime` and `factory.adapters.opencode_runtime` (`adapters`): each constructor loses the keyword `leftovers`, each class the property `leftovers` and the method `_end_leftovers`, each module its import of `own_identity`; a call's end is read as before without a leftovers fault.

`factory.adapters.make_commands` (`adapters`): `CommandUser` loses `leftovers`; `MakeProjectCommands._end_leftovers`, the keyword `merge_stderr` of `MakeProjectCommands._start` (only `_end_leftovers` passed `False`) and the imports of `LEFTOVERS_FAULT`, `leftovers_fault`, `leftovers_launch` and `own_identity` go. A command as a user is read as before without a leftovers fault.

`factory.entry.wiring` (`entry`): `LEFTOVERS_MODULE` and `leftovers_command` go (and from `__all__`); `build_boundaries` loses the keyword `end_leftovers`; neither runtime nor `CommandUser` gets a leftovers program.

Tests (the leave is decision 19 of `feature.md`):

- Deleted whole: `tests/entry/test_leftovers.py`, `tests/domain/test_leftovers.py`, `tests/adapters/test_agent_launch_leftovers.py`, `tests/adapters/test_claude_runtime_leftovers.py`, `tests/adapters/test_opencode_runtime_leftovers.py`, `tests/entry/test_wiring_leftovers.py`; `tests/leftovers_runtime_support.py` when no remaining module imports it (else S0005 deletes it).
- `tests/adapters/test_process_table.py::test_own_identity_is_the_running_process` is deleted; the module's other two tests stay.
- `tests/leftovers_support.py`: `AGENT`, `ROOT` and the import of `Identity` go; `process_entry` stays.
- `tests/adapters/test_make_commands_user.py::test_a_command_run_as_another_user_is_followed_by_the_leftovers_program` is deleted with `LeftoversRow`; `_user` builds `CommandUser` without `leftovers`.
- `tests/adapters/test_claude_runtime_container.py::test_a_call_in_a_container_starts_no_leftovers_program_and_no_temporary_folder` and the same test of `tests/adapters/test_opencode_runtime_container.py`: the runtime is built without `leftovers`; each keeps its name and checks the one launch.
- `tests/adapters/container_runtime_support.py`: its stand-in leftovers program goes when no test reads it.
- `tests/test_process_search.py::test_the_only_suppression_markers_are_the_four_in_the_process_wrapper`: the `entry/leftovers.py` entry goes; `tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module`: the set loses `factory.entry.leftovers`; `tests/entry/test_wiring_constants.py::test_the_wiring_offers_its_names_but_no_list_of_kinds_without_a_handler`: the name `leftovers_command` goes from its list; `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer`: the set loses `factory.entry.leftovers`. Each keeps its name.
- F0042-S0010's `tests/entry/test_wiring_stage_environment.py::test_a_container_instance_gets_the_dataset_s_adapters_and_asks_for_no_tool` and `::test_a_container_instance_s_runtime_runs_in_its_containers_unconfined`: each calls `build_boundaries` without `end_leftovers=True`, and the second loses its assertion `agent_runtime.leftovers is None` with the property; each keeps its name.
- F0040's `tests/entry/test_wiring_project_command_user.py::test_the_built_project_commands_run_as_the_agent_user_inside_a_seal`: the row `no-leftovers` and the columns `end_leftovers` and `leftovers` go, with the module's import of `leftovers_command`; the expected `CommandUser` has no `leftovers`; the test keeps its name (S0005 deletes the module).

## Acceptance criteria

1. The removed modules (rows of one parametrized test): `importlib.util.find_spec` is `None` for `factory.entry.leftovers` and `factory.domain.leftovers`.
2. The removed names (rows of one parametrized test): `own_identity` and `signal_every_other` are no attributes of `factory.adapters.process`; none of `LEFTOVERS_TIME_LIMIT`, `LEFTOVERS_FAULT`, `leftovers_due`, `leftovers_launch`, `due_leftovers_launch`, `leftovers_fault` is one of `factory.adapters.agent_launch`; `Starters.model_fields` is exactly `sudo_executable`, `login_files`; `CommandUser.model_fields` holds no `leftovers`; `leftovers_command` and `LEFTOVERS_MODULE` are none of `factory.entry.wiring`; neither runtime has the attribute `leftovers` nor a constructor parameter `leftovers`; `build_boundaries` has no parameter `end_leftovers`.
3. A call as another user is one call (rows of one parametrized test, Claude Code and opencode with the stand-in `sudo` of `tests/sudo_support.py` that records each call): a completed run with an `os_user` records exactly one `sudo` call per agent call, and a resumed run exactly two; a `make` command through `MakeProjectCommands` with a `CommandUser` records exactly one.
4. The kill at the limit stays (rows of one parametrized test): `killed_at_limit(os_user="agent", exit_status=137, duration=30 s, time_limit=30 s)` is `True`, the same at 29.9 s `False`; `killed_at_limit(os_user=None, exit_status=255, duration=30 s, time_limit=30 s, in_container=True)` is `True` (podman's `--timeout`, F0042-S0015), the same without `in_container` `False`; `run_process` of a stand-in that sleeps 30 seconds under a `time_limit` of 1 second ends `timed_out` within `ROOMY_BOUND_SECONDS`.
5. The source (one test reading `src/factory`): no module holds the strings `factory.entry.leftovers` or `cannot end the agent's processes`.
6. `make check` stays green.
7. docs: `docs/project-guide/agents.md`, *Ending the agent's leftover processes*: replaced by one sentence that a container ends with its call and podman's time limit ends it whole, and that the program went with F0044-S0003; `docs/project-guide/write-guard.md`, *The end of a run's processes*: one line in *Replaced in v1.2*; `docs/project-guide/processes-and-checks.md`, *Running as another user*: no leftovers program after a command; `docs/project-guide/README.md`, *The files*: the lines of those files follow, and *Shared test helpers*: the line of `leftovers_support.py` names only `process_entry`, and the line of `leftovers_runtime_support.py` goes if the module goes; `docs/project-guide/agents.md`, the signatures of `ClaudeCodeRuntime` and `OpencodeRuntime` and *The shared launch module* (the make class's `leftovers_launch` and `leftovers_fault`, the bullet on `Starters.leftovers`): no `leftovers`; `docs/project-guide/watching.md`, *Boundaries*: the paragraph on `leftovers_command` goes and `build_boundaries` has no `end_leftovers`; `docs/project-guide/stage-environment.md`, the table of the two environments and the sentence after it: no leftovers program and no `end_leftovers`; `docs/project-guide/processes-and-checks.md`, *Starting a process*, its known limits: no leftovers program ends a holder; `docs/operator-guide.md`, *The agent runs as a second user* and wherever it names the leftovers program or its fault `cannot end the agent's processes:`: the sentences go. `docs/decisions.md`: the entries "A run's leftover processes are ended by a program that runs as the agent" and "Every agent call is followed by the end of the agent's leftover processes" each gain one closing line: "Replaced by the end of the call's container, v1.2 F0044-S0003." `README.md`: none.

## Smoke test

```bash
for module in factory.entry.leftovers factory.domain.leftovers; do uv run python -c "import $module" 2>/dev/null && echo "$module present" || echo "$module gone"; done
uv run python -c 'from factory.adapters import process, agent_launch; from factory.entry import wiring; print([n for n, m in (("own_identity", process), ("signal_every_other", process), ("leftovers_launch", agent_launch), ("leftovers_command", wiring)) if hasattr(m, n)])'
```
Expect: three lines: `factory.entry.leftovers gone`; `factory.domain.leftovers gone`; `[]`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names concrete modules, removed names and the new `Starters` signature. Test changes are listed by test with the leave (decision 19, extended by 32a). Nothing is vague.
   Criteria: 1 to 5 each fit one parametrized or single test. 1 covers the two modules and 2 covers every removed name, field and parameter. 3 covers the single-call behaviour for both runtimes and the make class, resumed run included. 4 covers both sides of `killed_at_limit` (30 s and 29.9 s, with and without `in_container`) and the timed-out kill. 5 covers the source strings. The Interface states no rule with a failing side that needs its own criterion, because the story removes code. 6 and 7 are the closing criteria.
   Smoke test: both commands are runnable `uv run python -c` lines with no pytest, so there is no `-q` issue. The `Expect:` line gives three exact output lines that can be compared.
   Architecture: the removals touch domain, adapters and entry in the direction of the layers. `process_table` and the session kill stay (decision 7). No new interface or dependency.
   Scope: inside F0044 S0003 in `feature.md`. Nothing from "Out of scope" is touched. The docs and `CLAUDE.md` changes 4 and 6 fall outside the story, as decision 32 says.
4. factory: started tests as self.
5. tester: Question: one earlier test contradicts criterion 2, and the Interface's list of test changes leaves it out. `tests/adapters/test_runtimes_without_wrapper.py::test_the_starters_are_sudo_the_login_files_and_the_leftovers_program` (F0044-S0001) asserts `list(Starters.model_fields) == ["sudo_executable", "login_files", "leftovers"]`. Once `Starters` loses `leftovers`, that test fails, and the coder may not edit tests. The options I see:
   (a) Delete the test. Criterion 2's row `starters-fields` already checks the new field list. This is the one I would choose.
   (b) Keep the test and change its expectation to `["sudo_executable", "login_files"]`. Its name would then no longer match what it checks.
   (c) Change the expectation and rename the test to `test_the_starters_are_sudo_and_the_login_files`.
   Please say which one, and I will make that change.

   Everything else for this stage is written:
   criterion 1: tests/test_leftovers_program_removed.py::test_the_leftovers_modules_are_gone
   criterion 2: tests/test_leftovers_program_removed.py::test_the_names_that_started_the_leftovers_program_are_gone
   criterion 3: tests/adapters/test_one_call_as_another_user.py::test_a_call_as_another_user_is_one_sudo_call_per_agent_call
   criterion 4: tests/adapters/test_kill_at_the_limit_stays.py::test_a_call_is_still_killed_at_its_time_limit
   criterion 5: tests/test_leftovers_program_removed.py::test_no_module_names_the_leftovers_program_or_its_fault

   Files created: tests/test_leftovers_program_removed.py, tests/adapters/test_one_call_as_another_user.py, tests/adapters/test_kill_at_the_limit_stays.py.

   Earlier test changes, all ones the Interface names (decision 19 of feature.md):
   - Deleted: tests/entry/test_leftovers.py, tests/domain/test_leftovers.py, tests/adapters/test_agent_launch_leftovers.py, tests/adapters/test_claude_runtime_leftovers.py, tests/adapters/test_opencode_runtime_leftovers.py, tests/entry/test_wiring_leftovers.py.
   - tests/adapters/test_process_table.py: `test_own_identity_is_the_running_process` is gone.
   - tests/leftovers_support.py: `AGENT`, `ROOT` and the `Identity` import are gone; `process_entry` stays.
   - tests/adapters/test_make_commands_user.py: the leftovers test and `LeftoversRow` are gone, and `_user` no longer takes `leftovers`.
   - tests/adapters/test_claude_runtime_container.py and tests/adapters/test_opencode_runtime_container.py: the runtime is built without `leftovers`, and `write_record_program` is gone from tests/adapters/container_runtime_support.py.
   - tests/test_process_search.py, tests/test_wrapper_search.py, tests/entry/test_wiring_constants.py, tests/entry/test_wiring.py: the leftovers entries are gone.
   - tests/entry/test_wiring_stage_environment.py: `end_leftovers=True` and the `leftovers is None` assertion are gone.
   - tests/entry/test_wiring_project_command_user.py: the `no-leftovers` row, the `end_leftovers`/`leftovers` columns and the `leftovers_command` import are gone.
   - tests/leftovers_runtime_support.py stays: test_make_commands_user.py still imports `SUDO_LINE` from it, so S0005 deletes it.

   `make test` result: no module failed to import; every failure is a wrong result. These fail, as they should: every test of criteria 1, 2 and 5, test_process_search's markers test, test_wiring's importers test, test_wrapper_search's process-module test, and the `agent-user` and `no-sudo-found` rows of test_wiring_project_command_user.
   Criteria 3 and 4 already pass: with no leftovers program set, the runtimes and the make class make one `sudo` call today. They guard the behaviour while the code is removed.
   `make lint` is green. I did not run the type check, as the stage says.
