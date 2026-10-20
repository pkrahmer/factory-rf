---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 355
comments_read: [6293770931, 6294082194]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T14:51:29.564622Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T14:51:29.572073Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-20T14:51:49.232501Z'
  stage: intake
  run: 4f9a20ed0c8b4eff98a707432a740d10
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-20T14:53:10.596018Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-20T14:53:30.859826Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-20T14:54:05.891248Z'
  stage: intake
  run: 13a1c789d6cc4eef8ede8a25d3636424
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-20T14:54:27.414336Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-20T15:02:21.894103Z'
  stage: tests
  run: 43cea450362e46c887bc19beb33c6aca
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-20T15:02:43.317932Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-10-20T15:06:21.296569Z'
  stage: doing
  run: 6de6bf1d786e49b18be61c17e5eba147
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-10-20T15:07:42.103869Z'
  stage: doing
---

# The factory removes the git-ignored files after every agent run and at the restore

## Description

Nothing removes the git-ignored state of the checkout today. The undo does not see it, the result commit does not hold it, and the restore's `git clean -f -d` keeps it. So whatever an agent leaves in `.venv`, `__pycache__`, the tool caches or behind a nested `.gitignore` reaches every later `make check`, unseen in the pull request. This story adds the git operation `remove_ignored()`, which removes every untracked path the ignore rules match, folders whole (`git clean -ffdX`). The factory calls it in two places. The first is `run_sealed`, after the seal's check and the removal of nested repositories, when the run returned. So it comes before the undo and before the same stage's checks, and after the preflight's probe run too. The second is the tick's restore, after `reset_to("HEAD")` and before the switch to `main`, so that a crashed stage's state and anything a branch's own `.gitignore` hid are gone before the next stage and before the preflight's probe of `main`. Tracked files, untracked files that no rule matches (the agent's new files in its write paths) and the repository stay as they are. A path the factory cannot remove raises `GitError`: in the restore that is the existing stop `checkout_restore_failed`. The checks build what they need again: `uv run` creates `.venv` from `uv.lock`. `reset_to`, the undo and the result commit do not change. No ignored folder is kept: mutation testing runs only as sweeps outside the factory, and `make mutants` makes `mutants/` anew each time (the feature's decision 3, answer B).

## Interface

`factory.application.git` (`application`):

```python
class Git(ABC):
    @abstractmethod
    def remove_ignored(self) -> None:
        """Remove every untracked path the ignore rules match, a folder with all it holds.

        Tracked files, untracked paths no rule matches and the repository stay. A path that
        cannot be removed raises `GitError`.
        """
```

- The interface's twenty-fifth operation (F0023-S0001's `work_tree_id` is the twenty-fourth).

`factory.adapters.git_cli` (`adapters`):

- `GitCli.remove_ignored()` runs `git clean --quiet --force --force -d -X` in the working copy through `_run`, so a non-zero exit is a `GitError` whose command is `git clean --quiet --force --force -d -X`. The rules are those git reads: every `.gitignore` in the work tree and `.git/info/exclude`. The second `--force` also removes an ignored folder that holds a repository. A symbolic link is removed as a link and its target is untouched. An empty result is no error.

`factory.application.sealed_runs` (`application`):

- `run_sealed` calls `git.remove_ignored()` after the `try`/`finally` that checks the seal and removes the nested repositories, so only when the run returned and both passed. A run that raised leaves the ignored paths to the next tick's restore, and its error propagates unchanged. A `GitError` of the removal propagates. `SealedRun`, the keyword `run` (F0020-S0007) and every other step stay as they are.

`factory.application.tick` (`application`):

- `Tick._restore_checkout`: the log line of the uncommitted changes, `reset_to("HEAD")`, then `remove_ignored()`, then `checkout("main", start_point="origin/main")` and the deletion of the work items' local branches, as today. A `GitError` of the removal raises the stop `checkout_restore_failed` like every `GitError` of the restore. The restore writes no line for the removed paths, and the log line of the uncommitted changes never names an ignored path (`status()` does not list one).

Unchanged: `reset_to` (it keeps ignored paths, `tests/adapters/test_git_cli_restoring.py`), `UndoService`, `changed_paths`, `commit`, `StageFinisher`, the preflight.

