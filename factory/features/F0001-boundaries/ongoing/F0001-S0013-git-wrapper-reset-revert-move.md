---
stage: doing
pr: 13
blocked: null
comments_seen: 2
round: 1
attempts: 0
---
# The git wrapper: reset, revert and move

## Assignment (as of log entry 6)

Finish the writing half of the git wrapper (R9): reset the work tree to a ref and clean it, revert chosen paths to their content at a commit, and move a file. These are the steps that later features build on: a stall or a crash reverts or resets (F0004, F0005, F0008), the tick resets the checkout to the remote (F0006), a merge or a discard moves the story file (F0007). With this story the `Git` protocol has the nineteen operations R9 asks for, and a test proves that `GitCli` has each of them and the protocol no other. This story and S0012 were split from one story to keep each within 26 criteria. Covers R9; keeps kept thing 13 (recover by construction: reset and clean make the checkout disposable) and kept thing 5 (the undo's revert is the wrapper's, the rules for what to revert are F0004's). Per the human's answer in log entry 6, `move` follows the same path rule as `revert_paths`, so no folder is created outside the checkout. The closing criterion needs the operations of S0011, which comes before this story in id order.

## Interface

`src/factory/application/git.py` (adds three operations to `Git`, which now has nineteen)

```python
    def reset_to(self, ref: str) -> None: ...
    def revert_paths(self, commit: str, paths: Sequence[str]) -> None: ...
    def move(self, source: str, destination: str) -> None: ...
```

The rules, each with a criterion below:

- `reset_to(ref)` runs `git reset --hard <ref>` and then `git clean -fd`: tracked files, staged or not, go back to `ref`, the current branch points at `ref`, and untracked files and directories are removed; ignored paths stay. An unknown `ref` is a `GitError` and changes nothing.
- `revert_paths(commit, paths)` brings each path to its content at `commit` in the work tree and in the index when the file exists there, and deletes it from the work tree and the index when it does not exist at `commit` (a tracked or an untracked file); other paths are not touched; a path that is not there at either place is skipped. Each path is repository-relative with forward slashes; an absolute path, or one with a `..` segment, raises `ValueError` before any path is changed. An unknown `commit` is a `GitError`.
- `move(source, destination)` runs `git mv`, creating the destination's parent directories; the move is staged as a rename. A `source` that is not tracked, or a `destination` that exists, is a `GitError`. An absolute `source` or `destination`, or one with a `..` segment, raises `ValueError` before anything is created (the same `check_repository_path` rule as `revert_paths`).
- `Git` has exactly nineteen public operations: `fetch`, `remote_branches`, `resolve`, `show_file`, `list_files`, `is_ancestor`, `log`, `changed_paths`, `status`, `clone`, `checkout`, `commit`, `push`, `delete_remote_branch`, `delete_branch`, `merge`, `reset_to`, `revert_paths` and `move`; `GitCli` has each of them.

Tests: `tests/adapters/test_git_cli_restoring.py`, `tests/application/test_git_protocol.py`. The tests set up and verify with plain `git` through `run_git` (which starts git through `run_process`), and use the fixtures `remote`, `checkout` and `human`.

## Acceptance criteria

1. `reset_to(ref)` discards staged and unstaged changes of tracked files and points the current branch at `ref`.
2. `reset_to` removes untracked files and untracked directories and keeps a file named in `.gitignore`.
3. `reset_to("nope")` raises `GitError`, and an uncommitted change is still there.
4. `revert_paths(commit, ["a.txt", "b.txt"])` restores the content `a.txt` and `b.txt` had at `commit` (one edited, one deleted in the work tree), in the work tree and in the index.
5. `revert_paths` deletes a path that does not exist at `commit`: a file added and committed later, a file only staged, and an untracked file; a path that exists nowhere is skipped without an error.
6. `revert_paths` leaves the changes of paths it was not given as they are.
7. `revert_paths` raises `ValueError` for `../x`, for `a/../../x` and for an absolute path, and no path is changed, not even a valid one in the same call; `docs/a.txt` is accepted.
8. `revert_paths("nope", ["a.txt"])` raises `GitError`.
9. `move("a.txt", "docs/new/a.txt")` creates the folders, the file is at the new path, and `git status` shows a rename; the content is unchanged.
10. `move` raises `GitError` for a source that is not tracked and for a destination that already exists.
11. `Git` has exactly the nineteen operations named in the rules, and `GitCli` has each of them (a test compares the public names of the protocol with that list and checks `hasattr` on `GitCli`).
12. `move` raises `ValueError` for a `../x.txt` destination and for an absolute destination, and no folder appears outside the checkout.
13. make check stays green.
14. docs: `docs/project-guide.md` describes the operations of this story (reset and clean, revert of paths, move, and the path rule both of them follow) and lists the nineteen operations of the `Git` protocol with the feature that uses each.

## Demo

```bash
uv run python -c "
import tempfile
from pathlib import Path
from factory.adapters.git_cli import GitCli
from factory.adapters.process import ProcessRequest, run_process

def git(directory, *args):
    argv = ['git', '-c', 'user.name=demo', '-c', 'user.email=demo@example.invalid', *args]
    return run_process(ProcessRequest(argv=argv, cwd=directory)).stdout.strip()

root = Path(tempfile.mkdtemp())
git(root, 'init', '-q', '--initial-branch=main', 'work')
work = root / 'work'
(work / 'a.txt').write_text('base\n')
git(work, 'add', '-A')
git(work, 'commit', '-q', '-m', 'base')
cli = GitCli(work)
(work / 'junk.txt').write_text('x\n')
(work / 'a.txt').write_text('edited\n')
cli.reset_to('HEAD')
print((work / 'junk.txt').exists(), (work / 'a.txt').read_text().strip())
(work / 'a.txt').write_text('edited again\n')
cli.revert_paths('HEAD', ['a.txt'])
print((work / 'a.txt').read_text().strip())
cli.move('a.txt', 'docs/a.txt')
print((work / 'docs' / 'a.txt').exists(), (work / 'a.txt').exists())
"
```
Expect: three lines: `False base`, then `base`, then `True False`: the reset removed the untracked file and the edit, the revert restored the committed text, the move renamed the file.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names `src/factory/application/git.py` and the three signatures (`reset_to`, `revert_paths`, `move`) with concrete rules for each, plus the exact list of nineteen operations. Nothing is left to the coder's choice.
   - Criteria: 1-11 are each testable by one test function. Every rule has its failing side. An unknown ref is criterion 3, which also checks that nothing changed. Unsafe paths are criterion 7, including that no path is changed. An unknown commit is criterion 8. A move with an untracked source or an existing destination is criterion 10. The passing side of the path rule is covered by `docs/a.txt` in criterion 7. Criterion 11 covers the protocol/`GitCli` match. Criteria 12 (`make check`) and 13 (`docs:`) close the list.
   - Demo: the script uses only `GitCli`, `run_process` and `ProcessRequest`, so it can run. Its `Expect:` gives the three output lines (`False base`, `base`, `True False`), which can be checked exactly.
   - Architecture: the `Git` protocol is in the application layer and `GitCli` is in the adapters layer. Git is reached only through the wrapper. Inputs are plain strings and sequences, with no `dict[str, Any]`.
   - Scope: reset/clean, revert and move are listed in F0001's scope, and none of this is in "Out of scope". The rules for what to revert stay with F0004. The criterion-11 operations from S0011 are named in the Assignment.
3. tester: Wrote the red tests for reset_to, revert_paths, move and the nineteen-operation Git protocol.
   - criterion 1: tests/adapters/test_git_cli_restoring.py::test_reset_to_discards_tracked_changes_and_moves_the_branch
   - criterion 2: tests/adapters/test_git_cli_restoring.py::test_reset_to_removes_untracked_files_and_directories_and_keeps_ignored
   - criterion 3: tests/adapters/test_git_cli_restoring.py::test_reset_to_an_unknown_ref_raises_and_changes_nothing
   - criterion 4: tests/adapters/test_git_cli_restoring.py::test_revert_paths_restores_edited_and_deleted_files_in_work_tree_and_index
   - criterion 5: tests/adapters/test_git_cli_restoring.py::test_revert_paths_deletes_paths_missing_at_the_commit_and_skips_unknown_ones
   - criterion 6: tests/adapters/test_git_cli_restoring.py::test_revert_paths_leaves_other_paths_alone
   - criterion 7: tests/adapters/test_git_cli_restoring.py::test_revert_paths_refuses_unsafe_paths_before_changing_any (parametrized: `../x`, `a/../../x`, an absolute path; each sits next to the valid `a.txt` in one call) and ::test_revert_paths_accepts_a_path_in_a_subdirectory (`docs/a.txt`)
   - criterion 8: tests/adapters/test_git_cli_restoring.py::test_revert_paths_from_an_unknown_commit_raises
   - criterion 9: tests/adapters/test_git_cli_restoring.py::test_move_creates_folders_and_stages_a_rename (expects porcelain status `R  a.txt -> docs/new/a.txt`)
   - criterion 10: tests/adapters/test_git_cli_restoring.py::test_move_refuses_an_untracked_source_or_an_existing_destination (parametrized: untracked source, existing destination)
   - criterion 11: tests/application/test_git_protocol.py::test_git_has_exactly_the_nineteen_operations_and_git_cli_has_each
   Files created: tests/adapters/test_git_cli_restoring.py, tests/application/test_git_protocol.py.
   Every module imports, so there are no collection errors. `make test` fails as intended because `GitCli` does not have `reset_to`, `revert_paths` or `move` yet, and `Git` has only sixteen operations. `make lint` is green. I skipped the type check, as this stage says to.

   `make lint`: lint: green
   `make test`: FAILED tests/application/test_git_protocol.py::test_git_has_exactly_the_nineteen_operations_and_git_cli_has_each
4. coder: Added `reset_to`, `revert_paths` and `move` to the `Git` protocol and to `GitCli`. `make check` is green and the demo prints the three lines it expects (`False base`, `base`, `True False`).
      - `src/factory/application/git.py`: the protocol has the three new operations, nineteen in total, each with a docstring that gives its rule.
      - `src/factory/domain/git.py`: new `check_repository_path(path)`, the pure path rule. It raises `ValueError` for an empty path, an absolute path or one with a `..` segment.
      - `src/factory/adapters/git_cli.py`:
        - `reset_to` resolves the ref, then runs `reset --hard <commit> --` and `clean --force -d`, which keeps ignored files.
        - `revert_paths` checks every path before it touches any of them, then resolves the commit. A path that is a file at that commit is restored with `checkout <commit> -- <path>`, which updates the work tree and the index. Any other path is dropped from the index (`rm --cached --ignore-unmatch`) and its file is unlinked, so a path that exists nowhere is skipped.
        - `move` creates the destination's parent folders, then runs `git mv -- source destination`. git itself refuses an untracked source or an existing destination, which raises `GitError`.
      - Main decision: git resolves the ref or commit to an id before `reset` or `checkout` runs, through a new private `_resolve_or_raise`. `git reset` refuses `--end-of-options` after `--hard`, so a resolved commit id is how a ref that looks like an option stays safe. It also turns an unknown ref into a `GitError` before anything changes.
      - Rejected: restoring with `git restore --source --staged --worktree`. It fails on a path missing at the commit and still needs the separate delete path, so it bought nothing.
      - Refactor (6a3bf7f): `merge` now uses `_resolve_or_raise` for its unknown-ref check instead of a copy of the same code.
      - Noticed, not touched: `revert_paths` with a path that is a directory at both the commit and in the work tree would make `git rm` fail without `-r`, which raises `GitError`. The rule only speaks of files, so I left it.
      - Commits: 3cdcbe7 (feat), 6a3bf7f (refactor).

   `make check`: check: green
5. reviewer: Criteria 1–11 hold. Each one has a test that tests what it claims, and the coder's entry reports `make check` green. The architecture holds too: the path rule is a pure function in `factory.domain.git`, the protocol is in application and `GitCli` is in adapters. Before I pass or return this story I need one decision, because the gap is in the story's rules, not only in the code.

   Question: should `move` follow the same path rule as `revert_paths`?
   - What happens now: `src/factory/adapters/git_cli.py` `move` creates `(self._directory / destination).parent` with `mkdir(parents=True)` before git checks anything. So `move("a.txt", "../outside/x.txt")` or `move("a.txt", "/tmp/somewhere/x.txt")` creates folders outside the checkout. git then refuses the move and raises `GitError`, but the folders stay. This is the wrapper's only filesystem write that skips the boundary check this story introduces (`check_repository_path`).
   - The Interface gives `move` no path rule, so no criterion covers this failing side. The coder cannot add the check without an untested rule (R9/R13), which is why I am asking rather than returning the story to `doing`.

   Options:
   - (a) Extend the story. Add a rule: "`move` raises `ValueError` for an absolute `source` or `destination`, or one with a `..` segment, before anything is created." Add a criterion before the two closing ones, for example: "`move` raises `ValueError` for `../x.txt` and for an absolute destination, and no folder is created outside the checkout." The tester writes that test, then the coder calls `check_repository_path` on both arguments before `mkdir`.
   - (b) Accept it as it is. The callers (F0007) pass paths the factory builds, and git still refuses the move, so the only effect is empty folders. The story then passes to `docs` unchanged.

   I would choose (a). The fix is one line per argument, it reuses this story's own path rule, and the wrapper stays a boundary that validates its input.

   Nothing else is open. Smaller points I checked and accept:
   - The empty-path refusal in `check_repository_path` goes beyond the rule, but it is defensive and harmless.
   - `revert_paths` reads the whole blob through `show_file` only to test whether it exists, which reuses existing code.
   - `tests/application/test_git_protocol.py` imports `GitCli`, as the Interface places it.
6. human (pull request comment, 2026-10-13): (a): add the rule and the criterion before the two closing ones as you worded them: `move` raises `ValueError` for an absolute `source` or `destination`, or one with a `..` segment, before anything is created; the test checks `../x.txt` and an absolute destination and that no folder appears outside the checkout. It reuses this story's `check_repository_path`.
7. reviewer: Applied the human's answer (a) from entry 6 to the ticket. Assignment is now "as of log entry 6". The Interface rule for `move` now says: an absolute `source` or `destination`, or one with a `..` segment, raises `ValueError` before anything is created, using the same `check_repository_path` as `revert_paths`. The new criterion 12 is "`move` raises `ValueError` for a `../x.txt` destination and for an absolute destination, and no folder appears outside the checkout". The closing criteria become 13 (`make check`) and 14 (docs). The docs criterion now names the path rule for both revert and move. I re-read the rest of the diff against criteria 1–11, the architecture, security and quality. It holds as described in entry 5, so the only findings are the new rule.

   Findings:
   1. tests/adapters/test_git_cli_restoring.py: no test covers criterion 12. Fix: the tester adds a test that calls `move("a.txt", "../x.txt")` and `move` with an absolute destination outside the checkout (under `tmp_path`). The test expects `ValueError` and checks that no folder was created outside the checkout. The coder routes this to `tests` (R9).
   2. src/factory/adapters/git_cli.py `move`: `mkdir(parents=True)` runs before any path check, so an unsafe destination creates folders outside the checkout. Fix: call `check_repository_path(source)` and `check_repository_path(destination)` before the `mkdir`.
   3. src/factory/application/git.py `Git.move` docstring: it does not state the new path rule. Fix: add that an absolute path or a `..` segment in either argument raises `ValueError` before anything is created, matching the `revert_paths` docstring.
8. coder: The human's answer in entry 6 adds criterion 12, and no test covers it yet (reviewer finding 1). I did not touch the tests and did not change any code in this round. The new rule should first get a red test.
      - Test change for the tester: in `tests/adapters/test_git_cli_restoring.py`, add a test for criterion 12. It calls `checkout.move("a.txt", "../x.txt")`, and `move` with an absolute destination outside the checkout under `tmp_path` (for example `str(tmp_path / "outside" / "x.txt")`). Both calls expect `ValueError`, and the test checks that no folder appeared outside the checkout.
      - Open for the coder when the story comes back (findings 2 and 3):
        - In `src/factory/adapters/git_cli.py` `move`, call `check_repository_path` on `source` and on `destination` before the `mkdir`.
        - Add the path rule to the `Git.move` docstring in `src/factory/application/git.py`.
9. tester: tester (approved test change, entries 6–8): I added the criterion-12 test that the coder's entry 8 names. I did not touch any other test.
      - criterion 12: tests/adapters/test_git_cli_restoring.py::test_move_refuses_an_unsafe_destination_before_creating_any_folder. It is parametrized with two destinations: `../x.txt`, and an absolute `tmp_path/outside/x.txt` that lies outside the checkout. Each call to `checkout.move("a.txt", destination)` must raise `ValueError`. The test then checks that the top-level entries of `tmp_path`, the folder that holds the checkout, are the same as before the call, so no `outside` folder and no `x.txt` appear. It also checks that `a.txt` is still in place.
      - Why: the human chose option (a) in entry 6, and entry 7 added it to the Interface and as criterion 12.
      - `make test`: it fails as intended, on both parametrized cases only. `move` does not check its paths yet: git refuses the move and raises `GitError` instead of `ValueError`, and the absolute case also creates the `outside` folder. Every module imports.
      - `make lint`: green.
      - Open for the coder: reviewer findings 2 and 3 from entry 7. First, call `check_repository_path` on `source` and on `destination` in `GitCli.move` before the `mkdir`. Second, add the path rule to the `Git.move` docstring.

   `make lint`: lint: green
   `make test`: FAILED tests/adapters/test_git_cli_restoring.py::test_move_refuses_an_unsafe_destination_before_creating_any_folder[absolute]
