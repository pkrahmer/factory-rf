---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 448
comments_read: [6398933817]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T14:31:10.456696Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T14:31:10.463077Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-25T14:31:30.781949Z'
  stage: intake
  run: ff982a42912a470eb105926db63ad70c
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-25T14:33:45.355343Z'
  stage: intake
---

# The second user is removed

## Description

Since F0012 an instance with `FACTORY_AGENT_USER` starts every agent call as that user, `sudo -n -u <user> -- timeout --signal=KILL <limit> env -i <environment> <command>`, writes a run's files with mode `0640` so the user's group can read them, and since F0040 runs every project command the same way (`CommandUser`); the factory's git gives its `.git` the shared mode `0640` so the agent's group can read it, and the preflight's items `agent-user` and `tool:sudo` check the user and the tool. On a `container` instance the container is the second user: F0042-S0010 refuses an agent user there, and the runtime refuses a request with an operating-system user in a container. After S0003 (the leftovers program is removed) and S0004 (the fresh home is removed) nothing else runs as that user. This story removes the second user: the `sudo` chain and `env -i` of the launch module, the operating-system user of a request, the runtimes' `sudo_executable`, the run files' group mode, `CommandUser` and the commands' `sudo` path, the setting `FACTORY_AGENT_USER`, the two preflight items, the wiring's agent-user branches and the shared mode of the factory's git. What stays: a call in a container exactly as F0042 left it (podman's `--timeout` and its 255, `CONTAINER_KILL_STATUSES`); a call without a container (the inline environment's until S0008, and the suite's) runs as the factory's own user and is ended by the factory's own kill at its time limit; `MakeProjectCommands` runs `make` as the factory's own user (decision 3 of `feature.md`); the login shell and its files; the token file's folder check (`token-file`), which keeps other users of the host out of the token. `SealedProjectCommands` is left without a caller until S0006 removes `sealed_runs.py` (decision 13).

## Interface

`factory.adapters.agent_launch` (`adapters`): `SUDO_EXECUTABLE`, `SUDO_PREFIX`, `TIMEOUT_EXECUTABLE`, `SUDO_GRACE`, `RUN_FILE_MODE`, `CONTAINER_OS_USER`, `sudo_prefix` and `_limit_argument` go; `Starters` keeps `login_files` alone; these become:

```python
def launch(argv: Sequence[str], environment: Mapping[str, str], *, time_limit: timedelta) -> Launch: ...
def run_launch(request: AgentRunRequest, argv: Sequence[str], runtime_environment: Mapping[str, str], *, time_limit: timedelta) -> Launch: ...
def killed_at_limit(*, exit_status: int | None, duration: timedelta, time_limit: timedelta, in_container: bool = False) -> bool: ...
def call_refusal(stderr: str, *, printed: bool, starters: Starters) -> str | None: ...
def read_call_end(end: CallEnd, *, time_limit: timedelta, starters: Starters, in_container: bool = False) -> bool: ...
```

- `launch` gives `Launch(argv=list(argv), env=dict(environment), time_limit=time_limit)`.
- `killed_at_limit` is true only `in_container`, with an exit status in `CONTAINER_KILL_STATUSES` (F0042-S0015) and the limit reached; a call on the host is ended at its limit by the factory's own kill, which `run_process` reports as `timed_out`.
- `call_refusal` reads a refused login file only.

`factory.adapters.claude_runtime` and `factory.adapters.opencode_runtime` (`adapters`): each constructor loses `sudo_executable`, `ClaudeCodeRuntime` the property `sudo_executable` (opencode has none), the refusal of a request with an operating-system user and the `chmod` of the run files to `0640` (the files keep the mode the process's umask gives); `__all__` of `claude_runtime` loses `SUDO_EXECUTABLE`.

`factory.adapters.make_commands` (`adapters`): `CommandUser`, the keyword `user`, the property `user`, `_run_as`, `_refusal`, `_refusal_line` and the imports of `SUDO_PREFIX`, `launch` and `killed_at_limit` go; `MakeProjectCommands.__init__(directory, kill_points=None, *, executable="make")`.

`factory.domain.agent_runs.AgentRunRequest` (`domain`) loses `os_user`. `factory.domain.settings` (`domain`): `AGENT_USER_VARIABLE`, `InstanceSettings.agent_user`, `_agent_user` and F0042-S0010's fault `is set, but the container environment runs no second user` go; `FACTORY_AGENT_USER` is read by nothing. `factory.application.task`: the request carries no `os_user`.

`factory.application.preflight` (`application`): `agent_user_item`, `_AGENT_USER_ITEM` and `_NO_AGENT_USER` go; `_probe_request` sets no `os_user`; the hints that said `{settings.agent_user or 'the factory user'}` say `the factory user`.

`factory.entry.wiring` (`entry`): `build_boundaries(settings, token, *, hosting=None)` (the keyword `which` goes with the `sudo` it looked for); the `SUDO_EXECUTABLE` import, `project_command_environment` (and from `__all__`) and the agent-user branches of `_project_commands` and `agent_run_environment` go; the inline environment's project commands are `MakeProjectCommands(settings.checkout)` (so `_project_commands` and the inline environment's `git`, `log` and `which` go), and the container environment's stay F0042-S0010's `ContainerMakeCommands`; `machine_extras(boundaries, settings, environment)` loses `which`, which it read only for `tool:sudo` (`build_preflight` and `build_tick` keep theirs for `MachineChecks`), and adds neither `agent-user` nor `tool:sudo`; `git_environment` holds three pairs, `credential.helper`, `core.hooksPath` and `core.fsmonitor` (`GIT_CONFIG_COUNT` `3`), without `core.sharedRepository`.

Tests (the leave is decision 21 of `feature.md`):

- Deleted whole: `tests/adapters/test_claude_runtime_os_user.py`, `tests/adapters/test_claude_runtime_sudo_time_limit.py`, `tests/adapters/test_claude_runtime_file_modes.py`, `tests/adapters/test_make_commands_user.py`, `tests/adapters/test_opencode_sudo_time_limit.py`, `tests/application/test_agent_user_item.py`, `tests/application/test_task_os_user.py`, `tests/domain/test_settings_agent_user.py`, `tests/entry/test_wiring_agent_user.py`, `tests/entry/test_wiring_project_command_user.py`, `tests/entry/test_git_repository_modes.py`, F0044-S0003's `tests/adapters/test_one_call_as_another_user.py`, the helper modules `tests/sudo_support.py` and `tests/leftovers_runtime_support.py`. Before the deletion, under the standing leave, `REPLY`, `_request` (without its `os_user`) and `_without_locale` of `tests/adapters/test_claude_runtime_os_user.py` move to `tests/adapters/claude_stand_in.py` as `REPLY`, `claude_request` and `without_locale`, and the modules that import them import them from there, each test keeping its name and what it checks: `tests/adapters/test_claude_runtime_api_login.py`, `test_claude_runtime_login.py`, `test_claude_runtime_no_hook.py`, `test_claude_runtime_provider_limit.py`, `test_claude_runtime_resume_session.py`, `test_opencode_runtime.py`, `test_runtimes_without_wrapper.py`, `tests/entry/test_wiring_api_login.py`, `test_wiring_login.py` and `test_wiring_provider_limit.py`; its `_sudo_calls` and `_write_sudo` go with the tests that used them.
- The shared helpers lose the user, their callers unchanged: `opencode_request` of `tests/adapters/opencode_stand_in.py`, `run_request` of `tests/confine_support.py`, `container_request` of `tests/adapters/container_runtime_support.py` and `_request` of `tests/adapters/test_claude_runtime_container.py` lose the keyword `os_user`; `machine_item` of `tests/wiring_support.py` calls `machine_extras` without `every_tool`.
- `tests/adapters/test_agent_launch.py`: `test_launch_runs_the_call_as_the_user_under_a_kill_timeout_with_its_environment_alone` is deleted; `test_killed_at_limit_needs_a_user_a_kill_status_and_the_limit_reached` keeps its name and its rows become `in_container` rows.
- `tests/adapters/test_agent_launch_call_end.py::test_a_call_end_is_read_as_timed_out_when_its_own_timeout_killed_it_at_the_limit` and `::test_a_call_end_raises_the_refusal_read_after_its_time_limit`; `tests/adapters/test_agent_launch_container.py::test_in_a_container_a_kill_status_at_the_limit_is_the_limit` and `::test_a_container_call_killed_at_the_limit_is_read_as_the_limit_and_no_refusal`; F0042-S0015's `tests/adapters/test_agent_launch_container_kill.py::test_255_at_the_limit_is_a_kill_only_in_a_container`: the two rows with `os_user="agent"` go and the other five lose the column `os_user`; the module constant `STARTERS` of `tests/adapters/test_agent_launch_call_end.py` and the `Starters` of `test_a_container_call_killed_at_the_limit_is_read_as_the_limit_and_no_refusal` lose `sudo_executable`.
- `tests/adapters/test_claude_runtime_container.py::test_a_request_with_an_operating_system_user_is_refused_in_a_container` and the same test of `tests/adapters/test_opencode_runtime_container.py` are deleted.
- `tests/adapters/test_claude_runtime_login.py`: `test_with_a_user_the_login_shell_runs_after_sudo_and_env_i_and_hands_over_the_login` is deleted; `test_the_login_stands_in_no_argument_no_run_file_and_no_result`, `test_a_login_file_that_cannot_be_used_stops_the_run_naming_the_file` and the helper `_runtime` loses the user (the module has no `_guarded_request`); `tests/adapters/test_claude_runtime_api_login.py::test_the_key_stands_in_no_argument_no_run_file_and_no_result` and its `_runtime`; `tests/adapters/test_opencode_runtime.py::test_the_call_sees_its_configuration_file_and_only_the_request_s_environment`; `tests/adapters/test_opencode_runtime_launch.py`: `test_with_an_agent_user_sudo_starts_the_call_after_env_i_and_its_environment` is deleted, `test_the_call_gets_the_api_file_s_key_and_the_result_names_the_login`, `_runtime` and `_warned_by_sudo` lose the user.
- `tests/application/test_agent_run_probe.py::test_the_probe_runs_the_coder_on_a_small_budget_with_the_question_alone`, `::test_a_probe_that_does_not_complete_fails_with_its_detail`, `::test_a_runtime_that_cannot_run_the_probe_fails_with_its_message` and `::test_the_probe_calls_claude_with_the_flags_of_a_stage`; `tests/application/test_agent_run_probe_factory_user.py::test_the_opencode_login_hint_names_the_agent_user_or_the_factory_user` (its rows with an agent user go); `tests/application/test_agent_run_probe_login.py` (both tests); the `settings` helpers of `tests/application/test_agent_run_probe_api_login.py` and `tests/application/test_agent_run_probe_opencode.py`; the fixture `probe_settings` of `tests/conftest.py`; `tests/application/test_task.py::test_the_request_carries_the_agent_checkout_and_guard_without_os_user`; `tests/domain/test_agent_runs.py::test_minimal_request_has_empty_defaults_not_shared`.
- `tests/entry/test_wiring_boundaries.py`: `test_the_built_agent_runtime_starts_the_sudo_on_the_path_or_usr_bin_sudo` is deleted with its helper `which`; `test_git_environment_gives_the_credential_helper_the_shared_group_and_no_hooks` becomes `test_git_environment_gives_the_credential_helper_and_no_hooks` and checks the three pairs. `tests/entry/test_wiring_extras.py::test_the_extras_come_in_the_operator_guides_order_sudo_only_with_an_agent_user` and `::test_a_tick_stops_on_a_failed_extra_and_otherwise_probes_in_the_stages_environment`; `tests/entry/test_wiring_opencode.py::test_the_opencode_item_comes_after_confinement_only_under_opencode`; `tests/entry/test_wiring_run.py::test_build_tick_runs_one_stage_in_the_production_environment_under_its_instance`; F0042-S0010's `tests/domain/test_settings_stage_environment.py` and `tests/entry/test_wiring_stage_environment.py` (the rows with `FACTORY_AGENT_USER` or `which` go) and F0042-S0011's `tests/entry/test_wiring_container_extras.py` (the `inline` row with an agent user goes).
- `tests/test_test_children.py::test_the_stand_in_sudo_starts_the_interpreter_without_bytecode` is deleted with the module's import of `_write_sudo`; `tests/test_time_limits.py`: the rows that read the deleted modules go.
- F0044-S0001's `tests/adapters/test_runtimes_without_wrapper.py`: `test_a_claude_call_as_a_user_starts_the_login_words_then_the_call_after_env_i` is deleted; `test_only_sudo_and_the_login_shell_refuse_a_call` becomes `test_only_the_login_shell_refuses_a_call`: its row `sudo-refused` goes with `_sudo_refused` (the row `sudo-line-without-a-user` stays: a `sudo:` line is still no refusal), and `_login_refused` and the row `call-refusal-wrapper-line` call `call_refusal` without `timed_out` and `os_user`, with `Starters(login_files=...)`.
- F0044-S0003's `tests/adapters/test_kill_at_the_limit_stays.py::test_a_call_is_still_killed_at_its_time_limit` (the rows with `os_user="agent"` go, the others lose the keyword) and `tests/test_leftovers_program_removed.py::test_the_names_that_started_the_leftovers_program_are_gone` (the row `command-user` goes with the import of `CommandUser`; the row `starters-fields` reads `["login_files"]`).
- The settings of an agent user go: `tests/application/test_sealed_runs.py::test_the_probe_raises_when_the_run_swaps_git_and_the_preflight_lets_it_out` and `tests/application/test_nested_repositories.py::test_a_probe_run_that_leaves_a_nested_repository_fails_the_item` (its helper `_probe_settings`) build their settings without `agent_user`; `tests/domain/test_settings_url_edges.py::test_a_refused_setting_names_its_variable_and_its_fault` loses the row `agent-user`; F0042's `tests/entry/test_wiring_stage_environment_home.py::test_the_agent_run_s_home_follows_the_stage_environment` loses the row `inline-agent-user`.
- `tests/entry/test_wiring_boundaries.py::test_the_built_git_runs_with_the_git_options_of_the_settings` checks the three pairs; the structural `tests/entry/test_wiring_constants.py::test_the_wiring_offers_its_names_but_no_list_of_kinds_without_a_handler`: `KEPT` loses `project_command_environment`. In F0042-S0011's `tests/entry/test_wiring_container_extras.py`, `INLINE_ITEMS` loses `agent-user`. Each test keeps its name, except the two this list renames or deletes.

## Acceptance criteria

1. The removed names (rows of one parametrized test): none of `SUDO_EXECUTABLE`, `SUDO_PREFIX`, `TIMEOUT_EXECUTABLE`, `SUDO_GRACE`, `RUN_FILE_MODE`, `CONTAINER_OS_USER`, `sudo_prefix` is an attribute of `factory.adapters.agent_launch`; `Starters.model_fields` is exactly `login_files`; `CommandUser` is none of `factory.adapters.make_commands`; `AgentRunRequest.model_fields` holds no `os_user`; `InstanceSettings.model_fields` holds no `agent_user`; `AGENT_USER_VARIABLE` is none of `factory.domain.settings`; `agent_user_item` none of `factory.application.preflight`; `project_command_environment` none of `factory.entry.wiring`; no runtime class has the attribute `sudo_executable`; `build_boundaries` has the parameters `settings`, `token`, `hosting` and no other; `MakeProjectCommands.__init__` has no parameter `user`.
2. A call without a container (rows of one parametrized test, Claude Code and opencode, each with the `Recorder` of `tests/run_process_recorder.py` in place of the runtime module's `run_process`, and of `run_streaming` for opencode, so that each row reads the `ProcessRequest` the runtime handed over): the first word is the login shell (`/bin/sh`) when a login file is set and the runtime's executable when none is; no word is `sudo`, `/usr/bin/sudo`, `env` or `-i`; the environment is the request's without the two login variables, with the runtime's own entries (Claude Code's switches; opencode's switches and `OPENCODE_CONFIG`); and `call_refusal("sudo: a password is required\n", printed=False, starters=Starters(login_files=LoginFiles()))` is `None`.
3. `launch(["x"], {"A": "1"}, time_limit=30 s)` gives `Launch(argv=["x"], env={"A": "1"}, time_limit=30 s)`.
4. `killed_at_limit` (rows of one parametrized test, `time_limit` 30 s): `in_container=True` with 137, -9 or 255 at 30 s is `True`; with 255 at 29.9 s `False`; with 1 at 30 s `False`; `in_container=False` with 137 at 30 s is `False`.
5. `FACTORY_AGENT_USER` is read by nothing (rows of one parametrized test over `read_settings`): with `FACTORY_AGENT_USER=agent` and with `FACTORY_AGENT_USER=Bad Name` (refused until now) an `inline` environment gives the same settings as without it; a `container` environment with the dataset, the workspace, the image and `FACTORY_AGENT_USER=agent` is accepted (refused until now).
6. `git_environment()` is exactly `{"GIT_CONFIG_COUNT": "3", "GIT_CONFIG_KEY_0": "credential.helper", "GIT_CONFIG_VALUE_0": CREDENTIAL_HELPER, "GIT_CONFIG_KEY_1": "core.hooksPath", "GIT_CONFIG_VALUE_1": os.devnull, "GIT_CONFIG_KEY_2": "core.fsmonitor", "GIT_CONFIG_VALUE_2": "false"}`.
7. The preflight's extras (rows of one parametrized test over `machine_extras`): `inline` under Claude Code gives `token-file`, `agent-environment`, `agent-run-probe`; under opencode `token-file`, `agent-environment`, `opencode`, `agent-run-probe`; `container` gives F0042-S0011's list unchanged; a probe that ends `died` fails with a detail that holds `by hand as the factory user`, and under opencode with the login `none` also `log in once as the factory user`.
8. The project commands of a built instance (rows of one parametrized test over `build_boundaries` with `hosting` the fake): `inline` gives a `RecordingProjectCommands` whose `inner` is a `MakeProjectCommands`; `container` one whose `inner` is a `ContainerMakeCommands`.
9. `make check` stays green.
10. docs: `docs/operator-guide.md`: the section *The agent runs as a second user* goes, replaced by one paragraph in *The agent runtime* that a `container` instance runs every call in a throwaway container as the host's `factory` (`--userns=keep-id`) and an `inline` one as the factory's own user; its paragraphs **The agent's login token.** and **The agent's API key.** stay, moved into *The agent runtime* without their sentences on the agent user, `sudo` and `/home/agent`, while **The one `sudo` rule.**, **The preflight item `agent-user`.**, the table of checks on a running instance and **A `time_limit` under `sudo`.** go; *Configuration*: the row `FACTORY_AGENT_USER` goes; *The preflight's items*: the rows `agent-user` and `tool:sudo` go and the counts follow; every sentence that names `sudo -n -u`, `env -i`, the agent's own `timeout` or the mode `0640` of a run's files goes. `docs/project-guide/agents.md`, *The agent runtime* (the request has no `os_user`), *The `claude -p` runtime* and *The opencode runtime* (no `sudo_executable`, no call as another user, no end reason under an `os_user`), *Calls in a container* (no refusal of an `os_user`) and *The shared launch module*: no `sudo` chain, and `launch`, `killed_at_limit`, `call_refusal`, `read_call_end` and `Starters` as the Interface gives them; `docs/project-guide/stage-environment.md`: the table row `agent_runtime` and the items left out for `container` name no `sudo` and no `agent-user`; `docs/project-guide/stages.md`, the paragraph on `compose`: no `os_user`; `docs/operator-guide.md`: every sentence that names `FACTORY_AGENT_USER` or `<agent user>` goes or names the factory user (the fault order and the `container` paragraph of *Configuration*, *The agent runtime*, *The agent run's `PATH` and `HOME`*, the list of items left out for `container`, *The probe of the agent run*), and *The hosting-service token*'s paragraph **The project commands run as `agent`.** becomes one sentence that an `inline` project command runs as the factory's user and a `container` one in a check container; `docs/project-guide/processes-and-checks.md`, *Running as another user*: removed, with one line on what replaced it; `docs/project-guide/watching.md`, *Boundaries*: `git_environment`'s three pairs (`GIT_CONFIG_COUNT=3`, no `core.sharedRepository`) and `build_boundaries(settings, token, *, hosting=None)` without `which`; `docs/project-guide/README.md`, *The files*: the lines follow, and *Shared test helpers*: the lines of `sudo_support.py` and `leftovers_runtime_support.py` go. `docs/decisions.md`: the entries "The agent is started through `sudo -n -u agent -- env -i`, and a run's files are `0640`", "The factory's user may become `agent` for one command only, and a missing agent user is a stop", "The agent's own `timeout` kills a run under `sudo` at its time limit", "The project commands run as the agent user, with the git folder sealed" and "Git gets its credential helper and shared group through `GitOptions.environment`" each gain one closing line: "Replaced by the throwaway container, v1.2 F0044-S0005" (the last: "The shared group went with the second user, v1.2 F0044-S0005; the credential helper and the hooks stay"). `README.md`: none.

## Smoke test

```bash
uv run python - <<'EOF'
from factory.adapters import agent_launch, make_commands
from factory.domain.agent_runs import AgentRunRequest
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import git_environment

print([name for name in ("SUDO_EXECUTABLE", "SUDO_GRACE", "sudo_prefix") if hasattr(agent_launch, name)], hasattr(make_commands, "CommandUser"))
print("os_user" in AgentRunRequest.model_fields, "agent_user" in InstanceSettings.model_fields)
print(git_environment()["GIT_CONFIG_COUNT"], "core.sharedRepository" in git_environment().values())
EOF
```
Expect: three lines: `[] False`; `False False`; `3 False`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as self.
3. intake: Questions (the format check passed, so no findings from it):

   1. The Interface says the runtimes no longer `chmod` the run files to `0640` and that "the files keep the mode the process's umask gives". No criterion tests that. Criterion 1 only checks that `RUN_FILE_MODE` is gone, which a coder could satisfy while keeping a `chmod`, or while setting some other mode. Two coders could read the clause two ways and both pass. Options: (a) add a criterion, for example "a Claude Code and an opencode call without a container writes its run files with the mode the process's umask gives (rows of one parametrized test, a umask of 0o077 and one of 0o022)"; (b) drop the sentence from the Interface and keep only "the `chmod` goes". I would choose (a).

   2. Please confirm that nothing else needs a criterion. These all rest on the existing tests the Interface keeps, not on a new criterion:
      - `run_launch` and `read_call_end` are listed in the Interface with no stated behaviour change.
      - `call_refusal` "reads a refused login file only" has its failing side only through the unchanged `test_a_login_file_that_cannot_be_used_stops_the_run_naming_the_file`. Criterion 2 pins only the `sudo` line as no refusal.
      - I would accept this if you confirm it.

   The other checks, for the record:
   - Interface: names concrete modules and signatures.
   - Other criteria: 1 to 9 are each testable by a table of rows. Every rule has its failing side: criterion 4's host row, criterion 5's formerly refused values, and criterion 2's `sudo` line that is no longer a refusal.
   - Smoke test: runnable, and its pytest-free `Expect:` line is checkable.
   - Architecture: the changes sit in the right layers.
   - Scope: within F0044 and its S0005 line. The human's leave is decision 21 and decision 34(a).
4. 2026-10-25 human: 1. (a). Add the criterion, before the closing ones: a Claude Code call and an opencode call without a container write their run files with the mode the process's umask gives and no `chmod` (rows of one parametrized test: a umask of `0o077` and one of `0o022`, for each runtime). A new test needs no leave.
   2. Confirmed. `run_launch` and `read_call_end` keep their behaviour, and `call_refusal`'s refused-login-file side rests on the unchanged `test_a_login_file_that_cannot_be_used_stops_the_run_naming_the_file`. No further criterion is needed.
