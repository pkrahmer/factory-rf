# The agent runtimes end the agent's leftover processes after every call

## Description

S0001 built the program that ends every other process of its user. This story makes both agent runtimes start it after every call of a run that has an operating-system user, as that user, through the one `sudo` rule: `sudo -n -u <user> -- <python> -I -m factory.entry.leftovers --user <user>`, from the folder `/`, with an empty environment and a 30-second time limit. It runs before the run's temporary folder is removed, so no leftover process writes there meanwhile. It also runs inside `AgentRuntime.run`, so it comes before the factory checks the seal, removes nested repositories, undoes, or runs a check. A run resumed after its budget runs it after each of its two calls. It runs also after a call that `sudo`, the write guard's wrapper or the login shell refused. The runtime starts it only when it was built with the program's command (keyword `leftovers`), only for a request whose `os_user` is set, and never when that user is the factory process's own: in an agent's `make test` that is `agent`, and the program would end the run itself. When the program fails, or does not end in time, after a call that ended without an error of its own, the run raises `AgentRuntimeError` (`cannot end the agent's processes: <line>`), so nothing the factory cannot vouch for reaches the undo and the checks. When `sudo`, the wrapper or the login shell refused the call, that error stands. `build_boundaries` builds the runtime with the command by default (`end_leftovers=True`). A runtime built by a test has none, so every earlier runtime test keeps its calls. The interface `AgentRuntime` and the request do not change.

## Interface

`factory.adapters.agent_launch` (`adapters`):

```python
LEFTOVERS_TIME_LIMIT = timedelta(seconds=30)


class Starters(BaseModel):
    ...
    leftovers: list[str] | None = None


def leftovers_due(starters: Starters, os_user: str | None, own_user: str) -> bool: ...
def leftovers_launch(leftovers: Sequence[str], *, os_user: str, sudo_executable: str) -> Launch: ...
def leftovers_fault(*, exit_status: int | None, timed_out: bool, stderr: str) -> str | None: ...
```

- `Starters.leftovers`: the words that start the program, without `--user`, or `None` (the default) when the runtime starts none. Every existing construction of `Starters` stays valid.
- `leftovers_due`: true exactly when `starters.leftovers` is not `None`, `os_user` is not `None` and `os_user` differs from `own_user`.
- `leftovers_launch`: `Launch(argv=[*sudo_prefix(sudo_executable, os_user), *leftovers, "--user", os_user], env={}, time_limit=LEFTOVERS_TIME_LIMIT)`.
- `leftovers_fault`: `None` when `timed_out` is false and `exit_status` is 0. When `timed_out` is true it is `cannot end the agent's processes: no end within 30 s`. Otherwise it is `cannot end the agent's processes: <line>`, where `<line>` is the first line of `stderr` that starts with `LEFTOVERS_PREFIX` (`factory-leftovers:`), whole, or `exit status <exit_status>` when there is none (a `sudo:` line is never that line).
- The module still does not import `factory.adapters.process` (`tests/test_agent_launch_search.py`), which is why `leftovers_fault` takes the three values and not a `ProcessResult`.

`factory.adapters.claude_runtime` and `factory.adapters.opencode_runtime` (`adapters`):

```python
class ClaudeCodeRuntime(AgentRuntime):
    def __init__(self, ..., leftovers: Sequence[str] | None = None) -> None: ...

    @property
    def leftovers(self) -> list[str] | None:
        """The words that start the program ending the agent's leftover processes, or `None`."""


class OpencodeRuntime(AgentRuntime):
    def __init__(self, ..., leftovers: Sequence[str] | None = None) -> None: ...

    @property
    def leftovers(self) -> list[str] | None: ...
