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

- `CostRecord` gains `login: Login | None = None`, as its last field, after `instance`. A `started` record with a `login` is refused with `a started record has no login`, like its other measures.

`factory.application.costs` (`application`):

- `CostRecorder.complete` copies `result.login` into the completed record (`None` stays `None`).

`factory.adapters.cost_records_jsonl` (`adapters`):

- The writer leaves `login` out of a line when it is `None`, as it does for `instance`, so a line written before the field existed is written back as read; when set, it is the line's last key. The reader reads a line with or without it.

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

Changed under the feature's decision 19, by the tester only, nothing else in that module: `tests/test_compose.py`, the test `test_the_three_volumes_are_mounted_and_declared`, whose expected list gains the bind above as its fifth entry (the test keeps its name). `tests/adapters/test_claude_runtime_login.py` and `tests/entry/test_wiring_login.py` stay as they are: their imports from `factory.adapters.claude_runtime` reach the re-exported names.

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
15. The JSON Lines writer writes `"login":"api_key"` as the line's last key and leaves the key out for `None`. The reader reads both lines back to equal records, and one with `"instance"` and `"login"` keeps them in that order (rows).
16. `build_boundaries` with `api_login_file` set to a file holding a key gives a runtime whose run hands it to the stand-in, and with it unset hands none (rows, `confine_executable=None`).
17. `agent_run_probe_item` with a completed probe result whose `login` is `api_key`, `subscription`, `none` or `None` passes with the four details above. A `died` probe result with `login` `api_key` fails with today's first part and the API hint, and one with `subscription` fails with today's detail (rows).
18. A preflight run whose machine items pass, one of them with the detail `the agent runs log in with the API key from /home/agent/.anthropic-api-key`, writes the log line `preflight: agent-run-probe: the agent runs log in with the API key from /home/agent/.anthropic-api-key` and no line for items with an empty detail. A second run on the same image's stamp writes none (rows).
19. The Dockerfile sets `FACTORY_API_LOGIN_FILE` once, to the value the compose bind's `target` names, after the `FACTORY_CLAUDE_LOGIN_FILE` instruction and before `USER factory`. The compose bind is the fifth volume entry, exactly as above, and its target lies in the agent's home, outside `/home/factory/.secrets` and outside the named volumes.
20. `make check` stays green.
21. docs: `docs/operator-guide.md`: the configuration table gets `FACTORY_API_LOGIN_FILE` (not required; the image sets it to `/home/agent/.anthropic-api-key`; blank counts as unset). A section *The agent's API key* says: the host file `image/secrets/anthropic-api-key`, or the one `FACTORY_API_KEY_FILE` names for an instance's compose calls, must exist, empty for no key, or Compose refuses to start (as for `claude-token`); an instance that is to stay on the subscription keeps an empty file while another instance on the same machine has a key in its own; a key in it wins over the token, which is not read then; it is read at every call; save it as plain ASCII; switching back means emptying the file and recreating the container; the cost record's `login` and the log line `preflight: agent-run-probe: ...` show the login in force. The `agent-run-probe` row gets the passed detail and the API hint, and *The agent runtime* gets the `--api-login` words. `docs/project-guide.md`: `factory.adapters.agent_launch` as the runtimes' shared module, the login shell's report line and `AgentRunResult.login`. `docs/decisions.md`: an entry *An agent run logs in with an API key when its file holds one*, dated with the story, with the reasons of the feature's decisions 1 to 3.

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
