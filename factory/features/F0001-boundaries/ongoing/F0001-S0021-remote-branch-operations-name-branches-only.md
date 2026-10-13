---
stage: demo
pr: 24
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The git wrapper: push and delete_remote_branch act on branches only

<!-- proposed by feature acceptance of 2026-10-13; refine before promoting -->

## Assignment (as of log entry 1)

Close the last places where the git wrapper's remote operations (R9) act on something other than a branch. The third acceptance of F0001 found them against a real bare remote. S0020 made `push` and `delete_remote_branch` refuse a leading `+`, any `:` and any `*`. Git still reads two other things in their `branch`:

- `delete_remote_branch("v1")` with a **tag** `v1` on the remote deletes the tag and returns `"pushed"`. This is because `git push origin --delete v1` matches any ref named `v1`.
- `push("^main")` is a negative refspec: git pushes nothing and exits 0. `push("@")` and `push("HEAD")` push the checked-out branch under its own name. `push("v1")`, with `v1` a local tag and no local branch `v1`, pushes the tag. All four return `"pushed"`, yet afterwards there is no `origin/^main`, `origin/@`, `origin/HEAD` or `origin/v1`. This contradicts the project guide: "`"pushed"`: git exited 0; afterwards `origin/<branch>` in the checkout is the pushed commit."

The fix has two parts (option A of the acceptance report, decided by the human on 2026-10-13, FEATURE.md decision 23):

1. `check_branch_name` also refuses any value that git would not take as a branch name, and also `HEAD` and `@`.
2. `push` and `delete_remote_branch` name the branch as `refs/heads/<branch>` on git's command line, as the source only, with no `:<dst>`. A tag is then never pushed or deleted as a branch.

