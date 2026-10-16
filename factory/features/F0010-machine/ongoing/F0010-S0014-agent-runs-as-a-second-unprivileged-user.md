---
stage: doing
pr: 132
blocked: asked
comments_seen: 1
round: 1
attempts: 0
---
# Agent runs as a second unprivileged user

## Assignment (as of log entry 1)

Run every agent as the second operating-system user, `agent`, which the image story created and which owns nothing the factory keeps secret. This story builds the factory's side: the setting that names the user, the runtime's call, and the request. The runtime starts the agent through `sudo -n -u agent -- env -i` with exactly the environment of the request and the runtime's own switches, so neither the factory's environment nor its privileges come along. The composer names the user in the request, and the wiring gives the agent a `HOME` of its own. The runtime also writes the files of a run (its instructions, its guard settings and its hook settings) with the mode `0640`, so that the agent, who reads them as a member of the group `factory-work`, cannot rewrite its own guard settings: together with the directory `/state/runs`, which the agent cannot write either (the human's decision of 2026-10-14), a run cannot widen its own write paths (R32, WE2). The image side (the `sudo` rule, the user's variable, the umask) is the next story. This covers WE3.1 on the factory's side and, with the previous stories, the files side of WE3.3 and WE3.4, and implements R33. The second user, the `sudo` rule and the group exist only in a real image, so what v1's container can test is the runtime's call, the settings, the composition of the request and the files' modes; a real agent run as `agent` that tries to read the token file and the token, to push with `git -C . push origin main` and to call the hosting service's API is the morning observation. A time limit that the factory cannot enforce under `sudo` is not solved here: `run_process` kills the process group of the call, and the group's leader is a root-owned `sudo`, which the factory's user may not signal. Whether a `timeout` wrapper inside the `sudo` call or a kill through `sudo` is the right fix is the human's decision (`FEATURE.md`, decision 30); until then it is one of the morning observations. Claude's login for the model is the operator's one-time step as the user `agent` (`docker compose run --rm -it --user agent --entrypoint claude factory`), kept in the volume `claude-home`. The agent can write the agent home and `settings.json` there, which is left for v2 (the handover's section 8, L69).

## Interface

`src/factory/domain/settings.py` (extends the module)

```python
AGENT_USER_VARIABLE = "FACTORY_AGENT_USER"

class InstanceSettings(BaseModel):
    ...
    agent_user: Name | None = None            # the value of FACTORY_AGENT_USER; missing or blank is None
```

`src/factory/adapters/claude_runtime.py` (extends the constructor)

```python
class ClaudeCodeRuntime(AgentRuntime):
    def __init__(
        self,
        executable: str,
        state_directory: Path,
        kill_points: KillPoints | None = None,
        *,
        version_time_limit: timedelta = VERSION_TIME_LIMIT,
        sudo_executable: str = "/usr/bin/sudo",
    ) -> None: ...
```

`src/factory/entry/wiring.py` (extends the module)

```python
def agent_run_environment(settings: InstanceSettings, base: Mapping[str, str]) -> dict[str, str]: ...
```

Rules:

- `read_settings` sets `agent_user` from `FACTORY_AGENT_USER`; a value that does not match `Name` raises `SettingsInvalid` with `variable == "FACTORY_AGENT_USER"`. `InstanceSettings(agent_user="Agent")`, built directly, is refused as well.
- With `request.os_user` set to `U`, `ClaudeCodeRuntime.run` starts, in `request.working_directory`, the process `[sudo_executable, "-n", "-u", U, "--", "env", "-i", <NAME=value for each entry of {**request.environment, **SWITCHES}>, <executable>, <the arguments it builds without a user>]`. The subprocess is started with an empty environment of its own. With `request.os_user` `None` it starts `[executable, <arguments>]` directly with `{**request.environment, **SWITCHES}` as its environment, as before.
- When the process ends without a result and its standard error holds a line that starts `sudo:`, the runtime raises `AgentRuntimeError` whose detail contains that line, not a `died` result: a refused `sudo` is a misconfiguration, not a stall (the preflight's probe of an agent run finds it before any claim, see the story that builds it).
- `ClaudeCodeRuntime` sets the mode `0640` on each file of a run it writes (`instructions-<session>.md`, and with a guard `guard-<session>.json` and `hooks-<session>.json`) before it starts the call, whatever the factory's umask.
- The composer of agent run requests, `factory.application.task`, sets `os_user` to `boundaries.settings.agent_user`; when the boundaries have no settings, or the settings no `agent_user`, `os_user` is `None`. It adds nothing to the environment and takes nothing from it (F0005 decision 23).
- `agent_run_environment(settings, base)` returns a copy of `base`; when `settings.agent_user` is not `None` its `HOME` is `str(settings.agent_home.parent)`, the home of the agent user, else `base`'s entries are as they were. `build_tick` (the wiring of the instance's run) hands `handler_factory` the environment `agent_run_environment(settings, production_environment())`.

Tests: `tests/domain/test_settings_agent_user.py`, `tests/adapters/test_claude_runtime_os_user.py` (the stand-in executable of `tests/adapters/claude_stand_in.py` for `claude`, and a second stand-in script for `sudo` that records its arguments and then runs the rest of its command line after `--`), `tests/adapters/test_claude_runtime_file_modes.py` (a small stand-in of its own that records the mode of each file named by its arguments), `tests/application/test_task_os_user.py`, `tests/entry/test_wiring_agent_user.py`. The closed-model test builds the model through a variable typed `type[BaseModel]`. The test of criterion 14 makes the preflight of `build_tick` pass: a `which` that answers a path for every tool, settings with `pinned_agent_version="fake"` and the pipeline's agents installed in `settings.agent_home`, and a `Makefile` on `main` whose target `lint` is `true`, pushed with `human.push_file`. The settings of that test have `agent_home` equal to the `agent_home` fixture and `state_directory` in `tmp_path`, and the tick's boundaries carry the same settings (`dataclasses.replace(boundaries, settings=settings)`), because the composer reads `boundaries.settings.agent_user`.

## Acceptance criteria

1. `read_settings` sets `agent_user` to `agent` for `FACTORY_AGENT_USER=agent`, and to `None` when the variable is missing or blank.
2. `FACTORY_AGENT_USER` set to `Agent` or to `1x` raises `SettingsInvalid` with `variable == "FACTORY_AGENT_USER"`.
3. `InstanceSettings` built directly refuses `agent_user="Agent"` with `ValidationError` and accepts `agent_user="agent"` and `None`.
4. With `os_user=None` the runtime starts the stand-in for `claude` directly, with the entries of `request.environment` and of `SWITCHES` as its environment, and never starts the `sudo` stand-in.
5. With `os_user="agent"` the `sudo` stand-in receives the arguments `-n`, `-u`, `agent`, `--`, `env`, `-i`, then one `NAME=value` argument for each entry of `request.environment` and of `SWITCHES`, then the executable (WE3.1); the `sudo` stand-in itself runs with an empty environment.
6. With `os_user="agent"`, the `claude` stand-in behind the `sudo` stand-in sees the entries of `request.environment` and of `SWITCHES` as its environment, the three switches included, and nothing of the test process's own environment although it has `GH_TOKEN` set (apart from the `LC_CTYPE` the stand-in's Python adds).
7. With `os_user="agent"`, the agent process runs in `request.working_directory`.
8. A `sudo` stand-in that prints `sudo: a password is required` to standard error and exits 1 makes the runtime raise `AgentRuntimeError` whose detail contains that line.
9. A `sudo` stand-in that exits 1 with the standard error `boom` (no line that starts `sudo:`) gives a result with the end reason `died`, not an error.
10. A `sudo_executable` that does not exist makes the runtime raise `AgentRuntimeError`, not return a `died` result.
11. The files of a run are mode `0640` when the agent starts, also under a umask of `0000` (the instructions file, and with a guard the guard file and the hooks file).
12. A request composed by `factory.application.task` with `boundaries.settings.agent_user == "agent"` has `os_user == "agent"` and an `environment` equal to the one the composer was given; with no `agent_user` (or no settings) it has `os_user is None`.
13. `agent_run_environment` with `agent_user == "agent"` and `agent_home == Path("/home/agent/.claude")` gives `HOME == "/home/agent"` and leaves every other entry of `base` as it was; with no `agent_user` it returns `base`'s entries unchanged; `base` itself is not modified.
14. A `Tick` from `build_tick` with `settings.agent_user == "agent"` over a remote with one started story makes an agent request with `os_user == "agent"` and `environment["HOME"]` equal to `str(settings.agent_home.parent)`.
15. make check stays green.
16. docs: `docs/operator-guide.md` explains the two users (`factory`, uid 1000, runs the factory; `agent`, uid 1001, runs every agent), the variable `FACTORY_AGENT_USER`, that the files of a run are `0640` in a directory the agent cannot write, the one-time login as `agent`, and the morning observations of WE3.1, WE3.3 and WE3.4 with the commands that perform them, and of a `time_limit` reached under `sudo`; `docs/decisions.md` records why the agent is started through `sudo -n -u agent -- env -i`, why the run's files are `0640` (a run cannot widen its own write paths), that the agent home stays writable by the agent (L69, left for v2) and that the kill of a timed-out agent under `sudo` is open.

