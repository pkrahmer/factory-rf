---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 357
comments_read: [6297503471]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T17:53:17.870672Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T17:53:17.876419Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-20T17:53:39.283900Z'
  stage: intake
  run: 76bef9f7888d49d4b58b516b7c704c25
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-20T17:54:58.705534Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-20T17:55:16.703186Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-20T17:55:42.908407Z'
  stage: intake
  run: cacfa625b24b4076ab7f54b2b58e6895
---

# The project commands can run as the agent's user, under its own kill

## Description

Today `MakeProjectCommands` starts `make --no-print-directory <command>` as the factory's own user, with the factory's whole environment less three make variables. So `make check`, `lint`, `test`, the reports and the preflight's `lint` run code that agents wrote as the user who can read the hosting token file. This story gives the make class an optional user to run as: with a `CommandUser`, it starts the command through the same chain an agent run uses, `sudo -n -u <user> -- timeout --signal=KILL <limit>s env -i NAME=value ... make --no-print-directory <command>`, built by `launch` of `factory.adapters.agent_launch`. The command then sees only the environment the `CommandUser` names, nothing of the factory's. At the time limit the user's own `timeout` kills the command, because the factory may not signal root's `sudo`; the factory's kill waits 30 seconds longer (`SUDO_GRACE`), as for agent runs. A command killed so is a `time_limit` result. The user's `timeout` kills only its own process group, and the factory's kill cannot signal the user's processes (F0030's kill leaves them out): a process that left the group, such as a test's child that `run_process` starts in a session of its own, outlives the command. So with a `leftovers` program in the `CommandUser`, every command run as that user is followed by that program, as that user, as every call of an agent runtime is (F0027). A `sudo` that refuses (only `sudo:` lines and a failing status) is a `ProjectCommandError`, not a red check. Without a `CommandUser` the class runs exactly as today, so every existing test and caller keeps its behaviour. The wiring that hands the instance's agent user and the leftovers program to the class, and the seal around each command, are S0002's.

## Interface

`factory.adapters.make_commands` (`adapters`):

```python
class CommandUser(BaseModel):
    """The operating-system user a project command runs as, how to become it, its environment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    os_user: str
    sudo_executable: str
    environment: dict[str, str]
    leftovers: list[str] | None = None


class MakeProjectCommands(ProjectCommands):
    def __init__(
        self,
        directory: Path,
        kill_points: KillPoints | None = None,
        *,
        executable: str = "make",
        user: CommandUser | None = None,
    ) -> None: ...

    @property
    def user(self) -> CommandUser | None:
        """The user the commands run as, or `None` for the factory's own."""
```

- Without `user` (the default) `run` is unchanged: the factory's environment less `MAKELEVEL`, `MAKEFLAGS` and `MFLAGS`, no `sudo`, the factory's own kill at `time_limit`.
- With `user`, `run` starts the `Launch` that `launch([executable, "--no-print-directory", command], environment, os_user=user.os_user, sudo_executable=user.sudo_executable, time_limit=time_limit)` gives, where `environment` is `user.environment` less `MAKELEVEL`, `MAKEFLAGS` and `MFLAGS`. Its words are `[<sudo>, "-n", "-u", <os_user>, "--", "timeout", "--signal=KILL", "<limit>s", "env", "-i", "NAME=value", ..., <executable>, "--no-print-directory", <command>]`, the limit in whole seconds rounded up; the process request has `env` `{}`, `cwd` the directory, `merge_stderr` true and the time limit `time_limit` plus 30 seconds. No variable of the factory's own environment reaches the command.
- With `user`, a command whose `killed_at_limit(os_user=..., exit_status=..., duration=..., time_limit=time_limit)` is true (exit status 137 or -9 after at least `time_limit`) gives `status` `time_limit` and `exit_status` `None`, as one the factory killed itself does. Exit status 137 before `time_limit` is `failed` with `exit_status` 137.
- With `user`, a command that the rule above does not judge `time_limit`, with an exit status other than 0 and whose output holds at least one non-blank line, every non-blank line starting with `sudo:`, raises `ProjectCommandError(command, "<sudo_executable> refused the command: <the last such line>")`. The kill at the limit is judged first: a command killed by its own `timeout` whose only output is a `sudo:` warning (`sudo: unable to resolve host x`) is `time_limit`, not a refusal. A `sudo:` line beside other output is output like any other line, and a status of 0 is never a refusal.
- The checks of `time_limit` and of the command's name, and an executable that cannot be started (`ProjectCommandError` with the operating system's message), are unchanged and come before anything starts, with or without `user`.
- With `user` whose `leftovers` is set and whose `os_user` is not this process's own user (`own_identity().user`), every command that started is followed, whatever its result (passed, failed, `time_limit` or refused), by the `Launch` that `leftovers_launch(user.leftovers, os_user=user.os_user, sudo_executable=user.sudo_executable)` gives, run through `run_process` with `cwd` `/`. When `leftovers_fault(exit_status=..., timed_out=..., stderr=...)` gives a fault, `run` raises `ProjectCommandError(command, <the fault>)`; a refusal of the command itself wins and is raised instead. A leftovers program that cannot be started raises `ProjectCommandError(command, "cannot end the agent's processes: <the operating system's message>")`. Without `leftovers`, or when `os_user` is the own user, no second call is made. `leftovers_fault` is reused as F0027-S0002 tests it (`tests/adapters/test_agent_launch_leftovers.py`, its `timed_out` branch included); this story's tests cover the exit-status fault only and use no stand-in that waits out a time limit.
- The class reuses `launch`, `killed_at_limit`, `SUDO_GRACE`, `SUDO_PREFIX`, `leftovers_launch` and `leftovers_fault` from `factory.adapters.agent_launch` and copies none of them; `agent_launch` still does not import `factory.adapters.process`.
- `user` is the property that returns what the constructor was given.

