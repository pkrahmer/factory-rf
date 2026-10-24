---
stage: approval
blocked: null
round: 0
attempts: 1
crashes: 0
pull_request: 412
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T16:16:30.642974Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T16:16:30.648814Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-24T16:16:55.450012Z'
  stage: intake
  run: 7ceb56bb03c54c26b93d967b304006c5
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-24T16:17:16.090225Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-24T16:20:18.412903Z'
  stage: tests
  run: e824a66578b8489295ab5cf0ea526858
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-24T16:20:38.845912Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-24T16:22:11.933821Z'
  stage: doing
  run: daf52a504a4f4087b8c9d4643812fd24
- number: 8
  speaker: factory
  kind: stall
  at: '2026-10-24T16:22:11.956154Z'
  stage: doing
  run: daf52a504a4f4087b8c9d4643812fd24
  reason: check_red
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-24T16:22:34.652795Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-24T16:25:34.180105Z'
  stage: doing
  run: ccd07be656f54f78b6fca331b7271f2c
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-24T16:25:55.653842Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-24T16:26:36.727074Z'
  stage: review
  run: 72aeaf1ae32d40299e51b6dd06ff37b5
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-24T16:26:56.963868Z'
  stage: docs
- number: 14
  speaker: documenter
  kind: result
  at: '2026-10-24T16:27:25.106739Z'
  stage: docs
  run: c1f1e128dfa54140be528e322f384ef5
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-24T16:27:45.537428Z'
  stage: smoke-test
- number: 16
  speaker: smoke-tester
  kind: result
  at: '2026-10-24T16:28:08.007002Z'
  stage: smoke-test
  run: dbe8e79ed26d4e38b060f878f462a1e6
---

# No test sees the agent's login

## Description

An agent's run holds its login in its environment: `CLAUDE_CODE_OAUTH_TOKEN` under the subscription, `ANTHROPIC_API_KEY` under an API key, which the login shell hands to the runtime (`factory.adapters.agent_launch`). Every test an agent runs (`make test`, `make check`, a smoke test's pytest) inherits that environment, and so does every child process a test starts with the process's own environment (the `version()` calls of both runtimes). On 2026-10-24 an instance on an API key failed `tests/adapters/test_opencode_runtime_launch.py::test_the_version_is_the_first_word_of_a_call_without_login_words`, whose stand-in inherited `ANTHROPIC_API_KEY`, and pytest's assertion message printed the whole inherited environment, the key in full, into the run's output and from there into a journal entry (decision 21 of `feature.md`). This story makes the suite independent of the login of whoever runs it: one fixture in `tests/conftest.py`, used by every test, removes the two variables from the test process's environment before each test, so no test and no child process a test starts sees them, and the version test's assertion names only variable names when it fails. Nothing under `src/` changes; the runtimes still pass the login exactly as today. What stays: every other test as it is; the login of the agent's own run, which the factory gives and the suite never reads.

## Interface

No module under `src/factory/` changes.

`tests/conftest.py`: one fixture with `autouse=True`, named by the tester, that removes `LOGIN_VARIABLE` and `API_LOGIN_VARIABLE` (the two names `factory.adapters.agent_launch` defines, imported from there, not written again) from the test process's environment for the duration of each test, through `monkeypatch.delenv(name, raising=False)`, so the environment is restored after the test and a test may still set either name itself with `monkeypatch.setenv`. Leave: decision 18 (i) of `feature.md`.

`tests/adapters/test_opencode_runtime_launch.py::test_the_version_is_the_first_word_of_a_call_without_login_words`: its last assertion compares against the set of the call's variable names, `assert API_LOGIN_VARIABLE not in set(call.environment)`, so that a failure prints names and no value; the test keeps its name, its setup and what it checks. Leave: decision 18 (i).

Tests (the tester writes them): one new test module at the `tests/` root, `tests/test_no_agent_login.py` (the smoke test names it), holding one parametrized test over the two names that asserts the name is not in `os.environ` inside a test.