## Demo

```bash
uv run python -c "
from factory.domain.settings import read_settings
env = {'FACTORY_REPOSITORY_URL': '/srv/project.git', 'FACTORY_INSTANCE': 'factory-1', 'FACTORY_AGENT_USER': 'agent'}
print(read_settings(env).agent_user, read_settings({k: v for k, v in env.items() if k != 'FACTORY_AGENT_USER'}).agent_user)
"
```
Expect: one line, `agent None`.

```bash
uv run python -c "
from pathlib import Path
from factory.domain.settings import read_settings
from factory.entry.wiring import agent_run_environment
env = {'FACTORY_REPOSITORY_URL': '/srv/project.git', 'FACTORY_INSTANCE': 'factory-1', 'FACTORY_AGENT_USER': 'agent'}
print(agent_run_environment(read_settings(env), {'PATH': '/usr/bin', 'HOME': '/home/factory'}))
"
```
Expect: one line, `{'PATH': '/usr/bin', 'HOME': '/home/agent'}`.

```bash
uv run python -c '
import pathlib, tempfile
from datetime import timedelta
from decimal import Decimal
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
d = pathlib.Path(tempfile.mkdtemp())
sudo = d / "sudo"
sudo.write_text("#!/bin/sh\nprintf \"%s\\n\" \"$@\" > " + str(d / "argv") + "\n")
sudo.chmod(0o755)
agent = AgentDefinition(name="coder", model="opus", tools=["Read"], budget_usd=Decimal("4"), instructions="x")
request = AgentRunRequest(agent=agent, prompt="p", allowed_decisions=["question"], time_limit=timedelta(minutes=1), working_directory=d, environment={"PATH": "/usr/bin"}, os_user="agent")
ClaudeCodeRuntime("claude", d, sudo_executable=str(sudo)).run(request)
print(open(d / "argv").read().split()[:7])
'
```
Expect: one line, `['-n', '-u', 'agent', '--', 'env', '-i', 'PATH=/usr/bin']`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures (`domain/settings.py` with `AGENT_USER_VARIABLE` and `agent_user: Name | None`, `ClaudeCodeRuntime.__init__` with `sudo_executable`, `entry/wiring.py::agent_run_environment`). The argument list of the `sudo` call is spelled out exactly. Nothing is left for the coder to decide.
   - Criteria: each is testable by one test function. Every rule has its failing side. A bad name is refused in criteria 2 and 3. `sudo` refusing with a `sudo:` line is criterion 8 and a non-`sudo:` failure is 9. A missing `sudo` executable is 10. `os_user=None` is 4, 12 and 13. A missing or blank variable is 1. The `0640` mode under umask `0000` is 11. Every behaviour stated in an Interface comment (blank gives `None`, the `HOME` derivation, the empty subprocess environment) has a criterion.
   - Demo: all three blocks are runnable. Each `Expect:` line gives an exact output to compare. The third block's `sudo` stand-in writes its arguments, and the first seven are checked.
   - Architecture: settings sit in the domain layer, the process call in the one runtime wrapper, the composer in the application layer and the `HOME` wiring in the entry layer. This matches the layering in `CLAUDE.md`. No new dependency is needed.
   - Scope: within F0010's scope ("agent runs as a second unprivileged user", WE3.1 and R33). The `time_limit` under `sudo` stays open (decision 30) and is listed as a morning observation. This is not in the story's criteria. Running the project commands as `agent` is out of scope.