Tests (the tester writes them): `tests/adapters/test_make_commands_user.py`, with a real `Makefile` in `tmp_path` and a stand-in `sudo` (a script that records its arguments and its environment, and either runs what follows `--` or exits with a planned status and standard-error text), as `tests/adapters/test_claude_runtime_os_user.py` does with `_write_sudo`. The real `timeout` and `env` of the machine run under it. The leftovers program is always a stand-in (`write_program` of `tests/leftovers_runtime_support.py`, which records its arguments and exits with a planned status and standard error), never the real command (`CLAUDE.md`, *Tests*). `tests/adapters/test_make_commands.py` is not changed.

## Acceptance criteria

1. With `CommandUser(os_user="agent", sudo_executable=<stand-in>, environment={"PATH": "/usr/bin:/bin", "HOME": <tmp>})` and a target `check` whose recipe is `@echo "home=$$HOME token=$${FACTORY_TOKEN_FILE:-unset}"` then `@echo "to-stderr" >&2`, then `@echo "check: green"`, run with `time_limit` 30 seconds while the test's own environment sets `FACTORY_TOKEN_FILE` (`monkeypatch.setenv`): the stand-in records the arguments `["-n", "-u", "agent", "--", "timeout", "--signal=KILL", "30s", "env", "-i", "PATH=/usr/bin:/bin", "HOME=<tmp>", "make", "--no-print-directory", "check"]`. The result is `passed`, its `output_tail` holds the line `home=<tmp> token=unset` and the line `to-stderr` (`merge_stderr`), and its `targets` hold `check`.
2. The limit's words (rows of one parametrized test, with the stand-in `sudo`): `time_limit` 30 seconds gives `30s`, and 1.5 seconds gives `2s`.
3. The environment's make variables (rows of one parametrized test): a `CommandUser` whose `environment` holds `MAKELEVEL=1`, `MAKEFLAGS=w` or `MFLAGS=-w` besides `PATH` gives arguments without that assignment; `PATH` stays.
4. The kill at the limit (rows of one parametrized test): a target `slow` whose recipe is `@sleep 60`, run with the stand-in `sudo` and `time_limit` 3 seconds, gives `status` `time_limit` and `exit_status` `None`, after at least 3 and less than 25 seconds; the same with a stand-in `sudo` that first writes `sudo: unable to resolve host x` to standard error and then runs what follows `--` gives `time_limit` too and raises nothing.
5. The exit status 137 (rows of one parametrized test, the stand-in `sudo` exiting at once with a planned status and standard error `boom`): 137 gives `failed` with `exit_status` 137, and 1 gives `failed` with `exit_status` 1, each before the limit of 30 seconds.
6. The refusal (rows of one parametrized test, the stand-in `sudo` exiting with the planned status and standard error and running nothing): status 1 with `sudo: a password is required` raises `ProjectCommandError` whose `detail` is `<stand-in> refused the command: sudo: a password is required`. Status 1 with `sudo: unable to resolve host x` then `sudo: a password is required` raises it with the second line. Status 0 with `sudo: unable to resolve host x` is `passed`. Status 1 with `sudo: unable to resolve host x` then `boom` is `failed` with `exit_status` 1.
7. Before anything starts, with a `CommandUser`: `time_limit` 0 raises `ValueError`, and the command name `Check` raises `ProjectCommandError`, and the stand-in `sudo` records no call (rows of one parametrized test). A `CommandUser` whose `sudo_executable` does not exist raises `ProjectCommandError` whose `detail` starts with `[Errno 2] No such file or directory`.
8. `MakeProjectCommands(tmp_path).user` is `None`, and `MakeProjectCommands(tmp_path, user=u).user` is `u`.
9. The leftovers (rows of one parametrized test, a stand-in `sudo` that runs what follows `--`, a `CommandUser` whose `os_user` is `agent` and whose `leftovers` is a stand-in program): after `check` that passes, the stand-in `sudo` records a second call whose arguments are `["-n", "-u", "agent", "--", *<the stand-in's words>, "--user", "agent"]` and whose working directory is `/`, and the result is `passed`; after `slow` killed at its limit of 3 seconds, the same second call follows and the result is `time_limit`; a stand-in program that exits 1 with `factory-leftovers: 1 processes left after 50 rounds: 7` raises `ProjectCommandError` whose `detail` is `cannot end the agent's processes: factory-leftovers: 1 processes left after 50 rounds: 7`; a `leftovers` program that does not exist raises `ProjectCommandError` whose `detail` starts with `cannot end the agent's processes: [Errno 2] No such file or directory`; after a `failed` command (stand-in `sudo` exiting 1 with `boom`, running nothing) the second call is recorded and the result is `failed`; after a refused command (status 1, `sudo: a password is required`) the second call is recorded too, and the error is the `refused the command` one; when the command is refused and the leftovers stand-in exits 1 with a fault, the error is the `refused the command` one, not the leftovers one; a `CommandUser` without `leftovers`, and one whose `os_user` is the test's own user, make one call only.
10. `make check` stays green.
11. docs: `docs/project-guide/processes-and-checks.md`, *Project commands*: the keyword `user` and `CommandUser`, the chain it starts (the same as an agent run's, through `launch`), the environment of the command (only the `CommandUser`'s, less the three make variables), the user's own `timeout` as the kill and the 30 seconds of grace, the `time_limit` result of a command killed by it, the refusal and its `ProjectCommandError`, the leftovers program after every command run as another user and its fault, and that without `user` nothing changes. `docs/project-guide/agents.md`, *The shared launch module*: that the make class also starts its commands through `launch` and `killed_at_limit`; *Ending the agent's leftover processes*: that a project command run as the agent's user is followed by the same program. `docs/decisions.md`: none in this story; S0002 writes the entry that replaces *The project commands run as the factory's user and are left for v2*.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
FACTORY_TOKEN_FILE=/nowhere uv run python - "$d" <<'EOF'
import json
import sys
from datetime import timedelta
from pathlib import Path

