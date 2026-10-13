# The git wrapper: push and delete_remote_branch act on branches only

<!-- proposed by feature acceptance of 2026-10-13; refine before promoting -->

## Assignment (as of log entry 1)

Close the last places where the git wrapper's remote operations (R9) act on something other than a branch. The third acceptance of F0001 found them against a real bare remote. S0020 made `push` and `delete_remote_branch` refuse a leading `+`, any `:` and any `*`. Git still reads two other things in their `branch`:

- `delete_remote_branch("v1")` with a **tag** `v1` on the remote deletes the tag and returns `"pushed"`. This is because `git push origin --delete v1` matches any ref named `v1`.
- `push("^main")` is a negative refspec: git pushes nothing and exits 0. `push("@")` and `push("HEAD")` push the checked-out branch under its own name. `push("v1")`, with `v1` a local tag and no local branch `v1`, pushes the tag. All four return `"pushed"`, yet afterwards there is no `origin/^main`, `origin/@`, `origin/HEAD` or `origin/v1`. This contradicts the project guide: "`"pushed"`: git exited 0; afterwards `origin/<branch>` in the checkout is the pushed commit."

The fix has two parts (option A of the acceptance report; the human chooses, see below):

1. `check_branch_name` also refuses any value that git would not take as a branch name, and also `HEAD` and `@`.
2. `push` and `delete_remote_branch` name the branch as `refs/heads/<branch>` on git's command line, as the source only, with no `:<dst>`. A tag is then never pushed or deleted as a branch.

The refusal of `+`, `:` and `*` stays as decision 22 has it, so `push(":keep")` is still a `ValueError`. This is not the alternative rejected in decision 22 (the explicit `refs/heads/<b>:refs/heads/<b>`), but it is close to it, so the human decides before this is promoted:

- **A.** Both parts. This is the recommendation.
- **B.** Only part 1. Drop criteria 6–8, and the guide states that a tag sharing a branch's name is deleted.
- **C.** No code change. Replace this story with a docs-only one that states the edges.

The factory's own names (`main`, `work-item/<id>`) pass both parts unchanged. The local operations (`checkout`, `delete_branch`, `merge`, …) keep `check_git_argument`.

Covers R9 (the push and delete rules).

## Interface

`src/factory/domain/git.py` (the existing function, stricter)

```python
def check_branch_name(value: str) -> None:
    """Raise ValueError for a value that `git push` could read as anything but a branch name."""
```

The rules, each with a criterion below. `check_branch_name` raises `ValueError` for:

- everything it refuses today: an empty value, a leading `-`, a leading `+`, any `:` and any `*` (anywhere, not only at the end);
- the whole values `HEAD` and `@`;
- any `^`, `~`, `?`, `[`, `\`, space or ASCII control character (below 0x20, or 0x7f);
- any `..` and any `@{`;
- a leading or trailing `/`, and any `//`;
- a trailing `.`;
- a slash-separated component that starts with `.` or ends with `.lock`.

It accepts anything else, such as `main`, `work-item/F0001-S0001`, `feature/x`, `a+b`, `a@b` and `release-1.2`. These are the rules of `git check-ref-format --branch`, applied in the domain, without calling git.

`src/factory/adapters/git_cli.py`:

- `GitCli.push(branch)` still calls `check_branch_name` first, before `BEFORE_PUSH`, and then runs `git push --porcelain --set-upstream origin refs/heads/<branch>`. A `branch` with no local branch of that name is a `GitError`, also when a tag of that name exists. The outcomes and kill points are unchanged.
- `GitCli.delete_remote_branch(branch)` still calls `check_branch_name` first, and then runs `git push --porcelain origin --delete refs/heads/<branch>`. A tag of the same name on the remote is left alone. The outcomes, the "already gone is `pushed`" rule and the removal of the stale `origin/<branch>` are unchanged.

Tests: `tests/domain/test_git.py` for the function. `tests/adapters/test_git_cli_arguments.py` (refusals) and `tests/adapters/test_git_cli_branches.py` (tags, upstream) for the wrapper, with the fixtures `remote`, `checkout` and `human`.

## Acceptance criteria

1. `check_branch_name` raises `ValueError` for `"HEAD"`, `"@"`, `"^main"`, `"main~1"`, `"ma?n"`, `"ma[in"`, `"ma\\in"`, `"ma in"`, `"a\tb"`, `"a..b"`, `"a@{1}"`, `"/x"`, `"x/"`, `"a//b"`, `"x."`, `"feature/.x"`, `"x.lock"` and `"feature/x.lock/y"`.
2. `check_branch_name` raises `ValueError` for `"x*y"`: a `*` inside a name, not only at its end. It still raises for `""`, `"-x"`, `"+main"`, `":main"` and `"main:other"`.
3. `check_branch_name` accepts `"main"`, `"work-item/F0001-S0001"`, `"feature/x"`, `"a+b"`, `"a@b"` and `"release-1.2"`.
4. `checkout.push("^main")` raises `ValueError`, `BEFORE_PUSH` was not reached, and the remote still has `main` at the same commit.
5. `checkout.push("HEAD")` and `checkout.push("@")` each raise `ValueError`, and the remote has no branch other than those it had before.
6. With a tag `v1` in `checkout` and no local branch `v1`, `checkout.push("v1")` raises `GitError`, and the remote has no ref named `refs/heads/v1` or `refs/tags/v1`.
7. With a tag `v1` on the remote (pushed by `human`) and no remote branch `v1`, `checkout.delete_remote_branch("v1")` returns `"pushed"`, and the remote's `refs/tags/v1` is still there at the same commit.
8. `checkout.push("work-item/F0001-S0001")` of a new local branch returns `"pushed"`. Afterwards `origin/work-item/F0001-S0001` in the checkout is the local commit, and the branch's upstream (`git rev-parse --abbrev-ref work-item/F0001-S0001@{upstream}`) is `origin/work-item/F0001-S0001`.
9. `checkout.delete_remote_branch("keep")` of a branch `keep` that `human` pushed returns `"pushed"`. Afterwards the remote has no `keep`, and the checkout has no `origin/keep`.
10. `make check` stays green.
11. docs: the branch rule in the git wrapper section of `docs/project-guide.md` names the added refusals (`HEAD`, `@` and git's branch-name rules, with `^` as the example). It also says that `push` and `delete_remote_branch` name `refs/heads/<branch>`, so that a tag is never pushed or deleted as a branch. The meanings of `"pushed"` for both operations still read true. `docs/decisions.md`'s entry "A pushed branch is never read as a refspec" records the extension, and why it is not the explicit `refs/heads/<b>:refs/heads/<b>` that decision 22 rejected.

## Demo

```bash
uv run python -c "
import tempfile
from pathlib import Path
from factory.adapters.git_cli import GitCli
from factory.adapters.process import ProcessRequest, run_process
root = Path(tempfile.mkdtemp())
def git(*args, cwd):
    return run_process(ProcessRequest(argv=['git', *args], cwd=cwd)).stdout.split()
git('init', '-q', '--bare', '-b', 'main', str(root / 'r.git'), cwd=root)
a = GitCli(root / 'a'); a.clone(str(root / 'r.git'))
(root / 'a/x').write_text('1'); a.commit('one'); print(a.push('main'))
git('tag', 'v1', cwd=root / 'a'); git('push', '-q', 'origin', 'v1', cwd=root / 'a')
print(a.delete_remote_branch('v1'))
for name in ('^main', 'HEAD', '@', 'main~1'):
    try:
        a.push(name)
    except ValueError:
        print('refused', name)
print(git('for-each-ref', '--format=%(refname)', cwd=root / 'r.git'))
"
```
Expect: seven lines: `pushed`, `pushed`, `refused ^main`, `refused HEAD`, `refused @`, `refused main~1`, `['refs/heads/main', 'refs/tags/v1']`. The tag `v1` survived the branch deletion, and the remote has only `main` among its branches.

## Log (append only)

1. 2026-10-13 feature acceptance: proposed; the human refines and promotes.