```

- Both keep `leftovers` in their `Starters` and read the factory process's own user once per call with `factory.adapters.process.own_identity().user`.
- In `_call`, after the call's process returned (a call that cannot be started raises `cannot start <program>: <error>` as today, and nothing follows it): when `leftovers_due(...)`, start `leftovers_launch(...)` through the runtime's `_start` with the working directory `/`. Then, as today, the temporary folder's removal (when confined). The order of the processes a call starts is the call, the program, the removal.
- The program's result is read only when the call returned and the reading of its end raised no refusal (`call_refusal` today; `read_call_end` once F0039-S0001 is merged, which raises the refusal itself). Then a `leftovers_fault` that is not `None` raises `AgentRuntimeError(<the fault>)`, after the removal. So the order in `_call` is: the call, the program, the removal, the reading of the call's end, the program's fault. When the call gives a refusal, the call's own `AgentRuntimeError` is raised as today, and the program's result is not read.
- A run stopped by its budget is resumed in a second `_call`, so the program runs twice, once after each call. A run with `resume_session` makes one call, and a second one only when its budget stops it.
- `version()` starts no program: it has no operating-system user.

`factory.entry.wiring` (`entry`):

```python
LEFTOVERS_MODULE = "factory.entry.leftovers"


def leftovers_command() -> list[str]:
    """The words that start the leftovers program with this interpreter, isolated."""


