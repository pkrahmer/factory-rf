---
stage: demo
pr: 22
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
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
2. intake: accepted
   - Interface: `check_branch_name(value: str) -> None` in `src/factory/domain/git.py` is concrete. The ticket says which wrapper methods call it (`GitCli.push`, `GitCli.delete_remote_branch`, as their first statement) and which keep `check_git_argument`. The ticket states the rules fully: what is refused, what is accepted, and the effect of a refusal (no process, no `BEFORE_PUSH`).
   - Criteria: criteria 1 and 2 cover the function's refusing and accepting sides. Criteria 3 to 6 cover the wrapper's failing sides for `+`, `:` and the `delete_remote_branch` cases. Criterion 7 covers the passing side (`a+b`). Criterion 8 covers the local operations that stay unrefused. Each criterion fits one test function. The `*` rule has its function-level case (`refs/heads/x*`) in criterion 1; a wrapper-level `*` test is not listed, and I accept that.
   - Demo: the script is runnable with the existing wrapper API and the Expect line gives four checkable lines.
   - Architecture: the pure check sits in `factory.domain`, and the I/O stays in the `GitCli` wrapper in the adapters layer. The test locations and fixtures (`remote`, `checkout`, `human`) follow CLAUDE.md.
   - Scope: it is within F0001's git wrapper scope (decision 22, which sits in FEATURE.md) and touches nothing in the Out of scope list.
3. tester: wrote the red tests for the refspec refusal. I created no new files; the tests are added to two existing ones.
   - criterion 1: tests/domain/test_git.py::test_branch_name_that_git_push_reads_as_an_option_or_a_refspec_is_refused (parametrized: "", "-x", "+main", ":main", "main:other", "HEAD:refs/heads/x", "refs/heads/x*")
   - criterion 2: tests/domain/test_git.py::test_branch_name_without_refspec_syntax_is_accepted (main, work-item/F0001-S0001, feature/x, a+b)
   - criterion 3: tests/adapters/test_git_cli_arguments.py::test_push_of_a_forcing_refspec_is_refused_before_anything_runs (the remote's main stays at the human's tip, and BEFORE_PUSH is reached 0 times)
   - criterion 4: tests/adapters/test_git_cli_arguments.py::test_push_of_a_deleting_refspec_is_refused_and_the_remote_branch_stays (the human pushes `keep` first)
   - criterion 5: tests/adapters/test_git_cli_arguments.py::test_push_of_a_refspec_naming_another_ref_is_refused_and_creates_nothing
   - criterion 6: tests/adapters/test_git_cli_arguments.py::test_delete_remote_branch_of_a_refspec_is_refused (parametrized: "+main", "main:x"; the remote's for-each-ref output is unchanged)
   - criterion 7: tests/adapters/test_git_cli_arguments.py::test_push_of_a_new_branch_with_a_plus_inside_its_name_is_pushed
   - criterion 8: tests/adapters/test_git_cli_arguments.py::test_delete_branch_of_a_refspec_like_name_is_not_refused_and_changes_nothing (parametrized: "+x", "x:y"; the checkout's refs are unchanged). The current code already passes this one. It guards against `check_branch_name` spreading to the local operations.
   Files changed: tests/domain/test_git.py and tests/adapters/test_git_cli_arguments.py.
   Could not import: `check_branch_name` from `factory.domain.git`. tests/domain/test_git.py fails at collection with an ImportError, and pytest stops the run there, so the wrapper tests have not run yet. Once the function exists, the wrapper tests for criteria 3–6 should fail because no ValueError is raised.
   make lint: green. I added no wrapper-level `*` test, because the criteria list none (intake accepted this).

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
4. coder: implemented the refspec refusal in commit 7e390b1.
   - `src/factory/domain/git.py`: the new `check_branch_name(value)` first calls `check_git_argument`, so an empty value or a leading `-` is still refused. It then raises `ValueError` for a leading `+`, any `:` and any `*`. A comment says why each one is refused: `+` forces, `:` names another ref or deletes one, `*` is a pattern.
   - `src/factory/adapters/git_cli.py`: `push` and `delete_remote_branch` now call `check_branch_name` in place of `check_git_argument`, as their first statement. In `push` the check runs before `_reach(BEFORE_PUSH)` and before any git process. The local operations are unchanged and still use `check_git_argument`.
   - Design: the function reuses `check_git_argument` rather than repeating its checks, so the documented rule stays one rule with a stricter push-side extension. I took no other approach: the human's decision 22 rejected pushing an explicit `refs/heads/<b>:refs/heads/<b>` refspec.
   - Refactor: I read the diff (3 lines in the wrapper, one function in the domain) and found nothing to change, so there is no refactor commit.
   - Demo: run by hand, it prints the expected four lines (`rejected`, `refused +main`, `refused :main`, `['human', 'one'] ['main']`).
   - `make check`: green; total coverage 99.49 %.
   - Open: criterion 10 (docs in `docs/project-guide.md` and `docs/decisions.md`) is the documenter's. I did not write it.

   `make check`: check: green
5. reviewer: no findings.
   - Criteria: criteria 1 to 8 each have a test that targets them. These are `tests/domain/test_git.py` (refused and accepted tables) and `tests/adapters/test_git_cli_arguments.py` (`+main` with a diverged `main`, `:keep`, `HEAD:refs/heads/other`, `delete_remote_branch` of `+main` and `main:x`, `push("a+b")`, and `delete_branch` of `+x` and `x:y`). The wrapper tests use the real bare remote. Their asserts check the remote's state, and criterion 3 also checks that `BEFORE_PUSH` was reached 0 times on the same `kill_points` that the `checkout` fixture uses. The failing side of each rule (`+`, `:`, `*`, empty, `-`) is tested in the domain. The `*` rule has no wrapper-level test, which intake accepted. The coder's entry records `make check` green.
   - Architecture: `check_branch_name` is pure and sits in `factory.domain.git`, beside `check_git_argument`, which it reuses. `GitCli.push` and `GitCli.delete_remote_branch` call it as their first statement, before `_reach(BEFORE_PUSH)` and before any process. The local operations are untouched.
   - Security: there are no markers, secrets or string-built commands. The error message quotes only the refused value.
   - Quality: the function has a docstring, and its comment gives the reason for each refused character. There is no duplication and no dead code.
   - Ticket hygiene: the log names decision 22 and the rejected explicit-refspec alternative. Assignment matches what was built. Criterion 10 still states what the documenter must write.
6. documenter: no findings; code matches the Interface.
   - `docs/project-guide.md` (git wrapper section): added the branch rule after the argument rule. It names `check_branch_name`, `push` and `delete_remote_branch`. It gives the reasons (`+` forces, `:` names another ref or deletes one, `*` is a pattern), says `a+b` is fine, says a refusal is a `ValueError` before git and before `BEFORE_PUSH`, and says the local operations keep `check_git_argument`.
   - `docs/decisions.md`: new entry "A pushed branch is never read as a refspec", placed after the option-like values entry. It records the three push cases and the `delete_remote_branch` case, that `+main` is a name git allows, and the rejected alternative (an explicit `refs/heads/<b>:refs/heads/<b>` refspec).
   - Cross-read against the diff and found current: README, `docs/operator-guide.md`, and the project guide's push, `delete_remote_branch` and kill-point text. Its line "pushed when the branch is gone from the remote" is now true for `+x` too, because that call is refused.
   - Nothing stale left untouched. I ran no new examples: the docs add prose only, and the ticket's demo was run by the coder.
   - `make check` is green.

   `make check`: check: green