Tests (the tester writes them): `tests/adapters/test_git_cli_ignored.py` (a real local repository in `tmp_path` with a `.gitignore`, as `tests/adapters/test_git_cli_restoring.py` builds one), `tests/application/test_sealed_runs_ignored.py` (`run_sealed` with the fake agent runtime, whose `ScriptedRun.writes` places the stand-in files, and a test-local runtime that writes and then raises, as `SwappingRuntime` in `tests/application/test_sealed_runs.py` does), `tests/application/test_stage_run_ignored.py` (`StageRunner` with `open_story(..., makefile=..., main_files={".gitignore": ...})` from `tests/stage_run_support.py`, as `tests/application/test_stage_run.py` does), `tests/application/test_tick_ignored.py` (the restore, as `tests/application/test_tick.py` does). Every stand-in file is harmless text. Changed under the feature's decision 16, by the tester only and nothing else in those modules: `tests/application/test_git_interface.py` (`OPERATIONS` gains `"remove_ignored"`, and `test_git_has_exactly_the_twenty_four_operations_and_git_cli_has_each` becomes `test_git_has_exactly_the_twenty_five_operations_and_git_cli_has_each`), `tests/application/test_interfaces.py` (the Git test renamed the same way), and `tests/application/test_tick.py::test_the_restore_discards_changes_and_names_them_in_one_line` (`assert (directory / "ignored.log").exists()` becomes `assert not (directory / "ignored.log").exists()`).

## Acceptance criteria

