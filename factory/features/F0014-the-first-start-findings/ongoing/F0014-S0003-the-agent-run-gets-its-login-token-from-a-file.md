---
stage: review
pr: 196
blocked: null
comments_seen: 4
round: 0
attempts: 0
---
# The agent run gets its login token from a file

## Assignment (as of log entry 1)

Every new instance needs an interactive `claude` login as `agent`: a new `claude-home` volume, and the Podman machine with its own volumes, each needed one at the first start of 2026-10-17 (`planning/overnight/first-start-checklist.md`, "Results", fault 3). The human's answer (2026-10-17): every credential is injected from outside, and no instance needs an interactive login. The agent's login is a token made once with `claude setup-token`, kept in a file, and handed to each agent run only, as `CLAUDE_CODE_OAUTH_TOKEN`; the factory's own processes and the project commands never get it. This story builds the factory's half: a setting that names the file, `FACTORY_CLAUDE_LOGIN_FILE`; the `claude -p` runtime, which starts each call through a small shell that reads the file itself, as the user the call runs as (the agent, under `sudo`), and puts the one name into `claude`'s environment before it hands over to `claude` (`exec`); the wiring that hands the setting to the runtime; and the preflight's probe, whose detail names the file when the probe fails. The factory never reads the token, and the token stands in no process's arguments: not in those of `sudo`, `timeout`, `env`, the shell or `claude` (the human's answer after the pre-check, 2026-10-17, FEATURE decision 30). On a Linux host every host user's `ps` shows a container's processes with their arguments, so a token on a command line would be seen beyond the container. The name `CLAUDE_CODE_OAUTH_TOKEN` is Claude Code's, so it stays in the adapter that wraps `claude -p` (R12); the domain's allow list, `ALLOWED_ENVIRONMENT_NAMES`, keeps its six names, because it filters what is copied from the factory's own environment, and the token never passes through that environment (FEATURE decision 9). Without the file, or with a blank one, the login in the agent's home still works. A file that cannot be read, or that is not plain ASCII text (a file saved as UTF-16 by Windows PowerShell 5), stops the run with an error naming the file. S0004 mounts the file in the image and sets the variable; until then nothing changes for a running instance. The probe gets its run's result from `run_sealed` (S0009, S0010), which this story does not change. No test of an earlier story changes.

## Interface

`src/factory/domain/settings.py`:

- `CLAUDE_LOGIN_FILE_VARIABLE = "FACTORY_CLAUDE_LOGIN_FILE"`; the constant's name holds no word `token`, for ruff's `S105`, as the comment above `CREDENTIAL_FILE_VARIABLE` explains.
- `InstanceSettings` gains `claude_login_file: Path | None = None`.
- `read_settings` sets it with `_optional_path(environ, CLAUDE_LOGIN_FILE_VARIABLE)`: a path when the variable holds one; `None` when it is unset, empty or only spaces.

`src/factory/adapters/claude_runtime.py`:

- `LOGIN_VARIABLE = "CLAUDE_CODE_OAUTH_TOKEN"`, with a comment: Claude Code's name for a token made by `claude setup-token`.
- `SHELL_EXECUTABLE = "/bin/sh"`, the shell that reads the login file.
- `LOGIN_PREFIX = "factory-login:"`, the start of the one line the login shell writes on standard error when it cannot use the file.
- `LOGIN_SCRIPT`, a module constant: a POSIX `sh` script, started as `[SHELL_EXECUTABLE, "-c", LOGIN_SCRIPT, "factory-login", <login file>, <claude executable>, *<claude's arguments>]`. The login file is a positional argument, never part of the script's text. As the user it runs as, it does this, in order:
  - The file does not exist: it unsets `LOGIN_VARIABLE` and hands over to `claude` with its arguments (`exec`).
  - The file is not a regular file or cannot be read (a folder in its place, no read permission): it writes exactly the line `factory-login: cannot be read` on standard error and exits without starting `claude`.
  - The file holds a byte other than printable ASCII (`!` to `~`), space, tab, carriage return and line feed (a file saved as UTF-16, whose byte order mark and zero bytes are not ASCII): it writes exactly the line `factory-login: not ASCII text` on standard error and exits without starting `claude`. The check counts bytes (for example with `tr -d` and `wc -c` under `LC_ALL=C`), because a shell variable cannot hold a zero byte.
  - The file is empty or holds only whitespace: it unsets `LOGIN_VARIABLE` and hands over to `claude`.
  - Otherwise the token is the file's text with its whitespace removed; it exports `LOGIN_VARIABLE` with the token and hands over to `claude`.
  - It writes nothing else on standard error itself: the errors of the commands it uses to read the file are discarded.