The refusal of `+`, `:` and `*` stays as decision 22 has it, so `push(":keep")` is still a `ValueError`. This is not the alternative rejected in decision 22 (the explicit `refs/heads/<b>:refs/heads/<b>`): only the source is qualified. Rejected: only part 1 (a tag sharing a branch's name would still be deleted), and documenting the edges without a code change.

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

It accepts anything else, such as `main`, `work-item/F0001-S0001`, `feature/x`, `a+b`, `a@b`, `release-1.2`, `feature/HEAD` and `x.lock.y`. These are the rules of `git check-ref-format --branch`, applied in the domain, without calling git.

`src/factory/adapters/git_cli.py`:

- `GitCli.push(branch)` still calls `check_branch_name` first, before `BEFORE_PUSH`, and then runs `git push --porcelain --set-upstream origin refs/heads/<branch>`. A `branch` with no local branch of that name is a `GitError`, also when a tag of that name exists. The outcomes and kill points are unchanged.
- `GitCli.delete_remote_branch(branch)` still calls `check_branch_name` first, and then runs `git push --porcelain origin --delete refs/heads/<branch>`. A tag of the same name on the remote is left alone. A name git refuses, such as `a..b`, is now a `ValueError` before git runs, where it was a `GitError` from git. The outcomes, the "already gone is `pushed`" rule and the removal of the stale `origin/<branch>` are unchanged. With the qualified name, git exits 0 for a branch already gone from the remote (the remote warns "deleting a non-existent ref") and never prints "remote ref does not exist", so `ALREADY_DELETED_MARKER` and its check are removed.

Tests: `tests/domain/test_git.py` for the function. `tests/adapters/test_git_cli_arguments.py` (refusals) and `tests/adapters/test_git_cli_branches.py` (tags, upstream) for the wrapper, with the fixtures `remote`, `checkout` and `human`. The existing test `test_delete_remote_branch_of_an_invalid_ref_name_raises` in `tests/adapters/test_git_cli_branches.py`, written for S0012, expects a `GitError` for `delete_remote_branch("a..b")`. The tester changes it to expect `ValueError` (criterion 10); the human allows this change to a test another story wrote (FEATURE.md decision 23).

## Acceptance criteria

1. `check_branch_name` raises `ValueError` for `"HEAD"`, `"@"`, `"^main"`, `"main~1"`, `"ma?n"`, `"ma[in"`, `"ma\\in"`, `"ma in"`, `"a\tb"`, `"a..b"`, `"a@{1}"`, `"/x"`, `"x/"`, `"a//b"`, `"x."`, `"feature/.x"`, `"x.lock"`, `"feature/x.lock/y"` and `"a\x7fb"` (DEL).
2. `check_branch_name` raises `ValueError` for `"x*y"`: a `*` inside a name, not only at its end. It still raises for `""`, `"-x"`, `"+main"`, `":main"` and `"main:other"`.
3. `check_branch_name` accepts `"main"`, `"work-item/F0001-S0001"`, `"feature/x"`, `"a+b"`, `"a@b"`, `"release-1.2"`, `"feature/HEAD"` (`HEAD` and `@` are refused only as the whole value) and `"x.lock.y"` (`.lock` is refused only at the end of a component).
4. `checkout.push("^main")` raises `ValueError`, `BEFORE_PUSH` was not reached, and the remote still has `main` at the same commit.
5. `checkout.push("HEAD")` and `checkout.push("@")` each raise `ValueError`, and the remote has no branch other than those it had before.
6. With a tag `v1` in `checkout` and no local branch `v1`, `checkout.push("v1")` raises `GitError`, and the remote has no ref named `refs/heads/v1` or `refs/tags/v1`.
7. With a tag `v1` on the remote (pushed by `human`) and no remote branch `v1`, `checkout.delete_remote_branch("v1")` returns `"pushed"`, and the remote's `refs/tags/v1` is still there at the same commit.
8. `checkout.push("work-item/F0001-S0001")` of a new local branch returns `"pushed"`. Afterwards `origin/work-item/F0001-S0001` in the checkout is the local commit, and the branch's upstream (`git rev-parse --abbrev-ref work-item/F0001-S0001@{upstream}`) is `origin/work-item/F0001-S0001`.
9. `checkout.delete_remote_branch("keep")` of a branch `keep` that `human` pushed returns `"pushed"`. Afterwards the remote has no `keep`, and the checkout has no `origin/keep`.
10. `checkout.delete_remote_branch("a..b")` raises `ValueError`, and the remote's refs are unchanged. This replaces the `GitError` that the existing test `test_delete_remote_branch_of_an_invalid_ref_name_raises` in `tests/adapters/test_git_cli_branches.py` expects; the tester changes that test, and the human allows it.
11. `make check` stays green.
12. docs: the branch rule in the git wrapper section of `docs/project-guide.md` names the added refusals (`HEAD`, `@` and git's branch-name rules, with `^` as the example). It also says that `push` and `delete_remote_branch` name `refs/heads/<branch>`, so that a tag is never pushed or deleted as a branch. The meanings of `"pushed"` for both operations still read true. So do the operation table's command for `delete_remote_branch`, the sentence on an invalid ref name (now a `ValueError`, such as `a..b`) and the mentions of git's `remote ref does not exist` message (git no longer prints it for a qualified name; an already-gone branch is a plain exit 0). `docs/decisions.md`'s entry "A pushed branch is never read as a refspec" records the extension, and why it is not the explicit `refs/heads/<b>:refs/heads/<b>` that decision 22 rejected.

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
2. intake: accepted
   - Interface: `check_branch_name` in `src/factory/domain/git.py` has its signature and a complete rule list. `GitCli.push` and `delete_remote_branch` have their exact git command lines (`refs/heads/<branch>`, source only), the kept outcomes and kill points, and the removal of `ALREADY_DELETED_MARKER`. The tests' files and fixtures are named.
   - Criteria: 1 to 3 cover every rule of the function, with the passing and the failing side. They include `*` inside a name, `HEAD` and `@` only as a whole value, and `.lock` only at the end of a component. 4 to 6 cover the refusals in `push` and the tag case. 7 to 10 cover `delete_remote_branch`: the tag survives, the `refs/heads` upstream, the checkout's `origin/keep` removed, and `a..b` now a `ValueError`. Criterion 10 names the S0012 test to change, and decision 23 records the human's permission. Each is testable by one test function. The unchanged "already gone returns pushed" rule keeps S0012's existing test.
   - Demo: runnable with the existing `GitCli` and `run_process` API. The seven expected lines match the code: `pushed`, `pushed`, four `refused`, and the ref list.
   - Architecture: the pure name rules sit in the domain, with no git call. The git command lines sit only in the `GitCli` wrapper. No new dependency or module.
   - Scope: this is within F0001's git wrapper (R9) and matches decision 23. No Out-of-scope item is touched.
3. tester: wrote the tests for criteria 1–10. They fail on purpose and are the coder's specification.
      - criterion 1: tests/domain/test_git.py::test_branch_name_that_git_would_not_take_as_a_branch_is_refused (parametrized over all 19 values)
      - criterion 2: tests/domain/test_git.py::test_branch_name_with_a_star_inside_or_refspec_syntax_is_refused (`x*y`, `""`, `-x`, `+main`, `:main`, `main:other`)
      - criterion 3: tests/domain/test_git.py::test_branch_name_that_git_takes_as_a_branch_is_accepted (all 8 values)
      - criterion 4: tests/adapters/test_git_cli_arguments.py::test_push_of_a_negative_refspec_is_refused_before_anything_runs
      - criterion 5: tests/adapters/test_git_cli_arguments.py::test_push_of_the_checked_out_branch_by_alias_is_refused_and_creates_nothing (`HEAD`, `@`; the remote's refs are compared before and after)
      - criterion 6: tests/adapters/test_git_cli_branches.py::test_push_of_a_local_tag_without_a_local_branch_raises_and_pushes_nothing
      - criterion 7: tests/adapters/test_git_cli_branches.py::test_delete_remote_branch_leaves_a_remote_tag_of_the_same_name. `HumanClone` has no tag method, so the tag is created and pushed with `run_git` in the human's clone at `tmp_path / "human"`.
      - criterion 8: tests/adapters/test_git_cli_branches.py::test_push_of_a_new_branch_tracks_it_as_its_upstream
      - criterion 9: tests/adapters/test_git_cli_branches.py::test_delete_remote_branch_removes_a_branch_the_human_pushed. The checkout fetches first, so `origin/keep` exists before the deletion.
      - criterion 10: tests/adapters/test_git_cli_branches.py::test_delete_remote_branch_of_an_invalid_ref_name_raises. Changed from `GitError` to `ValueError`, with the human's permission in decision 23. It also asserts that the remote's refs are unchanged.
      Files changed: tests/domain/test_git.py, tests/adapters/test_git_cli_arguments.py, tests/adapters/test_git_cli_branches.py. No new files. The existing S0020 tests are untouched.
      Imports: every module imports; nothing failed to collect. The failures are wrong results: the current `check_branch_name` accepts the new values (for example `feature/.x`, `x.lock`, `feature/x.lock/y`, `a\x7fb`). Criteria 8 and 9 may already pass on the current code. They guard the `refs/heads/<branch>` change.
      `make lint` is green. The type check was skipped, as this stage says.

   `make lint`: lint: green
   `make test`: FAILED tests/domain/test_git.py::test_branch_name_that_git_would_not_take_as_a_branch_is_refused[a\x7fb]
4. coder: implemented; `make check` green; the demo prints the seven expected lines.
   - `src/factory/domain/git.py`: `check_branch_name` still has its earlier refusals (empty, leading `-`, leading `+`, any `:`, any `*`). It now also refuses the whole values `HEAD` and `@` (`BRANCH_ALIASES`) and anything `git check-ref-format --branch` would refuse. It does this in the domain through the private helpers `_is_valid_ref_name`, `_is_forbidden_character` and `_is_valid_component`, which check:
     - the characters `^ ~ ? [ \ space`, control characters and DEL;
     - the sequences `..`, `@{` and `//`;
     - a leading or trailing `/`, and a trailing `.`;
     - a component that starts with `.` or ends with `.lock`.
   - `src/factory/adapters/git_cli.py`:
     - `push` runs `git push --porcelain --set-upstream origin refs/heads/<branch>`.
     - `delete_remote_branch` runs `git push --porcelain origin --delete refs/heads/<branch>` and treats only exit 0 as `"pushed"`.
     - `ALREADY_DELETED_MARKER` and its comment are removed.
   - Commits: 3ecbe25 (feat), c3f992a (refactor: the rule constants are now declared before `check_branch_name`, which uses them).
   - Design: the name rules are a hand-written port of git's rules in the domain. I rejected calling `git check-ref-format`, because the domain must not run a tool and the wrapper would need an extra process for each push. Only the source is qualified (no `:<dst>`), as decision 23 says.
   - Left alone: the explicit leading/trailing `/` check overlaps a little with the component split (an empty component would otherwise pass). I kept it explicit because it reads clearer. The docs (criterion 12) are the documenter's job.

   `make check`: check: green
5. reviewer: no findings.
   - Criteria 1–10: each has a test that checks what its criterion says. Criteria 1–3 in `tests/domain/test_git.py` cover the failing side of every Interface rule. The boundaries are tested on both sides: `HEAD` and `@` refused as a whole value, while `feature/HEAD` and `a@b` pass; `.lock` refused at the end of a component, while `x.lock.y` passes; `*` refused inside a name, not only at the end. Criteria 4–5 in `tests/adapters/test_git_cli_arguments.py` check that `BEFORE_PUSH` is not reached and that the remote's refs are unchanged. Criteria 6–10 in `tests/adapters/test_git_cli_branches.py` cover the local tag (`GitError`, nothing pushed), the remote tag left alone, the upstream after a push, the removal of `origin/keep`, and `a..b` as a `ValueError` with the refs unchanged. S0012's already-gone test is still there and covers removing `ALREADY_DELETED_MARKER`. The coder's entry reports the factory's `make check` as green.
   - Architecture: the name rules are pure and live in `factory.domain.git` (no I/O, no git call). The command lines change only in `GitCli` (`src/factory/adapters/git_cli.py:280` and `:290`), which name only the source, `refs/heads/<branch>`, as decision 23 says. The local operations keep `check_git_argument`.
   - Security: the git argv is built as a list, not a shell string. Names are validated before any process runs. No suppression markers, no secrets, no new dependencies.
   - Quality: the helpers are small and private and have no docstrings, as CLAUDE.md allows. The comments say why. The removed marker leaves no dead code behind, and the `delete_remote_branch` docstring is still accurate.
   - Ticket hygiene: the coder's entry records the main decision (porting git's rules into the domain rather than calling `git check-ref-format`) and what was rejected. The Assignment matches what was built. The docs criterion (12) still describes what the documenter has to write.
6. documenter: wrote criterion 12; `make check` green. No code findings: the diff matches the Interface.
   - `docs/project-guide.md`:
     - The operation table and the push paragraph now show `refs/heads/<branch>` in both command lines.
     - The push outcomes say a local tag is no branch (`push("v1")` is a `GitError`).
     - The `delete_remote_branch` text drops the `remote ref does not exist` wording, says a remote tag is left alone, and says `a..b` is now a `ValueError`.
     - The branch rule names the added refusals: `HEAD`, `@`, and git's branch-name rules with `^main` as the example. It also explains why `refs/heads/<branch>` is named, as the source only.
   - `docs/decisions.md`: the entry "A pushed branch is never read as a refspec" records the extension (decision 23) and why it is not the explicit `refs/heads/<b>:refs/heads/<b>` that decision 22 rejected.
   - Cross-read and found current: the push outcome meanings, the kill points, the sentence on the local operations, `README.md` and `docs/operator-guide.md`. The latter two don't mention these operations.
   - I did not run the demo script. The new sentences come from the Interface, the ticket log and the diff.
   - Nothing stale seen outside this story.

   `make check`: check: green
