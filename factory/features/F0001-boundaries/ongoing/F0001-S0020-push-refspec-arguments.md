# The git wrapper: a pushed branch is never read as a refspec

<!-- proposed by feature acceptance of 2026-10-13; refine before promoting -->

## Assignment (as of log entry 1)

Close the second route to a forced push in the git wrapper (R9), which the second acceptance of F0001 found. S0015 made `GitCli` refuse a value that starts with `-`, so `push("--force")` no longer reaches git. `push(branch)` still passes `branch` to `git push` as a refspec, though, and git reads refspec syntax in it. The acceptance reproduced three cases against a real bare remote:

- `push("+main")` with `main` diverged force-pushes and overwrites the other writer's commit. A plain `push("main")` is `"rejected"`. This breaks "a push is never forced" (FEATURE.md decision 10, `docs/decisions.md`, the project guide).
- `push(":keep")` deletes the remote branch `keep` and returns `"pushed"`, bypassing `delete_remote_branch`.
- `push("HEAD:refs/heads/other")` creates a remote branch `other` that has no local counterpart.

`delete_remote_branch("+main")` returns `"pushed"` while `main` is still on the remote: git looked for a ref literally named `+main`. That contradicts the guide's "`pushed` when the branch is gone from the remote afterwards", in the reader's sense.

The wrapper refuses a branch that `git push` would read as a refspec, with `ValueError` before git runs and before any kill point. That covers a leading `+`, any `:` and any `*`: a pattern pushes every local branch that matches (`push("refs/heads/x*")`), or nothing while returning `"pushed"` (`push("x*")`); git never allows `*` in a branch name. It is the same kind of refusal as S0015's, so the documented rule stays one rule: refuse before git, in the domain. `git check-ref-format --branch` accepts `+main` as a name, so this refuses a name git allows. The factory's branch names (`main`, `work-item/<id>`) never take that form, so nothing it uses is lost.

Decided by the human on 2026-10-13 (FEATURE.md decision 22): refuse as above. Rejected: pushing the explicit refspec `refs/heads/<branch>:refs/heads/<branch>`, which cannot force, but turns `:keep` into a `GitError` and leaves the `delete_remote_branch` case to a separate rule.

Only `push` and `delete_remote_branch` change. The local operations (`checkout`, `delete_branch`, `merge`, …) keep `check_git_argument`, because git reads no refspec there: `checkout` and `merge` of a name with a `:` are already a `GitError`, and `delete_branch` of one finds no branch and changes nothing (decision 15).

Covers R9 (the push and delete rules).

## Interface

`src/factory/domain/git.py` (new function, beside `check_git_argument`)

```python
def check_branch_name(value: str) -> None:
    """Raise ValueError for a branch name that `git push` could read as an option or a refspec."""
```

The rules, each with a criterion below:

- `check_branch_name` raises `ValueError` for everything `check_git_argument` refuses (an empty value, a leading `-`). It also refuses a value that starts with `+`, a value that contains `:` and a value that contains `*`. It accepts anything else, such as `main`, `work-item/F0001-S0001`, `feature/x` and `a+b` (a plus inside a name).
- `GitCli.push(branch)` and `GitCli.delete_remote_branch(branch)` call `check_branch_name` in place of `check_git_argument`, as their first statement. A refused value starts no git process and changes nothing on the remote. `push` with a refused value does not reach `BEFORE_PUSH`.
- The local operations keep `check_git_argument` and do not call `check_branch_name`, because git reads no refspec there: `delete_branch("+x")` and `delete_branch("x:y")` are not refused, and change nothing when no such branch exists.

Tests: `tests/domain/test_git.py` for the function, and `tests/adapters/test_git_cli_arguments.py` for the wrapper, with the fixtures `remote`, `checkout` and `human`.

## Acceptance criteria

1. `check_branch_name` raises `ValueError` for `""`, `"-x"`, `"+main"`, `":main"`, `"main:other"`, `"HEAD:refs/heads/x"` and `"refs/heads/x*"`.
2. `check_branch_name` accepts `"main"`, `"work-item/F0001-S0001"`, `"feature/x"` and `"a+b"`.
3. With `main` diverged between `checkout` and `human`, `checkout.push("+main")` raises `ValueError`. The remote's `main` is still the human's commit, and `BEFORE_PUSH` was not reached.
4. With a branch `keep` on the remote, `checkout.push(":keep")` raises `ValueError`, and the remote still has `keep` at the same commit.
5. `checkout.push("HEAD:refs/heads/other")` raises `ValueError`, and the remote has no branch `other`.
6. `delete_remote_branch("+main")` and `delete_remote_branch("main:x")` each raise `ValueError`, and the remote's refs are unchanged.
7. `push("a+b")` of a new local branch `a+b` returns `"pushed"`, and the remote's `a+b` is the local commit: a plus inside a name is fine.
8. `delete_branch("+x")` and `delete_branch("x:y")` return without error and leave the local branches as they were: the local operations keep `check_git_argument`.
9. `make check` stays green.
10. docs: the argument rule in `docs/project-guide.md`'s git wrapper section names `check_branch_name`, `push` and `delete_remote_branch`, and says why (`+` forces, `:` names another ref or deletes one, `*` is a pattern). `docs/decisions.md`'s entry on option-like values, or a new entry beside it, records the refspec case and the alternative not taken.

## Demo

```bash
uv run python -c "
import tempfile
from pathlib import Path
from factory.adapters.git_cli import GitCli
from factory.adapters.process import ProcessRequest, run_process
root = Path(tempfile.mkdtemp())
run_process(ProcessRequest(argv=['git', 'init', '-q', '--bare', '-b', 'main', str(root / 'r.git')], cwd=root))
a, b = GitCli(root / 'a'), GitCli(root / 'b')
a.clone(str(root / 'r.git')); (root / 'a/x').write_text('1'); a.commit('one'); a.push('main')
b.clone(str(root / 'r.git')); (root / 'b/y').write_text('2'); b.commit('human'); b.push('main')
(root / 'a/z').write_text('3'); a.commit('diverged')
print(a.push('main'))
for name in ('+main', ':main'):
    try:
        a.push(name)
    except ValueError:
        print('refused', name)
b.fetch()
print([c.subject for c in b.log('origin/main')], [r.name for r in b.remote_branches()])
"
```
Expect: four lines: `rejected`, `refused +main`, `refused :main`, `['human', 'one'] ['main']`. The human's commit is still the remote's tip, and `main` still exists.

## Log (append only)

1. 2026-10-13 feature acceptance: proposed; the human refines and promotes.
