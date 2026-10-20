---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 1
pull_request: 357
comments_read: [6297503471, 6297615750, 6298194655]
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-20T18:32:01.120120Z'
  lease_duration: 60
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
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-20T17:56:03.673041Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-10-20T17:59:35.256447Z'
  stage: tests
  run: 1341da8ddf744e1db88bcfd600b6e72b
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-10-20T18:00:54.894419Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T18:01:13.260396Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-10-20T18:03:52.603417Z'
  stage: tests
  run: 4fc54d6de4254eefa8607d4a076403cd
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-20T18:04:13.374294Z'
  stage: doing
- number: 13
  speaker: factory
  kind: crash
  at: '2026-10-20T18:27:14.750353Z'
  stage: doing
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-20T18:27:16.964607Z'
  stage: doing
- number: 15
  speaker: coder
  kind: question
  at: '2026-10-20T18:29:17.507038Z'
  stage: doing
  run: 5e98650ff66a4116b559cf7bc1ffb85c
  blocked: question
- number: 16
  speaker: human
  kind: comment
  at: '2026-10-20T18:30:36.914481Z'
  stage: doing
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-20T18:30:55.149296Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-20T18:31:39.944499Z'
  stage: doing
  run: 3c805c88c44e4ccd8079d73a7cf18cf3
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-20T18:32:01.120120Z'
  stage: tests
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
7. factory: started tests as self.
8. tester: I wrote the tests for every criterion except one row of criterion 9, which I can't write as stated without choosing what it means.

   The question is about criterion 9, the row "a `leftovers` program that does not exist raises `ProjectCommandError` whose `detail` starts with `cannot end the agent's processes: [Errno 2] No such file or directory`".

   The leftovers call is `[<sudo>, "-n", "-u", "agent", "--", <program>, "--user", "agent"]`, so the factory only starts the stand-in `sudo`, and that `sudo` exists. When the program after `--` is missing, the stand-in's `execvp` fails inside the `sudo` process. The factory then sees exit status 1 and a traceback on standard error. `leftovers_fault` turns that into `cannot end the agent's processes: exit status 1`, not `[Errno 2] ...`. A real `sudo` would behave the same way (`sudo: ...: command not found`, status 1). So the factory only gets an `OSError` of its own, and that detail, when the first word of the leftovers launch (the `sudo`) cannot be started. In this setup that same `sudo` has just run the command.

   Options:
   (a) The row means "the leftovers call cannot be started". The test makes `sudo` disappear between the two calls: the `check` recipe removes the stand-in `sudo` file, so the leftovers launch fails with `[Errno 2]` and the expected detail is unchanged. The criterion's words would change to "the stand-in `sudo` removed by the command's recipe before the leftovers call".
   (b) Keep a program that does not exist after a `sudo` that runs it, and expect `cannot end the agent's processes: exit status 1`. That tests `leftovers_fault`'s status branch again, not the start failure.
   (c) Drop the row.
   I would choose (a): it is the only one that tests the Interface rule "a leftovers program that cannot be started raises ... <the operating system's message>".

   Done so far, all in `tests/adapters/test_make_commands_user.py` (created):
   - criterion 1: `test_the_command_runs_through_sudo_timeout_and_env_with_only_the_user_s_environment`
   - criterion 2: `test_the_limit_is_given_to_timeout_in_whole_seconds_rounded_up` (30 s → `30s`, 1.5 s → `2s`)
   - criterion 3: `test_the_outer_make_variables_of_the_user_s_environment_are_left_out` (`MAKELEVEL`, `MAKEFLAGS`, `MFLAGS`)
   - criterion 4: `test_a_command_killed_by_its_own_timeout_is_a_time_limit_result` (no warning / `sudo:` warning)
   - criterion 5: `test_an_exit_before_the_limit_is_a_failed_command_with_its_status` (137, 1)
   - criterion 6: `test_only_sudo_lines_and_a_failing_status_are_a_refusal` (four rows)
   - criterion 7: `test_the_checks_before_the_start_refuse_without_calling_sudo` (limit 0, `Check`) and `test_a_sudo_that_does_not_exist_is_a_project_command_error`
   - criterion 8: `test_the_user_property_returns_what_the_constructor_was_given`
   - criterion 9: `test_a_command_run_as_another_user_is_followed_by_the_leftovers_program`. Its rows are passed, time limit, program fault, failed, refused, the refusal winning over the fault, no leftovers, and the own user. The missing-program row is left out pending this question.
   - criteria 10 and 11 are not tests.

   The stand-in `sudo` is local to the module: it records its arguments, environment and working directory, then plays a warning and either exits as planned or runs what follows `--`. It always runs the leftovers program. That program is `write_program` from `tests/leftovers_runtime_support.py`. I changed no earlier test file.

   `make test`: the module could not be imported, an ImportError for `factory.adapters.make_commands.CommandUser`, which is the failure to expect before the code exists. `make lint` is green.