1. `GitCli.remove_ignored()` removes (rows of one parametrized test, a commit holding a `.gitignore` with the lines `.venv/`, `__pycache__/`, `*.pyc`, `.mypy_cache/` and `mutants/`, and `src/mod.py`; each row adds one stand-in and checks that it is gone afterwards): `.venv/lib/python3.12/site-packages/standin.pth`. `src/pkg/__pycache__/mod.cpython-312.pyc` (the whole `__pycache__` folder is gone). `src/stray.pyc`. `.mypy_cache/3.12/standin.json`. `mutants/src/mod.py`. `tests/hidden/conftest.py` beside a new `tests/hidden/.gitignore` holding `*` (the folder `tests/hidden` is gone, `.gitignore` included). `src/secret.py`, which a new `src/.gitignore` holding `secret.py` names. `scratch.log`, which `.git/info/exclude` names. `.venv/src/dep/` holding a repository made by `git init`. A symbolic link `src/stray.pyc` (matched by `*.pyc`) that points to a file outside the repository: afterwards the link is gone and the target file is still there with its content.
2. `GitCli.remove_ignored()` keeps (rows of one parametrized test, the same commit; each row adds one path and checks that it is there afterwards with its content): the tracked `src/mod.py`, also after an edit in the work tree (the edit stays). The tracked `.gitignore`. A new untracked `src/pkg/new.py`. A new `src/.gitignore` holding `secret.py`, which no rule matches. A symbolic link `.mypy_cache` that points to a folder outside the repository with a file in it, which the folder rule `.mypy_cache/` does not match: the link and the target's file both stay. In every row `git status --porcelain` (through `run_git`) is the same before and after the call, and `HEAD` is unchanged.
3. A path the factory cannot remove (rows of one parametrized test): an ignored folder `.venv/locked` of mode `0o555` holding a file makes `remove_ignored()` raise `GitError` whose `command` is `git clean --quiet --force --force -d -X` and whose `exit_status` is 1. The same folder with mode `0o755` is removed and nothing is raised. Without any ignored path the call raises nothing and changes nothing.
4. `run_sealed` (rows of one parametrized test, a checkout whose `main` holds a `.gitignore` with `.venv/`, `__pycache__/` and `*.pyc`). A run that writes `.venv/lib/standin.pth`, `src/__pycache__/a.cpython-312.pyc`, `tests/hidden/.gitignore` (`*`), `tests/hidden/conftest.py` and an untracked `src/new.py`, and returns, leaves only `src/new.py` of them. The result is the run's, and `nested_repositories` is `[]`. A run that also makes a repository at `.venv/dep/.git` gives `nested_repositories == [".venv/dep/.git"]`, and `.venv` is gone. A run that writes the same files and then raises `AgentRuntimeError("boom")` propagates that error, and `.venv/lib/standin.pth` and `tests/hidden/conftest.py` are still there. A run that writes `.venv/locked/x`, closes `.venv/locked` to mode `0o555` and returns makes `run_sealed` raise `GitError` whose `command` is `git clean --quiet --force --force -d -X`, and no `SealedRun` is returned.
5. A stage's checks do not see what its agent hid (rows of one parametrized test, `StageRunner` on a story at its stage with a check `check`, a `Makefile` whose `check` target is `test ! -e <path>`, and `main_files={".gitignore": ".venv/\n"}`). The agent's run writes `.venv/standin.pth` and the check is `test ! -e .venv/standin.pth`: the check is green, the report's `rule` is 6, and the result commit holds no `.venv/standin.pth`. The agent's run writes `<a write path of the stage's role>/standin.txt`, which the undo keeps and no rule ignores, and the check is `test ! -e` of that path: the check is red and the stage stalls with `check_red`.
6. The restore (rows of one parametrized test, `Tick` with the idle handler, as `tests/application/test_tick.py` builds it). A checkout on `main` with `.git/info/exclude` naming `ignored.log` and the file `ignored.log`: after `tick.run()`, `ignored.log` is gone, the tick is not stopped, and the factory log has no line naming `ignored.log`. A checkout on a local work-item branch whose commit holds `src/.gitignore` with `*.dat` and an untracked `src/x.dat`: after `tick.run()` the checkout is on `main` at `origin/main` and `src/x.dat` is gone. A checkout on `main` with `.git/info/exclude` naming `locked/` and a folder `locked` of mode `0o555` holding a file: `tick.run()` returns `stopped="checkout_restore_failed"`, and the stop's detail starts with `git clean --quiet --force --force -d -X failed (exit 1)`.
7. The earlier tests of the feature's decision 16 pass with exactly the changes it names: `OPERATIONS` with `"remove_ignored"` and the two renamed tests, and the restore test with its inverted line.
8. `make check` stays green.
9. docs: `docs/project-guide/git-and-hosting.md`, *Restoring the checkout*: `remove_ignored()`, its command, what it removes and keeps (the nested `.gitignore` files and `.git/info/exclude` included, links as links), its `GitError`, and that `reset_to` still keeps ignored paths. The table *Which feature uses which operation*: a row `remove_ignored` | F0027: after every agent run and at the restore. `docs/project-guide/watching.md`, *The tick*, step 3: `remove_ignored()` between `reset_to("HEAD")` and the switch to `main`, and why in that order (a branch's own `.gitignore`). The paragraph *Every agent run is sealed*: the removal after the check and the nested removal, only when the run returned, and that the preflight's probe run gets it too. `docs/project-guide/write-guard.md`, *The undo*, *Limits*: ignored paths are no longer left. They are removed before the undo by `run_sealed`, and the undo still does not judge them. The passage loses "(left for v2)". `docs/operator-guide.md`: the paragraph after the stops of the repository, "The restore throws away ...": ignored paths are removed too (`.venv`, the caches, `mutants/`, `.reports/`), so do not keep anything in the checkout. The row `checkout_restore_failed`: also an ignored folder the factory cannot empty. *The project's make targets*: the project's commands run on a checkout without any ignored state, so each builds what it needs (factory-rf's and the template's `uv run` create `.venv` from `uv.lock`; the first check after a rebuild of the image downloads the packages once), and a target that relies on an ignored file another stage left fails. The factory removes what an agent's run made there as its own user, through the group, so a project command an agent runs must leave its ignored files group-writable (the container's umask `002`); a stricter umask makes the removal fail with `checkout_restore_failed`. `docs/decisions.md`: an entry *The factory removes the git-ignored paths after every agent run and at the restore*, dated with the story, with the reasons of the feature's decisions 2 and 4 to 7.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
git -C "$d" init -q -b main
printf '.venv/\n__pycache__/\n' > "$d/.gitignore"
mkdir -p "$d/src" && echo 'x = 1' > "$d/src/mod.py"
git -C "$d" add -A && git -C "$d" -c user.name=t -c user.email=t@example.com commit -q -m base
mkdir -p "$d/.venv/lib/python3.12/site-packages" "$d/src/__pycache__" "$d/tests/hidden"
echo standin > "$d/.venv/lib/python3.12/site-packages/standin.pth"
echo standin > "$d/src/__pycache__/mod.cpython-312.pyc"
printf '*\n' > "$d/tests/hidden/.gitignore"
echo standin > "$d/tests/hidden/conftest.py"
echo 'y = 2' > "$d/src/new.py"
uv run -q python - "$d" <<'EOF'
import sys
from pathlib import Path

