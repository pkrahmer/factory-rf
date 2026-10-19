---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 248
comments_read: []
handed_over: null
claim:
  instance: self
  stage: review
  started_at: '2026-10-19T03:47:52.158635Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T03:29:12.890341Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T03:29:12.896925Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T03:29:32.769652Z'
  stage: intake
  run: 8b758a12977c4881aa29c6eb58f665e7
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T03:29:52.716385Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T03:35:33.914867Z'
  stage: tests
  run: 95cada9589c94b87841bee9f9018b545
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T03:35:54.189174Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T03:40:37.334360Z'
  stage: doing
  run: e85762e79ebd44d99777aa0b80aae03b
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T03:40:57.565858Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T03:42:26.125572Z'
  stage: review
  run: c4ddff7675b34486b84e063839ed3caa
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T03:42:46.663195Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-19T03:43:09.260855Z'
  stage: doing
  run: fb8f61893d9947efa2d3f0af11ef579e
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T03:43:29.068626Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-19T03:45:11.849601Z'
  stage: tests
  run: 7d8e592116184907b05661142bfa48ec
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-19T03:45:32.118987Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-10-19T03:47:32.009955Z'
  stage: doing
  run: f99f858e834e45a2a0019ad1eb1c1f3a
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-19T03:47:52.158635Z'
  stage: review
---

# The agent runs can log in with an API key

## Description

Today every agent run logs in with the subscription: the call's own shell reads the token file (`FACTORY_CLAUDE_LOGIN_FILE`) and hands its content to `claude` as `CLAUDE_CODE_OAUTH_TOKEN`. opencode cannot use the subscription, and an instance at the human's work runs on an API key; this repository's own build stays on the subscription. This story lets an agent run log in with an API key instead. A new setting, `FACTORY_API_LOGIN_FILE`, names a file the image mounts read-only at `/home/agent/.anthropic-api-key` from the host's `image/secrets/anthropic-api-key`, or from the host file that `FACTORY_API_KEY_FILE` names for the compose call, so that each instance on a machine can have its own (an empty file for the subscription, a key for opencode). When that file holds a key, the call's shell hands it to the run as `ANTHROPIC_API_KEY` and hands over no token. When the file is missing, empty or blank, everything stays as it is today. As with the token, the factory never reads the key: the run's own shell reads it at every call, so it reaches no argument, run file, result, journal, cost record or log, and not the factory's own environment. The shell reports on standard error which login it handed over; the runtime turns that report into the run's `login` (`api_key`, `subscription` or `none`). The cost record of each run keeps it, and the preflight's probe names the login in force in the factory log. The login shell moves into a new module, `factory.adapters.agent_launch`, so that the opencode runtime (S0004) reuses it. The rest of what the runtimes share moves there in S0002.

## Interface

`factory.domain.agent_runs` (`domain`):

```python
Login = Literal["api_key", "subscription", "none"]

class AgentRunResult(BaseModel):
    ...
    login: Login | None = None   # new, after permission_denials
```

