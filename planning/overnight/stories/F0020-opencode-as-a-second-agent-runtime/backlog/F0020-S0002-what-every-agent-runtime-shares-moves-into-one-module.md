# What every agent runtime shares moves into one module

## Description

The opencode runtime (S0004) starts its runs exactly as the Claude Code runtime does: as the agent user under `sudo -n -u <user> --`, killed by `timeout --signal=KILL` at its limit, its environment given by `env -i`, through `factory-confine` with the run's rules file and its own temporary folder, which is removed afterwards as the run's user; it reads the same refusal lines of `sudo` and the wrapper, resumes a budget stop with the same share and the same finish message, and adds up a resumed run's measures the same way. Today all of this sits in private helpers of `factory.adapters.claude_runtime`, so a second runtime would copy them. This story moves them, without changing what the Claude Code runtime does: the words, the rules, the refusals and the budget share into `factory.adapters.agent_launch`, which S0001 made for the login, and the summing of a resumed run into the domain, `resumed_result` in `factory.domain.agent_runs`. Each runtime keeps its own process calls: `agent_launch` builds words and texts and imports no process module. Every name an earlier test imports from `claude_runtime` or sets on it stays a name of that module that it reads at the call, so every earlier test passes unchanged; they are the proof that the Claude Code runtime behaves as before. Nothing calls the shared parts from a second runtime yet; S0004 does.

## Interface

`factory.domain.agent_runs` (`domain`):

```python
def resumed_result(first: AgentRunResult, second: AgentRunResult) -> AgentRunResult: ...
```

- The result of a run whose `first` call was resumed by the `second`: `second`'s `end_reason`, `decision`, `entry` and `login`, `first`'s refused tool calls followed by `second`'s, each unchanged (`PermissionDenial.path` included), and `duration` the sum of both.
- When `second.end_reason` is `time_limit`, nothing else is summed: `model_duration`, `turns`, `tokens` and `cost_usd` are `second`'s (R24: a call the time limit ended reports no measures, and the first call's alone are partial).
- Otherwise `model_duration`, `turns`, `cost_usd` and each count of `tokens` are the sums of both; a measure that one call left `None` is the other's, and one that both left `None` stays `None`.
- It moves the private `_resumed_result`, `_add` and `_add_tokens` of `claude_runtime`, which now calls `resumed_result` (the run's duration is still set afterwards from the whole run's clock, as today).

`factory.adapters.agent_launch` (`adapters`), beside S0001's login:

```python
ENTRY_DESCRIPTION = ...            # moved from claude_runtime
FINISH_MESSAGE = ...               # moved from claude_runtime
MINIMUM_RESUME_BUDGET = Decimal("0.50")   # moved
VERSION_TIME_LIMIT = timedelta(seconds=30)  # moved
SUDO_EXECUTABLE = "/usr/bin/sudo"  # moved
CLEANUP_TIME_LIMIT = timedelta(seconds=60)  # moved
TIMEOUT_EXECUTABLE = "timeout"     # moved
SUDO_GRACE = timedelta(seconds=30) # moved
KILL_STATUSES = frozenset({137, -9})  # moved
RUN_FILE_MODE = 0o640              # moved
TEMPORARY_PREFIX = "factory-run-"  # moved
CLEANUP_SCRIPT = ...               # moved
SUDO_PREFIX = "sudo:"              # moved
CONFINE_PREFIX = "factory-confine:"  # moved

class Launch(BaseModel):
    """The words, environment and time limit of one call, before the process module starts it."""
    argv: list[str]
    env: dict[str, str]
    time_limit: timedelta

def resume_budget(budget: Decimal) -> Decimal: ...          # moved
def launch(argv: Sequence[str], environment: Mapping[str, str], *, os_user: str | None,
           sudo_executable: str, time_limit: timedelta) -> Launch: ...
def sudo_prefix(sudo_executable: str, os_user: str) -> list[str]: ...
def confined_argv(argv: Sequence[str], confine_executable: str | None, rules: Path) -> list[str]: ...
def cleanup_argv(shell: str, temporary: Path, *, os_user: str | None, sudo_executable: str) -> list[str]: ...
def temporary_folder(root: Path, run: str) -> Path: ...
def existing_devices(folders: Sequence[str], files: Sequence[str]) -> list[WriteTarget]: ...
def run_confinement(request: AgentRunRequest, temporary: Path, *, runtime_folders: Sequence[str],
                    devices: Sequence[WriteTarget]) -> Confinement: ...
def line_starting(stderr: str, prefix: str) -> str | None: ...
def killed_at_limit(*, os_user: str | None, exit_status: int | None, duration: timedelta,
                    time_limit: timedelta) -> bool: ...
def first_word(output: str) -> str | None: ...
```

