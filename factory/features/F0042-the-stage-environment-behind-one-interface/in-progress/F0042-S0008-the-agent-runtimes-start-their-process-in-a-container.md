# The agent runtimes start their process in a container

## Description

Step 5 of the cycle (`planning/v1.2-plan.md`, "The cycle of a stage"): the agent's container runs today's chain minus `sudo`, `env -i` and `factory-confine`: the stage image, `/work` mounted, the login file mounted read-only, the request's allow-list environment as `--env` entries, the instructions file mounted read-only, `HOME=/work/home`, `--timeout` as the time limit, `--rm`. The two runtimes, `ClaudeCodeRuntime` and `OpencodeRuntime`, are not duplicated: each gets an optional `ContainerRuns`, and when it has one, every call's words come from `ContainerRuns.launch` instead of the `sudo` chain of the shared launch module, at the same place (`run_launch`). The call's files (the instructions file, opencode's configuration file) and the login files are mounted read-only at their own paths, so the words of the call do not change; the working directory inside the container is `/work/checkout`; a container ended by `--timeout` (exit status 137 or -9 at or after the limit) is read as `time_limit`, as the agent's own `timeout` under `sudo` is read today. No rules file, no temporary folder, no leftovers program and no `CLAUDE_CONFIG_DIR` in a container: those belong to the layers the container replaces. `version()` runs `<executable> --version` in a container too, so the preflight's `agent-runtime-version` reads the stage image's runtime. The runtimes are tested on `FakeContainerRuns` with the stand-in `claude` and `opencode` of the existing tests on the `PATH`; the wiring that gives a `container` instance's runtimes their `PodmanRuns` is S0010's. What stays: a runtime without a container behaves exactly as today, and every existing runtime test is unchanged.

## Interface

`factory.adapters.agent_launch` (`adapters`):

```python
def container_launch(
    containers: ContainerRuns,
    argv: Sequence[str],
    environment: Mapping[str, str],
    *,
    files: Sequence[Path],
    time_limit: timedelta,
) -> Launch:
    """`argv` with `environment` in a container; `files` mounted read-only at their own paths."""


def login_paths(files: LoginFiles) -> list[Path]:
    """The login files that are set, the subscription file first."""


def version_launch(
    executable: str, *, containers: ContainerRuns | None, time_limit: timedelta
) -> Launch:
    """The call of `<executable> --version`, on the host or in a container."""


def killed_at_limit(
    *,
    os_user: str | None,
    exit_status: int | None,
    duration: timedelta,
    time_limit: timedelta,
    in_container: bool = False,
) -> bool: ...


def read_call_end(
    end: CallEnd,
    *,
    time_limit: timedelta,
    os_user: str | None,
    starters: Starters,
    in_container: bool = False,
) -> bool: ...
```

- `container_launch` is `containers.launch(argv, mounts=[Mount(source=f, target=str(f), read_only=True) for f in files], environment=environment, time_limit=time_limit, working_directory=WORK_CHECKOUT)` turned into `Launch(argv=<its argv>, env=<its env>, time_limit=<its time_limit>)`; the files in the order given, each once. It raises what `launch` raises.
- `killed_at_limit` and `read_call_end` with `in_container` true judge the kill as they do for a call with an `os_user`: exit status 137 or -9 after at least `time_limit` is the time limit; before it, it is not. With `in_container` false (the default) nothing changes, so every existing caller and test is unchanged. The `sudo:` and `factory-confine:` refusals are not read for a container call (`os_user` is `None` and the confine executable too).
- `agent_launch` still does not import the process module.
- `Launch.env` becomes `dict[str, str] | None` (decision 11 of `feature.md`): `None` is the process's own environment, as `ProcessRequest.env` reads it, and is what `PodmanRuns.launch` gives; `container_launch` passes the `ContainerLaunch`'s `env` through as it is. Every existing caller passes a dict and is unchanged.
- `login_paths` is `[subscription, api]` with the unset ones left out; both runtimes mount `[*login_paths(files), <the call's file>]`.
- `version_launch` is `Launch(argv=[executable, "--version"], env=None, time_limit=time_limit)` without `containers` (today's call: the process's own environment) and `container_launch(containers, [executable, "--version"], {}, files=[], time_limit=time_limit)` with them; both runtimes' `version()` start it through `run_process` with `cwd` the current directory and read the first word as today.

`factory.adapters.claude_runtime.ClaudeCodeRuntime` and `factory.adapters.opencode_runtime.OpencodeRuntime` (`adapters`): the constructors gain the keyword `containers: ContainerRuns | None = None`.