- `login` says which login the run's calls were handed: `api_key` (the API login file's key), `subscription` (the token file's token) or `none` (neither file held one). It is `None` when the runtime has no login file at all. Unlike `decision` and `entry`, it may be set whatever the end reason. A resumed run's `login` is that of its last call.

`factory.domain.cost_records` (`domain`):

- `CostRecord` gains `login: Login | None = None`, as its last field, after `denied_paths` (the record's fields end `instance`, `denials`, `denied_paths`, `login`). A `started` record with a `login` is refused with `a started record has no login`, like its other measures.

`factory.application.costs` (`application`):

- `CostRecorder.complete` copies `result.login` into the completed record (`None` stays `None`).

`factory.adapters.cost_records_jsonl` (`adapters`):

- The writer leaves `login` out of a line when it is `None`, as it does for `instance`, `denials` and `denied_paths`, so a line written before the field existed is written back as read; when set, it is the line's last key, after `denied_paths`: `..., "instance", "denials", "denied_paths", "login"`. The reader reads a line with or without it.

`factory.domain.settings` (`domain`):

```python
API_LOGIN_FILE_VARIABLE = "FACTORY_API_LOGIN_FILE"

class InstanceSettings(BaseModel):
    ...
    api_login_file: Path | None = None   # new, after claude_login_file
```

- `read_settings` reads `api_login_file` as it reads `claude_login_file`: a path, or `None` when the variable is unset or blank.
- No Python name that contains `key`, `token`, `secret` or `password` is assigned a string literal (ruff's `S105` and `make secrets`; `CREDENTIAL_FILE_VARIABLE` is the precedent).

`factory.adapters.agent_launch` (`adapters`, new): what every agent runtime shares, the login first.

```python
SHELL_EXECUTABLE = "/bin/sh"                  # moved from claude_runtime
LOGIN_VARIABLE = "CLAUDE_CODE_OAUTH_TOKEN"     # moved from claude_runtime
API_LOGIN_VARIABLE = "ANTHROPIC_API_KEY"
LOGIN_PREFIX = "factory-login:"                # moved from claude_runtime
API_LOGIN_PREFIX = "factory-api-login:"
LOGIN_USED_PREFIX = "factory-login-used:"
API_LOGIN_OPTION = "--api-login"
LOGIN_SCRIPT = ...                             # moved from claude_runtime and extended

class LoginFiles(BaseModel):
    """The files an agent run's shell reads its login from; either may be unset."""
    subscription: Path | None = None
    api: Path | None = None

def login_argv(files: LoginFiles) -> list[str]: ...
def login_used(stderr: str) -> Login | None: ...
def login_refusal(stderr: str, files: LoginFiles) -> str | None: ...
def without_login(environment: Mapping[str, str]) -> dict[str, str]: ...
```

- `login_argv`: `[]` when neither file is set. With only `subscription`: `[SHELL_EXECUTABLE, "-c", LOGIN_SCRIPT, "factory-login", str(subscription)]`, the five words of today. With `api`: `[SHELL_EXECUTABLE, "-c", LOGIN_SCRIPT, "factory-login", "--api-login", str(api), str(subscription)]`, with `""` in place of the subscription file when it is unset. The runtime's own command follows these words.
- `LOGIN_SCRIPT`, run as the call's user, is the script of today with the following additions. It builds the variable names from the constants (an f-string, as today), so its source holds no `NAME="..."` pair of a secret's name.
  - With `--api-login <file>` and a file that holds a key (anything left once spaces, tabs, carriage returns and line feeds are removed): it exports `ANTHROPIC_API_KEY` with that text and unsets `CLAUDE_CODE_OAUTH_TOKEN`. It prints `factory-login-used: api_key` on standard error and `exec`s the command. It never reads the token file then.
  - With `--api-login <file>` and a file that exists but is not a readable regular file: it prints `factory-api-login: cannot be read` on standard error and exits 1. With bytes other than printable ASCII, space, tab, carriage return and line feed: `factory-api-login: not ASCII text`, exit 1. Either way the command is not started.
  - Otherwise (no `--api-login`, or the file is missing, empty or blank): it unsets `ANTHROPIC_API_KEY` and goes on with the token file exactly as today, refusals included. It prints `factory-login-used: subscription` when it exports a token, `factory-login-used: none` when it exports none. An empty token-file argument counts as a missing file.
- `login_used`: the word after `factory-login-used:` on the first line that starts with it, stripped. `None` when no line starts with it or the word is not one of the three logins.
- `login_refusal`: for the first line starting with `factory-api-login:`, `f"cannot read the agent's API login file {files.api}: {reason}"`; else for the first line starting with `factory-login:`, `f"cannot read the agent's login file {files.subscription}: {reason}"` (today's text); else `None`. `reason` is the rest of the line, stripped. `factory-login-used:` lines are no refusal.
- `without_login`: a copy of `environment` without `CLAUDE_CODE_OAUTH_TOKEN` and `ANTHROPIC_API_KEY`.
- `factory.adapters.agent_launch` does not import `factory.adapters.process` (`tests/test_wrapper_search.py` stays as it is): it builds words and texts, and each runtime starts its own processes.

`factory.adapters.claude_runtime` (`adapters`):

```python
class ClaudeCodeRuntime(AgentRuntime):
    def __init__(self, executable, state_directory, kill_points=None, *, version_time_limit=VERSION_TIME_LIMIT,
                 sudo_executable=SUDO_EXECUTABLE, login_file=None, confine_executable=None,
                 temporary_root=None, api_login_file: Path | None = None) -> None: ...
```

- The call's words before `claude` are `login_argv(LoginFiles(subscription=login_file, api=api_login_file))`. The call's environment drops both login names from the request's (`without_login`).
- The result's `login` is `login_used(stderr)` of the run's last call. A call without a usable reply whose standard error holds a refusal of `login_refusal` raises `AgentRuntimeError` with that text, as today for the token file.
- The version call gets no login words, as today.
- The module imports the moved names (`LOGIN_SCRIPT`, `LOGIN_VARIABLE`, `LOGIN_PREFIX`, `SHELL_EXECUTABLE`) from `factory.adapters.agent_launch` and lists them in its `__all__`, beside its own public names, as `factory.domain.settings` and `factory.entry.wiring` re-export; so every earlier test that imports them from `factory.adapters.claude_runtime` passes `mypy --strict` unchanged. Never `import X as X`: ruff's `PLC0414` refuses it.
- The temporary folder's removal keeps reading `SHELL_EXECUTABLE` from this module's namespace, so a test that sets `claude_runtime.SHELL_EXECUTABLE` still reaches the removal.

`factory.domain.contract` (`domain`), `src/factory/contract/*.schema.json`:

- `CostRecord` gains an optional field, so the records contract's minor version rises: `RECORDS_CONTRACT` goes from `"1.0"` to `"1.1"`, and the committed schemas are regenerated in this story with `uv run python -m factory.entry.contract` (never by hand): `cost-record.schema.json` gains the property `login` (a string of the three logins or null, not required), and every schema file carries `"x-records-contract": "1.1"`. `CostRecord`'s docstring says what `login` is, so the schema's description changes with it.

`factory.entry.wiring` (`entry`):

- `build_boundaries` passes `settings.api_login_file` to `ClaudeCodeRuntime` as `api_login_file`.

`factory.application.preflight` (`application`):

- `agent_run_probe_item`: a probe that completes passes with a detail that names the login of its result:
  - `api_key`: `f"the agent runs log in with the API key from {settings.api_login_file}"`;
  - `subscription`: `f"the agent runs log in with the subscription token from {settings.claude_login_file}"`;
  - `none`: `"the agent runs get no login from a file; the runtime uses the login kept in its home"`;
  - `None`: `""`, as today.
- A probe that does not complete and whose result's `login` is `api_key` ends its detail with `f"; the agent's API key is read from {settings.api_login_file}: check that it is valid and that its account has credit"` instead of today's token hint. Every other failed detail stays as today.
- `Preflight` writes one factory-log line `f"preflight: {item.name}: {item.detail}"` for every passed machine item with a non-empty detail, each time the machine's items run. It writes none when the stamp skips them.

`image/Dockerfile`, `image/compose.yml` (`image`, the coder's):

- The Dockerfile sets `ENV FACTORY_API_LOGIN_FILE=/home/agent/.anthropic-api-key` once, as its own instruction right after `ENV FACTORY_CLAUDE_LOGIN_FILE=/home/agent/.claude-token`, with a comment line above it: the agent's API key, which Compose mounts; each agent run's shell reads it, and an empty file is no key.
- The compose service's volumes gain, as the fifth entry, between the `claude-token` bind and the `hosting-token` bind, with a comment that an empty file means no API key:

  ```yaml
      - type: bind
        source: ${FACTORY_API_KEY_FILE:-./secrets/anthropic-api-key}
        target: /home/agent/.anthropic-api-key
        read_only: true
        bind:
          create_host_path: false
  ```

Tests (the tester writes them): `tests/adapters/test_agent_launch_login.py` (the script through the real `/bin/sh`, with a recording command written by `write_script` of `tests/confine_support.py`), `tests/adapters/test_claude_runtime_api_login.py` (the runtime with `tests/adapters/claude_stand_in.py`; it imports `REPLY`, `BUDGET_STOP`, `_request`, `_write_sudo` and `_sudo_calls` from the earlier modules and copies none of them; the `recorder` fixture and its `Recorder`, which `tests/adapters/test_claude_runtime_login.py` and `tests/adapters/test_claude_runtime_sudo_time_limit.py` each hold, move to `tests/conftest.py` under the standing leave of `CLAUDE.md` (*Tests*), because an imported fixture is ruff's `F811`), `tests/domain/test_login_records.py`, `tests/domain/test_settings_api_login.py`, `tests/adapters/test_cost_records_jsonl_login.py` (it imports the lines and records of `tests/adapters/test_cost_records_jsonl.py`), `tests/application/test_costs_login.py`, `tests/application/test_agent_run_probe_api_login.py`, `tests/entry/test_wiring_api_login.py`, `tests/test_api_login_mount.py` (it reads the Dockerfile through `tests/dockerfile_support.py`).

Changed under the feature's decision 19, by the tester only, nothing else in those modules: `tests/test_compose.py`, the test `test_the_three_volumes_are_mounted_and_declared`, whose expected list gains the bind above as its fifth entry (the test keeps its name); `tests/domain/test_contract.py`, the test `test_a_schema_starts_with_the_dialect_and_the_contract_version`, whose expected version is `"1.1"` (the test keeps its name). `tests/adapters/test_claude_runtime_login.py` and `tests/entry/test_wiring_login.py` stay as they are: their imports from `factory.adapters.claude_runtime` reach the re-exported names.

Test values: a stand-in key is held in a name without `key`, `token`, `secret` or `password` (`API_LOGIN = "stand-in-api-login"`, as `LOGIN = "stand-in-login"` today), and an environment entry is written with the name's constant (`{API_LOGIN_VARIABLE: API_LOGIN}`), never as a quoted `"ANTHROPIC_API_KEY": "..."` pair: detect-secrets flags both, and `make secrets` runs in the coder's `make check`.

## Acceptance criteria

1. `read_settings` gives `api_login_file` `Path("/home/agent/.anthropic-api-key")` for that value of `FACTORY_API_LOGIN_FILE`, and `None` when the variable is unset, empty or `"   "` (rows of one parametrized test).
2. Through `login_argv(LoginFiles(subscription=..., api=...))` and the real shell, a command started after the words sees `ANTHROPIC_API_KEY` equal to the API file's text without its whitespace, and no `CLAUDE_CODE_OAUTH_TOKEN`. Standard error holds `factory-login-used: api_key`. Rows: a key ending in a line feed; a key ending in carriage return and line feed; a token file that is a folder, which is never read (no refusal).
3. With an API file that is missing, empty or `"  \n"`, the command sees the token file's token as `CLAUDE_CODE_OAUTH_TOKEN` and `factory-login-used: subscription` is printed; with no token either, it sees neither name and `factory-login-used: none` is printed; with a token file that is a folder, `factory-login: cannot be read` is printed, the shell exits 1 and the command is not started. In every such row an `ANTHROPIC_API_KEY` in the shell's own environment does not reach the command (rows of one parametrized test, including the empty token-file argument).
4. An API file that is a folder prints `factory-api-login: cannot be read`, and one saved as UTF-16 prints `factory-api-login: not ASCII text`. Either exits 1 and the command is not started (rows).
5. `login_argv` gives `[]`, today's five words, the seven words with `""` for an unset subscription file, and the seven words with both paths (rows).
6. `login_used` gives `api_key`, `subscription` and `none` for their lines, the first such line when two are present, and `None` for no line and for `factory-login-used: other` (rows).
7. `login_refusal` gives the API text for a `factory-api-login: not ASCII text` line, today's text for a `factory-login: cannot be read` line, the API text when both lines are present in either order, and `None` for a stderr with only `factory-login-used: none` (rows).
8. `ClaudeCodeRuntime` built with a token file and an API file: when the API file holds a key, the stand-in `claude` sees `ANTHROPIC_API_KEY` and no token, and the result's `login` is `api_key`; when the API file is then emptied, the next run sees the token and its `login` is `subscription`. Built without `api_login_file`, a token file gives `subscription`, and built with no login file at all the `login` is `None` (rows).
9. A request whose environment carries `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` reaches the stand-in without it unless the files supply it (rows: each name, with and without an API file holding a key).
10. With an API file holding a key, the key stands in no argument the stand-in or the stand-in `sudo` sees, in no run file, in no `ProcessRequest` (the `recorder` fixture), and not in the result's JSON, with and without an `os_user` (rows).
11. An API file that is a folder, or UTF-16, stops the run with `AgentRuntimeError` `agent runtime failed: cannot read the agent's API login file <path>: cannot be read` or `...: not ASCII text`. The stand-in is never called and the state directory is left empty (rows).
12. A run stopped by its budget whose API file is emptied by the first call (a stand-in step that writes it) is resumed with the token. The resumed call sees `CLAUDE_CODE_OAUTH_TOKEN`, and the result's `login` is `subscription`.
13. The version call of a runtime with both files gets no login words and neither name.
14. A completed `CostRecord` keeps `login` `api_key` or `None`, and a `started` one with a `login` is refused with `a started record has no login` (rows). `CostRecorder.complete` with a result whose `login` is `api_key` writes it into the sidecar's completed record, and with `None` leaves it out.
15. The JSON Lines writer writes `"login":"api_key"` as the line's last key and leaves the key out for `None`. The reader reads both lines back to equal records, and a line with `"instance"`, `"denials"`, `"denied_paths"` and `"login"` keeps them in that order, `"login"` last (rows).
16. `build_boundaries` with `api_login_file` set to a file holding a key gives a runtime whose run hands it to the stand-in, and with it unset hands none (rows, `confine_executable=None`).
17. `agent_run_probe_item` with a completed probe result whose `login` is `api_key`, `subscription`, `none` or `None` passes with the four details above. A `died` probe result with `login` `api_key` fails with today's first part and the API hint, and one with `subscription` fails with today's detail (rows).
18. A preflight run whose machine items pass, one of them with the detail `the agent runs log in with the API key from /home/agent/.anthropic-api-key`, writes the log line `preflight: agent-run-probe: the agent runs log in with the API key from /home/agent/.anthropic-api-key` and no line for items with an empty detail. A second run on the same image's stamp writes none (rows).
19. The Dockerfile sets `FACTORY_API_LOGIN_FILE` once, to the value the compose bind's `target` names, after the `FACTORY_CLAUDE_LOGIN_FILE` instruction and before `USER factory`. The compose bind is the fifth volume entry, exactly as above, and its target lies in the agent's home, outside `/home/factory/.secrets` and outside the named volumes.
20. The records contract's version is `1.1` and the committed schemas are the generated ones: `cost-record.schema.json` lists `login` among its properties and not among its required ones, with the three logins and null as its values; the other four files differ from the earlier ones only in `x-records-contract`, which reads `1.1` in all five; `uv run python -m factory.entry.contract` leaves the committed files unchanged (the existing comparison test passes).
21. `make check` stays green.
22. docs: `docs/operator-guide.md`: the configuration table gets `FACTORY_API_LOGIN_FILE` (not required; the image sets it to `/home/agent/.anthropic-api-key`; blank counts as unset). A section *The agent's API key* says: the host file `image/secrets/anthropic-api-key`, or the one `FACTORY_API_KEY_FILE` names for an instance's compose calls, must exist, empty for no key, or Compose refuses to start (as for `claude-token`); an instance that is to stay on the subscription keeps an empty file while another instance on the same machine has a key in its own; a key in it wins over the token, which is not read then; it is read at every call; save it as plain ASCII; switching back means emptying the file and recreating the container; the cost record's `login` and the log line `preflight: agent-run-probe: ...` show the login in force. The `agent-run-probe` row gets the passed detail and the API hint, and *The agent runtime* gets the `--api-login` words. `docs/project-guide.md`: `factory.adapters.agent_launch` as the runtimes' shared module, the login shell's report line and `AgentRunResult.login`. `docs/decisions.md`: an entry *An agent run logs in with an API key when its file holds one*, dated with the story, with the reasons of the feature's decisions 1 to 3. `docs/operator-guide.md` and `docs/project-guide.md`: the records contract's version now reads `1.1`, and `login` is among the cost record's fields.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir "$d/work"
cat > "$d/claude" <<'EOF'
#!/bin/sh
printf '%s %s\n' "${ANTHROPIC_API_KEY:-unset}" "${CLAUDE_CODE_OAUTH_TOKEN:-unset}" >> "$(dirname "$0")/seen"
printf '%s\n' '{"type":"result","subtype":"success","is_error":false,"num_turns":1,"total_cost_usd":0.01,"usage":{"input_tokens":1,"output_tokens":1},"permission_denials":[],"structured_output":{"decision":"question","entry":"Done."}}'
EOF
chmod +x "$d/claude"
printf 'stand-in-subscription\n' > "$d/subscription"
printf 'stand-in-api-login\n' > "$d/api-login"
uv run -q python - "$d" <<'EOF'
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest

d = Path(sys.argv[1])
agent = AgentDefinition(name="coder", model="sonnet", tools=["Read"], budget_usd=Decimal("1"), instructions="Smoke.")
request = AgentRunRequest(agent=agent, prompt="Smoke.", allowed_decisions=["question"], time_limit=timedelta(seconds=60), working_directory=d / "work", environment={"PATH": "/usr/bin:/bin"})
runtime = ClaudeCodeRuntime(str(d / "claude"), d / "state", login_file=d / "subscription", api_login_file=d / "api-login")
print(runtime.run(request).login)
(d / "api-login").write_text("")
print(runtime.run(request).login)
EOF
cat "$d/seen"
```
Expect: four lines, `api_key`, `subscription`, `stand-in-api-login unset`, `unset stand-in-subscription`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: concrete modules and signatures throughout (`agent_launch` constants, `LoginFiles`, the four functions, the runtime constructor, `Login`, `CostRecord.login`, settings, wiring, preflight details, Dockerfile and compose lines). Every behaviour in it (the script's branches, argv shapes, report and refusal texts, the key order of the JSON line, the contract version, the preflight log line) has a criterion.
   Criteria: each is testable by one parametrized test with named rows. Each rule has both sides: key and no key (2, 3), unreadable and non-ASCII API file (4), a started record with a login refused (14), `None` left out of the line (15), a failed probe with `api_key` and with `subscription` (17), and a second preflight run that writes no log line (18). The rows for ordering and "first line" are in 6, 7 and 15.
   Smoke test: runnable as written (stand-in `claude`, real runtime, no sudo or confinement). The `Expect:` line gives four checkable lines in a fixed order.
   Architecture: the login shell and its helpers are in an adapters module that builds words and texts and does not import the process module. Wiring stays in `entry`, the preflight detail is in `application`, and the domain holds `Login` and the DTO fields. The records contract's version rise is covered by criterion 20.
   Scope: inside F0020's scope list for S0001. Nothing in Out of scope is touched. The edits to other stories' tests are the two named under decision 19.
4. factory: started tests as self.
5. tester: Wrote tests for criteria 1 to 20. One `make test` run shows them red for the right reasons. `make lint` is green.

   Criterion → test:
   - criterion 1: tests/domain/test_settings_api_login.py::test_the_api_login_file_setting_is_a_path_or_none_when_blank
   - criterion 2: tests/adapters/test_agent_launch_login.py::test_an_api_file_holding_a_key_hands_over_the_key_and_no_token
   - criterion 3: tests/adapters/test_agent_launch_login.py::test_without_a_key_the_shell_goes_on_with_the_token_file
   - criterion 4: tests/adapters/test_agent_launch_login.py::test_an_api_file_that_cannot_be_used_stops_the_shell
   - criterion 5: tests/adapters/test_agent_launch_login.py::test_the_login_words_name_the_files_that_are_set
   - criterion 6: tests/adapters/test_agent_launch_login.py::test_the_login_used_is_read_from_the_shell_s_report
   - criterion 7: tests/adapters/test_agent_launch_login.py::test_the_refusal_names_the_file_the_shell_could_not_use
   - criterion 8: tests/adapters/test_claude_runtime_api_login.py::test_the_api_file_s_key_wins_and_an_emptied_file_falls_back_to_the_token and ::test_without_an_api_file_the_login_is_the_token_s_or_none
   - criterion 9: tests/adapters/test_claude_runtime_api_login.py::test_the_request_s_login_entries_are_dropped_for_the_files
   - criterion 10: tests/adapters/test_claude_runtime_api_login.py::test_the_key_stands_in_no_argument_no_run_file_and_no_result
   - criterion 11: tests/adapters/test_claude_runtime_api_login.py::test_an_api_file_that_cannot_be_used_stops_the_run_naming_the_file
   - criterion 12: tests/adapters/test_claude_runtime_api_login.py::test_a_resumed_call_whose_api_file_was_emptied_gets_the_token
   - criterion 13: tests/adapters/test_claude_runtime_api_login.py::test_the_version_call_gets_no_login_words_and_neither_name
   - criterion 14: tests/domain/test_login_records.py::test_only_a_completed_record_keeps_a_login and tests/application/test_costs_login.py::test_the_completed_record_keeps_the_result_s_login
   - criterion 15: tests/adapters/test_cost_records_jsonl_login.py::test_the_writer_writes_the_login_last_only_when_set
   - criterion 16: tests/entry/test_wiring_api_login.py::test_the_built_runtime_hands_the_api_login_file_s_key_to_claude
   - criterion 17: tests/application/test_agent_run_probe_api_login.py::test_the_probe_detail_names_the_login_its_run_was_handed
   - criterion 18: tests/application/test_preflight_login_line.py::test_a_passed_machine_item_s_detail_is_logged_once_per_image
   - criterion 19: tests/test_api_login_mount.py::test_the_api_login_file_is_set_once_and_bind_mounted_read_only_in_the_agent_home, plus tests/test_compose.py::test_the_three_volumes_are_mounted_and_declared (changed under decision 19)
   - criterion 20: tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version (expected version now "1.1", under decision 19) and tests/domain/test_contract_login.py::test_the_committed_cost_record_schema_lists_the_optional_login_at_version_1_1. The existing comparison test covers the regenerated files.
   - criteria 21 and 22 (`make check`, docs) are not tests.

   Files created:
   - tests/adapters/test_agent_launch_login.py
   - tests/adapters/test_claude_runtime_api_login.py
   - tests/adapters/test_cost_records_jsonl_login.py
   - tests/application/test_agent_run_probe_api_login.py
   - tests/application/test_costs_login.py
   - tests/application/test_preflight_login_line.py
   - tests/domain/test_contract_login.py
   - tests/domain/test_login_records.py
   - tests/domain/test_settings_api_login.py
   - tests/entry/test_wiring_api_login.py
   - tests/test_api_login_mount.py
   - tests/run_process_recorder.py

   Two files not on the Interface's list:
   - The preflight log line (criterion 18) has its own module, tests/application/test_preflight_login_line.py. The probe test module only tests `agent_run_probe_item`, and this criterion needs a `Preflight` run. It reuses the constants and `RecordingWhich` of tests/application/test_preflight_run.py and injects the item through `MachineChecks`' `extra`.
   - The record contract has its own module, tests/domain/test_contract_login.py.

   Earlier test files changed:
   - Under decision 19, as the Interface names them: tests/test_compose.py and tests/domain/test_contract.py.
   - Under the standing leave to move a shared test helper (CLAUDE.md, *Tests*): tests/adapters/test_claude_runtime_login.py, tests/adapters/test_claude_runtime_sudo_time_limit.py and tests/conftest.py. Their two `Recorder` classes were not the same. The login one passed each request on to the real `run_process`; the sudo one answered with given `results`. They are now one `Recorder` in tests/run_process_recorder.py: it answers with the next given result and runs the request itself once none is left, so both earlier modules check exactly what they did before. The `recorder` fixture moved to tests/conftest.py. Those earlier tests stay green.

   Modules the test run could not import:
   - `factory.adapters.agent_launch` (new module)
   - the name `API_LOGIN_FILE_VARIABLE` in `factory.domain.settings`
   - the name `Login` in `factory.domain.agent_runs`

   The other new tests fail on wrong results: no `login` field or `api_login_file`, contract still at 1.0, no preflight log line, compose bind missing.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/test_api_login_mount.py - ImportError while importing test module...
6. factory: started doing as self.
7. coder: Implemented the API-key login as the Interface describes. `make check` is green: lint, types, layers, sast, secrets, licenses and test, with 99.09 % coverage.

   Built:
   - `src/factory/adapters/agent_launch.py` (new). It holds the moved `SHELL_EXECUTABLE`, `LOGIN_VARIABLE`, `LOGIN_PREFIX` and `LOGIN_SCRIPT`, plus `API_LOGIN_VARIABLE`, `API_LOGIN_PREFIX`, `LOGIN_USED_PREFIX`, `API_LOGIN_OPTION`, `LoginFiles`, `login_argv`, `login_used`, `login_refusal` and `without_login`. It also holds `line_starting`, which moved here from `claude_runtime` so the two modules do not each keep a copy. It does not import `factory.adapters.process`.
   - The extended `LOGIN_SCRIPT` uses two shell functions, `check_text` (the "cannot be read" and "not ASCII text" refusals, parameterised by prefix) and `stripped`. The API file and the token file share them instead of repeating the checks. When the API file holds a key, the script exports it, unsets the token, reports `api_key` and execs without reading the token file. Otherwise it unsets `ANTHROPIC_API_KEY` and goes on with today's token logic, reporting `subscription` or `none`. An empty token-file argument counts as missing.
   - `src/factory/adapters/claude_runtime.py`:
     - New `api_login_file` keyword. The runtime keeps a `LoginFiles` instead of `_login_file`.
     - The call's words come from `login_argv` and the environment from `without_login`.
     - `_result` sets `login` from `login_used(stderr)` on every path, so a resumed run carries the login of its last call.
     - `_check_login` raises `login_refusal`'s text when there is no usable reply.
     - The moved names are re-exported through `__all__`. `SHELL_EXECUTABLE` is still read from this module's namespace for the temporary folder's removal.
   - `src/factory/domain/agent_runs.py`: `Login` and `AgentRunResult.login`.
   - `src/factory/domain/cost_records.py`: `CostRecord.login`, described in the docstring and refused on a started record.
   - `src/factory/application/costs.py`: `complete` copies the login.
   - `src/factory/adapters/cost_records_jsonl.py`: `login` is left out of a line when `None`.
   - `src/factory/domain/settings.py`: `API_LOGIN_FILE_VARIABLE` and `api_login_file`.
   - `src/factory/entry/wiring.py`: passes `api_login_file` to the runtime.
   - `src/factory/application/preflight.py`:
     - `_login_hint` and `_login_detail` give the failed and passed probe details.
     - `Preflight._log_passed_details` writes `preflight: <name>: <detail>` for each passed item with a detail, only when the machine's items actually run (not when the stamp skips them).
   - `src/factory/domain/preflight.py`: the `PreflightItem` docstring now allows a detail on a passed item.
   - `src/factory/domain/contract.py`: `RECORDS_CONTRACT` is "1.1". All five `src/factory/contract/*.schema.json` files were regenerated with `uv run python -m factory.entry.contract`.
   - `image/Dockerfile` and `image/compose.yml`: the `ENV` line and the fifth bind, as specified.

   Main choice: the runtime holds one `LoginFiles` and hands it to the shared functions, so `ClaudeCodeRuntime` has no login logic of its own. That is the shape an opencode runtime can reuse. I rejected keeping a `_login_file`/`_api_login_file` pair with per-runtime branching. I also rejected writing the API branch as a second copy of the token file's readable and ASCII checks; the shared shell function replaces that.

   Noticed, not touched:
   - I could not run the story's smoke test: the shell refused the command (a permission denial, not a test failure). It is still untested end to end; the smoke-test stage runs it.
   - `claude_runtime.__all__` lists only the re-exported names plus `ClaudeCodeRuntime` and `resume_budget`, following the partial `__all__` in `factory.domain.settings`. Its other public constants (e.g. `SUDO_EXECUTABLE`) are still importable as module-level definitions.
   - The host file `image/secrets/anthropic-api-key` is the operator's to create; nothing in the repository creates it.
   - Docs are left to the documenter.
   - The work item's `.costs.jsonl` shows as modified in the working tree; that is the factory's own record.

   Description unchanged: no journal entry changed the task.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 36 known, 3 gone
8. factory: started review as self.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` against the work item. The acceptance criteria (group 1), architecture (group 2) and security (group 3) all hold.
   - Criteria 1 to 20 each have a test that checks what its criterion says. The coder's `make check` was green (entry 7).
   - `agent_launch` imports only `factory.domain`, not `process`.
   - No suppression markers were added.
   - `LOGIN_SCRIPT` is built only from constants.
   - A resumed run takes `login` from its second call through `model_copy`.
   - The five schema files differ only in what the story names.

   Group 4 (quality) fails on copies in the new test files. This is round 0, so they are findings:

   1. `tests/adapters/test_claude_runtime_api_login.py:152` `_utf_16` is a second copy of `_utf_16` in `tests/adapters/test_agent_launch_login.py:54`: the same body writing `API_LOGIN.encode("utf-16")`. The same module also defines its own `API_LOGIN` (line 17) and `SUBSCRIPTION` (line 18) instead of reusing those of `test_agent_launch_login.py:25-26`. `tests/entry/test_wiring_api_login.py:16` defines a third `API_LOGIN`. Fix: the tester imports `_utf_16`, `API_LOGIN` and `SUBSCRIPTION` from `adapters.test_agent_launch_login` in both modules, or moves them to one shared module under `tests/`. The earlier modules already share `REPLY` and `_request` this way. No test changes what it checks, and nothing under `src/` changes.

   Earlier tests (changed files that `main` already holds):
   - `tests/adapters/test_claude_runtime_login.py`: standing leave to move a shared test helper, also named in the story's Interface. Its `Recorder` and `recorder` fixture moved to `tests/run_process_recorder.py` and `tests/conftest.py`; every test keeps its name and what it checks.
   - `tests/adapters/test_claude_runtime_sudo_time_limit.py`: same leave, same move. The merged `Recorder` still answers with the given results first.
   - `tests/conftest.py`: same leave. It only gains the moved `recorder` fixture.
   - `tests/domain/test_contract.py`: the human's leave. The story names `test_a_schema_starts_with_the_dialect_and_the_contract_version` under the feature's decision 19 (expected version `"1.1"`), and the test keeps its name.
   - `tests/test_compose.py`: the human's leave. The story names `test_the_three_volumes_are_mounted_and_declared` under decision 19; the fifth bind was added and the test keeps its name.
10. factory: started doing as self.
11. coder: Round 1. The reviewer's only finding (entry 9) is about copied helpers in this story's test modules. It needs no change under `src/`, so I changed no code. The tester makes the change, because I never edit tests.

    The change: one copy each of `_utf_16`, `API_LOGIN` and `SUBSCRIPTION`. Today they are defined again in:
    - `tests/adapters/test_claude_runtime_api_login.py`: `API_LOGIN` and `SUBSCRIPTION` at lines 17-18, `_utf_16` at line 152.
    - `tests/entry/test_wiring_api_login.py`: `API_LOGIN` at line 16.

    The originals are in `tests/adapters/test_agent_launch_login.py` (lines 25, 26 and 54). The two modules above should import them from there, the way they already import `REPLY` and `_request` from other test modules. The other option is to move all three names to one shared module at the `tests/` root and import them from there in all three modules. Every test keeps its name and checks the same thing.

    Rejected: changing anything under `src/` to answer this finding. It is purely a test-code duplicate.

    Noticed, not touched: none beyond entry 7's list.

    The description is unchanged; no journal entry changed the task.
12. factory: started tests as self.
13. tester: Round 1. I removed the copied test helpers from the reviewer's finding (entry 9), as the coder's entry 11 describes. I took the first option the coder named: both modules now import the names from `tests/adapters/test_agent_launch_login.py`, the same way they already import `REPLY` and `_request`. I did not move the names to a new shared module.

    Changed (both are this story's test files):
    - `tests/adapters/test_claude_runtime_api_login.py`: deleted its own `API_LOGIN`, `SUBSCRIPTION` and `_utf_16`. It now imports all three from `adapters.test_agent_launch_login`.
    - `tests/entry/test_wiring_api_login.py`: deleted its own `API_LOGIN` and imports it from `adapters.test_agent_launch_login`.

    The values were identical in every copy, so every test keeps its name and checks the same thing. I created no new files and edited no earlier story's test file.

    The criterion-to-test mapping has not changed since entry 5.

    `make lint` is green. `make test` is green: 99.09 % coverage. Every module imports.

    `lint`: lint: green (0.0 s)
    `test`: test: green (38.4 s)
14. factory: started doing as self.
15. coder: Round 1, after the tester's change. The reviewer's only finding (entry 9) was about copied test helpers. The tester fixed it in entry 13: `tests/adapters/test_claude_runtime_api_login.py` and `tests/entry/test_wiring_api_login.py` now import `API_LOGIN`, `SUBSCRIPTION` and `_utf_16` from `tests/adapters/test_agent_launch_login.py`. Nothing under `src/`, `image/` or the schemas needed to change, so I left the code from entry 7 as it was and made no edits this run.

    Built (unchanged since entry 7):
    - `src/factory/adapters/agent_launch.py`
    - `src/factory/adapters/claude_runtime.py`
    - `src/factory/domain/agent_runs.py`, `cost_records.py`, `settings.py`, `contract.py`, `preflight.py`
    - `src/factory/application/costs.py`, `preflight.py`
    - `src/factory/adapters/cost_records_jsonl.py`
    - `src/factory/entry/wiring.py`
    - `src/factory/contract/*.schema.json`, regenerated
    - `image/Dockerfile`, `image/compose.yml`

    Main choice: the same as entry 7. The runtime holds one `LoginFiles` and leaves all the login work to the shared functions in `agent_launch`. I rejected a per-runtime `_login_file`/`_api_login_file` pair.

    Refactor: my working tree has no changes, so there is nothing to refactor this round.

    Checked: `make check` is green at 99.09 % coverage. The only file shown as modified is the work item's `.costs.jsonl`, which is the factory's record.

    Noticed, not touched: the points in entry 7 still stand. The smoke test has not been run end to end. The host file `image/secrets/anthropic-api-key` is the operator's to create. The docs are the documenter's.

    The description is unchanged: no journal entry changed the meaning of the task.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 36 known, 3 gone
16. factory: started review as self.
