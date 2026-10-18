# The nested-repository walk's untested sides

<!-- proposed by feature acceptance of 2026-10-18; refine before promoting -->

## Assignment (as of log entry 1)

F0014-S0010 made `GitCli.remove_nested_repositories()` remove every `.git` below the work tree's root after each agent run. Decision 31 says the walk "does not follow symbolic links, does not enter the root's own `.git` and does not enter a nested `.git` it found". The code keeps all three rules, but no test pins them. In F0014's feature acceptance, `os.walk(root, followlinks=True)` survived, and so did a walk that enters every `.git`. A walk that followed a link would remove the `.git` of whatever folder the link points to, through the link. That includes the checkout's own `.git` through a link to the root, and a repository outside the checkout. The agent can make such a link.

Every test also removes exactly one repository. So the list of two or more paths in the three texts that name them survived a changed separator: the stage's stall detail, the probe item's detail and the preparer's log line.

This story pins these rules. No behaviour is meant to change. If a criterion fails against today's code, that is a finding for the coder.

## Interface

No new names. The rules pinned here are those of today's code:
- `GitCli.remove_nested_repositories() -> list[str]` (`src/factory/adapters/git_cli.py`), with its walk `_nested_repositories(root)`:
  - it does not follow a symbolic link to a folder;
  - it does not enter the root's own `.git`;
  - it does not enter a `.git` it found.

  It returns the removed paths relative to the root, `/`-separated and sorted, as the interface `Git.remove_nested_repositories` (`src/factory/application/git.py`) states.
- The three texts join the paths with `", "`, in the sorted order:
  - `AfterAgent`'s stall detail for `nested_repository` (`src/factory/application/stage.py`), shown in the stall note after `which the factory removed: `;
  - the probe item's detail `the probe run left a git repository in the work tree, which the factory removed: <paths>` (`src/factory/application/preflight.py`);
  - the preparer's log line `removed nested repositories: <paths>` (`src/factory/application/scheduler.py`).

## Acceptance criteria

1. These are new rows of `tests/adapters/test_git_cli_nested.py::test_remove_nested_repositories_removes_and_reports_each_nested_git_entry` (FEATURE decision 34). Its body is unchanged: the returned list, the snapshot of `tmp_path` less the removed paths, the root's `.git`, and `resolve("HEAD")`. The checkout is the module's `directory` fixture, cloned from the `remote` fixture.
   - A symbolic link `mirror` at the root to a folder beside the checkout that holds a repository made by `git init`: returns `[]`. The link stays, and so does the target's `.git`.
   - A symbolic link `self` at the root to the root itself: returns `[]`, and the link stays.
   - A symbolic link `deep/up` to the checkout's parent folder: returns `[]`, and nothing in that folder changes.
2. A folder `.git/extra/.git` inside the root's own `.git`: returns `[]`, and the folder stays. This is a row of the same test.
3. A repository at `notes` whose `.git` holds a folder `modules/m/.git`: returns `["notes/.git"]` only, and `notes/.git` is gone with everything in it. This is a row of the same test.
4. A repository at `a` and another at `a/.cache`: returns `["a/.cache/.git", "a/.git"]`, the sorted order. The walk always meets `a/.git` first, whatever order the file system lists folders in. This is a row of the same test.
5. A stage whose agent leaves repositories at `a` and `b` stalls with the reason `nested_repository`, and its note contains `which the factory removed: a/.git, b/.git`. This is a new test function in `tests/application/test_nested_repositories.py`. It reuses the module's `_nesting` and `_launch`, `_stalled` and `_note` of `application.test_after_agent`, which it imports and does not copy.
6. A probe run that leaves repositories at `a` and `b` fails the item `agent-run-probe` with the detail `the probe run left a git repository in the work tree, which the factory removed: a/.git, b/.git`. This is the row `two-nested` of `test_a_probe_run_that_leaves_a_nested_repository_fails_the_item` (FEATURE decision 34).
7. The preparer, given an existing sealed checkout that holds repositories at `a` and `b`, writes the log line `removed nested repositories: a/.git, b/.git` and does not clone again (the test's file in the work tree stays). This is the row `two-nested` of `test_the_preparer_removes_the_nested_repositories_of_a_kept_checkout` (FEATURE decision 34).
8. `make check` stays green.
9. docs: none. The project guide's row for `remove_nested_repositories()` already says that the walk does not follow links, never enters a `.git` and returns the paths sorted. The operator guide already says that the stall note, the probe's item and the log line name the paths. No rule changes.

## Demo

```bash
uv run python -c "
import subprocess, tempfile
from pathlib import Path
from factory.adapters.git_cli import GitCli
root = Path(tempfile.mkdtemp())
checkout, outside = root / 'checkout', root / 'outside'
for folder in (checkout, outside, checkout / 'b', checkout / 'a'):
    subprocess.run(['git', 'init', '-q', str(folder)], check=True)
(checkout / 'mirror').symlink_to(outside, target_is_directory=True)
(checkout / 'self').symlink_to(checkout, target_is_directory=True)
print(GitCli(checkout).remove_nested_repositories())
print((outside / '.git').is_dir(), (checkout / '.git').is_dir(), (checkout / 'mirror').is_symlink())
"
```
Expect: two lines: `['a/.git', 'b/.git']`, then `True True True`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/adapters/test_git_cli_nested.py tests/application/test_nested_repositories.py tests/application/test_checkout_preparer_seal.py tests/application/test_agent_run_probe.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-18 human: created.
