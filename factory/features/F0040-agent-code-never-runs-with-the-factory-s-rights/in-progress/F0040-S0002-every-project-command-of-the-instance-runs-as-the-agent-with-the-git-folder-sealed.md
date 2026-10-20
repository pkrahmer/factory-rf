---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 362
comments_read: [6300047368]
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-20T19:57:52.856656Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T19:50:53.841824Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T19:50:53.847043Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-20T19:51:18.574081Z'
  stage: intake
  run: cd1b4e27b6914f36b3782c6e61705eaf
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-20T19:52:37.077355Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-20T19:52:55.086528Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-20T19:53:18.907924Z'
  stage: intake
  run: a949583acd0d4c26ba59460043635f01
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-20T19:53:39.833641Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-20T19:57:31.119987Z'
  stage: tests
  run: 9632f258239b4559bc1a07d57572d3ca
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-20T19:57:52.856656Z'
  stage: doing
---

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
- When `git.seal()` raises `RepositoryUnsealed`, nothing runs and it propagates. When `git.check_seal()` raises `RepositoryUnsealed` (the removal raises none), that error propagates, also over an error of the inner run, which becomes its context (as in `run_sealed`). A `ProjectCommandError` or `ValueError` of the inner run propagates when the seal holds.
- The nested repositories removed are written to the factory log in one line, `removed nested repositories after <command>: <path>, <path>`, the paths as `remove_nested_repositories` gave them (`a/.git`), in its order; no line when there is none. The result is unchanged either way.

`factory.entry.wiring` (`entry`):

```python
def project_command_environment(
    settings: InstanceSettings, base: Mapping[str, str]
) -> dict[str, str]:
    """The environment of a project command run as the agent user: the agent run's, no bytecode, uv copying."""


def build_boundaries(...) -> Boundaries: ...  # signature unchanged
```

- `project_command_environment` is `agent_run_environment(settings, base)` with `PYTHONDONTWRITEBYTECODE` set to `1` and `UV_LINK_MODE` set to `copy`, and nothing else added.
- `build_boundaries` with `settings.agent_user` set builds `RecordingProjectCommands(SealedProjectCommands(MakeProjectCommands(settings.checkout, user=CommandUser(os_user=settings.agent_user, sudo_executable=<the sudo which finds, or SUDO_EXECUTABLE>, environment=project_command_environment(settings, production_environment()), leftovers=leftovers_command() if end_leftovers else None)), git, log), git, records, clock, log)`, the same `git` and `log` the boundaries hold; the leftovers program is the one the agent runtime gets. Without `settings.agent_user` it builds `RecordingProjectCommands(MakeProjectCommands(settings.checkout), ...)` as today. Building starts no process.
- Unchanged: `ProjectCommands`, `RecordingProjectCommands`, `KnownResults`, `Preflight`, the pipeline definition's time limits, `MakeProjectCommands` without a user.

Tests (the tester writes them): `tests/application/test_sealed_project_commands.py`, with a real clone in `tmp_path` (`GitCli`) and a recording `ProjectCommands` of the test's own that inherits the interface and checks the seal while it runs (a group-writable bit set on `.git` before the call is gone during it); `tests/entry/test_wiring_project_command_user.py`, which builds the boundaries with settings with and without `agent_user` and reads the built objects (`MakeProjectCommands.user`). No test starts the real `sudo`.

## Acceptance criteria

