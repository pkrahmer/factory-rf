---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 444
comments_read: [6396634457]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-10-25T10:44:17.892927Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T10:40:39.245992Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T10:40:39.251939Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-25T10:40:59.942504Z'
  stage: intake
  run: 706131791ff74a248cca348a9c60d198
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-25T10:43:19.809593Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-25T10:43:37.543152Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-25T10:43:57.792726Z'
  stage: intake
  run: 12fda58793ae484899727422536edcd1
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-25T10:44:17.892927Z'
  stage: tests
---

# No agent call starts through the write guard's wrapper

## Description

Since F0019 (the write guard by the kernel) every agent call on the host starts through `factory-confine` with a rules file, its own temporary folder under the system's one and, for Claude Code, `CLAUDE_CONFIG_DIR`; the preflight item `confinement` checks the kernel's Landlock and the wrapper on the agent run's `PATH`. Since F0042 (the stage environment behind one interface) a `container` instance runs every agent call in a throwaway container, where the runtime refuses a confine executable, and the take keeps the write paths' meaning: what the agent wrote outside them is never taken. This story removes the wrapper from the call path: the shared launch module, both runtimes, the wiring and the preflight lose every part that builds, starts, reads or checks the wrapper, its rules and its temporary folder, and the shipped agents' rule R14 stops promising a kernel that refuses writes (decision 4 of `feature.md`). The modules of the kernel's guard themselves (`factory.adapters.landlock`, `factory.domain.confinement`, `factory.entry.confine`) and the definition's `tool_paths` stay until S0002 (the wrapper, the kernel's rules and the tool paths are removed). What stays: a call in a container is started exactly as F0042 left it; a call without a container (the inline environment's until S0008, and the suite's runtime tests for good, decision 2) starts the runtime's own command directly, through the login shell when a login file is set and through `sudo` when the request names an operating-system user (until S0005); the take and the undo refuse what the role may not write, unchanged.

## Interface

`factory.adapters.agent_launch` (`adapters`): these names go: `TEMPORARY_PREFIX`, `CLEANUP_SCRIPT`, `_CLEANUP_NAME`, `CLEANUP_TIME_LIMIT`, `CONFINE_PREFIX`, `confined_argv`, `cleanup_argv`, `temporary_folder`, `existing_devices`, `request_home`, `run_confinement`, `device_confinement`, `cleanup_launch`, and the module's imports of `factory.domain.confinement`. `Starters` loses the field `confine_executable`:

```python
class Starters(BaseModel):
    sudo_executable: str
    login_files: LoginFiles
    leftovers: list[str] | None = None
```

- `call_refusal(stderr, *, printed, timed_out, os_user, starters)` reads a refused `sudo` (a line beginning `sudo:`, only with an `os_user`) and a refused login file as today, and nothing else: a line beginning `factory-confine:` is no refusal of its own.

`factory.adapters.claude_runtime` (`adapters`): `ClaudeCodeRuntime.__init__` loses the keywords `confine_executable` and `temporary_root`, the property `confine_executable` and the `ValueError` for a confine executable beside `containers`; `_RunFiles` holds `instructions` alone; `CONFIG_VARIABLE`, `RUNTIME_FOLDER`, `_confinement`, `_config_folder` and `_remove_temporary_folder` go; `__all__` loses `CLEANUP_SCRIPT` and `CLEANUP_TIME_LIMIT`. `SWITCHES` and the call's environment otherwise are unchanged.

`factory.adapters.opencode_runtime` (`adapters`): `OpencodeRuntime.__init__` loses `confine_executable`, `temporary_root` and `runtime_folders`, the `ValueError` beside `containers`, and `RUNTIME_FOLDERS` goes; `_RunFiles` holds `config` alone; `_confinement` and `_remove_temporary_folder` go.

`factory.application.preflight` (`application`): `confinement_item`, `_kernel_fault`, `_CONFINEMENT_ITEM` and `_KERNEL_ADVICE` go, and its import of `factory.domain.confinement`. `_path_fault` stays (the `opencode` item reads it).

`factory.entry.wiring` (`entry`): `build_boundaries` loses the keyword `confine_executable` (its other keywords as F0042-S0010 left them); `_agent_runtime` passes neither a confine executable nor `runtime_folders`; `machine_extras` adds no `confinement` item for an `inline` instance (the `container` list of F0042-S0011 is unchanged); the import of `abi_version` and of `CONFINE_COMMAND` goes; `production_environment`'s comment no longer names `factory-confine`.