- `ClaudeCodeRuntime.__init__(self, executable, state_directory, kill_points=None, *, version_time_limit=VERSION_TIME_LIMIT, sudo_executable=SUDO_EXECUTABLE, login_file: Path | None = None)`: the new keyword is last; the docstring says that a run's calls get the token held in `login_file`, read by the call's own shell.
- `run(request)` does not read `login_file`, and it does not use `read_setting_file`, whose missing or blank file is a refusal.
  - With `login_file` set, every `claude -p` call of the run, the first and a resumed one, is started through the login shell: where the call's arguments held `[executable, *arguments]` they hold `[SHELL_EXECUTABLE, "-c", LOGIN_SCRIPT, "factory-login", str(login_file), executable, *arguments]`. With an `os_user` that list follows `sudo -n -u <user> -- timeout ... env -i <assignments>` as `claude` does today, so the shell runs as the agent; without one it is started directly, with the request's environment and the `SWITCHES`.
  - Each call's shell reads the file when it starts, so a resumed call and the next run use the file as it is then: a changed, new or removed file counts from the next call on, without a restart.
  - With `login_file` `None`, every call is started exactly as today.
  - The runtime drops `LOGIN_VARIABLE` from the request's environment in every case: the name comes from the file or not at all, and it is never among the `env -i` assignments.
  - A call that printed no reply and whose standard error holds a line starting with `LOGIN_PREFIX`: `AgentRuntimeError(f"cannot read the agent's login file {login_file}: {reason}")`, where `reason` is the rest of that line, stripped (`cannot be read` or `not ASCII text`). It is checked after a refused `sudo`, before the result is read; no run file is left in the state directory.
- `version()` is unchanged: `claude --version` is not started through the login shell.
- The token appears in no process's arguments, in no `AgentRunResult`, in no `AgentRuntimeError` and in none of the run's files (`instructions-<session>.md`, `guard-<session>.json`, `hooks-<session>.json`): the factory never holds it.

`src/factory/entry/wiring.py`: `build_boundaries` builds `ClaudeCodeRuntime(..., login_file=settings.claude_login_file)`. Nothing else in the wiring changes: `production_environment()` and `agent_run_environment(...)` give no `LOGIN_VARIABLE`.

`src/factory/application/preflight.py`: `agent_run_probe_item(boundaries, settings, environment)`, signature unchanged. When the probe run does not end `completed` and `settings.claude_login_file` is set, its detail is the present one followed by `; the agent's login token is read from <path>: make it with claude setup-token if it is missing, empty or expired`, where `<path>` is `settings.claude_login_file`. With `claude_login_file` `None`, the detail is the present one. The item does not look at the file itself; an unreadable file reaches it as the runtime's `AgentRuntimeError`, whose text names the file, as any runtime error does now.

`src/factory/domain/agent_runs.py` does not change.

Tests: new modules `tests/domain/test_settings_claude_login.py`, `tests/adapters/test_claude_runtime_login.py`, `tests/entry/test_wiring_login.py` and `tests/application/test_agent_run_probe_login.py`.

- `tests/adapters/test_claude_runtime_login.py` uses `Step`, `write_stand_in` and `read_calls` of `tests/adapters/claude_stand_in.py`. It imports `_write_sudo` and `_request` from `adapters.test_claude_runtime_os_user`, as `tests/adapters/test_claude_runtime_sudo_time_limit.py` does; there is no second copy of the `sudo` stand-in. The `sudo` stand-in records its whole argument list, which holds the chain after it (`timeout`, `env -i` and its assignments, the shell and its arguments, `claude` and its arguments), and hands over to it; the real `/bin/sh` runs the login script.
- `tests/application/test_agent_run_probe_login.py` uses the `boundaries` fixture, whose git is a real clone, so the probe's `run_sealed` (S0009) seals and checks it.
- Every test value is low-entropy prose (`stand-in-login`, `changed-login`), held in constants whose names have none of the words `token`, `secret`, `password` or `pass`. Ruff's `S105` takes a string assigned to such a name, or compared with a subscript whose literal key is `CLAUDE_CODE_OAUTH_TOKEN`, for a secret. So a test compares `environment[LOGIN_VARIABLE]` with such a constant and never writes the name `CLAUDE_CODE_OAUTH_TOKEN` as a literal.