from factory.adapters.git_cli import GitCli

root = Path(sys.argv[1])
GitCli(root).remove_ignored()
print(sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and path.relative_to(root).parts[0] != ".git"))
EOF
```
Expect: `['.gitignore', 'src/mod.py', 'src/new.py']`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run -q python - "$d" <<'EOF'
import dataclasses
import subprocess
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.sealed_runs import run_sealed
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest, AgentRunResult
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries

d = Path(sys.argv[1])


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args], cwd=cwd, check=True, capture_output=True)


git(d, "init", "-q", "--bare", "--initial-branch=main", "remote.git")
git(d, "clone", "-q", str(d / "remote.git"), "human")
(d / "human" / ".gitignore").write_text(".venv/\n__pycache__/\n", encoding="utf-8")
(d / "human" / "src").mkdir()
(d / "human" / "src" / "mod.py").write_text("x = 1\n", encoding="utf-8")
git(d / "human", "add", "-A")
git(d / "human", "commit", "-q", "-m", "base")
git(d / "human", "push", "-q", "origin", "main")
git(d, "clone", "-q", str(d / "remote.git"), "checkout")
checkout = d / "checkout"
settings = InstanceSettings(repository_url="https://github.com/example/project.git", instance="self", checkout=checkout, state_directory=d / "state", agent_home=d / "agents-home")
runtime = FakeAgentRuntime()
writes = {".venv/lib/standin.pth": "standin\n", "src/__pycache__/mod.cpython-312.pyc": "standin\n", "tests/hidden/.gitignore": "*\n", "tests/hidden/conftest.py": "standin\n", "src/new.py": "y = 2\n"}
runtime.queue(ScriptedRun(writes=writes, result=AgentRunResult(end_reason="completed", decision="doing", entry="Done.", duration=timedelta(seconds=1))))
boundaries = dataclasses.replace(build_boundaries(settings, "unused", hosting=FakeHostingService()), agent_runtime=runtime)
agent = AgentDefinition(name="coder", model="sonnet", tools=["Read"], budget_usd=Decimal("1"), instructions="Write.")
request = AgentRunRequest(agent=agent, prompt="Stage: doing", allowed_decisions=["doing", "question"], time_limit=timedelta(seconds=30), working_directory=checkout, environment={})
sealed = run_sealed(boundaries, request)
left = sorted(path.relative_to(checkout).as_posix() for path in checkout.rglob("*") if path.is_file() and path.relative_to(checkout).parts[0] != ".git")
print(sealed.result.end_reason, sealed.nested_repositories, left)
EOF
```
Expect: `completed [] ['.gitignore', 'src/mod.py', 'src/new.py']`

```bash
grep -c 'left for v2' docs/project-guide/write-guard.md || true
```
Expect: `0`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: 1. The Interface says "A symbolic link is removed as a link and its target is untouched" for `GitCli.remove_ignored()`, and no criterion tests that. Criterion 1 has no row with a symbolic link that an ignore rule matches. Criterion 2 only covers a link that no rule matches (`.mypy_cache` against the folder rule `.mypy_cache/`), which stays. Two coders could read the clause differently and both pass the tests. Options: (a) add a row to criterion 1: a symbolic link `src/stray.pyc` (matched by `*.pyc`) that points to a file outside the repository. Afterwards the link is gone and the target's file is still there with its content. (b) Drop the sentence from the Interface. I would choose (a).

   Everything else checks out:
   - Interface: it names the modules and signatures.
   - Criteria: apart from question 1, every clause has its own test, on the failing side as well. The failing side is the mode `0o555` folder in criteria 3, 4 and 6, and the raised run in criterion 4. The empty case is the third row of criterion 3.
   - Smoke test: the commands are runnable, and no pytest command is involved, so there is no `-q` issue. Each Expect line can be checked against the output.
   - Architecture and scope: both are within the layers in CLAUDE.md and within the feature's scope.

   Format check: passed.