def build_boundaries(..., end_leftovers: bool = True) -> Boundaries: ...
```

- `leftovers_command()` is `[sys.executable, "-I", "-m", LEFTOVERS_MODULE]`.
- `build_boundaries` passes `leftovers=leftovers_command()` to every agent runtime it builds when `end_leftovers` is true, and `leftovers=None` when it is false. Nothing else in it changes.

Unchanged: `AgentRuntime`, `AgentRunRequest`, `run_sealed`, `launch`, `cleanup_launch`, the login shell, `factory-confine`, and every runtime built without `leftovers`.

Tests (the tester writes them): `tests/adapters/test_agent_launch_leftovers.py`, `tests/adapters/test_claude_runtime_leftovers.py` and `tests/adapters/test_opencode_runtime_leftovers.py`. Each uses a stand-in `sudo` that records its arguments and working directory and runs what follows `--`, as `tests/adapters/test_claude_runtime_os_user.py` and `tests/adapters/test_claude_runtime_confinement.py` do, the stand-in `claude` of `tests/adapters/claude_stand_in.py` or `opencode` of `tests/adapters/opencode_stand_in.py`, and a stand-in program passed as `leftovers`: a script that records its arguments and exits with a planned status and standard-error text. Never the real command, by the human's change 1. Also `tests/entry/test_wiring_leftovers.py`. A request whose `os_user` must equal the factory's own user takes it from `pwd.getpwuid(os.getuid()).pw_name`. A request whose `os_user` must differ from it uses `factory-test-other`, a user no test runs as: the tests run as `agent` in an agent's `make test` and as `factory` in the factory's checks, and a row with `agent` would start no program in the first.

## Acceptance criteria

1. `leftovers_due` (rows of one parametrized test, own user `factory`): `leftovers` `["prog"]` with `os_user` `agent` gives true. `leftovers` `None` with `agent`, `["prog"]` with `os_user` `None`, and `["prog"]` with `os_user` `factory` each give false.
2. `leftovers_launch(["/opt/py", "-I", "-m", "factory.entry.leftovers"], os_user="agent", sudo_executable="/usr/bin/sudo")` gives `argv` `["/usr/bin/sudo", "-n", "-u", "agent", "--", "/opt/py", "-I", "-m", "factory.entry.leftovers", "--user", "agent"]`, `env` `{}` and `time_limit` 30 seconds.
3. `leftovers_fault` (rows of one parametrized test): status 0, not timed out, gives `None`, also with a `sudo: unable to resolve host x` line on standard error. Status 1 with standard error `sudo: unable to resolve host x\nfactory-leftovers: 2 processes left after 50 rounds: 7, 10\n` gives `cannot end the agent's processes: factory-leftovers: 2 processes left after 50 rounds: 7, 10`. Status 1 with standard error `sudo: a password is required\n` gives `cannot end the agent's processes: exit status 1`. `exit_status` `None` and timed out gives `cannot end the agent's processes: no end within 30 s`. Status 0 and timed out gives the same.
4. The `claude -p` runtime's order (rows of one parametrized test, built with the stand-in `sudo`, the stand-in `claude` replying once, a stand-in `factory-confine`, and `leftovers=[<stand-in program>]` exiting 0). With `os_user` `factory-test-other`, the stand-in `sudo` records three calls in this order: the run, then `["-n", "-u", "factory-test-other", "--", <stand-in program>, "--user", "factory-test-other"]` in the working directory `/`, then the removal of the temporary folder (its arguments hold `CLEANUP_SCRIPT`). The stand-in program records `["--user", "factory-test-other"]`, and the result is `completed` with decision `doing`. With `os_user` equal to the factory's own user, `sudo` records two calls, the run and the removal, and the program records nothing. Built without `leftovers`, with `os_user` `factory-test-other`, it records the same two calls.
5. A run without an operating-system user (`os_user` `None`, built with `leftovers`) starts no `sudo` and no program, and its result is the stand-in's reply. `version()` of a runtime built with `leftovers` starts only `claude --version`: the stand-in program records nothing.
6. A resumed run (the stand-in `claude` stops at its budget on the first call and replies on the second, `os_user` `factory-test-other`, built with `leftovers`): the stand-in program records two calls, and the `sudo` records are, in order, run, program, removal, run, program, removal.
7. The program's result (rows of one parametrized test, `os_user` `factory-test-other`, the stand-in `claude` replying): the program exiting 0 gives the stand-in's result. The program exiting 1 with standard error `factory-leftovers: 1 processes left after 50 rounds: 7\n` raises `AgentRuntimeError` whose `detail` is `cannot end the agent's processes: factory-leftovers: 1 processes left after 50 rounds: 7`, and the temporary folder was still removed (the removal's call is recorded after the program's). The program exiting 3 with nothing on standard error raises `AgentRuntimeError` with `cannot end the agent's processes: exit status 3`.
8. A call with an error of its own keeps it (rows of one parametrized test, `os_user` `factory-test-other`, the program exiting 1 with a `factory-leftovers:` line). The stand-in `sudo` refusing the run with `sudo: a password is required` and no reply raises `AgentRuntimeError` whose `detail` starts with `<sudo> refused the agent run: sudo: a password is required`, and the program was still started. The stand-in `factory-confine` refusing with a `factory-confine:` line and no reply raises the wrapper's error, and the program was still started.
9. The opencode runtime's order (rows of one parametrized test, the stand-in `opencode` printing its events, the stand-in `sudo`, a stand-in `factory-confine`, `leftovers=[<stand-in program>]`): with `os_user` `factory-test-other` the records are run, program (`--user factory-test-other`, in `/`), removal. With the factory's own user they are run and removal. The program exiting 1 with a `factory-leftovers:` line raises `AgentRuntimeError` with `cannot end the agent's processes: <that line>`.
10. `build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())` (rows of one parametrized test): by default the agent runtime's `leftovers` is `[sys.executable, "-I", "-m", "factory.entry.leftovers"]`, and with `end_leftovers=False` it is `None`. With `agent_runtime` `opencode` (F0020-S0008) the built `OpencodeRuntime`'s `leftovers` is the same list, and `None` with `end_leftovers=False`. `leftovers_command()` gives the same list as the default. Neither builds or starts a process.
11. `make check` stays green.
12. docs: `docs/operator-guide.md`, *The agent runs as a second user*: a paragraph after the one on the command line. After every call of a run as `agent`, the runtime runs `sudo -n -u agent -- /opt/factory/.venv/bin/python -I -m factory.entry.leftovers --user agent` from `/`. It ends every process of `agent` still running, a process started in a new session or with `nohup` included, before the run's temporary folder is removed and before the factory looks at the work tree. The `agent` user must therefore serve agent runs only. An operator's shell opened as `agent` (`docker exec -it -u agent <container> ...`, for `claude setup-token` or an opencode login) is ended by the next agent call, so run it while the instance is stopped. A failure stops the run with the error `cannot end the agent's processes: <line>` (the stage ends with a counted error; at the preflight's probe, `preflight_failed`). A run without `FACTORY_AGENT_USER` ends no processes. The table of morning observations, the row *A `time_limit` under `sudo`*, and the paragraph of the same name: after a run, `ps -o user,pid,ppid,stat,args -U agent` lists no process. `docs/project-guide/agents.md`, *The agent runtime*: `Starters.leftovers`, `leftovers_due`, `leftovers_launch`, `leftovers_fault`, the order after a call (the call, the program, the removal), when the program's result is read, and that a runtime built without `leftovers` starts none. `docs/project-guide/write-guard.md`, *The end of a run's processes*: who starts it and when. `docs/project-guide/watching.md`, *Boundaries*: `build_boundaries`' keyword `end_leftovers` and `leftovers_command()`. `docs/decisions.md`: an entry *Every agent call is followed by the end of the agent's leftover processes*, dated with the story, with the reasons of the feature's decisions 10 to 12, which says that it closes the window F0014 decision 21 left open (a process swapping `.git` after the seal's check).

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run -q python - "$d" <<'EOF'
import json
import os
import pwd
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
from factory.domain.errors import AgentRuntimeError

d = Path(sys.argv[1])
work = d / "work"
work.mkdir()
log = d / "calls.txt"
plan = d / "plan.txt"
reply = json.dumps({"type": "result", "subtype": "success", "is_error": False, "num_turns": 1, "total_cost_usd": 0.1, "duration_ms": 100, "usage": {"input_tokens": 1, "output_tokens": 1}, "permission_denials": [], "structured_output": {"decision": "doing", "entry": "Done."}})


def script(name: str, body: str) -> Path:
    path = d / name
    path.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
    path.chmod(0o755)
    return path


claude = script("claude", f"print({reply!r})\n")
program = script("leftovers", f"import sys\nstatus = int(open({str(plan)!r}).read())\nif status:\n    sys.stderr.write('factory-leftovers: 1 processes left after 50 rounds: 7\\n')\nsys.exit(status)\n")
sudo = script("sudo", f"import os, sys\nrest = sys.argv[sys.argv.index('--') + 1:]\nkind = 'program ' + ' '.join(rest[1:]) if rest[0] == {str(program)!r} else 'run'\nwhere = '/' if os.getcwd() == '/' else 'work' if os.getcwd() == {str(work)!r} else os.getcwd()\nopen({str(log)!r}, 'a').write(kind + ' in ' + where + '\\n')\nos.execvp(rest[0], rest)\n")
runtime = ClaudeCodeRuntime(str(claude), d / "state", sudo_executable=str(sudo), leftovers=[str(program)])
agent = AgentDefinition(name="coder", model="sonnet", tools=["Read"], budget_usd=Decimal("1"), instructions="Write.")
own = pwd.getpwuid(os.getuid()).pw_name
for user, status in [("smoke-other", "0"), ("smoke-other", "1"), (own, "1")]:
    plan.write_text(status, encoding="utf-8")
    log.write_text("", encoding="utf-8")
    request = AgentRunRequest(agent=agent, prompt="Stage: doing", allowed_decisions=["doing", "question"], time_limit=timedelta(seconds=30), working_directory=work, environment={"HOME": str(d)}, os_user=user)
    try:
        outcome = runtime.run(request).end_reason
    except AgentRuntimeError as error:
        outcome = error.detail
    name = "own" if user == own else user
    print(name, status, outcome, "|", "; ".join(log.read_text(encoding="utf-8").splitlines()))
EOF
```
Expect: three lines, `smoke-other 0 completed | run in work; program --user smoke-other in /`, then `smoke-other 1 cannot end the agent's processes: factory-leftovers: 1 processes left after 50 rounds: 7 | run in work; program --user smoke-other in /`, then `own 1 completed | run in work`

```bash
uv run -q python - <<'EOF'
import sys

from factory.entry.wiring import leftovers_command

print(leftovers_command() == [sys.executable, "-I", "-m", "factory.entry.leftovers"])
EOF
```
Expect: `True`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
