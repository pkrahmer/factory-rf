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

1. `GitCli.remove_ignored()` removes (rows of one parametrized test, a commit holding a `.gitignore` with the lines `.venv/`, `__pycache__/`, `*.pyc`, `.mypy_cache/` and `mutants/`, and `src/mod.py`; each row adds one stand-in and checks that it is gone afterwards): `.venv/lib/python3.12/site-packages/standin.pth`. `src/pkg/__pycache__/mod.cpython-312.pyc` (the whole `__pycache__` folder is gone). `src/stray.pyc`. `.mypy_cache/3.12/standin.json`. `mutants/src/mod.py`. `tests/hidden/conftest.py` beside a new `tests/hidden/.gitignore` holding `*` (the folder `tests/hidden` is gone, `.gitignore` included). `src/secret.py`, which a new `src/.gitignore` holding `secret.py` names. `scratch.log`, which `.git/info/exclude` names. `.venv/src/dep/` holding a repository made by `git init`.
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