4. 2026-10-20 human: Answer (2026-10-20): (a). Criterion 1 gains a row: a symbolic link `src/stray.pyc` (matched by `*.pyc`) that points to a file outside the repository; afterwards the link is gone and the target file is still there with its content. The Interface's sentence stays.
5. factory: started intake as self.
6. intake: accepted
   - Interface: `Git.remove_ignored()` in `factory.application.git`, `GitCli.remove_ignored()`, `run_sealed` and `Tick._restore_checkout` are named with signatures and the exact git command. Checked against the human's answer in journal entry 4 (a): I wrote exactly that into criterion 1, a new last row. It is a symbolic link `src/stray.pyc`, matched by `*.pyc`, that points to a file outside the repository. Afterwards the link is gone and the target file is still there with its content. The Interface sentence stays as it was. Nothing else in the story changed.
   - Criteria: every clause now has a test, on the failing side too. The failing side is the `0o555` folder in criteria 3, 4 and 6, and the raised run in criterion 4. The empty case is in criterion 3. The links are covered on both sides: a matched link is removed (criterion 1), an unmatched link stays (criterion 2). The restore (criterion 6), the order of the checks (criterion 5) and the earlier tests that change (criterion 7) each have a criterion. Each criterion fits one test function, or one parametrized test.
   - Smoke test: the commands are runnable and none runs pytest, so there is no `-q` issue. Each `Expect:` line can be checked against the output.
   - Architecture: the new operation is an abstract method of the `Git` ABC in `application`, implemented in `adapters.git_cli` through `_run`. The sealed run and the tick call it only through the interface. This agrees with the layers in `CLAUDE.md`.
   - Scope: it matches S0003 in the feature's Scope, and it touches nothing under Out of scope. The test changes it names are the ones feature decision 16 allows.
