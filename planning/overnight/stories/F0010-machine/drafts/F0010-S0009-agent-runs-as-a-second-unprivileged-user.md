# Agent runs as a second unprivileged user

## Assignment (as of log entry 1)

Run every agent as the second operating-system user, `agent`, which the image created in the pinned-image story and which owns nothing the factory keeps secret. The factory's own user may become `agent` for one command and for nothing else, through one `sudo` rule; the runtime starts the agent through `sudo -n -u agent -- env -i` with exactly the environment of the request, so neither the factory's environment nor its privileges come along. The agent shares the checkout with the factory through the group `factory-work`, so files either one creates are writable by both. This covers WE3.1 and, with the previous story, the files side of WE3.3 and WE3.4, and implements R33. The second user, the `sudo` rule and the group exist only in a real image, so what v1's container can test is the runtime's call, the settings, the composition of the request and a static test of the Dockerfile, the sudoers file and the compose file; a real agent run as `agent` that tries to read the token file and the token, to push with `git -C . push origin main` and to call the hosting service's API is the morning observation. Claude's login for the model is the operator's one-time step as the user `agent` (`docker compose run --rm -it --user agent --entrypoint claude factory`), kept in the volume `claude-home`. The agent can write the agent home and `settings.json` there, which is left for v2 (the handover's section 8, L69).

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
class ClaudeCodeRuntime:
    def __init__(
        self,
        executable: str,
        state_directory: Path,
        kill_points: KillPoints | None = None,
        *,
        sudo_executable: str = "/usr/bin/sudo",
    ) -> None: ...
