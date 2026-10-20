---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 362
comments_read: [6300047368, 6300375333]
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-20T20:13:00.141579Z'
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
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-20T20:01:14.995273Z'
  stage: doing
  run: 3043f46ac77e461482df25e27fa07cad
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-20T20:01:37.225727Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-20T20:02:50.540867Z'
  stage: review
  run: 423d1778351543d2ad6520eb5e73611c
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-20T20:03:12.276487Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-20T20:03:23.706620Z'
  stage: doing
  run: c396c95ec24040208e4158c5a1664f09
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-20T20:03:44.283805Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-10-20T20:06:13.559567Z'
  stage: tests
  run: a11c111508e046f0bf6097eb6e0860ec
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-20T20:06:34.374879Z'
  stage: doing
- number: 18
  speaker: coder
  kind: question
  at: '2026-10-20T20:07:18.208494Z'
  stage: doing
  run: 1594f6a87f224e0687cababb8c26fc09
  blocked: question
- number: 19
  speaker: human
  kind: comment
  at: '2026-10-20T20:08:38.340056Z'
  stage: doing
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-20T20:08:56.552238Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-10-20T20:09:28.911300Z'
  stage: doing
  run: 697550a9a820455f9b9c8009ae27eebf
- number: 22
  speaker: factory
  kind: started
  at: '2026-10-20T20:09:53.580798Z'
  stage: tests
- number: 23
  speaker: tester
  kind: result
  at: '2026-10-20T20:12:37.408829Z'
  stage: tests
  run: 26cbc40f015b48d3bc49b824a1df01d6
