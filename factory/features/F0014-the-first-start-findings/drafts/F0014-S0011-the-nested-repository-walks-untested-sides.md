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

1. These are new rows of the parametrized test of `remove_nested_repositories()`, in a checkout cloned from the `remote` fixture. In every row the root's `.git` stays and `resolve("HEAD")` still gives the clone's commit:
   - A symbolic link `mirror` at the root to a folder outside the checkout that holds a repository made by `git init`: returns `[]`. The link stays, and the target's `.git` stays.
   - A symbolic link `self` at the root to the root itself: returns `[]`, and the link stays.
   - A symbolic link `deep/up` to the checkout's parent folder: returns `[]`, and nothing outside the checkout changes.
2. A folder `.git/extra/.git` made inside the root's own `.git`: `remove_nested_repositories()` returns `[]`, and the folder stays.
3. A repository at `notes` whose `.git` holds a folder `modules/m/.git`: returns `["notes/.git"]` only, and `notes/.git` is gone with everything in it.
4. Two repositories at `b` and `a`, made in that order: returns `["a/.git", "b/.git"]`, sorted and not in the order they were made.
5. A stage whose agent leaves repositories at `a` and `b` stalls with the reason `nested_repository`. Its note contains `which the factory removed: a/.git, b/.git`.
6. A probe run that leaves repositories at `a` and `b` fails the item `agent-run-probe` with the detail `the probe run left a git repository in the work tree, which the factory removed: a/.git, b/.git`.
7. The preparer, given an existing sealed checkout holding repositories at `a` and `b`, removes both and writes the log line `removed nested repositories: a/.git, b/.git`. It does not clone again.
8. `make check` stays green.
9. docs: none. The operator guide and the decision log already state that the walk does not follow links and that the note names the paths. The rules do not change.

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
