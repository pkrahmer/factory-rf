# The factory's git runs no hooks

## Assignment (as of log entry 1)

The agent can write `/work/checkout/.git/hooks` (`drwxrwsr-x factory factory-work`, seen at the first start of 2026-10-17, `planning/overnight/first-start-checklist.md`, "Results", fault 2), and the factory's git runs the hooks it finds there as `factory`, the user who can read the hosting token. That is the indirect route to the token F0013 decision 15 named and left open; the first start confirmed it. The human's answer (2026-10-17): the factory's own git never runs hooks. `git_environment` in `src/factory/entry/wiring.py`, which already gives the factory's git `credential.helper` and `core.sharedRepository` as `GIT_CONFIG_KEY_<n>` and `GIT_CONFIG_VALUE_<n>` pairs, gains a third pair, `core.hooksPath` set to the null device. Git reads these pairs as command-line configuration, which wins over the checkout's own `.git/config`, so a `core.hooksPath` an agent writes there does not bring the hooks back. The bare remotes of the tests keep their hooks: git drops the `GIT_CONFIG_*` variables for the receiving side of a local push. The existing tests of a `pre-receive` or `update` hook push with `GitOptions()`, not with the factory's environment, so a new test pushes with `git_environment` to a remote whose `pre-receive` refuses. This is the first story of the feature, because it closes a route to the token. S0006, built right after it, takes away the agent's write access to `.git` altogether (fault 5: the configuration and `.git/info/attributes` too). This story stays as defence in depth: should a hook ever stand in `.git/hooks`, from a checkout made before S0006 or from a file the seal has not reached, the factory's git still does not run it. Two tests of F0010-S0003 change by the human's leave (FEATURE decision 7).

## Interface

`src/factory/entry/wiring.py`: `git_environment(helper: str = CREDENTIAL_HELPER) -> dict[str, str]`, signature unchanged, returns exactly these seven entries:

| Name | Value |
|---|---|
| `GIT_CONFIG_COUNT` | `3` |
| `GIT_CONFIG_KEY_0` | `credential.helper` |
| `GIT_CONFIG_VALUE_0` | `helper` |
| `GIT_CONFIG_KEY_1` | `core.sharedRepository` |
| `GIT_CONFIG_VALUE_1` | `group` |
| `GIT_CONFIG_KEY_2` | `core.hooksPath` |
| `GIT_CONFIG_VALUE_2` | `os.devnull` (`/dev/null`) |

Its comment says why the third pair is there: the agent can write the checkout's hooks, and the factory's git runs as the user who can read the token. Nothing else in `wiring.py` changes; `git_options(settings)` still hands `git_environment()` to `GitOptions`, and `GitCli` is not changed.

Tests: a new module `tests/entry/test_git_hooks.py`, with the `remote` fixture of `tests/conftest.py` and `clone` of `tests/git_support.py`. Each hook it installs is an executable shell script that creates a marker file under `tmp_path`, outside the checkout, so the marker never enters a commit. The factory's side runs `GitCli(checkout, GitOptions(environment=git_environment(<helper>)))`; the other side runs `GitCli(checkout, GitOptions())`, the wrapper's own isolation without the factory's environment, so that each row shows the hook is real. By the human's leave (FEATURE decision 7), and no other change to an earlier story's test, in `tests/entry/test_wiring_boundaries.py` (F0010-S0003):

- `test_git_environment_gives_the_credential_helper_and_the_shared_group`: the expected dict becomes the seven entries of the table above, for both rows; the test is renamed `test_git_environment_gives_the_credential_helper_the_shared_group_and_no_hooks`.
- `test_the_built_git_runs_with_the_git_options_of_the_settings`: its `pre-commit` hook no longer runs, so it observes the environment of the built git through a stand-in `git` first on the `PATH` (monkeypatched). The stand-in is written with `write_executable` of `tests/git_support.py` and renamed to `git` in its folder. It writes its environment as JSON to a file under `tmp_path` and hands over to the real git with `os.execv`, the real git's path read with `shutil.which("git")` before the `PATH` changes. Its four assertions stay, and it also asserts `GIT_CONFIG_KEY_2` = `core.hooksPath` and `GIT_CONFIG_VALUE_2` = `/dev/null`. Its name stays.

## Acceptance criteria