- `launch` without `os_user`: `argv` and `environment` as given, the time limit as given. With `os_user`: `[*sudo_prefix(sudo_executable, os_user), "timeout", "--signal=KILL", "<limit>s", "env", "-i", *("NAME=value" for each entry in the environment's order), *argv]`, an empty environment, and the time limit plus `SUDO_GRACE`; `<limit>` is the limit's seconds rounded up (`30s` for 29.2 seconds). These are today's words of `ClaudeCodeRuntime._process_request`.
- `sudo_prefix`: `[sudo_executable, "-n", "-u", os_user, "--"]`.
- `confined_argv`: `argv` unchanged without a wrapper; else `[confine_executable, "--rules", str(rules), "--", *argv]`.
- `cleanup_argv`: `[shell, "-c", CLEANUP_SCRIPT, "factory-cleanup", str(temporary)]`, after `sudo_prefix` when `os_user` is set.
- `temporary_folder`: `root / f"factory-run-{run}"`.
- `existing_devices`: a folder target for each of `folders` and a file target for each of `files` that exists, folders first, each in its given order.
- `run_confinement`: today's `_confinement` of `claude_runtime`, with the runtime's folders given relative to the request's `HOME` (`[".claude"]` for Claude Code): each becomes a folder target `<HOME>/<folder>` in the order given; a request without `HOME` gets none of them; a request without guard settings may write nothing of the checkout.
- `line_starting`: the first line of `stderr` that starts with `prefix`, else `None`.
- `killed_at_limit`: true only with an `os_user`, an exit status in `KILL_STATUSES` and a duration at or above the time limit.
- `first_word`: the first word of the first non-blank line, else `None`.
- No function here starts a process, reads `os.environ` or imports `factory.adapters.process`.

`factory.adapters.claude_runtime` (`adapters`):

