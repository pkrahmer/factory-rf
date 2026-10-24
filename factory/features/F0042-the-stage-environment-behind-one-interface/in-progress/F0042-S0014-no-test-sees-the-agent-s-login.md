---
stage: tests
blocked: null
round: 0
attempts: 0
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