1. `SealedProjectCommands(inner, git, log).run("check", time_limit=30 s)` over a real clone whose `.git` was made group-writable before the call: during the inner run `.git` is not group-writable (the inner command checks it), the inner run gets `check` and 30 seconds, and the result is the inner one unchanged.
2. After the run (rows of one parametrized test): an inner run that returns, one that raises `ProjectCommandError` and one that raises `ValueError` are each followed by `check_seal` and `remove_nested_repositories`: the `.git` of a nested repository the inner run made under the checkout (`git init` in a sub-folder) is gone afterwards, and the `ProjectCommandError` and the `ValueError` propagate in their rows.
3. The seal (rows of one parametrized test): when the inner run replaces `.git` with a group-writable copy, `run` raises `RepositoryUnsealed`; when the inner run also raised `ProjectCommandError`, `RepositoryUnsealed` is raised with that error as its `__context__`; in both rows the nested repository the inner run made is still there, because `check_seal` comes first and a failed seal removes nothing. When `.git` is missing before the call, `RepositoryUnsealed` is raised and the inner command was never called.
4. The factory log (rows of one parametrized test): after an inner run that made nested repositories in `a` and `b/c`, the log holds the one line `removed nested repositories after check: a/.git, b/c/.git`; after one that made none, it holds no line from the run.
5. `project_command_environment(settings, {"PATH": "/p", "HOME": "/home/factory", "LANG": "C.UTF-8"})` with `agent_user` `agent` and `agent_home` `/home/agent/.claude` gives `{"PATH": "/p", "HOME": "/home/agent", "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1", "UV_LINK_MODE": "copy"}`; without `agent_user` it gives the same with `HOME` `/home/factory`.
6. The wiring (rows of one parametrized test, `build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())`, `which` answering `/usr/bin/sudo` for `sudo`): with `agent_user="agent"`, `boundaries.project_commands` is a `RecordingProjectCommands` around a `SealedProjectCommands` around a `MakeProjectCommands` whose `user` is `CommandUser(os_user="agent", sudo_executable="/usr/bin/sudo", environment=project_command_environment(settings, production_environment()), leftovers=leftovers_command())`. With `end_leftovers=False`, the user's `leftovers` is `None`. Without `agent_user`, it is a `RecordingProjectCommands` around a `MakeProjectCommands` whose `user` is `None`. With `which` finding no `sudo`, the user's `sudo_executable` is `SUDO_EXECUTABLE`.
7. `SealedProjectCommands` inherits `ProjectCommands`.
8. `make check` stays green.
9. docs: `docs/operator-guide.md`: the paragraph **Left for v2.** under the hosting-service token is replaced. Every project command (`make check`, `lint`, `test`, `secrets`, `duplicates`, `documents`, and the preflight's `lint` on `main`) runs as `agent` through `sudo -n -u agent -- timeout --signal=KILL <limit>s env -i ... make --no-print-directory <command>`, with the agent run's environment, `PYTHONDONTWRITEBYTECODE=1` and `UV_LINK_MODE=copy`, so code an agent wrote never runs as `factory` and no output tail can hold the hosting token. The git folder is sealed before every command and checked after it, and every command is followed by the leftovers program as `agent` (**The end of the agent's processes.** says so for project commands too). What stays: the agent's own login files (`/home/agent/.claude-token`, `/home/agent/.anthropic-api-key`) are readable by `agent`, by design, so a test can still print the agent's login into the output tail, as an agent run could write it into its work. In *The agent runs as a second user*, the same chain for project commands, and in *The stops you will see here* or the preflight's section: a missing `sudo` rule now also turns the preflight's `lint` into a `preflight_failed` (`the probe on main could not run: project command lint failed: <sudo> refused the command: ...`). `docs/project-guide/processes-and-checks.md`, *Project commands*: `SealedProjectCommands`, its order and its errors, its log line, and the wiring with and without an agent user. `docs/project-guide/watching.md`, *Boundaries*: what `build_boundaries` builds as project commands. `docs/decisions.md`: the entry *The project commands run as the factory's user and are left for v2* is marked replaced, and a new entry *The project commands run as the agent user, with the git folder sealed*, dated with the story, with the reasons of the feature's decisions 1 to 7.

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
1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: Questions (the format check passed; the Interface, architecture, scope and smoke test are fine; two Interface rules have no criterion):

   1. The Interface says "A `ProjectCommandError` or `ValueError` of the inner run propagates when the seal holds". Criterion 2 tests `ProjectCommandError` only. `ValueError` has no criterion. Should I add one? Suggested: a row in criterion 2's parametrized test where the inner run raises `ValueError`, which propagates after `check_seal` and the removal. Or should I drop `ValueError` from the Interface?

   2. The Interface says "When `git.check_seal()` or the removal raises `RepositoryUnsealed`, that error propagates". Criterion 3 covers `check_seal` only, through a replaced `.git`. The removal's failure has no criterion. Should I add one, saying what makes `remove_nested_repositories` raise `RepositoryUnsealed` and what the test checks? `GitCli.remove_nested_repositories` (`src/factory/adapters/git_cli.py:396`) raises nothing of the kind. Suggested: drop "or the removal" from the Interface, or add a criterion with a recording `Git` of the test's own whose removal raises `RepositoryUnsealed`.

   3. Criterion 2 says `check_seal` and `remove_nested_repositories` are called "in that order" after the run. No criterion checks that order. Should the criterion 3 row, where the inner run replaces `.git`, also assert that the nested repository is not removed, or that it is? Please state which. Suggested: the order is `check_seal` first, so a failed seal removes nothing.
4. 2026-10-20 human: Answers (2026-10-20):
   1. Add it: a row in criterion 2's parametrized test where the inner run raises `ValueError`, which propagates after `check_seal` and the removal.
   2. Drop "or the removal" from the Interface: `GitCli.remove_nested_repositories` raises no `RepositoryUnsealed`, so only `check_seal` can.
   3. The order is `check_seal` first, as in `run_sealed`'s `finally`: a failed seal removes nothing. Criterion 3's row (the inner run replaces `.git`) also asserts that the nested repository is still there.
5. factory: started intake as self.
6. intake: accepted. I carried the human's answers (journal entry 4) into the story and changed nothing else.
   - Interface: `SealedProjectCommands.run` and `project_command_environment` name concrete modules and signatures. By answer 2, the rule now reads "When `git.check_seal()` raises `RepositoryUnsealed` (the removal raises none), that error propagates". Every rule has a criterion on both sides: seal at the start (3), seal after the run, over an inner error (3), the inner errors propagating (2), the log line and no line (4), the environment with and without `agent_user` (5), and the wiring with and without `agent_user`, `end_leftovers` and `which` (6).
   - Criteria: each fits one test function.
     - Per answer 1, criterion 2 gained a `ValueError` row that propagates after `check_seal` and the removal.
     - Per answer 3, criterion 3's replaced-`.git` rows also assert the nested repository is still there, since `check_seal` comes first and a failed seal removes nothing.
     - Criterion 7 covers the inheritance.
   - Smoke test: it is runnable and calls no pytest, so the `-q` rule does not apply. Its `Expect:` line is checkable: the log line, then `passed [False] False True`.
   - Architecture: `SealedProjectCommands` sits in `factory.application`, which knows only the `ProjectCommands`, `Git` and `FactoryLog` interfaces. The wiring stays in `factory.entry.wiring`, which is the only place that wires.
   - Scope: the story is within F0040's scope, which lists `sealed_runs.py` and `wiring.py` for S0002. It touches none of the out-of-scope items and changes no test another story wrote.
7. factory: started tests as self.
8. tester: Wrote red tests for criteria 1–7 against the Interface. As intended, `make test` stops on two collection errors (ImportError), because the module under test does not exist yet. `make lint` is green.

   - criterion 1: tests/application/test_sealed_project_commands.py::test_the_inner_command_runs_with_a_sealed_git_folder_and_its_result_is_returned
   - criterion 2: tests/application/test_sealed_project_commands.py::test_nested_repositories_are_removed_after_every_inner_run (rows: returns, project-command-error, value-error)
   - criterion 3: tests/application/test_sealed_project_commands.py::test_a_run_raises_unless_git_is_sealed_before_and_after_it (rows: opened-during-the-run, opened-then-project-command-error, missing-before-the-run; the nested repository is still there exactly when the inner command ran)
   - criterion 4: tests/application/test_sealed_project_commands.py::test_the_removed_nested_repositories_are_logged_in_one_line (rows: two-nested, none)
   - criterion 5: tests/entry/test_wiring_project_command_user.py::test_the_project_command_environment_is_the_agent_runs_without_bytecode_and_uv_copying (rows: agent-user, no-agent-user)
   - criterion 6: tests/entry/test_wiring_project_command_user.py::test_the_built_project_commands_run_as_the_agent_user_inside_a_seal (rows: agent-user, no-leftovers, no-sudo-found, no-agent-user)
   - criterion 7: tests/application/test_sealed_project_commands.py::test_sealed_project_commands_implement_the_project_commands_interface
   - criteria 8 and 9: no test; they are `make check` and the docs stage.

   Files created: `tests/application/test_sealed_project_commands.py` and `tests/entry/test_wiring_project_command_user.py`. I changed no earlier test file.

   What the tests use:
   - The inner command is the test's own `ProbeCommands(ProjectCommands)`. It records each call and whether `.git` was group-writable during it, then makes nested repositories with `git_support.run_git` and answers or raises through `project_command_support.raising`.
   - Git is the real `checkout` fixture clone (`GitCli`).
   - The log is `RecordingLog`, imported from `application.test_checkout_preparer_seal` the way `test_nested_repositories.py` already imports it, so no copy was made.

   The Interface names no accessor for the objects `RecordingProjectCommands` and `SealedProjectCommands` wrap. The wiring test therefore finds the wrapped object by type among the wrapper's instance attributes (`vars(outer)`, a local helper `_held`) and does not use private attribute names. The only thing the coder must do for this to work is keep the wrapped `ProjectCommands` as an ordinary attribute, not in `__slots__`.

   Modules the test run could not import: `factory.application.sealed_runs.SealedProjectCommands` and `factory.entry.wiring.project_command_environment`.

   `lint`: lint: green (0.8 s)
   `test`: ERROR tests/entry/test_wiring_project_command_user.py - ImportError while importing test module '/work/checkout/tests/entry/test_wiring_project_command_user.py'.
9. factory: started doing as self.