1. `git_environment()` returns exactly the seven entries of the Interface with the helper `/usr/local/bin/git-credential-factory`, and `git_environment("/opt/other-helper")` the same seven with `/opt/other-helper` as `GIT_CONFIG_VALUE_0` (the changed test of `tests/entry/test_wiring_boundaries.py`).
2. An executable `pre-commit` hook in the checkout's `.git/hooks` does not run when the factory's git commits with `git_environment`, and the commit is made; the same hook runs when `GitCli` commits with `GitOptions()`. One parametrized test holds this and criteria 3 to 5 as eight rows: each of the four operations once with `git_environment` and once with `GitOptions()`.
3. An executable `post-checkout` hook does not run when the factory's git checks out a new branch from `origin/main` with `git_environment`, and the branch is checked out; it runs with `GitOptions()`.
4. An executable `pre-push` hook does not run when the factory's git pushes a branch with `git_environment`, and `push` returns `pushed`; it runs with `GitOptions()`.
5. A `core.hooksPath` written into the checkout's `.git/config` (`git config core.hooksPath <folder>`, the folder under `tmp_path` outside the checkout and holding an executable `pre-commit`) does not bring the hook back: with `git_environment` the commit runs no hook; with `GitOptions()` the hook in that folder runs.
6. The built boundaries' git runs with the settings' identity and the factory's git environment, `core.hooksPath` = `/dev/null` among it (the changed test of `tests/entry/test_wiring_boundaries.py`).
7. A bare remote's hooks still run when the factory's git pushes to it: with an executable `pre-receive` hook in the `remote` fixture that exits 1, `push` of a new branch returns `rejected` and the remote has no such branch, both with `git_environment` and with `GitOptions()`. The two are rows of one parametrized test in `tests/entry/test_git_hooks.py`.
8. What must still hold: the factory's git still gets the token through its credential helper, and the existing tests of a remote's hooks and of the git wrapper pass (the tests of `tests/adapters/test_git_cli_writing.py`, `tests/adapters/test_git_cli_branches.py`, `tests/test_stop_table.py` and `tests/test_git_credential_helper.py`).
9. `make check` stays green.
10. docs: the operator guide's paragraph "Left for v2" in *The hosting-service token* no longer names git's hooks as a route: the factory's git sets `core.hooksPath` to `/dev/null` through its own environment, which wins over a `core.hooksPath` in the checkout's `.git/config`, so a hook in `/work/checkout/.git/hooks` never runs as `factory`; the project commands stay the route left for v2 (S0006's docs criterion later adds that the agent cannot write `.git` at all). The project guide's sentence on `git_environment` says seven entries, `GIT_CONFIG_COUNT=3` and the third pair. The decision log gets an entry "The factory's git runs no hooks" (the first start of 2026-10-17 confirmed the route, the human's answer, why the pairs win over the checkout's configuration, why a bare remote's hooks still run) and marks the open point on hooks in the entry "The token is a bind mount into a folder only the factory can enter" as closed by it. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "from factory.entry.wiring import git_environment; print(sorted(git_environment().items()))"
```
Expect: one line: `[('GIT_CONFIG_COUNT', '3'), ('GIT_CONFIG_KEY_0', 'credential.helper'), ('GIT_CONFIG_KEY_1', 'core.sharedRepository'), ('GIT_CONFIG_KEY_2', 'core.hooksPath'), ('GIT_CONFIG_VALUE_0', '/usr/local/bin/git-credential-factory'), ('GIT_CONFIG_VALUE_1', 'group'), ('GIT_CONFIG_VALUE_2', '/dev/null')]`.

```bash
uv run python -c "
import os, subprocess, tempfile
from pathlib import Path
from factory.entry.wiring import git_environment
repo = Path(tempfile.mkdtemp()) / 'repo'
subprocess.run(['git', 'init', '-q', str(repo)], check=True)
hook = repo / '.git' / 'hooks' / 'pre-commit'
hook.write_text('#!/bin/sh\necho hook ran\n', encoding='utf-8')
hook.chmod(0o755)
for label, extra in (('plain', {}), ('factory', git_environment())):
    done = subprocess.run(['git', '-C', str(repo), '-c', 'user.name=demo', '-c', 'user.email=demo@example.invalid', 'commit', '-q', '--allow-empty', '-m', label], env={**os.environ, **extra}, capture_output=True, text=True, check=True)
    print(label, 'hook ran' in done.stdout + done.stderr)
"
```
Expect: two lines: `plain True` and `factory False`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/entry/test_git_hooks.py tests/entry/test_wiring_boundaries.py tests/test_git_credential_helper.py tests/adapters/test_git_cli_writing.py tests/adapters/test_git_cli_branches.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
