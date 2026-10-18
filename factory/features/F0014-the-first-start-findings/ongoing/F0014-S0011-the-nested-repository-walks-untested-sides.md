---
stage: review
pr: 202
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
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
2. intake: accepted
   - Interface: no new names. It pins three walk rules of `GitCli.remove_nested_repositories()` (no link followed, the root's `.git` not entered, a found `.git` not entered). It also pins the sorted, `/`-separated return and the `", "` join in three named texts (`stage.py`, `preflight.py`, `scheduler.py`). The paths and signatures are concrete.
   - Criteria: each is testable by one test function or one row. Criteria 1 to 4 are rows of one existing parametrized test (decision 34's leave). Criteria 5 to 7 are one new function and two named rows. Each rule has its refused side (links not followed, `.git` not entered) and its passing side (the nested repositories are removed). The sorted-order comment has criterion 4, whose `a/.cache` layout makes the order independent of listing order.
   - Demo: both blocks are runnable. The first has fixed output (`['a/.git', 'b/.git']`, then `True True True`). The second has an `<n> passed` line to check against.
   - Architecture: the story adds tests only and touches no layer. The adapter and application texts it pins are already where `CLAUDE.md` puts them.
   - Scope: it is inside F0014. FEATURE decisions 34 and 36 give the leave for the added rows and name S0011 as tests only. Nothing in the story is listed under "Out of scope". The link case (a link to a repository is not itself a nested one) is decided in 36 (2).
3. tester: added the rows and the test function the criteria name. This story only pins how today's code already behaves, so the new tests pass against it. The branch has no red tests, and that is expected here, not a sign the tests are wrong: one `make test` run ended `test: green (33.6 s)` with 99.47 % coverage, and `make lint` is green.
   - criterion 1: `tests/adapters/test_git_cli_nested.py::test_remove_nested_repositories_removes_and_reports_each_nested_git_entry`, rows `link-to-repository-beside` (link `mirror` to `outside`, a folder beside the checkout made by `git init`), `link-to-root` (link `self`) and `link-to-parent` (link `deep/up` to the checkout's parent). All three expect `[]`. The test's existing snapshot of `tmp_path` shows that the links, the target's `.git` and the parent folder are unchanged.
   - criterion 2: same test, row `git-inside-roots-git` (`.git/extra/.git` folder), expects `[]`.
   - criterion 3: same test, row `git-inside-found-git` (repository at `notes`, folder `notes/.git/modules/m/.git`), expects `["notes/.git"]`. The snapshot shows the whole subtree is gone.
   - criterion 4: same test, row `sorted-dot-folder` (repositories at `a` and `a/.cache`), expects `["a/.cache/.git", "a/.git"]`.
   - criterion 5: `tests/application/test_nested_repositories.py::test_a_stage_whose_agent_leaves_two_repositories_names_both_in_the_stall_note`. It reuses `_nesting`, plus `_launch`, `_stalled`, `_note` and `_completed` imported from `application.test_after_agent`.
   - criterion 6: `tests/application/test_nested_repositories.py::test_a_probe_run_that_leaves_a_nested_repository_fails_the_item`, row `two-nested`.
   - criterion 7: `tests/application/test_nested_repositories.py::test_the_preparer_removes_the_nested_repositories_of_a_kept_checkout`, row `two-nested`. The existing body checks that the test's file stays, so the checkout was not cloned again.
   - New helpers in that module: `_nest_two`, which makes `b` before `a` so the sort is actually exercised, and the constant `TWO_NESTED`.
   Files changed: `tests/adapters/test_git_cli_nested.py`, `tests/application/test_nested_repositories.py`. No files created. No module failed to import. The type check was skipped, as the stage says. For the coder: nothing to implement unless `make check` finds a type problem in these tests.

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (33.9 s)
4. coder: nothing to implement. This story only adds tests that pin how today's code already behaves, and the tester's new rows and test function (`tests/adapters/test_git_cli_nested.py`, `tests/application/test_nested_repositories.py`) pass against the current `GitCli.remove_nested_repositories()` and the three texts that join its paths. I ran `make check` and it ended `check: green`: type check, layers, sast, secrets and licences all pass, `test: green (32.5 s)`, and coverage is 99.47 %. No source change and no commit of my own, so I had no diff to refactor. I left the tests and the docs alone (criterion 9: docs none). I noticed nothing outside the ticket.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