- A runtime built with `containers` and a `confine_executable` raises `ValueError` at construction: a container run is not confined by the kernel. Built with `containers` alone, it stores them; `containers` is a read-only property returning what was given (`None` by default).
- With `containers`, `run(request)`: a request whose `os_user` is set raises `AgentRuntimeError("a run in a container has no operating-system user")` before any file is written or call made. Otherwise the run's files are written as today into the state directory (the instructions file for Claude Code, the configuration file for opencode; no rules file, as without a confine executable), and each call's process request is `container_launch(containers, <the login shell words and the runtime's words, as today>, {**without_login(request.environment), **<the runtime's switches>}, files=[<the login files that are set, in the order subscription then API>, <the call's file>], time_limit=<the call's time limit>)` with `cwd` `request.working_directory`; `--workdir` inside is `/work/checkout` (through `container_launch`). The runtime's switches are Claude Code's `SWITCHES` (no `CLAUDE_CONFIG_DIR`: that is set only with a confine executable, as today) and opencode's `SWITCHES` with `OPENCODE_CONFIG` naming its configuration file at its own path. No leftovers program runs (no `os_user`), no temporary folder is removed (none was made).
- The end of a call in a container is read with `in_container=True`: a call that ends with exit status 137 or -9 at or after its time limit is `time_limit`, not resumed, its measures unknown; before the limit it is `died`. A call that completes is read exactly as today (the JSON reply, the events, the login line `factory-login-used:` from the mounted login files).
- `version()` with `containers` runs `version_launch(executable, containers=containers, time_limit=<the version time limit>)` through `run_process` with `cwd` the current directory and reads the first word as today.
- Without `containers` every behaviour is as today.

Tests (the tester writes them): `tests/adapters/test_claude_runtime_container.py` and `tests/adapters/test_opencode_runtime_container.py`, each with a `FakeContainerRuns(workspace)` on `tmp_path` whose folders `<workspace>/checkout` and `<workspace>/home` the test makes (the fake's shell enters the mapped working directory before the command, so without `checkout/` every call, `version()` included, ends with `cd: can't cd to ...`), the stand-ins `write_stand_in` of `tests/adapters/claude_stand_in.py` and of `tests/adapters/opencode_stand_in.py` on the request's `PATH`, the request's `working_directory` an existing folder under `tmp_path`, `HOME` `/work/home` (which the fake maps to `<workspace>/home`); `tests/adapters/test_agent_launch_container.py` for `container_launch`, `killed_at_limit` and `read_call_end` with `in_container`. The existing runtime and launch tests are unchanged.

## Acceptance criteria

1. `container_launch(fake, ["/bin/sh", "-c", "x"], {"HOME": "/work/home"}, files=[Path("/state/runs/instructions-1.md"), Path("/home/factory/.claude-token")], time_limit=timedelta(minutes=2))` returns a `Launch` whose `argv`, `env` and `time_limit` are the fake's `ContainerLaunch` fields, and the fake's recorded call has the mounts `[Mount(source=Path("/state/runs/instructions-1.md"), target="/state/runs/instructions-1.md", read_only=True), Mount(source=Path("/home/factory/.claude-token"), target="/home/factory/.claude-token", read_only=True)]`, the working directory `/work/checkout`, the environment and the time limit as given. `container_launch(fake, ["x"], {}, files=[Path("/work/x")], time_limit=timedelta(seconds=1))` raises `ValueError` (the fake's refusal of a target under `/work`) and the fake recorded no call. `Launch(argv=["/bin/true"], env=None, time_limit=timedelta(seconds=1))` is accepted with `env` `None`, and `container_launch` on a `ContainerRuns` of the test (a subclass of `FakeContainerRuns` whose `launch` returns the fake's `ContainerLaunch` with `env=None`) returns a `Launch` whose `env` is `None` (rows of one parametrized test).
2. `killed_at_limit` (rows of one parametrized test): `in_container=True`, exit 137, duration 61 s, limit 60 s is `True`; `in_container=True`, exit -9, duration 60 s, limit 60 s is `True`; `in_container=True`, exit 137, duration 59 s is `False`; `in_container=True`, exit 1, duration 61 s is `False`; `in_container=False`, `os_user=None`, exit 137, duration 61 s is `False` (today's rule); `read_call_end` with `in_container=True` and an end of exit 137 after the limit returns `True` and raises nothing, even when `stderr` holds a `sudo:` line.
3. `ClaudeCodeRuntime(<stand-in>, state, containers=fake, confine_executable="factory-confine")` raises `ValueError`; `ClaudeCodeRuntime(<stand-in>, state, containers=fake).containers is fake`; without the keyword `containers` is `None` (rows of one parametrized test; the same three rows for `OpencodeRuntime`).
4. A Claude Code run in a container: the stand-in `claude` on the request's `PATH` prints a completed reply; `run(request)` returns a completed result with the decision and entry, the fake's recorded call has the command `[<login shell words when a login file is set>, <stand-in>, "-p", ...]` with the instructions file's path among the words, the mounts `[<the login file>, <the instructions file>]` read-only at their own paths, the environment the request's less the logins plus `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1` and `PYTHONDONTWRITEBYTECODE=1` and without `CLAUDE_CONFIG_DIR`, the time limit the request's, the working directory `/work/checkout`; the stand-in's recorded working directory is `<workspace>/checkout` and its `HOME` is `<workspace>/home`; no rules file was written into the state directory and the instructions file is removed after the run. A second row with both `login_file` and `api_login_file` set has the mounts `[<the token file>, <the API file>, <the instructions file>]` in that order (the Interface's order, subscription then API). In both rows the token file's text stands in no word of the recorded command and in no value of its environment (decision 16).
5. An opencode run in a container: the same with the stand-in `opencode`, the mounts `[<the API login file when set>, <the configuration file>]`, the environment holding `OPENCODE_CONFIG=<the configuration file's path>` and `PYTHONDONTWRITEBYTECODE=1`, the configuration file removed after the run.
6. A request with `os_user="agent"` on a runtime with containers raises `AgentRuntimeError` whose `detail` is `a run in a container has no operating-system user`, and the fake recorded no call and the state directory holds no run file (rows for both runtimes).
7. The kill at the limit (rows of one parametrized test, both runtimes): a stand-in that exits 137 after 3 seconds under a request with `time_limit` 3 seconds gives `end_reason` `time_limit` with `cost_usd`, `turns` and `tokens` `None`, and the fake made exactly one call (no resume); a stand-in that exits 137 at once under `time_limit` 30 seconds gives `died`. The reading of podman's kill, which the fake cannot play (it adds no grace, so the factory's own kill fires at the limit too): with the call answered by a recorded `ProcessResult(exit_status=137, stdout=<a completed reply, or the events of one step for opencode>, stderr="", timed_out=False, duration=<d>)`, `d` of 30 seconds under `time_limit` 30 seconds gives `time_limit` and 29.9 seconds gives `died` (rows for both runtimes: the `recorder` fixture for Claude Code; for opencode `run_streaming` of `factory.adapters.opencode_runtime` replaced with `monkeypatch` by a function of the test that keeps the request and answers that result).
8. A Claude Code budget stop in a container is resumed as today: the stand-in's first reply has the budget subtype, the second completes; the fake recorded two calls, the second's command holding `--resume` and the same mounts.
9. `version()` with containers: the fake's recorded call has the command `[<stand-in>, "--version"]`, no mounts, an empty environment, the working directory `/work/checkout` and the version time limit; the return value is the stand-in's first word (rows for both runtimes). One more row pins `version_launch("claude", containers=None, time_limit=timedelta(seconds=30)) == Launch(argv=["claude", "--version"], env=None, time_limit=timedelta(seconds=30))`.
10. Without `containers`, `run` and `version` behave as today: `tests/adapters/test_claude_runtime*.py`, `test_opencode_*.py` and `test_agent_launch*.py` are unchanged and green, and one row of the new modules runs the same completed request through a runtime without containers and sees the stand-in's recorded working directory equal to the request's `working_directory`.
11. `make check` stays green.
12. docs: `docs/project-guide/agents.md`, *The agent runtime* and *The shared launch module*: the `containers` keyword, `container_launch` beside `launch`, what a call in a container gets (the mounts, the environment, `/work/checkout`, `HOME`), what it does not (no `sudo`, no `factory-confine`, no rules file, no leftovers, no temporary folder, no `CLAUDE_CONFIG_DIR`), the reading of `--timeout`'s kill through `in_container`, `version` in the container, the `ValueError` and the `AgentRuntimeError`; `docs/project-guide/stage-environment.md` gains the section *The agent's container* (one paragraph pointing to `agents.md` and naming step 5 of the cycle); `docs/operator-guide.md`, *The agent runtime*: one paragraph on what the chain is on a `container` instance (`podman run ... <image> /bin/sh -c <login shell> ... claude -p ...`), with the `:ro` mounts of the login and instructions files, pointing to the stage image of F0043. `docs/decisions.md`: none.

