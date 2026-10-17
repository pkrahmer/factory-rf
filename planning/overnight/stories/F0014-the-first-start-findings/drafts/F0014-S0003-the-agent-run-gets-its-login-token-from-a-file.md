# The agent run gets its login token from a file

## Assignment (as of log entry 1)

Every new instance needs an interactive `claude` login as `agent`: a new `claude-home` volume, and the Podman machine with its own volumes, each needed one at the first start of 2026-10-17 (`planning/overnight/first-start-checklist.md`, "Results", fault 3). The human's answer (2026-10-17): every credential is injected from outside, and no instance needs an interactive login. The agent's login is a token made once with `claude setup-token`, kept in a file, and handed to each agent run only, as `CLAUDE_CODE_OAUTH_TOKEN`; the factory's own processes and the project commands never get it. This story builds the factory's half: a setting that names the file, `FACTORY_CLAUDE_LOGIN_FILE`; the `claude -p` runtime, which reads the file at the start of every run and sets the one name in the environment of that run's calls; the wiring that hands the setting to the runtime; and the preflight's probe, whose detail names the file when the probe fails. The name `CLAUDE_CODE_OAUTH_TOKEN` is Claude Code's, so it stays in the adapter that wraps `claude -p` (R12); the domain's allow list, `ALLOWED_ENVIRONMENT_NAMES`, keeps its six names, because it filters what is copied from the factory's own environment, and the token never passes through that environment (FEATURE decision 9). Without the file the login in the agent's home still works. S0004 mounts the file in the image and sets the variable; until then nothing changes for a running instance. No test of an earlier story changes.

## Interface

`src/factory/domain/settings.py`:

- `CLAUDE_LOGIN_FILE_VARIABLE = "FACTORY_CLAUDE_LOGIN_FILE"`; the constant's name holds no word `token`, for ruff's `S105`, as the comment above `CREDENTIAL_FILE_VARIABLE` explains.
- `InstanceSettings` gains `claude_login_file: Path | None = None`.
- `read_settings` sets it with `_optional_path(environ, CLAUDE_LOGIN_FILE_VARIABLE)`: a path when the variable holds one; `None` when it is unset, empty or only spaces.

`src/factory/adapters/claude_runtime.py`:

- `LOGIN_VARIABLE = "CLAUDE_CODE_OAUTH_TOKEN"`, with a comment: Claude Code's name for a token made by `claude setup-token`.
- `ClaudeCodeRuntime.__init__(self, executable, state_directory, kill_points=None, *, version_time_limit=VERSION_TIME_LIMIT, sudo_executable=SUDO_EXECUTABLE, login_file: Path | None = None)`: the new keyword is last; the docstring says that a run's calls get the token held in `login_file`.
- `run(request)` reads `login_file` once, before the first call, and before it writes the run's files. The token is the file's text with surrounding whitespace stripped.
  - With a token, every `claude -p` call of the run, the first and a resumed one, gets `LOGIN_VARIABLE` set to the token in its environment: the request's environment, then `LOGIN_VARIABLE`, then `SWITCHES`. With an `os_user`, the token reaches `claude` through the `env -i` assignments like every other name.
  - `login_file` is `None`, the file does not exist, or it holds only whitespace: no call gets `LOGIN_VARIABLE`.
  - The runtime drops `LOGIN_VARIABLE` from the request's environment in every case: the name comes from the file or not at all.
  - The file exists but cannot be read (any `OSError` but `FileNotFoundError`, such as a folder in its place or no read permission): `AgentRuntimeError(f"cannot read the agent's login file {login_file}: {error}")`, raised before any call starts and before the run's files are written.
- `version()` is unchanged: `claude --version` never gets `LOGIN_VARIABLE`.
- The token appears in no `AgentRunResult`, in no `AgentRuntimeError` and in none of the run's files (`instructions-<session>.md`, `guard-<session>.json`, `hooks-<session>.json`).

`src/factory/entry/wiring.py`: `build_boundaries` builds `ClaudeCodeRuntime(..., login_file=settings.claude_login_file)`. Nothing else in the wiring changes: `production_environment()` and `agent_run_environment(...)` give no `LOGIN_VARIABLE`.

`src/factory/application/preflight.py`: `agent_run_probe_item(boundaries, settings, environment)`, signature unchanged. When the probe run does not end `completed` and `settings.claude_login_file` is set, its detail is the present one followed by `; the agent's login token is read from <path>: make it with claude setup-token if it is missing, empty or expired`, where `<path>` is `settings.claude_login_file`. With `claude_login_file` `None`, the detail is the present one. The item does not look at the file itself; an unreadable file reaches it as the runtime's `AgentRuntimeError`, whose text names the file, as any runtime error does now.

`src/factory/domain/agent_runs.py` does not change.

Tests: new modules `tests/domain/test_settings_claude_login.py`, `tests/adapters/test_claude_runtime_login.py` (with `write_stand_in` and `read_calls` of `tests/adapters/claude_stand_in.py`, and the `sudo` stand-in as `tests/adapters/test_claude_runtime_os_user.py` writes it), `tests/entry/test_wiring_login.py` and `tests/application/test_agent_run_probe_login.py`. Every test value is low-entropy prose (`stand-in-login`). detect-secrets scans the tests: no line writes the name `CLAUDE_CODE_OAUTH_TOKEN` and a value together as a literal pair (a dict entry or a `NAME=value` text); a test compares `environment[LOGIN_VARIABLE]` with a constant that holds the value.