from factory.adapters.make_commands import CommandUser, MakeProjectCommands
from factory.domain.errors import ProjectCommandError

d = Path(sys.argv[1])
(d / "Makefile").write_text('check:\n\t@echo "home=$$HOME token=$${FACTORY_TOKEN_FILE:-unset}"\n\t@echo "check: green"\nslow:\n\t@sleep 60\n', encoding="utf-8")
log = d / "sudo.jsonl"
refuse = d / "refuse"
sudo = d / "sudo"
sudo.write_text(
    f"#!{sys.executable}\nimport json, os, sys\nat = sys.argv.index('--')\n"
    f"open({str(log)!r}, 'a').write(json.dumps(sys.argv[1:]) + '\\n')\n"
    f"if os.path.exists({str(refuse)!r}):\n    sys.stderr.write('sudo: a password is required\\n')\n    sys.exit(1)\n"
    "os.execvp(sys.argv[at + 1], sys.argv[at + 1:])\n",
    encoding="utf-8",
)
sudo.chmod(0o755)
user = CommandUser(os_user="agent", sudo_executable=str(sudo), environment={"PATH": "/usr/bin:/bin", "HOME": str(d)})
commands = MakeProjectCommands(d, user=user)
result = commands.run("check", time_limit=timedelta(seconds=30))
words = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
print(result.status, f"home={d} token=unset" in result.output_tail.splitlines(), words[:7], words[-3:])
result = commands.run("slow", time_limit=timedelta(seconds=3))
print(result.status, result.exit_status, 3 <= result.duration.total_seconds() < 25)
refuse.write_text("", encoding="utf-8")
try:
    commands.run("check", time_limit=timedelta(seconds=30))
except ProjectCommandError as error:
    print(error.detail == f"{sudo} refused the command: sudo: a password is required")
