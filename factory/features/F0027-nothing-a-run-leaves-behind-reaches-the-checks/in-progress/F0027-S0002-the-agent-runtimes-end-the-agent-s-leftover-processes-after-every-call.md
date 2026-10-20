---
stage: approval
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 353
comments_read: [6292978197]
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T12:56:51.304918Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T12:56:51.311401Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T12:57:16.777668Z'
  stage: intake
  run: d3a704ff4836470baa997a20dcf16dd8
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T12:57:37.423128Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T13:04:31.476327Z'
  stage: tests
  run: 404645227610452188e7003a563fcea7
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T13:04:52.411497Z'
  stage: doing
- number: 7
  speaker: coder
  kind: question
  at: '2026-10-20T13:12:44.650702Z'
  stage: doing
  run: 7b6ef6cd2c85474bb9ca0d715714cf79
  blocked: question
- number: 8
  speaker: human
  kind: comment
  at: '2026-10-20T14:16:37.866619Z'
  stage: doing
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-20T14:16:56.429719Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-20T14:22:55.305197Z'
  stage: doing
  run: bc6e3e6aa2ae45b79f07e920b0c8303f
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-20T14:23:17.051768Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-20T14:24:29.530329Z'
  stage: review
  run: ab2ad42fc7074a59b37a38b308f02623
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-20T14:24:52.396848Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-20T14:25:09.544112Z'
  stage: doing
  run: 94006955e53142ba9061a32b24248581
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-20T14:25:31.446490Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-10-20T14:31:22.958076Z'
  stage: tests
  run: ff66cb6f80c64672808b18d0c882977b
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-20T14:31:44.364216Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-20T14:37:40.671153Z'
  stage: doing
  run: 90391088889b4238bbe9e59c242ffee2
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-20T14:38:04.534578Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-10-20T14:39:37.981931Z'
  stage: review
  run: 3665e1b83b6c418883f5cf1fb09d3b86
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-20T14:39:59.136469Z'
  stage: docs
- number: 22
  speaker: documenter
  kind: result
  at: '2026-10-20T14:41:15.876075Z'
  stage: docs
  run: 2148f39cd6a14b29954fec85c9c6abec
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-20T14:41:37.398438Z'
  stage: smoke-test
- number: 24
  speaker: smoke-tester
  kind: result
  at: '2026-10-20T14:42:15.367318Z'
  stage: smoke-test
  run: dd48f71186004fd2ac026ec1d06b916b