## Acceptance criteria

1. `read_settings` gives `claude_login_file` = `Path("/home/agent/.claude-token")` for `FACTORY_CLAUDE_LOGIN_FILE=/home/agent/.claude-token`, and `None` when the variable is unset, empty or only spaces (rows of one parametrized test).
2. With a login file holding `stand-in-login` followed by a newline, the `claude -p` call gets `LOGIN_VARIABLE` with the value `stand-in-login`, beside the request's environment and the `SWITCHES`.
3. No call gets `LOGIN_VARIABLE` when `login_file` is `None`, when the file does not exist, and when it holds only spaces and newlines; each of these runs completes as without a file (rows of one parametrized test with criterion 2's row).
4. A request whose environment carries `LOGIN_VARIABLE` reaches `claude` without it when there is no login file, and with the file's value when there is one (rows).
5. A run stopped by its budget and resumed gets the token in both calls.
6. With an `os_user`, the token reaches `claude` through `sudo` and `env -i`: the agent's environment holds `LOGIN_VARIABLE` with the file's value.
7. A login file that exists but cannot be read (a folder at its path) raises `AgentRuntimeError` whose message holds `cannot read the agent's login file` and the path; no call is made and no run file is left in the state directory.
8. With a login file, `version()` starts `claude --version` without `LOGIN_VARIABLE` in its environment.
9. The token's text is in none of the run's files while the call runs (the stand-in reads them), in no field of the `AgentRunResult`, and in no `AgentRuntimeError` of a refused `sudo`.
10. `scrub_environment` drops `LOGIN_VARIABLE` from a source that has it, and `ALLOWED_ENVIRONMENT_NAMES` still holds exactly `PATH`, `HOME`, `LANG`, `LC_ALL`, `TERM` and `TZ`.
11. `build_boundaries` with settings whose `claude_login_file` names a file builds a runtime whose run hands that file's token to `claude` (a stand-in `claude` as `settings.claude_executable`); with `claude_login_file` `None` the run gets none.
12. The probe's detail for a run that ends `died` is the present detail followed by `; the agent's login token is read from /home/agent/.claude-token: make it with claude setup-token if it is missing, empty or expired` when `claude_login_file` is that path, and the present detail alone when it is `None` (rows of one parametrized test, with and without an agent user).
13. A runtime that raises `AgentRuntimeError` for an unreadable login file fails the probe with a detail that names the file.
14. What must still hold: without a login file the runtime hands the agent only the request's environment and the switches (`tests/adapters/test_claude_runtime_environment.py`), and the probe's details are as pinned (`tests/application/test_agent_run_probe.py`).
15. `make check` stays green.
16. docs: the operator guide's configuration table gets a row for `FACTORY_CLAUDE_LOGIN_FILE` (no, not required; the file that holds the agent's login token, made with `claude setup-token`; no default; S0004's image sets it). *The agent runtime* says that the call runs under the token in that file when it holds one, and under the login in the agent's home when the variable is unset or the file is missing or blank; that the file is read at the start of every run, so a new token is used from the next run without a restart; that an unreadable file stops the run with `cannot read the agent's login file <path>: <error>`; that the token reaches only the `claude -p` calls, as `CLAUDE_CODE_OAUTH_TOKEN`, never the factory's own environment, the project commands or `claude --version`; that the allow list keeps its six names and the runtime adds this one; and that under `sudo` the token stands on the command line of the `sudo` and `timeout` processes inside the container, where only the factory's user and the agent's, both of whom can read the file, run. The time-limit observation in *The agent runs as a second user* becomes `docker exec <container> pgrep -u agent -l`, expected to print nothing after the limit, in place of `ps -eo user,pid,args`, which would print the token. *The probe of the agent run* names the new end of the detail. The project guide's entry of `ClaudeCodeRuntime` gives the new keyword and the reading rules, and its sentence on `InstanceSettings` names `claude_login_file`. The decision log gets an entry "The agent's login is a token from a file" (the first start's fault, the human's answer, why the name stays in the adapter and the allow list keeps six names, the command line under `sudo`, and the API key left out with its reason). No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
from factory.domain.settings import read_settings
base = {'FACTORY_REPOSITORY_URL': 'https://github.com/owner/project.git', 'FACTORY_INSTANCE': 'demo'}
print(read_settings({**base, 'FACTORY_CLAUDE_LOGIN_FILE': '/home/agent/.claude-token'}).claude_login_file)
print(read_settings({**base, 'FACTORY_CLAUDE_LOGIN_FILE': '  '}).claude_login_file)
"
```
Expect: two lines: `/home/agent/.claude-token` and `None`.

```bash
uv run python -c "from factory.domain.agent_runs import ALLOWED_ENVIRONMENT_NAMES; from factory.adapters.claude_runtime import LOGIN_VARIABLE; print(sorted(ALLOWED_ENVIRONMENT_NAMES), LOGIN_VARIABLE in ALLOWED_ENVIRONMENT_NAMES)"
```
Expect: one line: `['HOME', 'LANG', 'LC_ALL', 'PATH', 'TERM', 'TZ'] False`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/domain/test_settings_claude_login.py tests/adapters/test_claude_runtime_login.py tests/entry/test_wiring_login.py tests/application/test_agent_run_probe_login.py tests/adapters/test_claude_runtime_environment.py tests/application/test_agent_run_probe.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