EOF
```
Expect: three lines, `passed True ['-n', '-u', 'agent', '--', 'timeout', '--signal=KILL', '30s'] ['make', '--no-print-directory', 'check']`, then `time_limit None True`, then `True`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: Questions (the format check passed; no findings from it). The Interface states rules that no criterion tests, so two coders could read them differently and both pass:

   1. Interface: "a refusal of the command itself wins and is raised instead" of a leftovers fault. No criterion covers it. Should criterion 9 get a row: sudo refused (status 1, `sudo: a password is required`) with a leftovers stand-in that exits 1 with a fault, expecting `ProjectCommandError` with the `refused the command` detail and not the leftovers one? I would add it.

   2. Interface: "A leftovers program that cannot be started raises `ProjectCommandError(command, "cannot end the agent's processes: <the operating system's message>")`". Criterion 9 only has a stand-in that starts and exits 1. Should a row use a `leftovers` whose program does not exist, expecting a detail that starts with `cannot end the agent's processes: [Errno 2] No such file or directory`? I would add it.

   3. Interface: the leftovers program follows every started command "whatever its result (passed, failed, `time_limit` or refused)". Criterion 9 tests passed and `time_limit` only. Should it also have rows for `failed` (stand-in `sudo` exit 1 with `boom`) and for refused (second `sudo` call recorded even when the command was refused)? I would add both.

   4. Interface: "`leftovers_fault(exit_status=..., timed_out=..., stderr=...)` gives a fault". Criterion 9 tests only the exit-status-1 fault. The `timed_out` branch of the leftovers call is untested. Should a row cover a leftovers stand-in that runs past its limit, or is the exit-status row enough? I would accept the exit-status row alone if you say so, but then the Interface should not suggest more.

   5. Interface: the process request has `env` `{}`, `cwd` the directory, `merge_stderr` true. Only the environment effect (token unset) and the cwd, implicitly through the Makefile, are tested. Should a criterion name a check that `merge_stderr` holds, for example a recipe writing to stderr that appears in `output_tail`? I would add that to criterion 1's recipe or as its own row.

   Everything else I checked is fine: the Interface names concrete modules and signatures. The smoke test commands are runnable, use no pytest, and each `Expect:` line is checkable. The placement in `factory.adapters` fits the architecture, and the story stays inside the feature's scope.
4. 2026-10-20 human: Answers (2026-10-20):
   1. Yes: criterion 9 gains the row where sudo refuses (status 1, `sudo: a password is required`) and the leftovers stand-in exits 1 with a fault; expected `ProjectCommandError` with the `refused the command` detail, not the leftovers one.
   2. Yes: a row with a `leftovers` program that does not exist, expecting a detail that starts with `cannot end the agent's processes: [Errno 2] No such file or directory`.
   3. Yes: rows for `failed` (stand-in `sudo` exits 1 with `boom`) and for refused (the second `sudo` call is recorded even when the command was refused).
   4. The exit-status row is enough. `leftovers_fault`'s `timed_out` branch is F0027-S0002's and is tested in `tests/adapters/test_agent_launch_leftovers.py`; this story reuses it. Make the Interface say so (it reuses `leftovers_fault` as tested there) rather than suggest more, and keep the tests free of a stand-in that waits out a time limit.
   5. Yes: criterion 1's recipe also writes a line to stderr, and that line appears in `output_tail` (`merge_stderr`).
5. factory: started intake as self.
6. intake: accepted, with the human's answers of journal entry 4 carried into the story (their edit, not mine):
   - Interface: line on `leftovers_fault` now says it is reused as F0027-S0002 tests it (`timed_out` branch included), that this story's tests cover the exit-status fault only, and that none uses a stand-in that waits out a time limit (answer 4).
   - Criteria: criterion 1's recipe gains `@echo "to-stderr" >&2` and its expectation the line `to-stderr` in `output_tail` (answer 5). Criterion 9 gains rows for a leftovers program that does not exist (detail starts `cannot end the agent's processes: [Errno 2] No such file or directory`), for `failed` and refused commands (the second call is recorded), and for refused plus a faulting leftovers stand-in (the refusal wins) (answers 1 to 3). Every other rule has a criterion on both sides: the limit rounding, the three make variables, the 137 kill against the early 137, the refusal, the `sudo:` warning beside other output, status 0, the checks before start, the missing sudo, the property, and no second call without `leftovers` or for the own user.
   - Smoke test: runnable, no pytest involved, and the `Expect:` line is checkable. The recipe there is unchanged and still matches its expectation.
   - Architecture: the change sits in `factory.adapters.make_commands` and reuses `agent_launch` (adapters importing adapters, no layer reversed). The class inherits `ProjectCommands`.
   - Scope: within F0040's scope for S0001 (`make_commands.py`, `CommandUser`, the leftovers program) and not in its "Out of scope". The wiring and the seal are S0002's.
