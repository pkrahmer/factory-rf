# The git wrapper: history and work tree

## Assignment (as of log entry 1)

Add the last three reading operations of the git wrapper (R9): the log of a ref (optionally since another ref, optionally for one path), the paths changed since a commit (the commits after it together with the work tree, untracked files included), and the status of the work tree. They return factory-shaped DTOs (R7), never git's text. Later features read recovery state from them: the undo compares the work tree with the stage-start commit, the tick looks at the status before it restores the checkout. This story completes the reading half of the `Git` protocol that S0005 began; the writing half is S0006, S0012 and S0013. It was split from the first reading story to keep each story within 26 criteria. S0006 and S0012 do not depend on it, because their tests verify with plain `git`; S0013's closing criterion (the nineteen operations) does, and S0013 comes after this story in id order. Covers R9 and R7; keeps kept thing 3 (the remote is the truth: these operations describe what the checkout holds, and nothing is decided from them without the remote).

## Interface

`src/factory/domain/git.py` (adds to the module from S0002, S0005 and S0006)

```python
ChangeKind = Literal["added", "modified", "deleted"]

class ChangedPath(BaseModel):
    path: str
    change: ChangeKind

class CommitInfo(BaseModel):
    commit: CommitId
    parents: list[CommitId]
    subject: str
    author: str
    committed_at: AwareDatetime

class WorkTreeStatus(BaseModel):
    branch: str | None
    head: CommitId | None
    changes: list[ChangedPath]
```

`src/factory/application/git.py` (adds three operations to `Git`)

```python
    def log(self, ref: str, *, since: str | None = None, path: str | None = None) -> list[CommitInfo]: ...
    def changed_paths(self, since: str) -> list[ChangedPath]: ...
    def status(self) -> WorkTreeStatus: ...
```

The rules, each with a criterion below:

- A rename is a deletion plus an addition: `ChangeKind` has no `"renamed"`. All three models are frozen and forbid unknown keys; `committed_at` is aware and converted to UTC; commit ids are 40-character lowercase hexadecimal.
- `log(ref)` returns the commits reachable from `ref`, newest first, a commit always before its parents. `commit` and `parents` are full ids (the parents in git's order), `subject` is the first line of the message, `author` is the author's name, `committed_at` is the committer date. With `since`, only commits reachable from `ref` and not from `since` are returned (so `since == ref` gives `[]`). With `path`, only commits that changed that path (a file, or anything under a directory). A ref or `since` that does not exist is a `GitError`.
- `changed_paths(since)` is the net difference between the commit `since` and the work tree: every path whose content differs, whether the change is committed, staged, unstaged or an untracked file that is not ignored (those are `"added"`). A path that was added and deleted again, or changed and restored, is not listed. The list is sorted by path in plain string order; names with spaces and non-ASCII characters come back exactly. A `since` that does not exist is a `GitError`.
- `status()` returns `branch` (the checked-out branch, `None` when HEAD is detached), `head` (the commit HEAD points to, `None` in a repository without commits) and `changes`: one entry per path that differs from HEAD, staged, unstaged or untracked, sorted by path. A path that is deleted (staged or not) is `"deleted"`; a path that HEAD does not have (untracked, or newly staged, also when it was edited again after staging) is `"added"`; any other change is `"modified"`, so a tracked file that is changed, staged and changed again is `"modified"`. A path changed both staged and unstaged is listed once. Ignored paths are never listed.

Tests: `tests/adapters/test_git_cli_history.py`, `tests/domain/test_git_history.py`. The tests set up repositories with plain `git` through `run_git` (from `tests/git_support.py`, which starts git through `run_process`, never through `subprocess`).

## Acceptance criteria

1. `ChangedPath`, `CommitInfo` and `WorkTreeStatus` reject an unknown keyword argument and assignment to a field; `ChangeKind` rejects `"renamed"`; `CommitInfo` rejects a naive `committed_at`, converts one with another offset to UTC, and rejects a `commit` of 39 characters and a parent with an uppercase letter.
2. `log("HEAD")` after three commits returns three `CommitInfo` newest first, each `commit` and `parents` equal to what plain `git` reports, the `subject` of each, and `author` equal to `Test Author`.
3. `subject` is only the first line for a commit whose message has a subject, a blank line and a body.
4. `committed_at` is the committer date in UTC: for a commit made with a committer date in the time zone UTC+2, `committed_at.utcoffset()` is zero and the instant is the one plain `git log --format=%ct` reports.
5. `log("feature", since="main")` returns only the commits on `feature` that are not on `main`; `log("main", since="main")` returns `[]`.
6. `log("HEAD", path="docs/a.md")` returns only the commits that changed that file; with `path="docs"` it returns the commits that changed anything under it.
7. After a merge of two diverged branches, `log` returns the merge commit with two parents, before both of them.
8. `log` raises `GitError` for a ref that does not exist and for a `since` that does not exist, and `changed_paths` raises it for a `since` that does not exist.
9. `changed_paths(since)` after two commits that add `new.txt`, change `old.txt` and delete `gone.txt` returns `("gone.txt", "deleted")`, `("new.txt", "added")` and `("old.txt", "modified")`, sorted by path.
10. `changed_paths` also lists a staged new file, an unstaged change and an untracked file (as `"added"`), and does not list a path named in `.gitignore`.
11. A file renamed with `git mv` (or deleted and recreated under another name) appears as a deletion of the old path and an addition of the new one.
12. A file added after `since` and deleted again does not appear; a file changed and then restored to its content at `since` does not appear.
13. Paths with a space and a non-ASCII character, such as `a b/é.txt`, come back exactly in `changed_paths` and in `status`, and the lists are in plain string order.
14. `status()` of a clean checkout on `main` has `branch == "main"`, `head` equal to `HEAD` and `changes == []`.
15. `status()` lists an untracked file as `"added"`, an unstaged edit as `"modified"`, a newly staged file as `"added"`, a tracked file deleted in the work tree as `"deleted"`, and a file deleted with `git rm` as `"deleted"`.
16. A tracked file that is changed, staged and then changed again is listed once in `status()`, as `"modified"`.
17. A new file that is staged and then edited again is listed once in `status()`, as `"added"`.
18. A file renamed with `git mv` is listed in `status()` as a deletion of the old path and an addition of the new one.
19. With HEAD detached at a commit, `status().branch` is `None` and `head` is that commit.
20. In a repository without commits, `status().head` is `None`, `branch` is the name of the unborn branch, and an untracked file is listed as `"added"`.
21. `status()` does not list a path named in `.gitignore`.
22. make check stays green.
23. docs: `docs/project-guide.md` lists what `log`, `changed_paths` and `status` return (a rename is a deletion plus an addition, untracked files count, ignored ones do not) and says that the undo and the tick use them.

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
(work / 'a.txt').write_text('one\n')
git(work, 'add', '-A')
git(work, 'commit', '-q', '-m', 'first commit')
(work / 'a.txt').write_text('two\n')
git(work, 'add', '-A')
git(work, 'commit', '-q', '-m', 'second commit')
(work / 'b.txt').write_text('new\n')
(work / 'a.txt').write_text('three\n')
cli = GitCli(work)
print([commit.subject for commit in cli.log('HEAD')])
print([(item.path, item.change) for item in cli.changed_paths('HEAD~1')])
status = cli.status()
print(status.branch, [(item.path, item.change) for item in status.changes])
"
```
Expect: three lines: `['second commit', 'first commit']`, then `[('a.txt', 'modified'), ('b.txt', 'added')]`, then `main [('a.txt', 'modified'), ('b.txt', 'added')]`.

## Log (append only)

1. 2026-10-12 human: created.