`claude/agents/*.md` (the seven shipped agents): the line that begins `R14.` becomes the text of decision 4 of `feature.md`, word for word, in each of the seven files (the human's words; `claude/*` is the coder's write path).

Rules:

- No module under `src/factory` but `factory.entry.confine`, `factory.adapters.landlock` and `factory.domain.confinement` names the string `factory-confine:` or `CLAUDE_CONFIG_DIR`, or imports `factory.domain.confinement` or `factory.adapters.landlock` (S0002 removes those three).
- A call without a container starts `[*login words, <executable>, *arguments]`, the login words only when a login file is set, after `sudo`'s words when the request names an `os_user`; a run leaves no rules file in the state directory and makes no folder whose name begins `factory-run-`.

Tests (the tester writes and changes them; the leave is decision 17 of `feature.md`): new tests at the tester's choice, for example `tests/adapters/test_runtimes_without_wrapper.py`. Earlier tests:

- Deleted whole: `tests/adapters/test_claude_runtime_confinement.py`, `tests/adapters/test_claude_runtime_confinement_root.py`, `tests/adapters/test_opencode_confinement.py`, `tests/adapters/test_opencode_runtime_folders.py`, `tests/application/test_confinement_item.py`, `tests/entry/test_wiring_confinement.py`, `tests/entry/test_wiring_extras_path.py` (both of its rows are the `confinement` item's).
- `tests/adapters/test_agent_launch.py`: `test_confined_argv_puts_the_wrapper_and_its_rules_before_the_call`, `test_cleanup_argv_removes_the_temporary_folder_as_the_runs_user`, `test_temporary_folder_is_named_after_the_run_under_the_root`, `test_existing_devices_holds_the_existing_folders_then_the_existing_files` and `test_run_confinement_allows_the_runtime_folders_under_home_and_the_guarded_checkout` are deleted; the other tests keep their names and assertions, their `Starters` without `confine_executable`.
- `tests/adapters/test_agent_launch_call_end.py` (its three tests), `tests/adapters/test_agent_launch_container.py::test_a_container_call_killed_at_the_limit_is_read_as_the_limit_and_no_refusal`, `tests/adapters/test_agent_launch_leftovers.py::test_the_program_is_due_only_with_a_program_and_a_user_other_than_the_own`: their `Starters` lose `confine_executable`; a row that reads a `factory-confine:` line as a refusal goes.
- `tests/adapters/test_claude_runtime_no_hook.py::test_no_run_registers_a_hook`: its row `confined-guarded` goes with the module's import of `confined_runtime`; the rows of `_unconfined` keep what they check.
- `tests/adapters/test_claude_runtime_container.py::test_a_runtime_keeps_its_containers_and_refuses_them_with_a_confine_executable` and the same test of `tests/adapters/test_opencode_runtime_container.py`: the refusal half goes, the test keeps its name; `::test_a_call_in_a_container_starts_no_leftovers_program_and_no_temporary_folder` of both modules: it builds the runtime without `temporary_root` and checks that no folder whose name begins `factory-run-` is added under the system's temporary folder, and otherwise what it checks today.
- `tests/leftovers_runtime_support.py`: its import of `CLEANUP_SCRIPT` and the kind `removal` of `kind` go.
- `tests/adapters/test_claude_runtime_leftovers.py`: the helper `_runtime` builds the runtime without `confine_executable` and `temporary_root`; `::test_after_the_call_the_program_runs_as_the_user_from_the_root_before_the_removal`, `::test_a_resumed_run_starts_the_program_after_each_of_its_calls` and `::test_a_failed_program_after_a_good_call_is_a_runtime_error_after_the_removal` expect no `removal` kind; `::test_a_call_refused_by_sudo_or_the_wrapper_keeps_its_own_error_and_still_starts_the_program` loses its row `confine`. The same in `tests/adapters/test_opencode_runtime_leftovers.py` for `_runtime` and its two tests. Every test keeps its name.
- `tests/adapters/test_opencode_runtime_launch.py`: `test_through_the_wrapper_the_call_gets_its_rules_with_opencode_s_folders` and `test_a_wrapper_line_without_events_is_a_runtime_error_naming_it` are deleted with the helpers `_confined_runtime` and `_warned_by_wrapper`; `test_a_call_that_printed_valid_events_is_no_refusal_whatever_its_stderr_holds` loses its row `wrapper`; the module's imports of `temporary_folder`, `Confinement` and the stand-in wrapper go.
- `tests/application/test_agent_run_probe.py::test_the_probe_runs_once_for_each_image_build` (its extra item is no `confinement_item`), with the module's imports of `confinement_item` and `LANDLOCK_MINIMUM_ABI`.
- `tests/entry/test_wiring_boundaries.py::test_the_built_agent_runtime_keeps_its_run_files_under_runs`, `tests/entry/test_wiring_api_login.py`, `tests/entry/test_wiring_login.py`, `tests/entry/test_wiring_provider_limit.py` (their one test each: no `confine_executable=None` argument), `tests/entry/test_wiring_extras.py` (both tests: no `confinement` name in the lists), `tests/entry/test_wiring_opencode.py` (its four tests: `test_the_built_opencode_runtime_allows_the_instance_s_folders_after_opencode_s` is deleted; `test_the_opencode_item_comes_after_confinement_only_under_opencode` keeps its name and checks that `opencode` comes right before `agent-run-probe`); and the rows of F0042-S0011's `tests/entry/test_wiring_container_extras.py` that repeat the `inline` lists of `test_wiring_extras.py`.
- F0042-S0010's `tests/entry/test_wiring_stage_environment.py::test_a_container_instance_gets_the_dataset_s_adapters_and_asks_for_no_tool`, `::test_a_container_instance_s_runtime_runs_in_its_containers_unconfined` and `::test_a_container_instance_s_runtime_mounts_its_login_file`: the argument `confine_executable="factory-confine"` and the assertion that the runtime's `confine_executable` is `None` go; the build still succeeds and `which` is still asked for nothing.
- `tests/test_claude_agent_refusal.py`: the constant that holds R14 becomes decision 4's text, and the old ending its tests look for is the sentence that begins `the kernel refuses every other write`; every test keeps its name.
- `tests/test_hook_removed.py::test_the_hook_s_code_is_gone_and_the_kernel_s_guard_is_kept`: its row `confinement-item` expects `False`; `test_the_guard_settings_have_no_temporary_folder` is unchanged.
- `tests/test_time_limits.py`: its row `claude-confinement-wait` goes with the module it reads.
- `tests/confine_support.py` keeps every name a kept test module imports (`Layout`, `build_layout`, `read_records`, `write_script`, `run_request`, and `USAGE`, `write_rules`, `Replaced` and `Steps`, which `tests/entry/test_confine*.py` read until S0002); `confined_runtime` and the stand-in wrapper go when no test reads them.

## Acceptance criteria

1. The removed names (rows of one parametrized test): none of `TEMPORARY_PREFIX`, `CLEANUP_SCRIPT`, `CLEANUP_TIME_LIMIT`, `CONFINE_PREFIX`, `confined_argv`, `cleanup_argv`, `temporary_folder`, `existing_devices`, `request_home`, `run_confinement`, `device_confinement`, `cleanup_launch` is an attribute of `factory.adapters.agent_launch`; `Starters.model_fields` is exactly `sudo_executable`, `login_files`, `leftovers`; `confinement_item` is no attribute of `factory.application.preflight`; `RUNTIME_FOLDERS` is none of `factory.adapters.opencode_runtime`, and `CONFIG_VARIABLE` and `RUNTIME_FOLDER` none of `factory.adapters.claude_runtime`.
2. The constructors (rows of one parametrized test over `inspect.signature`): `ClaudeCodeRuntime.__init__` has no parameter `confine_executable` or `temporary_root`, and `OpencodeRuntime.__init__` none of `confine_executable`, `temporary_root`, `runtime_folders`; `build_boundaries` has no parameter `confine_executable`; `ClaudeCodeRuntime` has no attribute `confine_executable`.
3. A Claude Code call without a container (rows of one parametrized test): with an `os_user` and a stand-in `sudo` that records its words, the words after `env -i` and its assignments are the login shell's words when a login file is set and none when it is not, then the executable, then the arguments, and no word is `--rules` or ends in `factory-confine`; without an `os_user`, with a stand-in `claude` that records its environment and the files of the state directory while it runs, the environment holds `SWITCHES` and no `CLAUDE_CONFIG_DIR`, while the call runs the state directory holds one `instructions-*.md` file and no `confine-*.json`, and after the run no folder whose name begins `factory-run-` exists under the system's temporary folder that was not there before. The same for opencode: while the call runs the state directory holds one `opencode-*.json` and no `confine-*.json`, and after the run no folder whose name begins `factory-run-` exists under the system's temporary folder that was not there before.
4. The reading of a call's end (rows of one parametrized test over `call_refusal` and the runtimes): a call that printed no reply and whose standard error holds `factory-confine: the kernel offers Landlock ABI 2` raises no `AgentRuntimeError` and ends `died` (Claude Code and opencode, one row each); a call with an `os_user` whose standard error holds `sudo: a password is required` still raises `AgentRuntimeError` naming the `sudo` executable and that line; a login file the shell refused still raises naming the file; a call without an `os_user` that printed no reply and whose standard error holds a line beginning `sudo:` is no refusal: it raises no `AgentRuntimeError` and ends `died`.
5. A call in a container is unchanged: the existing tests of `tests/adapters/test_claude_runtime_container.py` and `tests/adapters/test_opencode_runtime_container.py` stay green with the changes the Interface names, and a runtime built with `containers` and a `FakeContainerRuns` records one launch whose read-only mounts are the set login files and the instructions (or configuration) file at their own paths and whose working directory is `/work/checkout`.
6. The preflight's extras (rows of one parametrized test over `machine_extras`): an `inline` instance without an agent user gives `token-file`, `agent-user`, `agent-environment`, `agent-run-probe`; with an agent user `token-file`, `agent-user`, `tool:sudo`, `agent-environment`, `agent-run-probe`; under opencode `opencode` stands right before `agent-run-probe`; a `container` instance gives F0042-S0011's list unchanged; no list holds `confinement`.
7. The source (one test reading `src/factory`): no module but `factory.entry.confine`, `factory.adapters.landlock` and `factory.domain.confinement` holds the string `factory-confine:` or `CLAUDE_CONFIG_DIR`, and only those three import `factory.domain.confinement` or `factory.adapters.landlock`; and `factory.entry.wiring` holds not even the bare string `factory-confine` (its comment included).
8. R14 (rows of one parametrized test over the seven files under `claude/agents/`): each holds the line of decision 4 of `feature.md` exactly once, and none holds `the kernel refuses every other write` or `$TMPDIR`.
9. `make check` stays green.
10. docs: `docs/project-guide/agents.md`, *The shared launch module*, *The `claude -p` runtime* and *The opencode runtime*: a call starts the runtime's command directly or in a container, with no wrapper, rules file, temporary folder or `CLAUDE_CONFIG_DIR`; *The seven agents*: the bullet on R14 says what decision 4's text says (the take keeps only the role's write paths, a write elsewhere is lost, temporary files through `mktemp` or `tempfile`); `docs/project-guide/write-guard.md`, *The start wrapper* and *The kernel's write guard*: one sentence at the top of each that no agent call starts through the wrapper since F0044-S0001 and that S0002 removes the module, and the paragraph on `confinement_item` goes; `docs/project-guide/stage-environment.md`: the list of items a `container` instance leaves out no longer names `confinement`; `docs/operator-guide.md`, *The agent runs as a second user*: the `sudo` chain has no `factory-confine --rules ...` words; `docs/operator-guide.md`, *The kernel refuses every other write*: the section says that the kernel's guard is no longer started and what keeps the write paths (the take on a `container` instance, the undo on an `inline` one), and *The preflight's items*: the row `confinement` goes and the count of items for each environment follows. `docs/decisions.md`: the entries "Every agent run is confined by the kernel" and "No agent runs without the kernel's write guard" each gain one closing line: "Replaced by the dataset's rollback and the take, v1.2 F0044-S0001." `README.md`: none.

## Smoke test

```bash
uv run python - <<'EOF'
import inspect
from factory.adapters import agent_launch
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.application import preflight

names = ("CONFINE_PREFIX", "cleanup_launch", "confined_argv", "device_confinement", "temporary_folder")
print(sorted(name for name in names if hasattr(agent_launch, name)))
parameters = {**inspect.signature(ClaudeCodeRuntime).parameters, **inspect.signature(OpencodeRuntime).parameters}
print(sorted(name for name in ("confine_executable", "runtime_folders", "temporary_root") if name in parameters))
print(hasattr(preflight, "confinement_item"))
EOF
```
Expect: three lines: `[]`; `[]`; `False`

```bash
grep -L 'the kernel refuses every other write' claude/agents/*.md | wc -l
```
Expect: `7`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as vm.
3. intake: 1. Interface rule on `call_refusal`: it reads a refused `sudo` "only with an `os_user`". Criterion 4 tests only the side that raises (a call with an `os_user` and `sudo: a password is required`). Nothing tests the other side: a line beginning `sudo:` in the standard error of a call without an `os_user`, with no reply printed, is no refusal and the call ends `died`. Two coders could read that clause two ways and both would pass. Proposal: add that row to criterion 4, before the two closing criteria. Do you accept it?

   2. Interface rule: "a run ... makes no folder whose name begins `factory-run-`". Criterion 3 checks this for Claude Code only. For opencode it checks the state directory's files and says nothing about a `factory-run-` folder. `OpencodeRuntime` loses `temporary_root` too. Proposal: add the `factory-run-` check to the opencode row of criterion 3. Do you accept it?

   3. Interface line: `production_environment`'s comment "no longer names `factory-confine`". No criterion covers it. Criterion 7 reads only for the string `factory-confine:` with a colon, and the comment may be written without it. Options: (a) widen criterion 7 to the bare `factory-confine` for `factory.entry.wiring` only (the other modules the story keeps may still say it in prose); (b) drop the line from the Interface as untestable prose. I would choose (a).

   The other checks found nothing to ask:
   - Interface: it names concrete modules, names and signatures, and `Starters` is shown in full.
   - Smoke test: the commands are runnable and run no pytest. Each `Expect:` line is checkable against the output (`[]`, `[]`, `False`; `7`).
   - Architecture: the changes stay in the layers `CLAUDE.md` describes, and the removed names have no other callers.
   - Scope: the story is S0001 of `feature.md` and keeps the S0002 modules. R14's text is decision 4 word for word, with the human's leave from decisions 17, 29(e) and 30.
4. 2026-10-25 human: 1: yes, add the row (a line beginning `sudo:` on the standard error of a call without an `os_user`, no reply printed: no refusal, the call ends `died`) to criterion 4's parametrized test.
   2: yes, add the `factory-run-` check to the opencode row of criterion 3.
   3: (a), widen criterion 7 to the bare `factory-confine` for `factory.entry.wiring` only.
   Add all three yourself, then continue.
5. factory: started intake as vm.
6. intake: accepted

   Carried in from the human's answer (journal entry 4), written into the story as the human's edits and not as my own improvements:
   - Criterion 3, opencode row: after the run, no folder whose name begins `factory-run-` exists under the system's temporary folder that was not there before (answer 2).
   - Criterion 4: a new row. A call without an `os_user` that printed no reply and whose standard error holds a line beginning `sudo:` is no refusal. It raises no `AgentRuntimeError` and ends `died` (answer 1).
   - Criterion 7: `factory.entry.wiring` holds not even the bare string `factory-confine`, its comment included (answer 3, option a).

   Checks:
   - Interface: it names concrete modules, names and signatures. `Starters` is shown in full. Every removal is listed per module, and the earlier tests to delete or change are named one by one. R14 is decision 4's text, which the human confirmed in 29(e).
   - Criteria: each is testable by a parametrized test or a single test.
     - Every rule has its failing side. `call_refusal` reads `sudo:` only with an `os_user` (criterion 4, both sides now), and `factory-confine:` is no refusal (criterion 4).
     - The two rules on starting a call are covered by criterion 3: the login words only when a login file is set, and no rules file or `factory-run-` folder.
     - R14 is covered by criterion 8, and the container call being unchanged by criterion 5.
   - Smoke test: both commands are runnable and run no pytest, so no `-q` question arises. Each `Expect:` line is checkable: `[]`, `[]`, `False`, and `7`.
   - Architecture: the changes stay inside the four layers `CLAUDE.md` describes. The three kept modules (`confine`, `landlock`, `confinement`) are left to S0002 as stated.
   - Scope: the story is S0001 of `feature.md`. The R14 text change is the one agent edit the feature allows. The test leave is decisions 17, 29(f) and 30(a), and the docs passages follow 30(c).
7. factory: started tests as vm.
