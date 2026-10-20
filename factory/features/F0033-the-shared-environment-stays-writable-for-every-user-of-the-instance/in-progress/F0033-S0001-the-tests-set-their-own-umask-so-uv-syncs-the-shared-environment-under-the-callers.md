---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 322
comments_read: []
handed_over: null
claim:
  instance: self
  stage: review
  started_at: '2026-10-20T03:12:46.483254Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T03:07:05.394197Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T03:07:05.400190Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T03:07:20.335856Z'
  stage: intake
  run: 86a602382667462689d7937fa3fd09d7
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T03:07:40.825004Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T03:10:05.320191Z'
  stage: tests
  run: 3bd08a1a75524331b7dc53a0d442046c
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T03:10:25.606843Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T03:12:25.649242Z'
  stage: doing
  run: ce6f409e5c2c45b1855eebad87eec620
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T03:12:46.483254Z'
  stage: review
---

# The tests set their own umask, so uv syncs the shared environment under the caller's

## Description

The `Makefile`'s `test` recipe runs `umask 022` before `uv run pytest`, because the tests' own checkouts must not come out group-writable, or the seal refuses them. But `uv run` syncs the checkout's `.venv` first, so a reinstall of the project inside `make test` also runs under `022`. On 2026-10-19 an agent's run, as `agent`, left the project's `dist-info` folder in `.venv` as `drwxr-sr-x` with `-rw-r--r--` files. The factory's next `make lint`, as `factory`, could not remove them, and the instance stopped with `main_branch_failing` (the feature's *Goal*). This story moves the tests' umask into the tests. A `pytest_configure` hook in `tests/conftest.py` sets the process umask to `0o022` for every pytest run, whatever umask the run was started under. A test module run on its own with `uv run pytest <module>` then gets the same umask as `make test`. Once this story is merged, the human's change 1 drops `umask 022` from the recipe, so uv syncs under the caller's umask: `002` in the instance and under `sudo`. Nothing under `src/` changes, and the coder writes nothing (the feature's decision 4). Unchanged: the `group_umask` fixture, which sets `0o002` for one test and then restores the previous umask (now `0o022`); every other test; and the `Makefile`, which is the human's.

## Interface

No module under `src/factory/` changes.

`tests/conftest.py` (under the leave of the feature's decision 5) gains a constant and a hook:

```python
TESTS_UMASK = 0o022


def pytest_configure() -> None:
    """Run every test under the umask `0o022`, whatever umask pytest was started under."""
```

- `pytest_configure` takes no parameter: pluggy calls a hook implementation with only the arguments it names, and an unused `config` is ruff's `ARG001`. It calls `os.umask(TESTS_UMASK)` and nothing else. It restores no earlier umask: the run's process ends with the run.
- Each pytest-xdist worker loads `tests/conftest.py` as well, and it starts under the main process's umask in any case, so `make test`'s workers run under `0o022` too. No criterion of its own: no test can tell the two causes apart.
- The fixtures `group_umask` (`tests/conftest.py`) and `open_umask` (`tests/adapters/test_claude_runtime_file_modes.py`) stay as they are. They set their own umask for one test and restore the one before, which is then `0o022`.

Tests (the tester writes them): `tests/test_tests_umask.py` (new), at the `tests/` root because the hook lies outside the layers. It starts its child pytest through `factory.adapters.process.run_process`, as `tests/test_entrypoint_umask.py` starts its shell.

## Acceptance criteria

1. A test runs under the tests' umask: `test_a_test_runs_under_the_tests_umask` reads the process umask (`os.umask(0)` and then setting it back) and finds `0o022`, which equals `TESTS_UMASK`. A file it writes with `Path.write_text` in `tmp_path` has the mode bits `0o644`, and a folder it makes with `Path.mkdir` has `0o755` (`stat.S_IMODE`).
2. The umask holds whatever umask pytest was started under (rows of one parametrized test, the starting umask `000`, `002`, `022` and `077`). Each row runs `sh -c 'umask <row>; exec "$@"' sh <sys.executable> -m pytest -p no:cacheprovider --no-header tests/test_tests_umask.py::test_a_test_runs_under_the_tests_umask` through `run_process`. It runs in the repository's root, with only `PATH`, `HOME` and `TMPDIR` in its environment (`TMPDIR` the row's `tmp_path`), a time limit of 60 seconds and `merge_stderr=True`. Each row ends with exit status 0, and the last non-blank line of its output starts with `1 passed in `. Without the hook, the rows `000`, `002` and `077` fail.
3. `make check` stays green.
4. docs: `docs/project-guide/processes-and-checks.md`, *Project commands*, a short paragraph at the end of the section's own text, before its subsection *Known results*. The tests set their own umask, `0o022`, in `pytest_configure` of `tests/conftest.py`, so that the checkouts they make are not group-writable and the seal accepts them, whatever umask pytest starts under. The `Makefile` sets no umask for `make test`, so `uv run` syncs `.venv` under the caller's umask, which is `002` in the container and under `sudo`. A test that needs another umask sets it and restores the earlier one, as `group_umask` does. `docs/decisions.md`: an entry *The tests set their own umask, and uv syncs under the caller's*, dated with the story. It covers the fault of 2026-10-19 (`main_branch_failing`, the agent-owned `factory-0.1.0.dist-info` made under `make test`'s `umask 022`), the decision, and the rejected `UV_NO_SYNC` for agents, a repair of modes after every agent call, and a shell wrapper in the recipe (the feature's decisions 1 and 2). It adds one line naming the new entry to the entry *The factory's user may become `agent` for one command only, and a missing agent user is a stop*, which explains the entrypoint's `umask 002`. `docs/operator-playbook.md`, section 5: the row *`make check` red only inside v1.1's container* changes its *Done* column to: the tests set `umask 022` themselves (`tests/conftest.py`), and `make mutants` runs under `umask 022`. A new row follows it. *Seen*: `main_branch_failing`, `uv` cannot remove `.venv/.../factory-0.1.0.dist-info/INSTALLER`. *Cause*: `make test`'s `umask 022` applied to uv's reinstall as `agent`. *Done*: `chown factory:factory-work` and `chmod g+w` by hand, then F0033. `README.md` and `docs/operator-guide.md`: none, since nothing the operator configures changes.

## Smoke test

```bash
umask 002
uv run pytest -p no:cacheprovider --no-header tests/test_tests_umask.py 2>&1 | tail -n 1 | grep -c -E '^5 passed in '
```
Expect: `1` (criterion 1's test and criterion 2's four rows pass, started under `umask 002`)

```bash
grep -c -F 'os.umask(TESTS_UMASK)' tests/conftest.py
```
Expect: `1`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: no `src/` change. `tests/conftest.py` gains `TESTS_UMASK = 0o022` and `pytest_configure() -> None`, which takes no parameter and calls only `os.umask(TESTS_UMASK)`. The new test module `tests/test_tests_umask.py` is named, and it starts its child through `factory.adapters.process.run_process`. The Interface has no comment with a behaviour that lacks a criterion. The xdist note says it has no criterion of its own, with its reason.
   - Criteria: criterion 1 is one test function. It checks the umask value, the 0o644 file mode and the 0o755 folder mode. Criterion 2 is one parametrized test with rows 000, 002, 022 and 077. Its command, environment, time limit, exit status and last output line are all spelled out, and it names the rows that fail without the hook. The rule is "the umask is 0o022 whatever the starting umask", and the rows cover the side that must change (000, 002, 077) and the side that is already right (022). The hook has no failing input of its own. Criterion 3 is `make check`. Criterion 4 is the docs criterion, with paths, sections and wording.
   - Smoke test: both commands are runnable. The first expects `5 passed in `, which is 1 test plus 4 rows. The second expects a count of 1 for `os.umask(TESTS_UMASK)`. Both `Expect:` lines can be checked against the output.
   - Architecture: the hook is in `tests/conftest.py`, the shared fixtures file, and the child process starts through the process wrapper, not a direct subprocess. Nothing is added to `src/`, so the layers are untouched.
   - Scope: this matches the feature's Scope, S0001 and decisions 4 and 5. The `Makefile`, the `mutants` recipe and the other items in Out of scope are not touched. Decision 5 gives the leave to change `tests/conftest.py`.
4. factory: started tests as self.
5. tester: Wrote the tests and the `tests/conftest.py` hook from the Interface. The story says the coder writes nothing and the hook lives in a test file, which is in my write paths, so I wrote it under the feature's decision 5.

   - criterion 1: tests/test_tests_umask.py::test_a_test_runs_under_the_tests_umask
   - criterion 2: tests/test_tests_umask.py::test_the_tests_umask_holds_whatever_umask_pytest_was_started_under (rows `000`, `002`, `022`, `077`). Each row starts the child through `factory.adapters.process.run_process` with `sh -c 'umask <row>; exec "$@"' sh <sys.executable> -m pytest -p no:cacheprovider --no-header <criterion 1's test id>`. The child runs in the repository root, with only `PATH`, `HOME` and `TMPDIR` (the row's `tmp_path`) in its environment, a 60 s time limit and `merge_stderr=True`. The test asserts exit status 0 and that the last non-blank line starts with `1 passed in `.
   - criterion 3 (`make check`) and criterion 4 (docs): no test. They belong to the factory's checks and the docs stage.

   Files: created `tests/test_tests_umask.py`. Changed `tests/conftest.py`: added `TESTS_UMASK = 0o022` and `pytest_configure() -> None`, which calls only `os.umask(TESTS_UMASK)`. No other earlier test file changed.

   Red run: I ran `make test` once before adding the hook. It failed on collection: `ERROR tests/test_tests_umask.py - ImportError`, because `TESTS_UMASK` did not exist in `conftest` yet. Every other test passed, and the coverage gate was reached (99.14 %). That was the only module the runner could not import.

   After adding the hook, I ran the story's smoke-test command once under `umask 002` to check the hook: `5 passed in 2.27s`. That is one run beyond step 2's single `make test`, so the hook I wrote is checked, not assumed. `make lint` is green, after fixing one I001 (a blank line) in conftest. I skipped the type check, as the stage says.

   Open: nothing for the coder to write. The next stage only needs `make check` green and the docs of criterion 4.

   `lint`: lint: green (0.0 s)
   `test`: test: green (47.0 s)
6. factory: started doing as self.
7. coder: I wrote no code. The story says that nothing under `src/` changes and that the coder writes nothing, under the feature's decision 4. The tester already wrote the hook in `tests/conftest.py` under decision 5: `TESTS_UMASK = 0o022` and `pytest_configure() -> None`, which calls only `os.umask(TESTS_UMASK)`. They also wrote the new tests in `tests/test_tests_umask.py`.

   What I did:
   - I read the diff against `main`, which covers only those two test files.
   - I checked the hook against the `## Interface`. It matches: no parameter, one `os.umask` call, and no earlier umask restored.
   - I ran `make check` in the foreground. It is green (`test: green (45.4 s)`, total coverage 99.14 %, `check: green`).

   Main choice: leave the tester's hook exactly as it is, since I never edit tests. The rejected alternative was moving the hook to a module under `src/`. That would contradict the Interface ("No module under `src/factory/` changes"), and the hook belongs to the test run, not to the package.

   Refactor: nothing to change. There is no diff of mine, and the hook is already minimal.

   Description: no journal entry changed the meaning of the task, so the Description stays as it is.

   Noticed, not touched: criterion 4's docs (`docs/project-guide/processes-and-checks.md`, `docs/decisions.md`, `docs/operator-playbook.md` section 5) are the documenter's. The `Makefile`'s `umask 022` in the `test` recipe stays until the human's change 1 drops it.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