---

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
11. The opencode runtime keeps a call's own error (rows of one parametrized test, `os_user` `factory-test-other`, the program exiting 1 with a `factory-leftovers:` line, the stand-in `opencode` printing its events). The stand-in `sudo` refusing the run with `sudo: a password is required` raises `AgentRuntimeError` whose `detail` starts with `<sudo> refused the agent run: sudo: a password is required`, and the program was still started. The stand-in `factory-confine` refusing with a `factory-confine:` line raises the wrapper's error, and the program was still started.
12. `make check` stays green.
13. docs: `docs/operator-guide.md`, *The agent runs as a second user*: a paragraph after the one on the command line. After every call of a run as `agent`, the runtime runs `sudo -n -u agent -- /opt/factory/.venv/bin/python -I -m factory.entry.leftovers --user agent` from `/`. It ends every process of `agent` still running, a process started in a new session or with `nohup` included, before the run's temporary folder is removed and before the factory looks at the work tree. The `agent` user must therefore serve agent runs only. An operator's shell opened as `agent` (`docker exec -it -u agent <container> ...`, for `claude setup-token` or an opencode login) is ended by the next agent call, so run it while the instance is stopped. A failure stops the run with the error `cannot end the agent's processes: <line>` (the stage ends with a counted error; at the preflight's probe, `preflight_failed`). A run without `FACTORY_AGENT_USER` ends no processes. The table of morning observations, the row *A `time_limit` under `sudo`*, and the paragraph of the same name: after a run, `ps -o user,pid,ppid,stat,args -U agent` lists no process. `docs/project-guide/agents.md`, *The agent runtime*: `Starters.leftovers`, `leftovers_due`, `leftovers_launch`, `leftovers_fault`, the order after a call (the call, the program, the removal), when the program's result is read, and that a runtime built without `leftovers` starts none. `docs/project-guide/write-guard.md`, *The end of a run's processes*: who starts it and when. `docs/project-guide/watching.md`, *Boundaries*: `build_boundaries`' keyword `end_leftovers` and `leftovers_command()`. `docs/decisions.md`: an entry *Every agent call is followed by the end of the agent's leftover processes*, dated with the story, with the reasons of the feature's decisions 10 to 12, which says that it closes the window F0014 decision 21 left open (a process swapping `.git` after the seal's check).

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
1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: it names concrete modules and signatures (`agent_launch`, both runtimes, `wiring`), and I checked that `sudo_prefix`, `own_identity`, `LEFTOVERS_PREFIX` and `factory.entry.leftovers` already exist (S0001 is in `done/`). Each stated behaviour has a criterion: `leftovers_due` (1), `leftovers_launch` (2), `leftovers_fault` (3), the order of the calls (4, 9), the resume (6), `version()` (5), and `leftovers_command` and `build_boundaries` (10).
   - Criteria: each can be tested by one test function, with exact values. Both sides of each rule have one. For the due rule these are `None` leftovers, `None` user and own user. For the fault rule they are status 0, status 1 with and without a `factory-leftovers:` line, and timed out with and without a status. For the result they are exit 0, 1 and 3. A call's own error that wins is covered for both `sudo` and `factory-confine` (8). A runtime built without `leftovers` is covered in 4. The `end_leftovers` side is covered in 10.
   - Smoke test: the commands are runnable Python snippets with stand-in scripts, and the story needs no paid call. They don't run pytest, so the `-q` rule does not apply. Each `Expect:` line gives the exact output lines or `True`.
   - Architecture: the helpers sit in `adapters.agent_launch`, which the two runtime wrappers use. The keyword is wired only in `entry.wiring`, and the `AgentRuntime` interface does not change. `agent_launch` stays free of `process` imports, which is why `leftovers_fault` takes three plain values.
   - Scope: it matches the feature's S0002 line (agent_launch, both runtimes, wiring). The story needs no change to another story's test (decision 16 says "S0002: none"). It stays out of S0001's program and S0003's git removal.
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1 to 10. They are red on purpose and form the coder's specification.

   - criterion 1: tests/adapters/test_agent_launch_leftovers.py::test_the_program_is_due_only_with_a_program_and_a_user_other_than_the_own
   - criterion 2: tests/adapters/test_agent_launch_leftovers.py::test_the_program_starts_through_sudo_as_the_user_with_an_empty_environment
   - criterion 3: tests/adapters/test_agent_launch_leftovers.py::test_the_program_s_fault_names_its_line_its_status_or_its_time_limit
   - criterion 4: tests/adapters/test_claude_runtime_leftovers.py::test_after_the_call_the_program_runs_as_the_user_from_the_root_before_the_removal
   - criterion 5: tests/adapters/test_claude_runtime_leftovers.py::test_a_run_without_a_user_and_the_version_start_neither_sudo_nor_the_program
   - criterion 6: tests/adapters/test_claude_runtime_leftovers.py::test_a_resumed_run_starts_the_program_after_each_of_its_calls
   - criterion 7: tests/adapters/test_claude_runtime_leftovers.py::test_a_failed_program_after_a_good_call_is_a_runtime_error_after_the_removal
   - criterion 8: tests/adapters/test_claude_runtime_leftovers.py::test_a_call_refused_by_sudo_or_the_wrapper_keeps_its_own_error_and_still_starts_the_program
   - criterion 9: tests/adapters/test_opencode_runtime_leftovers.py::test_after_the_call_the_program_runs_as_the_user_from_the_root_before_the_removal
   - criterion 10: tests/entry/test_wiring_leftovers.py::test_the_built_runtime_starts_the_leftovers_program_unless_it_is_turned_off
   - criteria 11 and 12 (make check, docs) have no test of their own.

   Files created:
   - tests/leftovers_runtime_support.py: shared stand-ins for the two runtime test files. The stand-in `sudo` records its arguments and working directory. When its plan says so it refuses the agent's run with a line, but never the program or the removal; otherwise it runs what follows `--`. The stand-in leftovers program records its arguments and exits with a planned status and standard-error text. `kinds()` sorts each `sudo` record into run, program or removal. `OTHER_USER` is `factory-test-other`. `own_user()` comes from `pwd.getpwuid(os.getuid())`.
   - tests/adapters/test_agent_launch_leftovers.py, tests/adapters/test_claude_runtime_leftovers.py, tests/adapters/test_opencode_runtime_leftovers.py, tests/entry/test_wiring_leftovers.py.

   The runtime tests use the existing stand-ins: `claude_stand_in`, `opencode_stand_in`, and `write_confine` / `run_request` from `confine_support`. They never use the real leftovers command. I changed no earlier test file.

   In criterion 8 the refusal's detail is checked with `startswith`, as the criterion words it for `sudo`. The same check applies to the wrapper's `<confine> refused the agent run: <LINE>`.

   `make test` result: what the test runner could not import:
   - `test_agent_launch_leftovers.py`: `leftovers_due`, `leftovers_fault` and `leftovers_launch` are missing from `factory.adapters.agent_launch`.
   - `test_wiring_leftovers.py`: `leftovers_command` is missing from `factory.entry.wiring`.

   The claude and opencode runtime tests fail with `TypeError`: the runtimes do not take the `leftovers` keyword yet.

   `make lint` is green. The type check was skipped, as the stage says.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/entry/test_wiring_leftovers.py - ImportError while importing test module '/work/checkout/tests/entry/test_wiring_leftovers.py'.
6. factory: started doing as self.
7. coder: Stopped with everything built except one lint finding I am not allowed to fix. `make types` and `make test` are green, including all of this story's new tests. `make lint` is red with `src/factory/entry/wiring.py:236:5: PLR0913 Too many arguments in function definition (6 > 5)`, so `make check` is red.

   Question: the Interface adds `end_leftovers` to `build_boundaries`. That gives it six arguments, and ruff's `max-args` is 5. Existing tests already use `hosting=`, `which=` and `confine_executable=`, and the new test uses `end_leftovers=`, so none of them can be dropped. I see three options:
   - (a) Add `"src/factory/entry/wiring.py" = ["PLR0913"]` to `[tool.ruff.lint.per-file-ignores]` in `pyproject.toml`. This is how the two runtime constructors are already handled (lines 62–63). I tried it and the write guard refused it (`pyproject.toml` is outside my write paths), so this needs your commit or a write path.
   - (b) An inline `# noqa: PLR0913`. I tried this too: `tests/test_process_search.py::test_the_only_suppression_markers_are_the_four_in_the_process_wrapper` fails on it. It would also need your leave under "Not without asking".
   - (c) Change the signature, for example by putting `which`, `confine_executable` and `end_leftovers` into one options model. That changes the Interface and other stories' tests (`test_wiring_boundaries.py`, `test_wiring_login.py`, `test_wiring_confinement.py` and others).

   I would choose (a). Once it is in, nothing else needs to change and the stage can end with `review`.

   What I built (in the working tree):
   - `src/factory/adapters/agent_launch.py`: the new names as specified: `LEFTOVERS_TIME_LIMIT`, `Starters.leftovers`, `leftovers_due`, `leftovers_launch` and `leftovers_fault`. Two additions:
     - `due_leftovers_launch(starters, os_user, own_user) -> Launch | None`, which both runtimes share. It narrows the types after `leftovers_due`.
     - A constant `LEFTOVERS_FAULT`.

     The module still does not import `process`.
   - `src/factory/adapters/claude_runtime.py` and `src/factory/adapters/opencode_runtime.py`:
     - A `leftovers` keyword and property.
     - `_end_leftovers`, which reads `own_identity().user` once per call and starts the program from `/` through `_start`.
     - In `_call` the order is: the call, the program, the removal, the refusal check (the call's own error wins), then the program's fault.
   - `src/factory/entry/wiring.py`: `LEFTOVERS_MODULE`, `leftovers_command()`, and `build_boundaries(..., end_leftovers=True)`, which passes the command to both runtimes through `_agent_runtime`.

   Main choice: I compute the fault right after the program runs but raise it only after the refusal check. I rejected reading the program's result after the refusal check: it gives the same order of processes, but the code would have to keep the `ProcessResult` until then.

   Refactor: I renamed the `_call` local to `leftovers_error`, and replaced the docstrings on the private `_end_leftovers` with a comment.

   Noticed, not touched: `_end_leftovers`, `_remove_temporary_folder` and `_request_of` are near-copies in the two runtimes. That matches the existing duplication, and merging them is beyond this story.
8. 2026-10-20 human: The human's answer (2026-10-20): (a). `main` now holds `"src/factory/entry/wiring.py" = ["PLR0913"]` under `[tool.ruff.lint.per-file-ignores]` in `pyproject.toml` (commit 52cfe595), beside the two runtime constructors. No noqa in the source; nothing else changes. Merge `main` and end with `review`.
9. factory: started doing as self.
10. coder: Picked up the human's answer (a). The branch already holds `main` with the PLR0913 per-file ignore for `src/factory/entry/wiring.py` (commit 52cfe595, merged in f61d08ec), so I did not merge anything. With that ignore in place the code from my last round passes as it is: `make check` is green (`check: green`, test coverage 99.17 %). I changed no code this round.

    What I built (from the last round, now passing all checks):
    - `src/factory/adapters/agent_launch.py`:
      - The names the Interface asks for: `LEFTOVERS_TIME_LIMIT`, `Starters.leftovers`, `leftovers_due`, `leftovers_launch` and `leftovers_fault`.
      - Two additions: the constant `LEFTOVERS_FAULT`, and `due_leftovers_launch`, a shared helper for both runtimes that returns `Launch | None`.
      - The module still does not import `process`.
    - `src/factory/adapters/claude_runtime.py` and `src/factory/adapters/opencode_runtime.py`:
      - A `leftovers` keyword and a `leftovers` property.
      - `_end_leftovers`: it reads `own_identity().user` once per call and starts the program through `_start` from `/`.
      - The order in `_call`: the call, the program, the removal, the call's refusal (the call's own error wins), then the program's fault.
    - `src/factory/entry/wiring.py`: `LEFTOVERS_MODULE`, `leftovers_command()`, and `build_boundaries(..., end_leftovers=True)`, which passes the command through `_agent_runtime` to both runtimes.

    Main choice: the fault is worked out right after the program ends but raised only after the refusal check. The rejected alternative was to keep the program's `ProcessResult` and read it after the refusal check. The processes start in the same order either way, but that version carries a whole result through `_call` for no gain.

    Refactor: I read the diff against `main` again and found nothing to change.

    Description: the journal changed nothing in the task's meaning. The answer only added a lint configuration on `main`.

    Noticed, not touched: `_end_leftovers`, `_remove_temporary_folder` and `_request_of` are near-copies in the two runtimes. The duplication between the runtimes was already there; merging them would be a restructuring beyond this story.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 33 known, 3 gone
11. factory: started review as self.
12. reviewer: 1. criterion 11 added: it needs its test. Where: `## Acceptance criteria` of this work item. What is wrong: `src/factory/adapters/opencode_runtime.py` `_call` has its own copy of the precedence rule from the Interface: a call that `sudo`, the wrapper or the login shell refused keeps its own error, and the program still runs. It raises `refusal` before `leftovers_error`. Criterion 8 pins this rule only for the `claude -p` runtime. Criterion 9 pins only the order and the fault for opencode. So in opencode, swapping the two raises, or skipping the program after a refused call, fails no test. What would fix it: the tester adds the test for criterion 11 to `tests/adapters/test_opencode_runtime_leftovers.py`, with a `sudo` row and a `factory-confine` row in one parametrized test, using `write_sudo(..., refusal=...)` and `write_confine(layout, Played())` as the claude test does. Nothing under `src/` changes. The closing criteria are renumbered to 12 (`make check`) and 13 (docs).

    Checked and found in order:
    - Criteria 1 to 10 each have a test that checks what its criterion says.
    - The fault rule is tested on both sides: status 0 with and without a `sudo:` line; status 1 with and without a `factory-leftovers:` line; timed out with status `None` and with status 0.
    - The due rule is tested on every side: no program, no user, own user and another user.
    - Entry 10 records `check: green` after the coder.
    - I stopped at group 1 and did not report on groups 2 to 5.

    Earlier tests: the diff only adds test files (every test path has status `A`). No test file on `main` was changed, so no leave was needed.
13. factory: started doing as self.
14. coder: Criterion 11 needs only its test, so I changed no code this round. The reviewer added the criterion in entry 12: the opencode runtime keeps a refused call's own error, and the program still runs. It is already in `## Acceptance criteria`, and the closing criteria are now 12 and 13. The code already does what it asks: `_call` in `src/factory/adapters/opencode_runtime.py` raises the refusal before the program's fault, and it starts the program in both cases.

    What the tester needs to add: the test for criterion 11 in `tests/adapters/test_opencode_runtime_leftovers.py`. It should be one parametrized test with a `sudo` row (`write_sudo(..., refusal=...)`) and a `factory-confine` row (`write_confine(layout, Played())`), built like the claude test for criterion 8.

    What I built: unchanged from entry 10 (`src/factory/adapters/agent_launch.py`, `src/factory/adapters/claude_runtime.py`, `src/factory/adapters/opencode_runtime.py`, `src/factory/entry/wiring.py`). The main choice there still stands: the program's fault is worked out right after the program ends but raised only after the call's refusal check. I rejected keeping the whole `ProcessResult` in `_call` until after that check.

    Description: it already holds criterion 11, so I did not rewrite it. Entry 12 changed nothing else in the task's meaning.

    Noticed, not touched: as in entry 10, `_end_leftovers`, `_remove_temporary_folder` and `_request_of` are near-copies in the two runtimes. Merging them would be a restructuring beyond this story.

    I did not run `make check` this round, because no code changed. Entry 10 recorded it green.
15. factory: started tests as self.
16. tester: I wrote the test for criterion 11, which the reviewer added in entry 12 and the coder named in entry 14. The tests for the other criteria have not changed.

    - criterion 11: tests/adapters/test_opencode_runtime_leftovers.py::test_a_call_refused_by_sudo_or_the_wrapper_keeps_its_own_error_and_still_starts_the_program

    How it is built: it is one test with two rows, built like the claude runtime's test for criterion 8.
    - The `sudo` row uses `write_sudo(..., refusal="sudo: a password is required\n")`.
    - The `confine` row uses `write_confine(layout, Played())`.
    - In both rows the stand-in program exits 1 with a `factory-leftovers:` line, and `os_user` is `factory-test-other`.
    - The test checks that `detail` starts with `<refuser> refused the agent run: <line>`, and that the program recorded `["--user", "factory-test-other"]`, so it was still started.

    Change to the existing test: the order test in the same file built its runtime inline. I moved that setup into a private helper, `_runtime(layout, program, *, sudo_refusal, confine_played)`, which both tests now use. That test keeps its name and checks the same thing. I wrote that file myself for this story, so no leave was needed. I changed no test file from another story.

    Files changed: tests/adapters/test_opencode_runtime_leftovers.py. I created no new files.

    Modules the test runner could not import: none. The code is already built, so the new test passes rather than failing first. The coder said as much in entry 14: `_call` in `src/factory/adapters/opencode_runtime.py` already raises the refusal before the program's fault, and starts the program in both cases. `make test` ends `test: green` (coverage 99.17 %), and `make lint` ends `lint: green`.

    `lint`: lint: green (0.0 s)
    `test`: test: green (157.0 s)
17. factory: started doing as self.
18. coder: The tester added the test for criterion 11 in entry 16 (`tests/adapters/test_opencode_runtime_leftovers.py::test_a_call_refused_by_sudo_or_the_wrapper_keeps_its_own_error_and_still_starts_the_program`). It passes against the code as it already was, so I changed no code this round. `make check` is green: `check: green`, test coverage 99.17 %.

    What I built (unchanged since entry 10):
    - `src/factory/adapters/agent_launch.py`:
      - The names the Interface asks for: `LEFTOVERS_TIME_LIMIT`, `Starters.leftovers`, `leftovers_due`, `leftovers_launch` and `leftovers_fault`.
      - Two additions: the constant `LEFTOVERS_FAULT`, and `due_leftovers_launch`, a helper both runtimes share that returns `Launch | None`.
      - The module still does not import `process`.
    - `src/factory/adapters/claude_runtime.py` and `src/factory/adapters/opencode_runtime.py`:
      - A `leftovers` keyword and property.
      - `_end_leftovers`, which reads `own_identity().user` once per call and starts the program from `/` through `_start`.
      - The order in `_call`: the call, the program, the removal, the call's refusal (the call's own error wins), then the program's fault.
    - `src/factory/entry/wiring.py`: `LEFTOVERS_MODULE`, `leftovers_command()`, and `build_boundaries(..., end_leftovers=True)`. It passes the command to both runtimes through `_agent_runtime`.

    Main choice: the program's fault is worked out right after the program ends, but raised only after the refusal check. I rejected keeping the whole `ProcessResult` in `_call` until after that check.

    Refactor: no code changed this round, so there was nothing new to refactor. The diff is the same one I reviewed in entry 10.

    Description: entry 16 changed nothing in the task's meaning, and criterion 11 is already in the description.

    Noticed, not touched: `_end_leftovers`, `_remove_temporary_folder` and `_request_of` are near-copies in the two runtimes. Merging them would be a restructuring beyond this story.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 5 new, 33 known, 3 gone
19. factory: started review as self.
20. reviewer: no findings

    What I checked (round 1). I read the diff myself and did not rely on the work item's account of it.
    - Group 1, acceptance criteria:
      - Criteria 1 to 11 each have a test that checks what the criterion says. Criterion 11, which the round 0 review added, is `tests/adapters/test_opencode_runtime_leftovers.py::test_a_call_refused_by_sudo_or_the_wrapper_keeps_its_own_error_and_still_starts_the_program`. It is one parametrized test with a `sudo` row and a `factory-confine` row. It checks that the refusal's detail starts with `<refuser> refused the agent run: <line>` while the program exits 1, and that the program was still started.
      - Both sides of each stated rule are tested: due (no program, no user, own user, another user), fault (status 0 with and without a `sudo:` line, status 1 with and without a `factory-leftovers:` line, timed out with status `None` and with status 0), the result (exit 0, 1, 3), and `end_leftovers` (default and `False`, for both runtimes).
      - Entry 18 records `check: green` after the coder.
    - Group 2, architecture:
      - The shared helpers are in `factory.adapters.agent_launch`, which still does not import `factory.adapters.process`.
      - Both runtimes start the program only through their own `_start`, from `/`. The program's arguments are a list, with `sudo -n` and an empty environment.
      - The wiring is only in `factory.entry.wiring`. `AgentRuntime` and `AgentRunRequest` are unchanged. No new module calls a command-line tool.
    - Group 3, security: no secrets, and no shell or SQL built from strings. No `nosec` or `nosemgrep` marker and no baseline entry. The only new marker is the ruff `noqa: PLR0913` in a test, which gives its reason (see Notes).
    - Group 4, quality:
      - Public names carry docstrings, and both constructor docstrings and the `build_boundaries` docstring describe the new keyword.
      - I ran `make duplicates`: 5 new.
        - Four are similar code between `claude_runtime` and `opencode_runtime`. Of these, the only duplication this diff adds is the 8-line `_end_leftovers` in each runtime. The other three are earlier copies whose keys moved because lines shifted.
        - The fifth is `ManualWaiter` in `clock.py`, which this diff does not touch.
      - I do not count `_end_leftovers` as a finding. Sharing it would mean `agent_launch` handling a `ProcessResult`, which the Interface rules out (`leftovers_fault` takes three values for that reason). The Interface itself puts the start in each runtime's `_call` through its own `_start`, the same pattern as the existing `_remove_temporary_folder` and `_request_of`.
      - `due_leftovers_launch` tests `None` again only to narrow the types, and its comment says so.
    - Group 5, hygiene:
      - The journal gives the main choice and what was rejected: the fault is worked out after the program ends but raised after the refusal check, rather than keeping the `ProcessResult` until then.
      - The Description matches what was built, and the docs criterion (13) still says what the reader must know.

    Earlier tests: every test path in `git diff --name-status main...HEAD` has status `A`, so no test file on `main` was changed and no leave was needed.

    Notes:
    1. `tests/adapters/test_opencode_runtime_leftovers.py:59`: `# noqa: PLR0913` on the test with five columns. It gives its reason and follows `tests/adapters/opencode_stand_in.py:120` and `:237`. One row model, or fewer columns, would make it unnecessary.
    2. `tests/adapters/test_claude_runtime_leftovers.py:8-9`: imports `BUDGET_STOP` from `test_claude_runtime_login` and `REPLY` from `test_claude_runtime_os_user`, which are other stories' test modules. Under the standing leave, they could move to a shared module under `tests/`.
21. factory: started docs as self.
22. documenter: wrote the documentation criterion 13 asks for. I changed only documents, so I did not run `make check`; the factory's checks after this stage decide. I did not run the smoke test's commands, and the new text rests on the journal, the Interface and the diff, which I read.

    Files changed:
    - `docs/operator-guide.md`:
      - *The agent runs as a second user*: a new paragraph, "The end of the agent's processes", after the one on the command line. It gives the `sudo -n -u agent -- ... factory.entry.leftovers --user agent` command, the order before the removal and the seal, and the two calls of a resumed run. It says the `agent` user must serve agent runs only and that an operator's shell as `agent` is ended by the next call. It gives the error text and its three `<line>` forms, says what happens with no `FACTORY_AGENT_USER` or with the factory's own user, and says that a refused call keeps its own error.
      - Morning observations: a new table row and a new paragraph, "The agent's processes after a run" (`ps -o user,pid,ppid,stat,args -U agent` lists nothing).
    - `docs/project-guide/agents.md`:
      - Both runtime signatures now show `leftovers=None`.
      - The shared launch module's list gains `Starters.leftovers`, `leftovers_due`, `leftovers_launch`, `leftovers_fault` and `due_leftovers_launch`.
      - A new section, "Ending the agent's leftover processes", gives the order in `_call`: the call, the program, the removal, the call's refusal, the program's fault. It says a runtime built without `leftovers` starts none, names the tests, and notes the near-copy helpers.
    - `docs/project-guide/write-guard.md`: replaced "Nothing starts it yet" with who starts the program, when, and what a failure does.
    - `docs/project-guide/watching.md`: *Boundaries* now has the `end_leftovers` keyword, `leftovers_command()` and `LEFTOVERS_MODULE`.
    - `docs/decisions.md`: a new entry, "Every agent call is followed by the end of the agent's leftover processes", dated with the story. It gives the reasons of the feature's decisions 10 to 12 and says it closes the window F0014 decision 21 left open. I took the reasons and the rejected options from the journal and the Description, because I did not have the feature's decision text. The human should check that wording.

    Cross-read and found current against the diff: `docs/project-guide/README.md` (its index line for `write-guard.md` already names the program), the rest of the operator guide's *The agent runtime* sections, and `docs/project-guide/agents.md` outside the new parts. I found no code that contradicts the Interface, so I have no findings for the coder.

    Stale text I noticed and did not touch:
    - The operator guide's opening paragraph (line 3) lists what is built and does not mention this feature. I left it because it is a general summary.
    - The reviewer's two notes (a `noqa: PLR0913` in a test, and shared test constants imported from other stories' test modules) are test matters and not mine.

    `check`: check: green (not run again: passed on tree b8c2cdbccc63 at 2026-10-20T14:34:53Z)
    `secrets`: secrets: green (2.4 s)
    `documents`: documents ok