3. tester: Tests written from the Interface and criteria 1–14. Criteria 15–16 are for the coder and the documenter.

   - criterion 1: tests/domain/test_settings_agent_user.py::test_the_agent_user_comes_from_its_variable_or_is_none (set, missing, empty, blank)
   - criterion 2: tests/domain/test_settings_agent_user.py::test_an_agent_user_that_is_no_name_is_refused_naming_its_variable (`Agent`, `1x`)
   - criterion 3: tests/domain/test_settings_agent_user.py::test_settings_built_directly_accept_only_a_name_as_agent_user (`agent`, None and `Agent`, built through a variable typed `type[BaseModel]`)
   - criterion 4: tests/adapters/test_claude_runtime_os_user.py::test_without_a_user_the_agent_starts_directly_and_sudo_never_runs
   - criterion 5: tests/adapters/test_claude_runtime_os_user.py::test_with_a_user_sudo_gets_the_user_env_i_the_environment_and_the_executable. The six leading arguments are checked in order. The `NAME=value` arguments are compared as a sorted list, because the Interface does not fix their order. Then comes the executable, and the `sudo` stand-in's environment is empty apart from LC_CTYPE.
   - criterion 6: tests/adapters/test_claude_runtime_os_user.py::test_with_a_user_the_agent_sees_only_the_request_environment_and_the_switches (GH_TOKEN set in the test process)
   - criterion 7: tests/adapters/test_claude_runtime_os_user.py::test_with_a_user_the_agent_runs_in_the_request_working_directory
   - criterion 8: tests/adapters/test_claude_runtime_os_user.py::test_a_sudo_refusal_is_a_runtime_error_naming_its_line
   - criterion 9: tests/adapters/test_claude_runtime_os_user.py::test_a_failure_without_a_sudo_line_is_a_dead_run
   - criterion 10: tests/adapters/test_claude_runtime_os_user.py::test_a_missing_sudo_executable_is_a_runtime_error
   - criterion 11: tests/adapters/test_claude_runtime_file_modes.py::test_the_files_of_a_run_are_0640_when_the_agent_starts (with and without a guard, under umask 0000 set by a fixture that restores the old umask)
   - criterion 12: tests/application/test_task_os_user.py::test_the_request_runs_as_the_settings_agent_user_with_the_given_environment (agent user, no agent user, no settings)
   - criterion 13: tests/entry/test_wiring_agent_user.py::test_the_agent_run_environment_sets_home_to_the_agent_users_home (also checks that `base` is not modified)
   - criterion 14: tests/entry/test_wiring_agent_user.py::test_a_tick_with_an_agent_user_runs_the_agent_as_that_user_in_its_home. Preflight passes the way the ticket describes: `which` answers every tool, `pinned_agent_version="fake"`, the agents are installed in `agent_home`, a `Makefile` with `lint: true` is pushed, and the boundaries are rebuilt with `dataclasses.replace(..., settings=settings)`.

   How the stand-ins work:
   - The `sudo` stand-in, inside test_claude_runtime_os_user.py, records its arguments and environment to `sudo-calls.jsonl`. It then either plays a scripted refusal (stderr and exit status) or runs `os.execvp` on everything after `--`, so the real `env -i` runs the `claude` stand-in from tests/adapters/claude_stand_in.py.
   - The file-mode stand-in records the mode of each file its arguments name, and of the files next to them. The guard file is named only inside the hooks file, so it is found that way.

   Files created:
   - tests/domain/test_settings_agent_user.py
   - tests/adapters/test_claude_runtime_os_user.py
   - tests/adapters/test_claude_runtime_file_modes.py
   - tests/application/test_task_os_user.py
   - tests/entry/test_wiring_agent_user.py

   `make test` is red as intended. It stopped at collection errors in tests/domain/test_settings_agent_user.py (`AGENT_USER_VARIABLE` cannot be imported from factory.domain.settings) and tests/entry/test_wiring_agent_user.py (`agent_run_environment` cannot be imported from factory.entry.wiring). The collection errors interrupt the run, so the other three files did not run. They should fail on missing behaviour: the `sudo_executable` keyword, the `agent_user` field, `os_user` not being set, and the file modes. `make lint` is green. The type check was skipped, as this stage allows.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: All tests pass and `make check` is green, with coverage at 99.54 %. Commits: 03b8861 (the feature) and 4d42435 (the refactor).

   What I built:
   - `src/factory/domain/settings.py`: added `AGENT_USER_VARIABLE` and `InstanceSettings.agent_user: Name | None`. `read_settings` reads the variable through `_agent_user`. A missing or blank value gives `None`; a value that is not a name raises `SettingsInvalid` naming the variable. The name check that `_instance` already had became a shared `_name(variable, value)`, so there is no second copy of it.
   - `src/factory/adapters/claude_runtime.py`: added the keyword `sudo_executable` (default `/usr/bin/sudo`).
     - `_process_request` builds either the direct call as before, or `[sudo, -n, -u, U, --, env, -i, NAME=value…, executable, args…]` started with `env={}`.
     - `_sudo_refusal` raises `AgentRuntimeError` with the `sudo:` line when the call has a user, did not time out and printed no parseable reply. Any other failure stays a `died` result.
     - The error for a program that cannot be started now names the program that failed (`sudo` or `claude`).
     - `_write_files` writes each file of the run and then sets mode `0640` on it (`RUN_FILE_MODE`) before the call starts. The mode does not depend on the umask.
   - `src/factory/application/task.py`: `TaskComposer._os_user()` returns `boundaries.settings.agent_user`, or `None` when there are no settings. The environment is passed through unchanged.
   - `src/factory/entry/wiring.py`: added `agent_run_environment(settings, base)`, which copies `base` and, when there is an agent user, sets `HOME` to `agent_home.parent`. `build_tick` passes `handler_factory` the result of `agent_run_environment(settings, production_environment())`.

   Main decision: a `sudo:` line counts as a refusal only when no reply could be parsed from standard output. That follows the Interface wording "ends without a result", so an agent whose own output happens to contain such a line is not treated as a refused `sudo`. The alternative I rejected was checking standard error alone: it would also turn a completed run into an error.

   Refactor (4d42435):
   - Split `_call` into `_process_request` and the module-level helper `_sudo_refusal`.
   - Replaced a first draft that listed the run's files with `exists()` by one loop that writes each file and sets its mode.

   Noticed but not touched:
   - The time limit under `sudo` is still open (decision 30). `run_process` kills the process group, whose leader is a root-owned `sudo` in a real image. Only the morning observation can show the effect.
   - The documentation criterion (16) is for the documenter.

   `make check`: check: green