## Smoke test

```bash
uv run pytest tests/adapters/test_claude_runtime_container.py tests/adapters/test_opencode_runtime_container.py tests/adapters/test_agent_launch_container.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir -p "$d/work/checkout" "$d/state"
uv run python - "$d" <<'EOF'
import sys
from datetime import timedelta
from pathlib import Path

from factory.adapters.agent_launch import container_launch, killed_at_limit
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_containers import FakeContainerRuns

d = Path(sys.argv[1])
fake = FakeContainerRuns(d / "work")
started = container_launch(fake, ["/bin/sh", "-c", 'pwd; echo "$HOME"'], {"HOME": "/work/home"}, files=[d / "state" / "instructions-1.md"], time_limit=timedelta(seconds=5))
print(started.argv[4].replace(str(d), "D"), {name: value.replace(str(d), "D") for name, value in (started.env or {}).items()}, fake.calls[0].mounts[0].read_only, fake.calls[0].working_directory)
print(killed_at_limit(os_user=None, exit_status=137, duration=timedelta(seconds=61), time_limit=timedelta(seconds=60), in_container=True), killed_at_limit(os_user=None, exit_status=137, duration=timedelta(seconds=61), time_limit=timedelta(seconds=60)))
try:
    ClaudeCodeRuntime("claude", d / "state", containers=fake, confine_executable="factory-confine")
except ValueError:
    print("refused", ClaudeCodeRuntime("claude", d / "state", containers=fake).containers is fake)
EOF
```
Expect: three lines, `D/work/checkout {'HOME': 'D/work/home'} True /work/checkout`, `True False`, `refused True`

## Journal