9. 2026-10-20 human: Answer (2026-10-20): (a). The row means "the leftovers call cannot be started": the `check` recipe removes the stand-in `sudo` before the leftovers call, and the expected detail stays `cannot end the agent's processes: [Errno 2] No such file or directory`. Change the criterion's words to say so. My earlier answer 2 was imprecise; this replaces it.
10. factory: started tests as self.
11. tester: I wrote the missing row of criterion 9 the way the human answered in entry 9 (option a). The row is `leftovers-cannot-start` in `test_a_command_run_as_another_user_is_followed_by_the_leftovers_program`. Its `check` recipe ends with `@rm -f '<stand-in sudo>'`, so the leftovers launch cannot start. The test expects `ProjectCommandError` with a `detail` that starts with `cannot end the agent's processes: [Errno 2] No such file or directory`, and exactly one recorded `sudo` call. To support it, `_write_makefile` gained an optional `removes` path, and `LeftoversRow` gained `removes_sudo` and `whole_detail`, the latter for checking only the start of the detail.

    The human asked for the criterion's words to change. The work item is outside the tester's write paths (`tests/*`), so I did not edit it. Criterion 9's words still say "a `leftovers` program that does not exist". Whoever may write the work item should reword it to: "the stand-in `sudo` removed by the `check` recipe before the leftovers call".

    Mapping, all in `tests/adapters/test_make_commands_user.py`:
    - criterion 1: `test_the_command_runs_through_sudo_timeout_and_env_with_only_the_user_s_environment`
    - criterion 2: `test_the_limit_is_given_to_timeout_in_whole_seconds_rounded_up`
    - criterion 3: `test_the_outer_make_variables_of_the_user_s_environment_are_left_out`
    - criterion 4: `test_a_command_killed_by_its_own_timeout_is_a_time_limit_result`
    - criterion 5: `test_an_exit_before_the_limit_is_a_failed_command_with_its_status`
    - criterion 6: `test_only_sudo_lines_and_a_failing_status_are_a_refusal`
    - criterion 7: `test_the_checks_before_the_start_refuse_without_calling_sudo`, `test_a_sudo_that_does_not_exist_is_a_project_command_error`
    - criterion 8: `test_the_user_property_returns_what_the_constructor_was_given`
    - criterion 9: `test_a_command_run_as_another_user_is_followed_by_the_leftovers_program` (rows: passed, time-limit, program-fault, leftovers-cannot-start, failed, refused, refusal-wins-over-the-fault, no-leftovers, own-user)
    - criteria 10 and 11: no test (`make check`, docs).

    Files: `tests/adapters/test_make_commands_user.py` (created in the earlier run of this stage, extended now). No earlier test file was changed.

    `make test`: the module cannot be imported, an ImportError for `CommandUser` from `factory.adapters.make_commands`. That is the expected failure before the code exists. `make lint` is green.

    `lint`: lint: green (0.6 s)
    `test`: ERROR tests/adapters/test_make_commands_user.py - ImportError while importing test module '/work/checkout/tests/adapters/test_make_commands_user.py'.