## Acceptance criteria

1. `read_settings` gives `claude_login_file` = `Path("/home/agent/.claude-token")` for `FACTORY_CLAUDE_LOGIN_FILE=/home/agent/.claude-token`, and `None` when the variable is unset, empty or only spaces (rows of one parametrized test).
2. With a login file holding `stand-in-login` followed by a newline, the `claude -p` call gets `LOGIN_VARIABLE` with the value `stand-in-login`, beside the request's environment and the `SWITCHES`.
3. No call gets `LOGIN_VARIABLE` when `login_file` is `None`, when the file does not exist, when it is empty, and when it holds only spaces and newlines; each of these runs completes as without a file (rows of one parametrized test with criterion 2's row).
4. A request whose environment carries `LOGIN_VARIABLE` reaches `claude` without it when there is no login file, and with the file's value when there is one (rows).
5. Each call reads the file when it starts: in a run stopped by its budget and resumed, the first call rewrites the login file with `changed-login` (the stand-in's `writes`); the first call got `stand-in-login`, and the resumed call gets `changed-login`.
6. One runtime reads the file again at every run. Rows of one parametrized test, each two runs of one `ClaudeCodeRuntime` with the file changed between them:
   - `stand-in-login`, then `changed-login`: the second run's call gets `changed-login`.
   - no file, then `stand-in-login`: the first run's call gets no `LOGIN_VARIABLE`, the second gets `stand-in-login`.
   - `stand-in-login`, then the file removed: the second run's call gets no `LOGIN_VARIABLE`.
7. With an `os_user`, the token reaches `claude` through `sudo`, `env -i` and the login shell: the agent's environment holds `LOGIN_VARIABLE` with the file's value. The `sudo` call's `env -i` assignments are the request's names and the `SWITCHES`, one each, and no `LOGIN_VARIABLE`; after them come `/bin/sh`, `-c`, `LOGIN_SCRIPT`, `factory-login`, the login file's path, the `claude` executable and `claude`'s arguments.
8. The token is in no argument list. For a request with a guard (so that the instructions, guard and hooks files all exist), with and without an `os_user` (rows of one parametrized test), the text `stand-in-login` is in none of the arguments the `sudo` stand-in records (its list holds the whole chain after `sudo`), in none of the arguments the `claude` stand-in records, in none of the run's files while the call runs (the stand-in reads them), and in no field of the `AgentRunResult`. Without an `os_user` the shell's arguments are the tail that criterion 7 pins.
9. A login file that cannot be used stops the run: `AgentRuntimeError` whose message is `agent runtime failed: cannot read the agent's login file <path>: <reason>`; the `claude` stand-in records no call, and no run file is left in the state directory. Rows of one parametrized test:
   - a folder at the path: `cannot be read`
   - a file holding `stand-in-login` encoded as UTF-16 with its byte order mark (`"stand-in-login".encode("utf-16")`): `not ASCII text`
   - a file holding `stand-in-login` encoded as UTF-16 without a byte order mark (`"stand-in-login".encode("utf-16-le")`, zero bytes between the letters): `not ASCII text`
   - the UTF-16 file with the byte order mark, with an `os_user`: `not ASCII text`

   No row depends on file permissions, which root ignores.
10. With a login file, and `LOGIN_VARIABLE` removed from the test process's environment (`monkeypatch.delenv(LOGIN_VARIABLE, raising=False)`, because `version()` inherits that environment), `version()` starts `claude --version` without `LOGIN_VARIABLE` in its environment and without the login shell (the stand-in records `--version` as its only argument).
11. `scrub_environment` drops `LOGIN_VARIABLE` from a source that has it, and `ALLOWED_ENVIRONMENT_NAMES` still holds exactly `PATH`, `HOME`, `LANG`, `LC_ALL`, `TERM` and `TZ`.
12. `build_boundaries` with settings whose `claude_login_file` names a file builds a runtime whose run hands that file's token to `claude` (a stand-in `claude` as `settings.claude_executable`); with `claude_login_file` `None` the run gets none.
13. The probe's detail for a run that ends `died`, `no_result`, `time_limit` or `budget`, with and without an agent user, is the present detail followed by `; the agent's login token is read from /home/agent/.claude-token: make it with claude setup-token if it is missing, empty or expired` when `claude_login_file` is that path, and the present detail alone when it is `None`. A run that ends `completed` passes with no detail when `claude_login_file` is that path. All rows of one parametrized test.
14. The probe with a `ClaudeCodeRuntime` whose `login_file` is a folder fails with a detail that holds `cannot read the agent's login file` and the folder's path, and does not hold `claude setup-token`.
15. What must still hold: without a login file the runtime hands the agent only the request's environment and the switches, and starts `claude` as before (`tests/adapters/test_claude_runtime_environment.py`, `tests/adapters/test_claude_runtime_os_user.py`), and the probe's details are as pinned (`tests/application/test_agent_run_probe.py`).
16. `make check` stays green.
17. docs: The operator guide:
    - Its configuration table gets a row for `FACTORY_CLAUDE_LOGIN_FILE`: no, not required; the file that holds the agent's login token, made with `claude setup-token`, as plain ASCII text; blank counts as unset; no default; S0004's image sets it.
    - *The agent runtime* says:
      - the call runs under the token in that file when it holds one, and under the login in the agent's home when the variable is unset or the file is missing or blank;
      - the file is read by a small shell at the start of every `claude -p` call, as the user the call runs as (the agent, under `sudo`), so a new token is used from the next call without a restart; the factory itself never reads it;
      - a file that cannot be read, or that is not plain ASCII text (a file saved as UTF-16 by Windows PowerShell 5), stops the run with `cannot read the agent's login file <path>: cannot be read` or `...: not ASCII text`;
      - the token reaches only the `claude -p` calls, as `CLAUDE_CODE_OAUTH_TOKEN`, never the factory's own environment, the project commands or `claude --version`;
      - the token stands in no process's arguments, so neither `ps` inside the container nor a host user's `ps` on a Linux host shows it;
      - the allow list keeps its six names and the runtime's shell adds this one.
    - *The probe of the agent run* names the new end of the detail.

    The project guide:
    - The entry of `ClaudeCodeRuntime` gives the new keyword, the login shell, its arguments and its rules, and the error.
    - The sentence on the agent run's environment ("`ClaudeCodeRuntime` runs the agent with `request.environment` plus its `SWITCHES` and nothing of the process's own environment") adds the token the login shell reads from the file and the dropped request entry.
    - The `build_boundaries` paragraph gives `login_file=settings.claude_login_file`.
    - The sentence on `InstanceSettings` names `claude_login_file`.

    The decision log gets an entry "The agent's login is a token from a file". It gives the first start's fault, the human's answer, why the name stays in the adapter and why the allow list keeps six names, and why the agent's own shell reads the file: the token stands on no command line, which every host user's `ps` shows on a Linux host unless `/proc` is mounted with `hidepid=2`. It names what was rejected: the factory reading the file and passing the token as an `env -i` assignment on the `sudo` command line. It names the API key, left out, with its reason.

    No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

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
uv run python -c "
import subprocess, tempfile
from pathlib import Path
from factory.adapters.claude_runtime import LOGIN_SCRIPT, LOGIN_VARIABLE, SHELL_EXECUTABLE
folder = Path(tempfile.mkdtemp())
(folder / 'plain').write_bytes(b'stand-in-login\n')
(folder / 'blank').write_bytes(b' \n')
(folder / 'utf-16').write_bytes('stand-in-login'.encode('utf-16'))
(folder / 'folder').mkdir()
for label in ('plain', 'missing', 'blank', 'utf-16', 'folder'):
    done = subprocess.run([SHELL_EXECUTABLE, '-c', LOGIN_SCRIPT, 'factory-login', str(folder / label), 'printenv', LOGIN_VARIABLE], capture_output=True, text=True, check=False)
    print(label, done.stdout.strip() or '-', done.stderr.strip() or '-')
"
```
Expect: five lines: `plain stand-in-login -`, `missing - -`, `blank - -`, `utf-16 - factory-login: not ASCII text`, `folder - factory-login: cannot be read`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/domain/test_settings_claude_login.py tests/adapters/test_claude_runtime_login.py tests/entry/test_wiring_login.py tests/application/test_agent_run_probe_login.py tests/adapters/test_claude_runtime_environment.py tests/adapters/test_claude_runtime_os_user.py tests/application/test_agent_run_probe.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: concrete modules and signatures throughout (settings constant and field, `LOGIN_VARIABLE`/`SHELL_EXECUTABLE`/`LOGIN_PREFIX`/`LOGIN_SCRIPT`, the runtime's new keyword, wiring, probe detail). The helpers it names exist (`_write_sudo`, `_request`, `Step.writes`, `write_stand_in`, `read_calls`, `_optional_path`, `SUDO_EXECUTABLE`), and the script's arguments and its order of cases are pinned.
   - Criteria: each is testable by one test function or one parametrized test. Every Interface rule has a criterion, and so does its failing side. Missing, empty and blank files are criteria 3 and 6. A folder in place of the file and UTF-16 with and without a byte order mark, with and without `os_user`, are criterion 9. The probe's failing side is 13 and 14, and the `completed` side is 13. The request's login variable being dropped is criterion 4. `version()` is criterion 10, the allow list is 11, wiring is 12, and settings unset, empty and blank is 1. One gap: the "no read permission" case has no row, because root ignores permissions. The ticket says so itself, and the folder row covers the same script branch. Not a question.
   - Demo: the commands are runnable, and each `Expect:` line is checkable (exact output lines, or the pytest summary with no failed, error or skipped count).
   - Architecture: the Claude Code name stays in `factory.adapters`; the domain only gains a path setting and the allow list is untouched; the wiring and the probe change as layered. The only external tools are `/bin/sh` and `sudo`, both reached through the runtime wrapper.
   - Scope: within FEATURE.md's S0003 row (the setting, runtime, wiring and probe detail), and the image/compose work is left to S0004. The API key, a preflight item of its own for the file, and the hosting token are out of scope and not touched. The write paths cover the four source files named. Decisions 9 to 13, 30(c) and 33 agree with the ticket.
3. tester: Wrote the red tests for every acceptance criterion. `make lint` is green. One `make test` run fails for the right reasons: three new modules cannot import names that do not exist yet, and the probe test gets the wrong detail.

   Criterion → test:
   - criterion 1: tests/domain/test_settings_claude_login.py::test_the_login_file_setting_is_a_path_or_none_when_blank (rows: path, unset, empty, spaces)
   - criterion 2: tests/adapters/test_claude_runtime_login.py::test_the_call_gets_the_login_from_a_file_that_holds_one_and_otherwise_none (row `token`)
   - criterion 3: the same test, rows `no-setting`, `missing`, `empty`, `blank`; each run also has to end `completed`
   - criterion 4: tests/adapters/test_claude_runtime_login.py::test_the_request_s_login_entry_is_dropped_for_the_file_s (rows: no-setting, missing, token)
   - criterion 5: tests/adapters/test_claude_runtime_login.py::test_a_resumed_call_reads_the_login_file_again
   - criterion 6: tests/adapters/test_claude_runtime_login.py::test_one_runtime_reads_the_login_file_again_at_every_run (rows: changed, new, removed)
   - criterion 7: tests/adapters/test_claude_runtime_login.py::test_with_a_user_the_login_shell_runs_after_sudo_and_env_i_and_hands_over_the_login
   - criterion 8: tests/adapters/test_claude_runtime_login.py::test_the_login_stands_in_no_argument_no_run_file_and_no_result (rows: user, no-user)
   - criterion 9: tests/adapters/test_claude_runtime_login.py::test_a_login_file_that_cannot_be_used_stops_the_run_naming_the_file (rows: folder, utf-16, utf-16-without-mark, utf-16-with-a-user)
   - criterion 10: tests/adapters/test_claude_runtime_login.py::test_the_version_call_gets_no_login_and_no_login_shell
   - criterion 11: tests/adapters/test_claude_runtime_login.py::test_the_allow_list_keeps_its_six_names_and_scrubbing_drops_the_login
   - criterion 12: tests/entry/test_wiring_login.py::test_the_built_runtime_hands_the_login_file_s_token_to_claude (rows: login-file, no-login-file)
   - criterion 13: tests/application/test_agent_run_probe_login.py::test_a_probe_that_does_not_complete_names_the_login_file_when_one_is_set (four reasons × with and without an agent user × login file or none, plus a `completed` row that passes with an empty detail)
   - criterion 14: tests/application/test_agent_run_probe_login.py::test_a_login_file_the_runtime_cannot_read_fails_the_probe_with_the_runtime_s_message
   - criterion 15: covered by the existing tests/adapters/test_claude_runtime_environment.py, tests/adapters/test_claude_runtime_os_user.py and tests/application/test_agent_run_probe.py, which this stage did not change
   - criteria 16 and 17: `make check` and the docs, not tests

   Notes for the coder:
   - The criterion 2 and 3 checks are a subset check: `{**GIVEN, **SWITCHES}` must be contained in claude's environment. They do not require equality, because `/bin/sh` may add its own variables (PWD and the like).
   - The criterion 8 test and the `version()` test (criterion 10) put a `run_process` wrapper in front of `claude_runtime.run_process`. It records each `ProcessRequest` and then calls the real `run_process`. With it the tests check that the token is nowhere in the factory's process request, neither in `argv` nor in `env`. The wrapper also pins that the shell's argv without an `os_user` is the criterion 7 tail, and that `version()` starts `[executable, "--version"]` directly.
   - The runtime module also imports `_sudo_calls` from adapters.test_claude_runtime_os_user, next to `_write_sudo` and `_request`. That reuses the existing helper rather than copying it.
   - The test requests carry no PATH, as the `_request` helper of the earlier tests does, so the login script has to work under `env -i` without a PATH.

   Files created: tests/domain/test_settings_claude_login.py, tests/adapters/test_claude_runtime_login.py, tests/entry/test_wiring_login.py, tests/application/test_agent_run_probe_login.py.

   Could not import: `CLAUDE_LOGIN_FILE_VARIABLE` from factory.domain.settings, and `LOGIN_SCRIPT`, `LOGIN_VARIABLE` and `SHELL_EXECUTABLE` from factory.adapters.claude_runtime (test_settings_claude_login, test_claude_runtime_login, test_wiring_login). test_agent_run_probe_login imports, and its rows fail on the detail. No criterion needed interpretation.

   `make lint`: lint: green (0.0 s)
   `make test`: ERROR tests/entry/test_wiring_login.py - ImportError while importing test mod...
4. coder: Question: one test row cannot pass against the ticket. In `tests/application/test_agent_run_probe_login.py::test_a_probe_that_does_not_complete_names_the_login_file_when_one_is_set[completed-login-file]`, line 79 builds `AgentRunResult(end_reason="completed", duration=...)` and only afterwards adds the decision and entry with `model_copy`. The validator in `src/factory/domain/agent_runs.py:149` refuses a `completed` result that has no decision ("a completed run needs a decision"), so the test fails with a `ValidationError` before it reaches the probe. The ticket says `agent_runs.py` does not change.

   Options:
   (a) The tester builds the `completed` result with `decision="question", entry="probe"` in the constructor, for example `AgentRunResult(end_reason=reason, duration=..., **({"decision": "question", "entry": "probe"} if reason == "completed" else {}))`, or with a small helper. My choice: no code change and no change to what the test means.
   (b) Loosen the domain validator. I reject this: it contradicts the ticket and weakens a rule earlier stories rely on.

   State: the implementation is committed (25131133). Every other new test passes, as do the pinned tests for criterion 15. `make lint`, `make types` and `make layers` are green; `make test` is red on this one row only.
   - `src/factory/domain/settings.py`: `CLAUDE_LOGIN_FILE_VARIABLE`, and `InstanceSettings.claude_login_file` read through `_optional_path`.
   - `src/factory/adapters/claude_runtime.py`:
     - New constants `LOGIN_VARIABLE`, `SHELL_EXECUTABLE`, `LOGIN_PREFIX` and `LOGIN_SCRIPT`. `LOGIN_SCRIPT` is a POSIX sh script. It checks that the file exists, then that it is a regular file `cat` can read, then counts the bytes left after `LC_ALL=C tr -d '!-~ \t\r\n'`, then strips whitespace and either exports or unsets the variable before `exec "$@"`. It runs under `env -i` with no PATH, because dash falls back to its built-in default path.
     - New keyword `login_file`.
     - `_claude_argv` puts the shell in front of `claude` for the first call and for a resumed one.
     - `LOGIN_VARIABLE` is always dropped from the request's environment.
     - `_check_login` raises `AgentRuntimeError` after the `sudo` check when stdout is not a reply and stderr has a `factory-login:` line.
     - `version()` is unchanged.
   - `src/factory/entry/wiring.py`: passes `login_file=settings.claude_login_file`.
   - `src/factory/application/preflight.py`: adds the login-file hint to the detail of a run that did not complete.

   Rejected: leaving out the separate check for a file that cannot be read and letting the ASCII count catch it. That would report a folder as plain text, since `tr` sees no bytes. A dangling symlink counts as a missing file (`test -e`), matching the ticket's wording.

   For review: the ticket pins a constructor signature that exceeds ruff's PLR0913 limit (6 > 5). I added `# noqa: PLR0913` with a reason comment on `ClaudeCodeRuntime.__init__`. A ruff `noqa` is not on the "not without asking" list, but the reviewer may want it noted. The refactor pass is still to do after the answer.
5. human (pull request comment, 2026-10-17): (a): the tester builds the `completed` result with `decision="question", entry="probe"` in the constructor (or a small helper); `agent_runs.py` and its validator stay. The criterion is unchanged. The `# noqa: PLR0913` with its reason on `ClaudeCodeRuntime.__init__` is fine: the ticket pins that signature.
6. coder: The human's answer (entry 5) is option (a), which is a test change, so I'm handing this to the tester. I did not touch the test or the code. The change: in `tests/application/test_agent_run_probe_login.py::test_a_probe_that_does_not_complete_names_the_login_file_when_one_is_set` (line 79), the `completed` row must pass `decision="question", entry="probe"` to the `AgentRunResult` constructor, either inline or through a small helper, and must not add them afterwards with `model_copy`. The reason is that the validator in `src/factory/domain/agent_runs.py` refuses a `completed` result with no decision before the probe ever runs. `agent_runs.py` stays unchanged, and so does the criterion. The implementation is already committed (25131133), and the human accepted its `# noqa: PLR0913` on `ClaudeCodeRuntime.__init__`. Still open for the next doing pass: the refactor step, and `make check`, which is red on this one row until the tester's change lands.
7. tester: Made the test change the human approved in entry 5, option (a), and only that. In `tests/application/test_agent_run_probe_login.py`, `test_a_probe_that_does_not_complete_names_the_login_file_when_one_is_set` no longer builds the result first and then adds `decision`/`entry` with `model_copy`. It now queues `_probe_result(reason)`, a new small private helper next to the rows. For `completed` the helper constructs `AgentRunResult(end_reason=reason, duration=5 s, decision="question", entry="probe")` directly; for every other reason it constructs `AgentRunResult(end_reason=reason, duration=5 s)`. The rows, the criterion and `agent_runs.py` are unchanged.

   `make lint`: lint: green (0.1 s).

   `make test` (one run) is still red, but not because of this test: the `completed-login-file` row no longer fails. The one failure is the existing structural test `tests/test_process_search.py::test_the_only_suppression_markers_are_the_four_in_the_process_wrapper`. It reports `{'adapters/claude_runtime.py': {377: {'noqa: PLR0913'}}}`, which is the coder's `# noqa: PLR0913` on `ClaudeCodeRuntime.__init__`. The human accepted that marker in entry 5, but this test only allows the four markers in `adapters/process.py`. I did not change that test because it is outside the approved change and not mine. Open for the coder: remove the need for the marker (for example by grouping the constructor's parameters while keeping the pinned call shape), or raise it with the human as a test change of `test_process_search.py`.

   `make lint`: lint: green (0.0 s)
   `make test`: FAILED tests/test_process_search.py::test_the_only_suppression_markers_are_the_four_in_the_process_wrapper
8. coder: Question: the `# noqa: PLR0913` you accepted in entry 5 conflicts with an existing structural test, and I can't fix that without a change you have to approve. `tests/test_process_search.py::test_the_only_suppression_markers_are_the_four_in_the_process_wrapper` allows suppression markers only in `src/factory/adapters/process.py`. It reports `adapters/claude_runtime.py:377 noqa: PLR0913`, the marker on `ClaudeCodeRuntime.__init__`. That is the only red test (tester, entry 7). The ticket pins the signature `(executable, state_directory, kill_points=None, *, version_time_limit, sudo_executable, login_file)`. Ruff doesn't count `self`, so that's 6 arguments against `max-args = 5` in `pyproject.toml`. I can't drop the marker without one of these:

   (a) A test change: `test_process_search.py` also allows this one marker on `ClaudeCodeRuntime.__init__`. I would end with `tests`, and the tester makes that change.
   (b) A tool-configuration change, no marker: in `pyproject.toml`, add `"src/factory/adapters/claude_runtime.py" = ["PLR0913"]` under `[tool.ruff.lint.per-file-ignores]`, with a reason comment. This is narrow, but it turns the rule off for the whole module, and `pyproject.toml` is configuration that agents don't touch without asking.
   (c) Raise `max-args` to 6 for the whole project. This loosens the rule everywhere, so I reject it.
   (d) Pass the keyword options as `**options: Unpack[RuntimeOptions]` with a TypedDict. Calls look the same, but the pinned signature turns into an opaque one. I reject it as a clever workaround.

   My choice is (b). It touches no test, adds no marker in the source, and keeps the exception to the one module whose signature the ticket pins. I would also remove the `# noqa` and its comment. If you prefer (a), I'll hand over to the tester.

   Current state: the implementation is committed (25131133): `src/factory/domain/settings.py`, `src/factory/adapters/claude_runtime.py` (login shell, `LOGIN_SCRIPT`, `_claude_argv`, `_check_login`, request entry dropped), `src/factory/entry/wiring.py` and `src/factory/application/preflight.py`. All the new tests and the pinned tests pass. The refactor pass and the final `make check` are left for the next doing pass, after your answer.
9. human (pull request comment, 2026-10-17): (b): done as the human's change on `main` (3a90bb42): `pyproject.toml` ignores `PLR0913` for `src/factory/adapters/claude_runtime.py`, with its reason. Remove the `# noqa: PLR0913` and its comment; `tests/test_process_search.py` stays unchanged. The criterion is unchanged.
10. coder: Did what the human's answer in entry 9 asked. `pyproject.toml` on `main` (3a90bb42, merged into the branch) now ignores `PLR0913` for this module, so I removed the `# noqa: PLR0913` and its reason comment from `ClaudeCodeRuntime.__init__` in `src/factory/adapters/claude_runtime.py` (fb07f73c). `tests/test_process_search.py` was not changed, and neither was any other test. `make check`: check: green, with branch coverage at 99.45 %.

    What the ticket built (implementation in 25131133):
    - `src/factory/domain/settings.py`: `CLAUDE_LOGIN_FILE_VARIABLE`, and `InstanceSettings.claude_login_file` read through `_optional_path`.
    - `src/factory/adapters/claude_runtime.py`:
      - New constants `LOGIN_VARIABLE`, `SHELL_EXECUTABLE`, `LOGIN_PREFIX` and `LOGIN_SCRIPT`. `LOGIN_SCRIPT` is a POSIX sh script that checks, in this order:
        - the file is missing: unset the variable, then `exec`;
        - it is not a regular file or `cat` can't read it: print `cannot be read`;
        - bytes remain after `LC_ALL=C tr -d '!-~ \t\r\n'`: print `not ASCII text`;
        - otherwise strip the whitespace, then export the variable, or unset it if nothing is left, and `exec "$@"`.
      - The script works under `env -i` with no PATH because dash falls back to its built-in path.
      - `_claude_argv` puts the login shell in front of `claude` for the first call and for a resumed one.
      - `LOGIN_VARIABLE` is always dropped from the request's environment.
      - `_check_login` raises `AgentRuntimeError` after the `sudo` check when the call printed no reply and a `factory-login:` line is on stderr.
      - `version()` is unchanged.
    - `src/factory/entry/wiring.py`: passes `login_file=settings.claude_login_file`.
    - `src/factory/application/preflight.py`: adds the login-file hint to the detail of a probe run that did not complete.

    Main decision: the agent's own shell reads the file, so the factory never holds the token and it stands in no process's arguments. Rejected: dropping the separate readability check and letting the ASCII byte count catch unreadable files. `tr` sees no bytes in a folder, so a folder would pass as empty text. A dangling symlink counts as a missing file (`test -e`).

    Refactor pass: I read `git diff main...HEAD` (outside `factory/` and `tests/`) and found nothing to rename, simplify or deduplicate, so there is no refactor commit. Noticed but not touched: that diff also shows `docs/runs/2026-10-12-overnight/night-log.md`, the human's file, which came in with the merge of main; I did not edit it.

    `make check`: check: green
    `make duplicates`: duplicates: 0 new, 39 known, 0 gone