## Acceptance criteria

1. Inside a test, neither `CLAUDE_CODE_OAUTH_TOKEN` nor `ANTHROPIC_API_KEY` is in `os.environ`, also when the pytest process was started with both set (rows of one parametrized test over the two names; the smoke test runs it with both set).
2. A test that sets one of the two names with `monkeypatch.setenv` sees the value it set (one row per name in the same new module), and after the test the variable is back as the pytest process had it: the fixture removes through `monkeypatch`, not through `os.environ` directly (a row that reads `tests/conftest.py`'s text and finds `monkeypatch.delenv` and no `os.environ.pop` and no `del os.environ`).
3. `tests/adapters/test_opencode_runtime_launch.py::test_the_version_is_the_first_word_of_a_call_without_login_words` passes when the pytest process was started with `ANTHROPIC_API_KEY` set (the smoke test), and its last assertion is `assert API_LOGIN_VARIABLE not in set(call.environment)`.
4. Every other test under `tests/` keeps its name and passes unchanged.
5. `make check` stays green.
6. docs: `docs/project-guide/processes-and-checks.md`, in its passage on the tests (or the section that names `tests/conftest.py`'s shared fixtures): one paragraph that the suite removes the agent's two login variables from every test's environment, why (an agent's run holds them; a child process with the process's own environment inherits them; an assertion message prints what it compares), and that an assertion about an environment compares names (`set(environment)`), never the mapping. `README.md`, `docs/operator-guide.md`, `docs/decisions.md`: none (no behaviour of the factory changes).

## Smoke test

```bash
env "$(printf 'ANTHROPIC_%s=x' API_KEY)" "$(printf 'CLAUDE_CODE_OAUTH_%s=x' TOKEN)" uv run pytest tests/test_no_agent_login.py "tests/adapters/test_opencode_runtime_launch.py::test_the_version_is_the_first_word_of_a_call_without_login_words" 2>&1 | tail -1 | sed -E 's/[0-9]+ passed/N passed/; s/ in [0-9.]+s.*$//'
```
Expect: one line that starts with `N passed` and names no `failed` and no `error`.

## Journal

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: no `src/` change. It names `tests/conftest.py` (one autouse fixture using `monkeypatch.delenv(name, raising=False)`), the two constants `LOGIN_VARIABLE` and `API_LOGIN_VARIABLE` (both exist in `factory.adapters.agent_launch`, lines 47 and 49), the one assertion in the version test (currently line 246, `not in call.environment`), and the new module `tests/test_no_agent_login.py`. The fixture's name is left to the tester, as the story says.
   - Criteria: each is testable by one parametrized test or one named test. Criterion 1 covers both names. Criterion 2 covers the set side (a test that sets the name sees its value) and the restore side (a text row on `conftest.py` that requires `monkeypatch.delenv` and forbids `os.environ.pop` and `del os.environ`). Criterion 3 covers the version test's passing and the exact text of its last assertion. Criteria 4 and 5 are the usual closing ones. Criterion 6 is the docs criterion. The Interface has no failing-side rule, because nothing is validated or rejected.
   - Smoke test: runnable. The `env` and `printf` splitting only keeps the variable names out of the command text. `pyproject.toml` already sets `-q` in `addopts` and the command adds none, so the summary line `N passed in Xs` is printed. `tail -1 | sed` reduces it to `N passed`, which the `Expect:` line can be checked against.
   - Architecture: tests only, with the fixture in the shared `tests/conftest.py` and the new module at the `tests/` root, as CLAUDE.md allows. It imports the names from the adapters layer and does not repeat them.
   - Scope: it is listed in `feature.md`'s Scope ("`tests/conftest.py`: no test sees the agent's login (S0014)"), it is not in Out of scope, and it follows the human's decision 21. The change to the opencode version test, written by another story, has the leave in decision 18 (i).
4. factory: started tests as self.
5. tester: Tests written. The story is tests-only and the coder never edits tests (R9), so the tester stage also made the two test changes the Interface names: the conftest fixture and the version test's last assertion. Both have the leave of decision 18 (i).

   - criterion 1: tests/test_no_agent_login.py::test_a_test_does_not_see_the_login (rows `subscription`, `api-key`)
   - criterion 2: tests/test_no_agent_login.py::test_a_test_that_sets_the_login_sees_its_own_value (one row per name) and tests/test_no_agent_login.py::test_the_login_is_removed_through_monkeypatch (rows: `monkeypatch.delenv` present, no `os.environ.pop`, no `del os.environ` in tests/conftest.py)
   - criterion 3: tests/adapters/test_opencode_runtime_launch.py::test_the_version_is_the_first_word_of_a_call_without_login_words (passing it with `ANTHROPIC_API_KEY` set is the smoke test's job). Its last line is pinned by tests/test_no_agent_login.py::test_the_version_test_compares_variable_names_only.
   - criterion 4: the existing suite, unchanged apart from the one assertion above.
   - criterion 5: `make check`, which is the coder's to run. Criterion 6 (docs) is the documenter's.

   Files:
   - created: tests/test_no_agent_login.py
   - changed: tests/conftest.py, which has the new autouse fixture `without_agent_login`. It imports `LOGIN_VARIABLE` and `API_LOGIN_VARIABLE` from `factory.adapters.agent_launch` and calls `monkeypatch.delenv(name, raising=False)` for each.
   - changed: tests/adapters/test_opencode_runtime_launch.py, where the last assertion is now `assert API_LOGIN_VARIABLE not in set(call.environment)`. The test keeps its name, setup and check.

   Run: `make test` was green (62.3 s, coverage 99.18 %), and every import resolved. That run came before I added `test_the_version_test_compares_variable_names_only`, so the new test has not run yet; the factory's run will be its first. Because the fixture is already in place, these tests pass rather than fail red, and nothing under `src/` is meant to change. What is left for the coder is `make check` (the type check included) and handing on to the docs stage. `make lint` is green, after `ruff format` wrapped two lines.

   Rejected: checking from inside the suite that the variable comes back after a test, because pytest's own process state cannot be seen across tests. Criterion 2 pins that through its text row instead, as it says.

   `lint`: lint: green (0.5 s)
   `test`: test: green (62.0 s)
6. factory: started doing as self.
7. coder: No code changed. As the Interface says, nothing under `src/factory/` changes in this story. The tester already made the only changes it needs: the autouse fixture `without_agent_login` in `tests/conftest.py`, the version test's last assertion in `tests/adapters/test_opencode_runtime_launch.py`, and the new `tests/test_no_agent_login.py`. They are on this branch, and I left them as they are (R9).

   What I did: ran `make check`, which ended with `check: green` (test: green, 63.4 s, coverage 99.18 %). That run includes `test_the_version_test_compares_variable_names_only`, which the tester had not run yet. I also ran the smoke test's pytest command with both login variables set to `x`: `9 passed`, no failures and no errors.

   Main choice: to add nothing under `src/`. The alternative I rejected was to strip the login variables inside the runtimes' `version()` calls. That would change the factory's behaviour, which is outside this story's scope, since the story says the runtimes keep passing the login exactly as they do today.

   Refactor: there is no diff of mine to refactor.

   Noticed but did not touch: none. The Description is unchanged, because no journal entry changed what the task means. Criterion 6 (the paragraph in `docs/project-guide/processes-and-checks.md`) is for the documenter.
8. factory: Stage doing stalled (attempt 1 of 2): a check is red after the stage: `check`
   Using CPython 3.12.15 interpreter at: /usr/local/bin/python3.12
   Creating virtual environment at: .venv
   Installed 106 packages in 90ms
   Bytecode compiled 4164 files in 337ms
   All checks passed!
   Bytecode compiled 4164 files in 77ms
   lint: green (0.5 s)
   Bytecode compiled 4164 files in 99ms
   make: *** [Makefile:39: types] Error 139
9. factory: started doing as self.
10. coder: No code changed this round either: as the Interface says, nothing under `src/factory/` changes. The only changes are the tester's: the autouse fixture `without_agent_login` in `tests/conftest.py`, the last assertion in `tests/adapters/test_opencode_runtime_launch.py`, and the new `tests/test_no_agent_login.py`. They stay as they are (R9).

    The stall: the factory's `make check` stopped at `make: *** [Makefile:39: types] Error 139`. That is a segfault of the mypy process, not a type error, and it happened right after the run created a fresh `.venv`. This story changes only tests, and those type-check cleanly. I could not reproduce the crash:
    - `make check` in the foreground ended with `check: green` (test: green, 61.8 s, coverage 99.18 %).
    - `make types` passed three times with the existing cache: `Success: no issues found in 751 source files`, 0.2 s each.
    - It passed twice more from a cold cache (`MYPY_CACHE_DIR` set to a fresh folder from `mktemp -d` each time), 3.9 s each.

    So the crash looks like a one-off failure of mypy itself, or of the machine, outside this work item. If it comes back on the factory's check, it needs the human, not a code change here.

    Main choice: to add nothing under `src/` and hand forward. The alternative I rejected was to strip the login variables inside the runtimes' `version()` calls. That would change the factory's behaviour, which the story rules out.

    Refactor: there is no diff of mine to refactor.

    Noticed but did not touch: the segfault (exit 139) of `make types` in a freshly created venv, which I could not reproduce. The Description is unchanged, because no journal entry changed what the task means. Criterion 6 (the paragraph in `docs/project-guide/processes-and-checks.md`) is for the documenter.

    `check`: check: green
    `duplicates`: duplicates: 14 new, 38 known, 0 gone
11. factory: started review as self.
12. reviewer: no findings

    What I read: the work item, and `git diff main...HEAD -- . ':!factory'`, which touches three files: `tests/conftest.py`, `tests/adapters/test_opencode_runtime_launch.py` and the new `tests/test_no_agent_login.py`. Nothing under `src/` changes, as the Interface says.

    Checks against the criteria:
    - criterion 1: `tests/test_no_agent_login.py::test_a_test_does_not_see_the_login` is one parametrized test with a row for each name. Each row asserts against `set(os.environ)`, so a failure prints names only. The started-with-both-set side belongs to the smoke test, as the criterion says.
    - criterion 2, set side: `test_a_test_that_sets_the_login_sees_its_own_value` has one row per name.
    - criterion 2, restore side: `test_the_login_is_removed_through_monkeypatch` checks the text of `tests/conftest.py` in three rows: `monkeypatch.delenv` present, no `os.environ.pop`, no `del os.environ`. On `main`, `tests/conftest.py` does not contain `monkeypatch.delenv`, so the present row pins the new fixture and not some earlier text.
    - the fixture: `without_agent_login` at `tests/conftest.py:64` imports both names from `factory.adapters.agent_launch` instead of writing them again, and removes each through `monkeypatch.delenv(name, raising=False)`, as the Interface asks.
    - criterion 3: the version test's last line is now `assert API_LOGIN_VARIABLE not in set(call.environment)` (`tests/adapters/test_opencode_runtime_launch.py:246`). `test_the_version_test_compares_variable_names_only` pins that line. The test's name and setup are unchanged; the diff changes only that line.
    - criteria 4 and 5: the factory's `make check` after the coder was green (journal entry 10: `check: green`). That came after the stall in entry 8, a mypy segfault (exit 139) in a fresh venv, which entry 10 could not reproduce. This diff changes no file that bears on that crash.
    - the Interface: it states no rejected input and no limit, so this group has no failing side to test.

    Architecture and security: tests only, with the shared fixture in `tests/conftest.py` and the new module at the `tests/` root, as `CLAUDE.md` allows. No silencing marker and no secret; the test values are `"x"`.

    Hygiene: the journal gives the main decision, nothing under `src/`, and what was rejected: stripping the login inside the runtimes' `version()` calls. The Description matches what was built. The docs criterion, criterion 6, still says what the reader must know.

    Earlier tests (`git diff --name-status main...HEAD`, status other than `A`):
    - `tests/conftest.py`: the human's leave, decision 18 (i) of `feature.md`, which the story names.
    - `tests/adapters/test_opencode_runtime_launch.py`: the human's leave, decision 18 (i) of `feature.md`, which the story names. Only the last assertion of `test_the_version_is_the_first_word_of_a_call_without_login_words` changed, within that leave.
13. factory: started docs as self.
14. documenter: Docs written for criterion 6. I changed one file, and I did not run `make check`, because only a document changed (the factory's checks decide).

    Changed:
    - `docs/project-guide/processes-and-checks.md`: a new paragraph right after the umask paragraph, which is the passage on the tests' `tests/conftest.py` setup. It says the autouse fixture `without_agent_login` removes `CLAUDE_CODE_OAUTH_TOKEN` and `ANTHROPIC_API_KEY` from every test through `monkeypatch.delenv`, and names the two constants it takes from `factory.adapters.agent_launch`. It gives the three reasons: an agent's run holds the variables, a child process with the process's own environment inherits them, and an assertion message prints what it compares. It says a test may still set either name with `monkeypatch.setenv`, and that an assertion about an environment compares `set(environment)`, never the mapping. It points to `tests/test_no_agent_login.py`.

    Cross-read against the diff (`tests/conftest.py`, the version test's last assertion, the new test module; nothing under `src/` changed) and found current: `README.md`, `docs/operator-guide.md` and `docs/decisions.md`. The story's docs criterion says none for them, because no behaviour of the factory changes. In `docs/project-guide/processes-and-checks.md`, the passages on the runtimes' `version()` calls and on the project commands' environment still hold. Neither the runtimes nor the commands changed.

    Findings for the coder: none. The code matches the Interface: the fixture removes both names through `monkeypatch.delenv` with names imported from `agent_launch`, and the version test's last assertion is `assert API_LOGIN_VARIABLE not in set(call.environment)`.

    Stale text I saw and did not touch: none.

    `check`: check: green (not run again: passed on tree ca0ddc2bb546 at 2026-10-24T16:24:21Z)
    `secrets`: secrets: green (0.8 s)
    `documents`: documents ok
15. factory: started smoke-test as self.
16. smoke-tester: Smoke test passed with no findings. I ran the one command under `## Smoke test` from the repository root, exactly as written, with both login variables set to `x`.

    Command 1 (`env … uv run pytest tests/test_no_agent_login.py "tests/adapters/test_opencode_runtime_launch.py::test_the_version_is_the_first_word_of_a_call_without_login_words" 2>&1 | tail -1 | sed …`):

    ```
    N passed
    ```

    It met its `Expect:` line: it printed one line, starting with `N passed`, with no `failed` and no `error`.

    Checking the criteria again:
    - Criteria 1 and 3: the smoke test is their started-with-both-set side, and it passed.
    - Criterion 3's assertion text: `tests/adapters/test_opencode_runtime_launch.py:246` reads `assert API_LOGIN_VARIABLE not in set(call.environment)`.
    - Criterion 2's restore side: `tests/conftest.py:68` removes through `monkeypatch.delenv(name, raising=False)`, and the file has no `os.environ.pop` and no `del os.environ`.
    - No criterion is contradicted. I did not re-run criteria 4 and 5 (the full suite and `make check`) here; they rest on the factory's earlier green `make check` on this tree (entries 10 and 14).

    Findings: none.