5. reviewer: Review, round 0. Checklist group 1 (acceptance criteria) fails, so I stopped there. Criteria 1–14 each have a test that checks what the criterion says, and the coder's entry reports `make check` green. The findings are on the `sudo` refusal rule, which has a side no test covers and one condition the Interface does not state:

   1. `src/factory/adapters/claude_runtime.py:291` (`_sudo_refusal`): the coder added `or process.timed_out`, which is not in the Interface and no test covers it. The Interface's rule says "when the process ends without a result", and the runtime counts a timed-out process as one without a result (line 231). So a timed-out run as `agent` whose standard error has a `sudo:` line (for example sudo's `sudo: unable to resolve host` warning) should raise `AgentRuntimeError` under the Interface, but this code returns a `time_limit` result. Fix: drop the condition so the code matches the Interface. Or, if keeping it is right, end with `question` so the human can add it to the Interface with a criterion the tester can test.
   2. Gap in the story's criteria, Interface rule 3 ("ends without a result" and a `sudo:` line): the failing side of "without a result" has no criterion. That is a run as `agent` that gives a parseable reply while its standard error holds a `sudo:` line, and it should return the result, not raise. The branch at `src/factory/adapters/claude_runtime.py:293` (`_parse_reply(...) is not None`) is untested, and criteria 8 and 9 cover only the `sudo:`-line side. Fix: the coder asks the human with `question` to add a criterion before criterion 15, for example "a `sudo` stand-in that prints `sudo: unable to resolve host x` to standard error and then runs the agent, which replies, gives that reply's result, not an error". The tester then writes it as a row next to criteria 8 and 9.