12. factory: started doing as self.
13. factory: crash 1: the run of stage doing ended without a result. Its work is discarded back to commit 2a269f88a37eed2ae92923253c2460275795a257.
14. factory: started doing as self.
15. coder: I stopped after implementing the code: 19 of the 27 tests in `tests/adapters/test_make_commands_user.py` pass, and 8 fail. The cause is in the tests, not the code, and I may not edit tests. There are two questions.

    What I built, in `src/factory/adapters/make_commands.py`, left in the working tree:
    - `CommandUser` and the `user` keyword and property.
    - `run` splits into `_run_as_own_user`, which works exactly as before, and `_run_as`. `_run_as` builds the call with `launch` from `factory.adapters.agent_launch`, giving it `user.environment` less the three make variables.
    - At the limit, the result is `time_limit` when `killed_at_limit` says so. A command refused by `sudo` (failing status, every non-blank line starting with `sudo:`, not killed at the limit) raises `<sudo> refused the command: <last line>`.
    - After every started command, the leftovers program runs through `leftovers_launch`, then its result goes to `leftovers_fault`. It runs with `cwd` `/`, and its standard error is kept separate so that `leftovers_fault` can read it. If it cannot start, the error is `cannot end the agent's processes: <OS message>`. A refusal of the command wins over a leftovers fault.
    - Nothing from `agent_launch` is copied.
    - `ruff`, `mypy --strict` on the file and import-linter are green. I did not run `make check`, because it is red on these tests. The refactor pass and the full `make check` are still to do.

    Main choice: I judge the refusal on the merged output, because `merge_stderr` is true for the command. That is how the Interface words it ("whose output holds..."). The alternative I rejected was reusing `call_refusal`: it takes the first `sudo:` line, not the last, and it needs `Starters`.

    Question 1: the leftovers rows fail on this machine (7 rows of `test_a_command_run_as_another_user_is_followed_by_the_leftovers_program`: passed, time-limit, program-fault, leftovers-cannot-start, failed, refused, refusal-wins-over-the-fault).
    - The test uses `os_user="agent"` as the "other" user, but this stage runs as the OS user `agent` (`whoami` prints `agent`). The Interface says no leftovers call is made when `os_user` is `own_identity().user`, so the second `sudo` call never happens (`assert 1 == 2` at `tests/adapters/test_make_commands_user.py:399`).
    - In a scratch copy in `$TMPDIR` where I changed `"agent"` to `"factory-test-other"` (the `OTHER_USER` of `tests/leftovers_runtime_support.py`), all of those rows pass.
    - Options:
      - (a) The tester uses `OTHER_USER` instead of `"agent"` as the other user in the leftovers rows and their expected `sudo` arguments. Criterion 9's words change from `agent` to a user no test runs as.
      - (b) The code ignores the own-user rule. That breaks the Interface and F0027's reason for the rule.
    - I would choose (a).

    Question 2: criterion 1's recipe cannot produce a target.
    - The recipe prints `check: green`, and the criterion expects `targets` to hold `check`. But `target_times` (`factory.domain.checks`) reads only `<target>: green (<seconds> s)` lines, as `make check` prints them.
    - `test_the_command_runs_through_sudo_timeout_and_env_with_only_the_user_s_environment` therefore fails at `tests/adapters/test_make_commands_user.py:162` (`assert [] == ['check']`).
    - Options:
      - (a) The tester changes the recipe's last line to `@echo "check: green (0.1 s)"`, and criterion 1 changes the same way.
      - (b) Drop the `targets` assertion.
      - (c) Widen `target_times` to accept a line without seconds. That changes a domain rule outside this story.
    - I would choose (a).

    Noticed, not touched: criterion 9's words still say "a `leftovers` program that does not exist". The human's answer in entry 9 rewords that. The work item is outside my write paths, so I did not change it.
16. 2026-10-20 human: Answers (2026-10-20):
    1. (a). The leftovers rows use `OTHER_USER` from `tests/leftovers_runtime_support.py` as the other user, in the call and in the expected `sudo` arguments; criterion 9 says "a user no test runs as" instead of `agent`. The own-user rule stays as the Interface states it.
    2. (a). Criterion 1's recipe ends with `@echo "check: green (0.1 s)"`, and the criterion changes the same way; `target_times` stays as it is.
    Both are changes to this story's own new test module. Criterion 9's wording for the missing program follows the answer of entry 9.
17. factory: started doing as self.
18. coder: Per the human's answers in entry 16, two changes to `tests/adapters/test_make_commands_user.py` are needed. (1) In `test_a_command_run_as_another_user_is_followed_by_the_leftovers_program`, replace `"agent"` with `OTHER_USER` from `tests/leftovers_runtime_support.py`, both as the `CommandUser`'s `os_user` and in the expected `sudo` arguments (`-u` and `--user`), in every row except `own-user`. (2) In `test_the_command_runs_through_sudo_timeout_and_env_with_only_the_user_s_environment`, change the recipe's last line from `@echo "check: green"` to `@echo "check: green (0.1 s)"`.

    I changed no code this round. The implementation in `src/factory/adapters/make_commands.py` was committed by the previous doing run, as entry 15 describes. When the tests come back I will run `make test` and then `make check`, and do the refactor pass. Neither has been run on this code yet.

    Not done: I tried to reword the work item's criteria 1 and 9 to match the answers of entries 9 and 16, and the write guard refused it (`PermissionError: [Errno 13]`). I did not try another route. The new wording should be:
    - Criterion 1: the recipe ends with `@echo "check: green (0.1 s)"`.
    - Criterion 9: "a user no test runs as (`OTHER_USER`)" instead of `agent`.
    - Criterion 9: "a leftovers call that cannot be started (the stand-in `sudo` removed by the `check` recipe before the leftovers call)" instead of "a `leftovers` program that does not exist".

    Someone who may write the work item has to make those edits.
19. factory: started tests as self.