7. factory: started tests as self.
8. tester: I wrote the tests for every acceptance criterion. Criterion → test:
   - criterion 1: tests/adapters/test_git_cli_ignored.py::test_remove_ignored_removes_every_untracked_path_the_rules_match (10 rows: venv, pycache-folder, pattern, mypy-cache, mutants, nested-gitignore-hides-itself, nested-gitignore, info-exclude, nested-repository, link-as-link. Every row also checks that the outside target file keeps its content.)
   - criterion 2: tests/adapters/test_git_cli_ignored.py::test_remove_ignored_keeps_tracked_and_unmatched_paths (5 rows: tracked-edit, tracked-gitignore, new, new-gitignore, unmatched-link. Each row compares `git status --porcelain` and HEAD before and after.)
   - criterion 3: tests/adapters/test_git_cli_ignored.py::test_remove_ignored_raises_git_error_for_a_path_it_cannot_remove (rows: 0o555 → GitError with command `git clean --quiet --force --force -d -X` and exit 1; 0o755 → removed; nothing ignored → work tree and status unchanged)
   - criterion 4: tests/application/test_sealed_runs_ignored.py::test_a_returned_run_leaves_no_ignored_path_and_a_raised_one_leaves_them (rows: returned, nested-repository, raised, unremovable. A test-local `ThenRuntime` lets the fake runtime write through `ScriptedRun.writes`, then makes the nested repository, raises `AgentRuntimeError("boom")` or locks `.venv/locked`.)
   - criterion 5: tests/application/test_stage_run_ignored.py::test_the_checks_do_not_see_what_the_agent_hid (story at stage `doing`, role coder, whose `check` is `test ! -e <path>`. Rows: ignored → rule 6, no stall, path not in the result commit; in-write-path `src/standin.txt` → stall `check_red`.)
   - criterion 6: tests/application/test_tick_ignored.py::test_the_restore_removes_the_ignored_paths (rows: info-exclude, branch-gitignore, unremovable. The last checks `stopped="checkout_restore_failed"` and that the stop's detail starts with `git clean --quiet --force --force -d -X failed (exit 1)`.)
   - criterion 7: these are the edits feature decision 16 allows, and nothing else in those modules:
     - tests/application/test_git_interface.py: `OPERATIONS` gains `"remove_ignored"`; the test is renamed to test_git_has_exactly_the_twenty_five_operations_and_git_cli_has_each.
     - tests/application/test_interfaces.py: renamed to test_git_abstract_methods_are_exactly_its_twenty_five_operations.
     - tests/application/test_tick.py::test_the_restore_discards_changes_and_names_them_in_one_line: the assertion is now `assert not (directory / "ignored.log").exists()`.
   - criteria 8 and 9 (`make check` stays green, and docs) are not tests.

   The rows that need a folder of mode 0o555 are skipped under root, as the existing restore test does. Each test sets the folder's mode back to 0o755 in a `finally`.

   Files created: tests/adapters/test_git_cli_ignored.py, tests/application/test_sealed_runs_ignored.py, tests/application/test_stage_run_ignored.py, tests/application/test_tick_ignored.py.

   Import failures: none. `factory.application.git` and `factory.adapters.git_cli` both import. The tests fail because `remove_ignored` does not exist and nothing removes the ignored paths yet. In the one `make test` run, for example, the tick rows failed with `assert not True` (the ignored file is still there) and `assert None == 'checkout_restore_failed'`, and the restore test fails on its inverted line. `make lint` is green, after `ruff format` re-wrapped two lines in test_tick_ignored.py.

   Nothing needed interpreting, and nothing is open.

   `lint`: lint: green (0.0 s)
   `test`: FAILED tests/application/test_tick.py::test_the_restore_discards_changes_and_names_them_in_one_line - AssertionError: assert not True
9. factory: started doing as self.
10. coder: I wrote the code, but `make check` is red because of one test that cannot pass. I did not change that test.

    The failing test is `tests/application/test_sealed_runs_ignored.py::test_a_returned_run_leaves_no_ignored_path_and_a_raised_one_leaves_them[raised]`. Line 154 asserts `str(error.value) == "boom"`. But `AgentRuntimeError.__init__` (`src/factory/domain/errors.py:90`) passes `f"agent runtime failed: {detail}"` to its base class. `tests/domain/test_errors.py::test_agent_runtime_error_names_its_detail` pins that text: `str(error) == "agent runtime failed: boom"`. From the `make test` run:
    ```
        assert str(error.value) == "boom"
    E   AssertionError: assert 'agent runtime failed: boom' == 'boom'
    ```
    The rest of that row already passes. The error propagates unchanged and its type matches. `.venv/lib/standin.pth` and `tests/hidden/conftest.py` are still there. Every other new test and every changed test passes. Lint, types and layers are green.

    Options:
    - (a) The tester changes line 154 to `assert error.value.detail == "boom"`. That checks the error the run raised, with the detail the criterion names.
    - (b) The tester changes line 154 to `assert str(error.value) == "agent runtime failed: boom"`.
    - (c) Change `AgentRuntimeError` so its text is the bare detail. That breaks the earlier `test_errors.py` test and every message built on that text.

    I would choose (a). Once you answer, I end the next round with `tests` and name that one line.

    What I built:
    - `src/factory/application/git.py`: the abstract `Git.remove_ignored()`, with the Interface's docstring.
    - `src/factory/adapters/git_cli.py`: `GitCli.remove_ignored()`, which runs `clean --quiet --force --force -d -X` through `_run`, so a non-zero exit is a `GitError` with that command.
    - `src/factory/application/sealed_runs.py`: `run_sealed` calls `git.remove_ignored()` after the `try`/`finally`. So it runs only when the run returned and both the seal check and the nested removal passed. A run that raised leaves its ignored paths to the restore.
    - `src/factory/application/tick.py`: `_restore_checkout` calls `remove_ignored()` between `reset_to("HEAD")` and the switch to `main`. Its `GitError` reaches the existing `checkout_restore_failed` handler.

    Main choice: I put the removal after the `finally` block instead of inside it. Inside, it would also run after a raised run. The Interface leaves that case to the restore, and a second git error inside `finally` would hide the run's own error. I did not consider removing the paths from Python, as `remove_nested_repositories` does. The Interface asks for git's own rules: every nested `.gitignore` and `.git/info/exclude`.

    Refactor: I read the diff and found nothing to change. The only edit was shortening the docstring of `run_sealed`, which was over the line limit.

    Noticed but not touched: nothing.
11. 2026-10-20 human: Answer (2026-10-20): (a). The tester changes line 154 of this story's own `tests/application/test_sealed_runs_ignored.py` to `assert error.value.detail == "boom"`; nothing else changes, and `AgentRuntimeError` keeps its text.