6. coder: coder, round 1: fixed finding 1; finding 2 needs the human's decision, so this is a question.

   Finding 1 is fixed in 0ebb835. `_sudo_refusal` in `src/factory/adapters/claude_runtime.py` no longer skips timed-out runs. It now counts a run as "without a result" in the same way `_result` does: the reply is unparseable or the process timed out. Such a run as `agent` with a `sudo:` line in standard error now raises `AgentRuntimeError`, as the Interface says. `make check` is green and coverage is 99.54 %.

   Finding 2 is open. The reviewer pointed out that one side of Interface rule 3 has no criterion: a run as `agent` that does give a result while its standard error holds a `sudo:` line. That run should return the result and not raise. Because of this gap, the branch `_parse_reply(...) is not None and not process.timed_out` is untested.

   Question for the human: should a criterion be added before criterion 15? My proposed wording: "15. A `sudo` stand-in that prints `sudo: unable to resolve host x` to standard error and then runs the agent, which replies, gives that reply's result, not an `AgentRuntimeError`." The tester would write it as a row next to criteria 8 and 9 in `tests/adapters/test_claude_runtime_os_user.py`.

   Options:
   - (a) Add the criterion as worded. This is what I would choose: sudo really does print that warning on hosts with a mismatched hostname, so the rule matters in practice.
   - (b) Leave the criteria as they are and accept the untested branch.

   With (a), the next run of doing ends with `tests`, naming that test row.
