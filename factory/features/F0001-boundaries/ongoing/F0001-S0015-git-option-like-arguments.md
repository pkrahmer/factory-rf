---
stage: tests
pr: 17
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The git wrapper: no argument is read as an option, and git speaks one language

<!-- proposed by feature acceptance of 2026-10-13; refine before promoting -->

## Assignment (as of log entry 1)

Close two holes in the git wrapper (R9) that the feature acceptance of F0001 found.

**Option-like names.** `GitCli` passes a caller's branch, ref, start point or url to git where git still accepts options. So `push("--force")` runs `git push --porcelain --set-upstream origin --force`, which force-pushes the checked-out branch over another writer's commit. The acceptance reproduced this. It breaks "a push is never forced" (FEATURE.md decision 10, `docs/decisions.md`). `clone`, `checkout`, `delete_remote_branch`, `delete_branch`, `show_file`, `list_files` and `is_ancestor` have the same shape, found by reading the code. No git ref, branch name or remote url starts with `-`, so the wrapper refuses such a value with `ValueError` before git runs. It does so in every operation that takes one, the way `check_repository_path` guards paths (S0013).

Rejected (the human, 2026-10-13): passing the values after `--end-of-options`. `git reset` refuses that marker after `--hard`, `clone` wants `--` instead, and a refused value would then be a `GitError` or even `"unreachable"` (exit 128) depending on the command. One rule in the domain is simpler to state and to test.

**Locale.** The push outcomes `"unreachable"` and an already-deleted remote branch are recognised by git's English messages (S0006, S0012). `GitCli` inherits the process environment, so an operator whose locale selects translated git messages would get a `GitError` instead. Every git call therefore runs with `LC_ALL=C`, set last like the configuration isolation. This was found by reading the code and not reproduced. `LC_ALL=C` does not change how the wrapper reads paths: the `-z` listings are the paths' bytes whatever the locale, and `run_process` decodes them as UTF-8 itself.

Covers R9; keeps kept thing 13 (a push is never forced, recover by construction).

## Interface

`src/factory/domain/git.py` (new function, beside `check_repository_path`)

```python
def check_git_argument(value: str) -> None:
    """Raise ValueError for a ref, branch, start point, commit or url git could read as an option."""
```

The rules, each with a criterion below:

- `check_git_argument` raises `ValueError` for an empty value and for a value that starts with `-`; it accepts anything else (`main`, `origin/main`, `HEAD~1`, `work-item/F0001-S0001`, `a-b`, a path or `file://` url).
- `GitCli` calls `check_git_argument` before it starts git, and before it reaches any kill point, on:
  - `resolve(ref)`, `show_file(ref, …)`, `list_files(ref, …)`;
  - `is_ancestor(ancestor, descendant)`, both;
  - `log(ref, since=…)`, both when given; `changed_paths(since)`;
  - `clone(url)`; `checkout(branch, start_point=…)`, both when given;
  - `push(branch)`, `delete_remote_branch(branch)`, `delete_branch(branch)`;
  - `merge(ref)`, `reset_to(ref)`, `revert_paths(commit, …)`.

  A refused value starts no git process and changes nothing; `push` with a refused value does not reach `BEFORE_PUSH`.
- Every git command `GitCli` runs has `LC_ALL=C` in its environment, set after the process environment and `options.environment` together with the identity and the configuration isolation, so neither can lift it.

Tests: `tests/domain/test_git.py` for the function; `tests/adapters/test_git_cli_arguments.py` (new) for the wrapper, with the fixtures `remote`, `checkout` and `human`, and a stand-in `executable` from `tests/git_support.write_executable` where a test must show that git was not started or must read git's environment.

## Acceptance criteria

1. `check_git_argument` raises `ValueError` for `""`, `"-x"` and `"--force"`.
2. `check_git_argument` accepts `"main"`, `"origin/main"`, `"HEAD~1"`, `"work-item/F0001-S0001"` and a `file://` url.
3. With `main` diverged between `checkout` and `human`, `checkout.push("--force")` raises `ValueError`, the remote's `main` is still the human's commit, and `BEFORE_PUSH` was not reached.
4. `delete_remote_branch("--all")` raises `ValueError`, and the remote's branches are unchanged.
5. `clone("--upload-pack=x")` raises `ValueError` and the bound directory is not created.
6. `checkout("--detach")` and `checkout("x", start_point="--orphan")` raise `ValueError`; the current branch and HEAD are as they were.
7. `delete_branch("-D")` raises `ValueError`.
8. Each of `resolve`, `show_file`, `list_files`, `is_ancestor` (each position), `log` (`ref` and `since`), `changed_paths`, `merge`, `reset_to` and `revert_paths` raises `ValueError` for `"-x"`. A stand-in `executable` that records its calls was never started (a parametrized test).
9. `push("work-item/F0001-S0001")` of a new branch still returns `"pushed"`: a hyphen inside a name is fine.
10. A git command run by `GitCli` sees `LC_ALL=C`, also when the process environment and `options.environment` set `LC_ALL=de_DE.UTF-8` (a stand-in `executable` that writes its `LC_ALL` to a file).
11. make check stays green.
12. docs: `docs/project-guide.md`'s git wrapper section states the argument rule (`check_git_argument`, which operations, before anything runs) and `LC_ALL=C` beside the configuration isolation; `docs/decisions.md` records why option-like values are refused and not passed after `--end-of-options`.

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
try:
    a.push('--force')
except ValueError:
    print('refused')
b.fetch()
print([c.subject for c in b.log('origin/main')])
"
```
Expect: three lines: `rejected`, `refused`, `['human', 'one']`. The human's commit is still the remote's tip.

## Log (append only)

1. 2026-10-13 feature acceptance: proposed; the human refines and promotes.
2. intake: accepted
   - Interface: `check_git_argument(value: str) -> None` in `factory/domain/git.py` is concrete, and the rules name every `GitCli` operation that takes a ref, branch, start point, commit or url. I compared the list with the public methods of `git_cli.py`. `fetch`, `remote_branches`, `status`, `commit` and `move` take no such value (`move`'s paths are already guarded by `check_repository_path`). The `LC_ALL=C` ordering relative to the environment, identity and isolation is stated. Every Interface comment has a criterion.
   - Criteria: 1 and 2 test the function, with both the refusing and the accepting side. 3 to 8 each test one refusal and what stays unchanged (remote, directory, HEAD, no process started, `BEFORE_PUSH` not reached). 9 is the passing side for a hyphen inside a name. 10 tests the locale override. Each is testable by one test function (8 and 10 are parametrized). Each rule has its failing side.
   - Demo: runnable as written. Its `Expect:` line is checkable: `rejected`, `refused`, `['human', 'one']`.
   - Architecture: the rule is a pure function in the domain and the adapter calls it, as `check_repository_path` is used. This fits the layers and the git wrapper rule (R9).
   - Scope: it is within F0001's git wrapper scope and not in its "Out of scope". The feature's decision 21 records the human's choice of refusal over `--end-of-options`.
