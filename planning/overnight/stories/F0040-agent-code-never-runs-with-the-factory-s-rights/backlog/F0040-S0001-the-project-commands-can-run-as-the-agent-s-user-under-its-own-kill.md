# The project commands can run as the agent's user, under its own kill

## Description

Today `MakeProjectCommands` starts `make --no-print-directory <command>` as the factory's own user, with the factory's whole environment less three make variables. So `make check`, `lint`, `test`, the reports and the preflight's `lint` run code that agents wrote as the user who can read the hosting token file. This story gives the make class an optional user to run as: with a `CommandUser`, it starts the command through the same chain an agent run uses, `sudo -n -u <user> -- timeout --signal=KILL <limit>s env -i NAME=value ... make --no-print-directory <command>`, built by `launch` of `factory.adapters.agent_launch`. The command then sees only the environment the `CommandUser` names, nothing of the factory's. At the time limit the user's own `timeout` kills the command, because the factory may not signal root's `sudo`; the factory's kill waits 30 seconds longer (`SUDO_GRACE`), as for agent runs. A command killed so is a `time_limit` result. A `sudo` that refuses (only `sudo:` lines and a failing status) is a `ProjectCommandError`, not a red check. Without a `CommandUser` the class runs exactly as today, so every existing test and caller keeps its behaviour. The wiring that hands the instance's agent user to the class, and the seal around each command, are S0002's.

## Interface

`factory.adapters.make_commands` (`adapters`):

```python
class CommandUser(BaseModel):
    """The operating-system user a project command runs as, how to become it, its environment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    os_user: str
    sudo_executable: str
    environment: dict[str, str]


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
- With `user`, a command with an exit status other than 0 whose output holds at least one non-blank line, every non-blank line starting with `sudo:`, raises `ProjectCommandError(command, "<sudo_executable> refused the command: <the last such line>")`. A `sudo:` line beside other output is output like any other line, and a status of 0 is never a refusal.
- The checks of `time_limit` and of the command's name, and an executable that cannot be started (`ProjectCommandError` with the operating system's message), are unchanged and come before anything starts, with or without `user`.
- The class reuses `launch`, `killed_at_limit`, `SUDO_GRACE` and `SUDO_PREFIX` from `factory.adapters.agent_launch` and copies none of them; `agent_launch` still does not import `factory.adapters.process`.
- `user` is the property that returns what the constructor was given.

Tests (the tester writes them): `tests/adapters/test_make_commands_user.py`, with a real `Makefile` in `tmp_path` and a stand-in `sudo` (a script that records its arguments and its environment, and either runs what follows `--` or exits with a planned status and standard-error text), as `tests/adapters/test_claude_runtime_os_user.py` does with `_write_sudo`. The real `timeout` and `env` of the machine run under it. `tests/adapters/test_make_commands.py` is not changed.

## Acceptance criteria

1. With `CommandUser(os_user="agent", sudo_executable=<stand-in>, environment={"PATH": "/usr/bin:/bin", "HOME": <tmp>})` and a target `check` whose recipe is `@echo "home=$$HOME token=$${FACTORY_TOKEN_FILE:-unset}"` then `@echo "check: green"`, run with `time_limit` 30 seconds while the test's own environment sets `FACTORY_TOKEN_FILE` (`monkeypatch.setenv`): the stand-in records the arguments `["-n", "-u", "agent", "--", "timeout", "--signal=KILL", "30s", "env", "-i", "PATH=/usr/bin:/bin", "HOME=<tmp>", "make", "--no-print-directory", "check"]`. The result is `passed`, its `output_tail` holds the line `home=<tmp> token=unset`, and its `targets` hold `check`.
2. The limit's words (rows of one parametrized test, with the stand-in `sudo`): `time_limit` 30 seconds gives `30s`, and 1.5 seconds gives `2s`.
3. The environment's make variables (rows of one parametrized test): a `CommandUser` whose `environment` holds `MAKELEVEL=1`, `MAKEFLAGS=w` or `MFLAGS=-w` besides `PATH` gives arguments without that assignment; `PATH` stays.
4. The kill at the limit: a target `slow` whose recipe is `@sleep 60`, run with the stand-in `sudo` and `time_limit` 3 seconds, gives `status` `time_limit` and `exit_status` `None`, after at least 3 and less than 25 seconds.
5. The exit status 137 (rows of one parametrized test, the stand-in `sudo` exiting at once with a planned status and standard error `boom`): 137 gives `failed` with `exit_status` 137, and 1 gives `failed` with `exit_status` 1, each before the limit of 30 seconds.
6. The refusal (rows of one parametrized test, the stand-in `sudo` exiting with the planned status and standard error and running nothing): status 1 with `sudo: a password is required` raises `ProjectCommandError` whose `detail` is `<stand-in> refused the command: sudo: a password is required`. Status 1 with `sudo: unable to resolve host x` then `sudo: a password is required` raises it with the second line. Status 0 with `sudo: unable to resolve host x` is `passed`. Status 1 with `sudo: unable to resolve host x` then `boom` is `failed` with `exit_status` 1.
7. Before anything starts, with a `CommandUser`: `time_limit` 0 raises `ValueError`, and the command name `Check` raises `ProjectCommandError`, and the stand-in `sudo` records no call (rows of one parametrized test).
8. `MakeProjectCommands(tmp_path).user` is `None`, and `MakeProjectCommands(tmp_path, user=u).user` is `u`.
9. `make check` stays green.
10. docs: `docs/project-guide/processes-and-checks.md`, *Project commands*: the keyword `user` and `CommandUser`, the chain it starts (the same as an agent run's, through `launch`), the environment of the command (only the `CommandUser`'s, less the three make variables), the user's own `timeout` as the kill and the 30 seconds of grace, the `time_limit` result of a command killed by it, the refusal and its `ProjectCommandError`, and that without `user` nothing changes. `docs/project-guide/agents.md`, *The shared launch module*: that the make class also starts its commands through `launch` and `killed_at_limit`. `docs/decisions.md`: none in this story; S0002 writes the entry that replaces *The project commands run as the factory's user and are left for v2*.

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