- Uses the functions above in place of its private copies, which it no longer holds: `_since` and the reply's parsing stay its own.
- Every name an earlier test imports from it or sets on it stays a module-level name of it: the moved `ENTRY_DESCRIPTION`, `FINISH_MESSAGE`, `VERSION_TIME_LIMIT`, `SUDO_EXECUTABLE`, `CLEANUP_TIME_LIMIT`, `resume_budget` and `CLEANUP_SCRIPT` are imported from `factory.adapters.agent_launch` and listed in the module's `__all__`, as S0001's login names are (never `import X as X`, ruff's `PLC0414`); `SWITCHES`, `CONFIG_VARIABLE` and `RUNTIME_FOLDER`, which are Claude Code's own, stay defined here.
- `Launch` is frozen and forbids unknown keys, like every model (`tests/test_model_configuration.py` finds it).
- The values a test sets on the module are read from its namespace at the call and passed to the shared functions: `SHELL_EXECUTABLE` and `CLEANUP_TIME_LIMIT` for the removal, `DEVICE_FOLDERS` and `DEVICE_FILES` for `existing_devices`, and `run_process` for every call.
- What a run does is unchanged: arguments, environment, run files and their modes, rules, refusals, resume, measures and errors.

Tests (the tester writes them): `tests/adapters/test_agent_launch.py` (the words and the rules; `run_confinement` with the request of `run_request` and the folders of `build_layout` from `tests/confine_support.py`, imported, not copied), `tests/domain/test_resumed_result.py`, `tests/test_agent_launch_search.py` (with `tests/source_search.py`). No earlier test changes: the tests of the Claude Code runtime (`tests/adapters/test_claude_runtime*.py`, `tests/entry/test_wiring*.py`, `tests/test_model_configuration.py`) pass as they are.

## Acceptance criteria

1. `launch(["claude", "-p", "x"], {"HOME": "/home/agent", "PATH": "/bin"}, os_user=None, sudo_executable="/usr/bin/sudo", time_limit=timedelta(seconds=30))` keeps the words, the environment and the 30 seconds; with `os_user="agent"` and 29.2 seconds it gives `["/usr/bin/sudo", "-n", "-u", "agent", "--", "timeout", "--signal=KILL", "30s", "env", "-i", "HOME=/home/agent", "PATH=/bin", "claude", "-p", "x"]`, an empty environment and 59.2 seconds (rows).
2. `confined_argv` gives the words unchanged without a wrapper and `["factory-confine", "--rules", "/state/runs/confine-r.json", "--", "claude"]` with one (rows).
3. `cleanup_argv("/bin/sh", Path("/tmp/factory-run-r"), ...)` gives the five words without a user and the same after `["/usr/bin/sudo", "-n", "-u", "agent", "--"]` with one (rows); `temporary_folder(Path("/tmp"), "r")` is `/tmp/factory-run-r`.
4. `existing_devices` of an existing and a missing folder and an existing and a missing file gives the existing folder's folder target, then the existing file's file target.
5. `run_confinement` with `runtime_folders=[".claude"]` holds `<HOME>/.claude` as a folder target; with `[".local/share/opencode", ".cache/opencode"]` it holds both in that order; a request without `HOME` holds neither; a request without guard settings holds no path of the checkout (rows).
6. `line_starting` gives the first matching line of two, and `None` for no match and for a match that is not at a line's start (rows).
7. `killed_at_limit` is true for exit 137 and for -9 at the limit with a user; false below the limit, without a user, and for exit 1 (rows).
8. `first_word` gives `2.1.296` for `"\n2.1.296 (Claude Code)\n"` and `None` for `""` and `"  \n"` (rows).
9. `resume_budget` gives `0.50` for `1`, `1.00` for `4` and `0.63` for `2.50` (rows, as `claude_runtime.resume_budget` today).
10. `resumed_result` of two completed calls with every measure sums them, joins the refused calls in order, each with its `path` unchanged, and takes the second's decision, entry and login; a measure only one call reported is that call's; one neither reported stays `None`; a second call ended by `time_limit` keeps its own measures and gets both calls' refused calls; the duration is always the sum (rows).
11. No function of `factory.adapters.agent_launch` starts a process: `tests/test_wrapper_search.py` and `tests/test_process_search.py` pass unchanged; and neither `factory.adapters.agent_launch` nor `factory.adapters.claude_runtime` reads `os.environ` (a source search over both modules, which finds it in a snippet that does).
12. Every earlier test of the Claude Code runtime passes unchanged, among them those that set `claude_runtime.SHELL_EXECUTABLE`, `CLEANUP_TIME_LIMIT`, `DEVICE_FOLDERS`, `DEVICE_FILES` and `run_process`.
13. `make check` stays green.
14. docs: `docs/project-guide.md`, where S0001 introduced `factory.adapters.agent_launch`: it also holds the words of a run's start (`sudo`, `timeout`, `env -i`, `factory-confine`), the rules, the removal of the run's folder, the refusals and the resume share, for every runtime; `resumed_result` in the domain adds up a resumed run. `docs/decisions.md`: an entry *What the agent runtimes share lies in one module*, dated with the story, with the reasons of the feature's decision 4.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run -q python - "$d" <<'EOF'
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from factory.adapters.agent_launch import confined_argv, launch, resume_budget
from factory.domain.agent_runs import AgentRunResult, resumed_result

d = Path(sys.argv[1])
started = launch(["claude"], {"HOME": "/home/agent"}, os_user="agent", sudo_executable="/usr/bin/sudo", time_limit=timedelta(seconds=10))
print(" ".join(started.argv), started.time_limit.total_seconds())
print(" ".join(confined_argv(["claude"], "factory-confine", d / "rules.json")).replace(str(d), "D"))
print(resume_budget(Decimal("4")))
first = AgentRunResult(end_reason="budget", duration=timedelta(seconds=1), turns=3, cost_usd=Decimal("1.00"))
second = AgentRunResult(end_reason="completed", decision="question", entry="Done.", duration=timedelta(seconds=2), turns=1, cost_usd=Decimal("0.25"))
both = resumed_result(first, second)
print(both.end_reason, both.turns, both.cost_usd, both.duration.total_seconds())
EOF
```
Expect: four lines, `/usr/bin/sudo -n -u agent -- timeout --signal=KILL 10s env -i HOME=/home/agent claude 40.0`, `factory-confine --rules D/rules.json -- claude`, `1.00`, `completed 4 1.25 3.0`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
