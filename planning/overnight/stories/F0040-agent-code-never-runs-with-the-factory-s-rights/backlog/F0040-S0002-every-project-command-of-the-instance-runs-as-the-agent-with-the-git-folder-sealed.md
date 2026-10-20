# Every project command of the instance runs as the agent, with the git folder sealed

## Description

S0001 let the make class run its commands as another user. This story makes the instance use it. When the instance has an agent user (`FACTORY_AGENT_USER`, `agent` in the image), `build_boundaries` builds the make class with a `CommandUser` for that user, the `sudo` the preflight checks, and the agent run's environment of the instance plus `PYTHONDONTWRITEBYTECODE=1`. So every project command the factory runs (a stage's checks and reports through `KnownResults`, and the preflight's `lint` on `main`) runs as `agent`, who cannot enter the token's folder, and its output tail can no longer hold the hosting token. Each command also runs with the checkout's git folder sealed, as an agent run does: between an agent run and its checks the factory's own git writes group-writable files into `.git` (the undo, the commit), and a command running as `agent` must find `.git` the factory's alone. A new application class, `SealedProjectCommands`, seals the git folder before the command and checks the seal and removes nested repositories after it, as `run_sealed` does for an agent run. Without an agent user (tests, local runs) the wiring builds the project commands exactly as today. The command records, the known results and the commands' time limits are unchanged. Clearing the agent's home before each command is S0004's.

## Interface

`factory.application.sealed_runs` (`application`):

```python
class SealedProjectCommands(ProjectCommands):
    """Runs another implementation's project commands with the checkout's git folder sealed."""

    def __init__(self, inner: ProjectCommands, git: Git, log: FactoryLog) -> None: ...

    @override
    def run(self, command: str, *, time_limit: timedelta) -> CheckResult: ...
```

- `run` calls `git.seal()`, then `inner.run(command, time_limit=time_limit)`, then, also when the run raised, `git.check_seal()` and `git.remove_nested_repositories()`, in that order, and returns the inner result unchanged.
- When `git.seal()` raises `RepositoryUnsealed`, nothing runs and it propagates. When `git.check_seal()` or the removal raises `RepositoryUnsealed`, that error propagates, also over an error of the inner run, which becomes its context (as in `run_sealed`). A `ProjectCommandError` or `ValueError` of the inner run propagates when the seal holds.
- The nested repositories removed are written to the factory log in one line, `removed nested repositories after <command>: <path>, <path>`, the paths as `remove_nested_repositories` gave them (`a/.git`), in its order; no line when there is none. The result is unchanged either way.

`factory.entry.wiring` (`entry`):

```python
def project_command_environment(
    settings: InstanceSettings, base: Mapping[str, str]
) -> dict[str, str]:
    """The environment of a project command run as the agent user: the agent run's, no bytecode."""


def build_boundaries(...) -> Boundaries: ...  # signature unchanged
```

- `project_command_environment` is `agent_run_environment(settings, base)` with `PYTHONDONTWRITEBYTECODE` set to `1`, and nothing else added.
- `build_boundaries` with `settings.agent_user` set builds `RecordingProjectCommands(SealedProjectCommands(MakeProjectCommands(settings.checkout, user=CommandUser(os_user=settings.agent_user, sudo_executable=<the sudo which finds, or SUDO_EXECUTABLE>, environment=project_command_environment(settings, production_environment()))), git, log), git, records, clock, log)`, the same `git` and `log` the boundaries hold. Without `settings.agent_user` it builds `RecordingProjectCommands(MakeProjectCommands(settings.checkout), ...)` as today. Building starts no process.
- Unchanged: `ProjectCommands`, `RecordingProjectCommands`, `KnownResults`, `Preflight`, the pipeline definition's time limits, `MakeProjectCommands` without a user.

Tests (the tester writes them): `tests/application/test_sealed_project_commands.py`, with a real clone in `tmp_path` (`GitCli`) and a recording `ProjectCommands` of the test's own that inherits the interface and checks the seal while it runs (a group-writable bit set on `.git` before the call is gone during it); `tests/entry/test_wiring_project_command_user.py`, which builds the boundaries with settings with and without `agent_user` and reads the built objects (`MakeProjectCommands.user`). No test starts the real `sudo`.

## Acceptance criteria