23. factory: started smoke-test as self.
24. smoke-tester: I ran the two commands under `## Smoke test` from the repository root, exactly as written and in order. Neither starts a server. I changed nothing.

    **Command 1** (the `claude -p` runtime with a stand-in `sudo`, `claude` and leftovers program, run for three requests), exit status 0:

    ```
    smoke-other 0 completed | run in work; program --user smoke-other in /
    smoke-other 1 cannot end the agent's processes: factory-leftovers: 1 processes left after 50 rounds: 7 | run in work; program --user smoke-other in /
    own 1 completed | run in work
    ```

    This met its `Expect:` line: the three lines are identical to the expected ones.

    **Command 2** (`leftovers_command()`), exit status 0:

    ```
    True
    ```

    This met its `Expect:` line (`True`).

    **Against the acceptance criteria:** nothing in the output contradicts a criterion.
    - With a user other than the factory's own, the program runs after the call, from `/`, with `--user <user>` (criteria 4 and 9).
    - When the program exits 1 after a clean call, the run raises `cannot end the agent's processes: <the factory-leftovers: line>` (criterion 7).
    - With the factory's own user, no program starts and the run completes even though the plan said exit 1 (criterion 4).
    - `leftovers_command()` gives `[sys.executable, "-I", "-m", "factory.entry.leftovers"]` (criterion 10).

    The smoke test builds the runtime without `factory-confine`, so no temporary-folder removal appears in the records. That fits the Interface, which removes the folder only when confined. The removal and the other criteria (resume, refused calls, opencode, `build_boundaries`) are not exercised here; the story's tests cover them.

    **Findings:** none.