- number: 24
  speaker: factory
  kind: started
  at: '2026-10-20T20:13:00.141579Z'
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
8. In criterion 6's rows with `agent_user="agent"`, the built `SealedProjectCommands` holds the very `git` and `log` objects the boundaries hold (`boundaries.git`, `boundaries.log`, compared by identity), so the seal is taken on the checkout the commands run in and the log line reaches the factory log.
9. `make check` stays green.
10. docs: `docs/operator-guide.md`: the paragraph **Left for v2.** under the hosting-service token is replaced. Every project command (`make check`, `lint`, `test`, `secrets`, `duplicates`, `documents`, and the preflight's `lint` on `main`) runs as `agent` through `sudo -n -u agent -- timeout --signal=KILL <limit>s env -i ... make --no-print-directory <command>`, with the agent run's environment, `PYTHONDONTWRITEBYTECODE=1` and `UV_LINK_MODE=copy`, so code an agent wrote never runs as `factory` and no output tail can hold the hosting token. The git folder is sealed before every command and checked after it, and every command is followed by the leftovers program as `agent` (**The end of the agent's processes.** says so for project commands too). What stays: the agent's own login files (`/home/agent/.claude-token`, `/home/agent/.anthropic-api-key`) are readable by `agent`, by design, so a test can still print the agent's login into the output tail, as an agent run could write it into its work. In *The agent runs as a second user*, the same chain for project commands, and in *The stops you will see here* or the preflight's section: a missing `sudo` rule now also turns the preflight's `lint` into a `preflight_failed` (`the probe on main could not run: project command lint failed: <sudo> refused the command: ...`). `docs/project-guide/processes-and-checks.md`, *Project commands*: `SealedProjectCommands`, its order and its errors, its log line, and the wiring with and without an agent user. `docs/project-guide/watching.md`, *Boundaries*: what `build_boundaries` builds as project commands. `docs/decisions.md`: the entry *The project commands run as the factory's user and are left for v2* is marked replaced, and a new entry *The project commands run as the agent user, with the git folder sealed*, dated with the story, with the reasons of the feature's decisions 1 to 7.

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
10. coder: Built the sealed project commands and wired them for the agent user. `make check` is green and no test was changed.

    - `src/factory/application/sealed_runs.py`: new class `SealedProjectCommands(ProjectCommands)`. `run` does these steps in order:
      - calls `git.seal()`, then the inner `run`;
      - in a `finally`, calls `check_seal()` and then `remove_nested_repositories()`;
      - writes one log line, `removed nested repositories after <command>: <paths>`, only when something was removed;
      - returns the inner result unchanged.

      Because of the `finally`, an inner error becomes the context of a `RepositoryUnsealed` from the check, and a failed check removes nothing. The module docstring now says "Sealed runs" instead of "Sealed agent runs".
    - `src/factory/entry/wiring.py`:
      - `project_command_environment` is `agent_run_environment` with `PYTHONDONTWRITEBYTECODE=1` and `UV_LINK_MODE=copy` added. It is exported in `__all__`.
      - `build_boundaries` now works out the `sudo` executable and the leftovers program once and passes the same values to both the agent runtime and the new private `_project_commands`.
      - `_project_commands` builds `MakeProjectCommands(settings.checkout)` as before when there is no agent user. With an agent user it builds `SealedProjectCommands(MakeProjectCommands(..., user=CommandUser(...)), git, log)`, using the git and log the boundaries hold.
      - The wrapped objects are plain instance attributes, as the wiring test's `vars()` lookup needs.

    Main choice: `SealedProjectCommands` keeps its own `try/finally`, the same shape as `run_sealed`, and does not share code with it. I rejected pulling a shared "seal around a callable" helper out of `run_sealed`. That function also calls `remove_ignored()` after a run that returned and builds a `SealedRun`, which project commands do neither of, so the shared part would be only the three git calls, and the change would reach into `run_sealed`, which this story does not touch.

    Refactor pass: I read the diff once. The only change was dropping the repeated `which("sudo")` and leftovers expressions in favour of two locals in `build_boundaries`. Nothing else needed changing.

    Noticed but did not touch: `make duplicates` reports 5 new findings, none in the files I changed:
    - four similar-code findings shared by `claude_runtime` and `opencode_runtime` (`due_leftovers_launch`, `call_refusal`, `_end_leftovers`, `version_printed`);
    - dead code: `ManualWaiter` in `adapters/clock.py`.

    It also reports 3 known findings as gone (`ManualClock`, `advance`, `data` in `work_item_markdown`), so `security/duplicates-baseline.txt` is out of date.

    The docs criterion (criterion 9) is left to the docs stage.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 33 known, 3 gone
11. factory: started review as self.
12. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'`: `src/factory/application/sealed_runs.py`, `src/factory/entry/wiring.py` and two new test files. I read them against the work item.

    What holds:
    - **Code:** `SealedProjectCommands.run` seals the git folder, runs the inner command, then calls `check_seal` and `remove_nested_repositories` in a `finally`, as `run_sealed` does. So a failed check removes nothing, and an error from the inner command becomes the context of `RepositoryUnsealed`. The log line is written only when something was removed. `project_command_environment` and the wiring match the Interface.
    - **Criteria 1 to 7:** each has a passing test that checks what the criterion says. The journal reports the coder's `make check` as green.
    - **Architecture:** `sealed_runs` imports only application interfaces and domain types, and only `factory.entry.wiring` wires.
    - **Security:** no silencing markers, no secrets, and no commands built from strings.

    I accept the coder's choice not to share code between `SealedProjectCommands` and `run_sealed`. Only the three git calls would be shared, since `run_sealed` also runs `remove_ignored` and returns a `SealedRun`.

    `make duplicates` reports 5 new findings. All are in files this diff does not touch (`claude_runtime`, `opencode_runtime`, `adapters/clock.py`), so none counts against this story.

    Findings:
    1. criterion 8 added: it needs its test. The Interface says `build_boundaries` builds the `SealedProjectCommands` with "the same `git` and `log` the boundaries hold". No criterion covered this, and `tests/entry/test_wiring_project_command_user.py::test_the_built_project_commands_run_as_the_agent_user_inside_a_seal` checks only `MakeProjectCommands.user`. The current code passes the right objects (`src/factory/entry/wiring.py:266`). But wiring that built a second `GitCli` on another folder, or a second log, would pass every test while sealing the wrong checkout. The fix is for the tester to assert, in the test's agent-user rows, that the sealed object holds `boundaries.git` and `boundaries.log`, compared by identity (for example `_held(sealed, GitCli) is boundaries.git`). No change under `src/` is needed. I added the criterion as 8 and renumbered the closing ones to 9 (`make check`) and 10 (docs).

    Earlier tests: none. The diff only adds test files (`tests/application/test_sealed_project_commands.py`, `tests/entry/test_wiring_project_command_user.py`).
13. factory: started doing as self.
14. coder: Criterion 8 needs a test. In entry 12 the reviewer added criterion 8: the built `SealedProjectCommands` holds the same `git` and `log` objects that the boundaries hold, compared by identity. It needs only its test, so I changed no code.

    - **Code:** `src/factory/entry/wiring.py:266` already passes the boundaries' `git` and `log` to `SealedProjectCommands`. Nothing under `src/` changes.
    - **Test:** the tester should extend `tests/entry/test_wiring_project_command_user.py::test_the_built_project_commands_run_as_the_agent_user_inside_a_seal`. In its rows with `agent_user="agent"` (agent-user, no-leftovers, no-sudo-found), it should assert that the sealed object's held `Git` is `boundaries.git` and its held `FactoryLog` is `boundaries.log`. The reviewer suggested comparing by identity through `_held`, for example `_held(sealed, GitCli) is boundaries.git`.
    - **Description:** entry 12 already changed the Description, adding criterion 8 and renumbering the closing criteria to 9 and 10. I rewrote nothing.
    - **Not touched:** nothing new beyond what entry 10 noted about `make duplicates`.
15. factory: started tests as self.
16. tester: I added the test for criterion 8, which the reviewer added in entry 12 and the coder named in entry 14. I changed no code.

    - criterion 8: `tests/entry/test_wiring_project_command_user.py::test_the_built_project_commands_run_as_the_agent_user_inside_a_seal`. In its three agent-user rows (`agent-user`, `no-leftovers`, `no-sudo-found`) it now also checks `_held(sealed, Git) is boundaries.git` and `_held(sealed, FactoryLog) is boundaries.log`. The `no-agent-user` row returns before those lines, because it has no sealed object.
    - How it finds them: through the test's existing `_held` helper, by the interface types `factory.application.git.Git` and `factory.application.machine.FactoryLog`, not by `GitCli`. That way the check doesn't depend on which implementation the wiring picks. `_held` also requires exactly one held object of each type.
    - Criteria 1 to 7 keep the tests that entry 8 mapped.

    Files changed: `tests/entry/test_wiring_project_command_user.py` (two imports, two assertions). I created no files.

    The test run imported every module. The new test passes now because `src/factory/entry/wiring.py:266` already passes the boundaries' `git` and `log`, so it isn't red. That matches entry 14, which said no code change is needed.

    `make test`: test: green (61.3 s), coverage 99.18 %. `make lint`: lint: green (0.2 s).

    `lint`: lint: green (0.6 s)
    `test`: test: green (60.6 s)
17. factory: started doing as self.
18. coder: Stopped before handing forward: `make check` is red because of the test added for criterion 8, and I may not change tests. No code changed this round. `src/factory/application/sealed_runs.py` and `src/factory/entry/wiring.py` are still as entry 10 left them.

    `make types` fails with:
    ```
    tests/entry/test_wiring_project_command_user.py:96: error: Only concrete class can be given where "type[Git]" is expected  [type-abstract]
    tests/entry/test_wiring_project_command_user.py:97: error: Only concrete class can be given where "type[FactoryLog]" is expected  [type-abstract]
    ```
    The cause is that the helper `_held[T](outer, kind: type[T])` gets the abstract interfaces `Git` and `FactoryLog`, and mypy refuses an abstract class where `type[T]` is expected. The tester ran only `make lint` and `make test`, which is why entry 16 shows green. The test does pass at runtime. Nothing under `src/` can fix a type error inside the test, so the check stays red until the test changes.

    Question: may the tester change the two assertions at lines 96–97 of `test_the_built_project_commands_run_as_the_agent_user_inside_a_seal`? I see three options:
    - (a) Look up the concrete classes: `_held(sealed, GitCli) is boundaries.git` and `_held(sealed, TimestampedFactoryLog) is boundaries.log`. This is the reviewer's own example in entry 12. It ties the test to the implementations the wiring picks, but the test already does that with `MakeProjectCommands`.
    - (b) Check identity without a type: `assert any(value is boundaries.git for value in vars(sealed).values())`, and the same for `boundaries.log`.
    - (c) Loosen `_held`'s parameter to `type[object]` and cast the result. This is the weakest choice, because it loses the typing.

    I would choose (a). If you agree, I will end the next run with `tests`, naming that change, for the tester to make.

    Noticed but did not touch: the `make duplicates` findings that entry 10 recorded.
19. 2026-10-20 human: Answer (2026-10-20): (a). The tester changes lines 96–97 of this story's own `test_the_built_project_commands_run_as_the_agent_user_inside_a_seal` to look up the concrete classes (`_held(sealed, GitCli) is boundaries.git`, `_held(sealed, TimestampedFactoryLog) is boundaries.log`). The tester runs `make check`, not only `make lint` and `make test`, before handing on.
20. factory: started doing as self.
21. coder: No code changed this round, and nothing new was built. `src/factory/application/sealed_runs.py` and `src/factory/entry/wiring.py` are still as entry 10 left them. `make check` stays red only because of the `type-abstract` errors in the test, which entry 18 quoted.

    Test change for the tester, following the human's answer (a) in entry 19: in `tests/entry/test_wiring_project_command_user.py::test_the_built_project_commands_run_as_the_agent_user_inside_a_seal`, change lines 96–97 so they look up the concrete classes instead of the abstract interfaces:
    - `_held(sealed, Git) is boundaries.git` becomes `_held(sealed, GitCli) is boundaries.git`, importing `GitCli` from `factory.adapters.git_cli`.
    - `_held(sealed, FactoryLog) is boundaries.log` becomes `_held(sealed, TimestampedFactoryLog) is boundaries.log`, importing `TimestampedFactoryLog` from `factory.adapters.factory_log`.
    - Drop the `Git` and `FactoryLog` imports if nothing else in the file uses them.

    These are the classes the wiring builds (`src/factory/entry/wiring.py:257` for `GitCli`, `:223` for `TimestampedFactoryLog`), so the identity checks keep passing at runtime and `mypy --strict` accepts them. As entry 19 says, the tester runs `make check` before handing on.

    Main choice: none this round. I hand the test back rather than change it (R9). The alternative, changing the test myself, is not allowed.

    Description: the journal changed no meaning of the task beyond criterion 8, which entry 12 already added, so I rewrote nothing. Noticed but did not touch: the `make duplicates` findings that entry 10 recorded.
22. factory: started tests as self.
23. tester: I made the test change that the human approved in entry 19 and the coder named in entry 21. I changed no code.

    - criterion 8: `tests/entry/test_wiring_project_command_user.py::test_the_built_project_commands_run_as_the_agent_user_inside_a_seal`. Its two identity checks now look up the concrete classes the wiring builds: `_held(sealed, GitCli) is boundaries.git` and `_held(sealed, TimestampedFactoryLog) is boundaries.log`. Before, they looked up the abstract `Git` and `FactoryLog`, which `mypy --strict` refused with `type-abstract`.
    - Imports: I added `GitCli` from `factory.adapters.git_cli` and `TimestampedFactoryLog` from `factory.adapters.factory_log`. I removed the imports of `Git` and `FactoryLog`, because nothing else in the file used them.
    - Criteria 1 to 7 keep the tests that entry 8 mapped.

    Files changed: `tests/entry/test_wiring_project_command_user.py` (imports and two assertions). I created no files. The test run imported every module.

    As entry 19 asked, I ran `make check` and not only `make lint` and `make test`: check: green (test: green (64.4 s), coverage 99.18 %). The test passes now because the code was already right; this change only fixes the type error.

    `lint`: lint: green (0.6 s)
    `test`: test: green (64.3 s)
24. factory: started doing as self.