1. `SealedProjectCommands(inner, git, log).run("check", time_limit=30 s)` over a real clone whose `.git` was made group-writable before the call: during the inner run `.git` is not group-writable (the inner command checks it), the inner run gets `check` and 30 seconds, and the result is the inner one unchanged.
2. After the run (rows of one parametrized test): an inner run that returns, and one that raises `ProjectCommandError`, are each followed by `check_seal` and `remove_nested_repositories`: the `.git` of a nested repository the inner run made under the checkout (`git init` in a sub-folder) is gone afterwards, and the `ProjectCommandError` propagates in the second row.
3. The seal (rows of one parametrized test): when the inner run replaces `.git` with a group-writable copy, `run` raises `RepositoryUnsealed`; when the inner run also raised `ProjectCommandError`, `RepositoryUnsealed` is raised with that error as its `__context__`. When `.git` is missing before the call, `RepositoryUnsealed` is raised and the inner command was never called.
4. The factory log (rows of one parametrized test): after an inner run that made nested repositories in `a` and `b/c`, the log holds the one line `removed nested repositories after check: a/.git, b/c/.git`; after one that made none, it holds no line from the run.
5. `project_command_environment(settings, {"PATH": "/p", "HOME": "/home/factory", "LANG": "C.UTF-8"})` with `agent_user` `agent` and `agent_home` `/home/agent/.claude` gives `{"PATH": "/p", "HOME": "/home/agent", "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}`; without `agent_user` it gives the same with `HOME` `/home/factory`.
6. The wiring (rows of one parametrized test, `build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())`, `which` answering `/usr/bin/sudo` for `sudo`): with `agent_user="agent"`, `boundaries.project_commands` is a `RecordingProjectCommands` around a `SealedProjectCommands` around a `MakeProjectCommands` whose `user` is `CommandUser(os_user="agent", sudo_executable="/usr/bin/sudo", environment=project_command_environment(settings, production_environment()))`. Without `agent_user`, it is a `RecordingProjectCommands` around a `MakeProjectCommands` whose `user` is `None`. With `which` finding no `sudo`, the user's `sudo_executable` is `SUDO_EXECUTABLE`.
7. `SealedProjectCommands` inherits `ProjectCommands`.
8. `make check` stays green.
9. docs: `docs/operator-guide.md`: the paragraph **Left for v2.** under the hosting-service token is replaced. Every project command (`make check`, `lint`, `test`, `secrets`, `duplicates`, `documents`, and the preflight's `lint` on `main`) runs as `agent` through `sudo -n -u agent -- timeout --signal=KILL <limit>s env -i ... make --no-print-directory <command>`, with the agent run's environment and `PYTHONDONTWRITEBYTECODE=1`, so code an agent wrote never runs as `factory` and no output tail can hold the hosting token. The git folder is sealed before every command and checked after it. What stays: the agent's own login files (`/home/agent/.claude-token`, `/home/agent/.anthropic-api-key`) are readable by `agent`, by design, so a test can still print the agent's login into the output tail, as an agent run could write it into its work. In *The agent runs as a second user*, the same chain for project commands, and in *The stops you will see here* or the preflight's section: a missing `sudo` rule now also turns the preflight's `lint` into a `preflight_failed` (`the probe on main could not run: project command lint failed: <sudo> refused the command: ...`). `docs/project-guide/processes-and-checks.md`, *Project commands*: `SealedProjectCommands`, its order and its errors, its log line, and the wiring with and without an agent user. `docs/project-guide/watching.md`, *Boundaries*: what `build_boundaries` builds as project commands. `docs/decisions.md`: the entry *The project commands run as the factory's user and are left for v2* is marked replaced, and a new entry *The project commands run as the agent user, with the git folder sealed*, dated with the story, with the reasons of the feature's decisions 1 to 7.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run python - "$d" <<'EOF'
import stat
import subprocess
import sys
from datetime import timedelta
from pathlib import Path
from typing import override

from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.git_cli import GitCli
from factory.adapters.clock import SystemClock
from factory.application.project_commands import ProjectCommands
from factory.application.sealed_runs import SealedProjectCommands
from factory.domain.checks import CheckResult

d = Path(sys.argv[1])
checkout = d / "checkout"
subprocess.run(["git", "init", "-q", str(checkout)], check=True)
git = GitCli(checkout)
(checkout / ".git").chmod(0o775)
seen: list[bool] = []


class Probe(ProjectCommands):
    @override
    def run(self, command: str, *, time_limit: timedelta) -> CheckResult:
        seen.append(bool((checkout / ".git").stat().st_mode & stat.S_IWGRP))
        subprocess.run(["git", "init", "-q", str(checkout / "nested")], check=True)
        return CheckResult(command=command, status="passed", exit_status=0, duration=timedelta(0), last_line="", output_tail="")


log = TimestampedFactoryLog(d / "factory.log", SystemClock())
result = SealedProjectCommands(Probe(), git, log).run("check", time_limit=timedelta(seconds=30))
print(result.status, seen, (checkout / "nested" / ".git").exists(), (d / "factory.log").read_text(encoding="utf-8").strip().endswith("removed nested repositories after check: nested/.git"))
EOF
```
Expect: two lines, the factory log's own line on standard output, `<UTC time stamp> removed nested repositories after check: nested/.git`, then `passed [False] False True`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