```

`src/factory/application/preflight.py` (extends the module)

```python
def extra_items(
    settings: InstanceSettings, which: Callable[[str], str | None], uid: int
) -> list[Callable[[], PreflightItem]]: ...
```

`image/sudoers-factory-agent`

```text
factory ALL=(agent) NOPASSWD: ALL
```

`image/Dockerfile` gains these instructions before `USER factory`:

```dockerfile
COPY image/sudoers-factory-agent /etc/sudoers.d/factory-agent
RUN chmod 0440 /etc/sudoers.d/factory-agent && visudo -cf /etc/sudoers.d/factory-agent
ENV FACTORY_AGENT_USER=agent
```

`image/entrypoint.sh` gains, directly after `set -eu`, the line `umask 002`, and among its `git config --global` lines `git config --global core.sharedRepository group`.

Rules:

- `read_settings` sets `agent_user` from `FACTORY_AGENT_USER`; a value that does not match `Name` raises `SettingsInvalid` with `variable == "FACTORY_AGENT_USER"`.
- With `request.os_user` set to `U`, `ClaudeCodeRuntime.run` starts, in `request.working_directory`, the process `[sudo_executable, "-n", "-u", U, "--", "env", "-i", <NAME=value for each entry of request.environment>, <executable>, <the arguments it builds without a user>]`. The subprocess is started with an empty environment of its own. With `request.os_user` `None` it starts `[executable, <arguments>]` directly with `request.environment` as its environment, as before.
- When the process ends without a result and its standard error holds a line that starts `sudo:`, the runtime raises `AgentRuntimeError` whose detail contains that line, not a `died` result: a refused `sudo` is a misconfiguration, not a stall.
- The composer of agent run requests, `factory.application.task`, sets `os_user` to `boundaries.settings.agent_user`, and when that is not `None` also sets `HOME` in the environment to the parent of `boundaries.settings.agent_home`. When the boundaries have no settings, or the settings no `agent_user`, `os_user` is `None` and the composer adds no `HOME`.
- `extra_items(settings, which, uid)` returns `[lambda: token_file_item(settings.token_file, uid=uid)]`, and, when `settings.agent_user` is not `None`, a second callable that returns `tool_item("sudo", which)`. `run_instance` passes its result to `MachineChecks`.
- The sudoers file holds exactly one rule, the one shown, and no line gives `agent` anything.

Tests: `tests/domain/test_settings.py`, `tests/adapters/test_claude_runtime_os_user.py` (the stand-in executable of F0001-S0008 for `claude`, and a second stand-in script for `sudo` that records its arguments and then runs the rest of its command line after `--`), `tests/application/test_task_os_user.py`, `tests/application/test_preflight_extra_items.py`, `tests/test_image_users.py` (the Dockerfile, the sudoers file and the compose file), `tests/test_entrypoint.py` (the stub `python` of the entrypoint story also writes `umask` to a file).

## Acceptance criteria

1. `read_settings` sets `agent_user` to `agent` for `FACTORY_AGENT_USER=agent`, and to `None` when the variable is missing or blank.
2. `FACTORY_AGENT_USER` set to `Agent` or to `1x` raises `SettingsInvalid` with `variable == "FACTORY_AGENT_USER"`.
3. With `os_user=None` the runtime starts the stand-in for `claude` directly, with exactly `request.environment` as its environment, and never starts the `sudo` stand-in.
4. With `os_user="agent"` the `sudo` stand-in receives the arguments `-n`, `-u`, `agent`, `--`, `env`, `-i`, then one `NAME=value` argument for each entry of `request.environment`, then the executable (WE3.1); the `sudo` stand-in itself runs with an empty environment.
5. With `os_user="agent"`, the `claude` stand-in behind the `sudo` stand-in sees exactly `request.environment` as its environment, although the test process has `GH_TOKEN` set.
6. With `os_user="agent"`, the agent process runs in `request.working_directory`.
7. A `sudo` stand-in that prints `sudo: a password is required` to standard error and exits 1 makes the runtime raise `AgentRuntimeError` whose detail contains that line.
8. A `sudo_executable` that does not exist makes the runtime raise `AgentRuntimeError`, not return a `died` result.
9. A request composed by `factory.application.task` with `settings.agent_user == "agent"` and `settings.agent_home == Path("/home/agent/.claude")` has `os_user == "agent"` and `environment["HOME"] == "/home/agent"`; with no `agent_user` (or no settings) it has `os_user is None` and no `HOME` entry.
10. `extra_items` returns one callable whose item is `token-file` when `agent_user` is `None`, and two, `token-file` and `tool:sudo` in that order, when `agent_user` is `agent`; the `tool:sudo` item fails when `which` answers `None` for `sudo`.
11. The Dockerfile copies `image/sudoers-factory-agent` to `/etc/sudoers.d/factory-agent`, sets mode `0440`, validates it with `visudo -cf`, and sets `ENV FACTORY_AGENT_USER=agent`, all before `USER factory`.
12. `image/sudoers-factory-agent` holds, apart from blank and comment lines, exactly the line `factory ALL=(agent) NOPASSWD: ALL`, and no line of it names `root`, `ALL=(ALL`, or the user `agent` as the one who may use `sudo`.
13. The uid of the compose secret `hosting-token` equals the uid the Dockerfile gives the user `factory` and differs from the uid it gives `agent`, and `agent`'s uid is not 0 (WE3.1: the token file is readable only by the factory's user).
14. The entrypoint sets `umask 002` before it starts the instance (the stub sees `0002`) and sets the global git configuration `core.sharedRepository` to `group`.
15. `make check` stays green.
16. docs: `docs/operator-guide.md` explains the two users (`factory`, uid 1000, runs the factory; `agent`, uid 1001, runs every agent), the shared group `factory-work`, the one `sudo` rule, the one-time login as `agent`, and the morning observation of WE3.1, WE3.3 and WE3.4 with the commands that perform it; `docs/decisions.md` records why the agent is started through `sudo -n -u agent -- env -i` and that the agent home stays writable by the agent (L69, left for v2).

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
grep -v '^#' image/sudoers-factory-agent | grep -v '^$'
```
Expect: exactly one line, `factory ALL=(agent) NOPASSWD: ALL`.

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
